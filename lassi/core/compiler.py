from __future__ import annotations

from typing import Union, Optional, Iterable
import subprocess
from enum import Enum
import sys
import shlex
from pathlib import Path

class InvalidLanguage(Exception):
    pass

class Language(Enum):
    C = 'C'
    CPP = 'C++'
    CUDA = 'CUDA'
    OMP = 'OMP'
    HIP = 'HIP'
    SYCL = 'SYCL'

    @staticmethod
    def from_string(s: str) -> "Language":
        s = s.strip().upper()
        for lang in Language:
            if lang.name == s or lang.value.upper() == s:
                return lang
        raise ValueError(f"Unknown language string: {s}")

    @staticmethod
    def _get_extension_map():
        return {
            Language.C: ".c",
            Language.CPP: ".cpp",
            Language.CUDA: ".cu",
            Language.OMP: ".cpp",
            Language.HIP: ".cu",
            Language.SYCL: ".cpp",
        }

    @classmethod
    def from_extension(cls, ext: str) -> "Language":
        ext = ext.lower().strip()
        ext_map = cls._get_extension_map()

        for lang, lang_ext in ext_map.items():
            if lang_ext == ext:
                return lang
        raise ValueError(f"Unknown file extension: {ext}")

    def extension(self) -> str:
        return self._get_extension_map()[self]
 
class Compiler(Enum):
    GCC = "gcc"
    GPP = "g++"
    NVCC = "nvcc"
    CLANG = "clang"
    CLANGPP = "clang++"
    HIPCC = "hipcc"
    DPCPP = "dpcpp"     # SYCL compiler
    ICC = "icc"         # Intel C compiler
    ICPPC = "icpc"      # Intel C++ compiler
    MAKE = "make"
    CGEIST = "cgeist"

    @staticmethod
    def from_string(s: str) -> "Compiler":
        s = s.strip().lower()
        for comp in Compiler:
            if comp.value.lower() == s or comp.name.lower() == s:
                return comp
        raise ValueError(f"Unknown compiler string: {s}")

    @staticmethod
    def _get_language_map():
        return {
            Language.C: [Compiler.GCC, Compiler.CLANG, Compiler.ICC],
            Language.CPP: [Compiler.GPP, Compiler.CLANGPP, Compiler.ICPPC],
            Language.CUDA: [Compiler.NVCC],
            Language.OMP: [Compiler.GPP, Compiler.CLANGPP],
            Language.HIP: [Compiler.HIPCC],
            Language.SYCL: [Compiler.DPCPP],
        }

    @classmethod
    def from_language(cls, lang: Language) -> "Compiler":
        lang_map = cls._get_language_map()
        if lang not in lang_map:
            raise ValueError(f"No compiler mapping for language: {lang}")
        return lang_map[lang][0]  # return the default compiler

    @classmethod
    def list_for_language(cls, lang: Language) -> list["Compiler"]:
        """Return all compilers that support a given language."""
        lang_map = cls._get_language_map()
        if lang not in lang_map:
            raise ValueError(f"No compiler mapping for language: {lang}")
        return lang_map[lang]

class CompilationError(Exception):
    pass

class CompilerTool:
    """
    Helper for compiling source files using a specified compiler and default flags.
    """

    def __init__(
        self,
        compiler: "Compiler",
        kwds: str = "",
        language: Optional["Language"] = None,
    ):
        self.compiler = compiler
        self.default_kwds = kwds
        self.language = language

    @staticmethod
    def from_string(s: str) -> "CompilerTool":
        return CompilerTool(Compiler.from_string(s))
    
    @classmethod
    def from_language(cls, lang: Language) -> "CompilerTool":
        return CompilerTool(Compiler.from_language(lang))
    
    """
    Find torchlib paths
    """
    @classmethod
    def find_torchlib_paths(cls) -> dict[str, Path]:
        result = subprocess.run(
            ["python3", "-c", "import torch; print(torch.__file__)"],
            capture_output=True,
            text=True
        )
        torch_path = Path(result.stdout.strip()).parent
        torch_inc = torch_path / "include"
        torch_api_inc = torch_path / "include" / "torch" / "csrc" / "api" / "include"
        torch_lib = torch_path / "lib"

        return {
            "TORCH_INC": torch_inc,
            "TORCH_API_INC": torch_api_inc,
            "TORCH_LIB": torch_lib
        }

    def get_version(self) -> str:
        # Show compiler version
        return subprocess.run(
            [self.compiler.value, "--version"],
            capture_output=True,
            text=True
        )

    def compile(
        self,
        files: Union[Path, Iterable[Path]],
        kwds: Optional[Union[str, Iterable]] = None,
        include_dirs: Optional[Union[Path, Iterable[Path]]] = None,
        library_dirs: Optional[Union[Path, Iterable[Path]]] = None,
        output_file: Optional[Path] = None
    ) -> Path:

        kwds = kwds if kwds is not None else self.default_kwds

        if isinstance(kwds, (list, tuple, set)):
            kwds = " ".join(str(x) for x in kwds)
        elif not isinstance(kwds, str):
            raise TypeError("kwds must be a string or iterable of strings/numbers")

        # Normalize file paths
        if isinstance(files, (Path, str)):
            files = [Path(files)]
        else:
            files = [Path(f) for f in files]
        
        files = [f.resolve() for f in files]

        if output_file is None:
            output_file = files[0].with_suffix("")  # use first file name without extension
        else:
            output_file = Path(output_file).resolve()

        # Handle include directories
        includes = []
        if include_dirs:
            if isinstance(include_dirs, (Path, str)):
                include_dirs = [include_dirs]
            for d in include_dirs:
                includes.extend(["-I", str(Path(d).resolve())])

        # Handle library directories
        libraries = []
        if library_dirs:
            if isinstance(library_dirs, (Path, str)):
                library_dirs = [library_dirs]
            for d in library_dirs:
                libraries.extend(["-L", str(Path(d).resolve())])

        lang_info = f" for language {self.language.value}" if self.language else ""
        files_str = ", ".join(str(f) for f in files)
        print(f"Compiling {files_str} using {self.compiler.value}{lang_info}...")

        # Build command
        cmd = [self.compiler.value]
        for f in files:
            # If using a C++ compiler but the file is a .c file, force C compilation
            # to avoid name mangling issues with headers that use extern "C"
            if self.compiler in [Compiler.GPP, Compiler.CLANGPP] and f.suffix == ".c":
                cmd.extend(["-x", "c", str(f), "-x", "none"])
            else:
                cmd.append(str(f))

        cmd.extend([
            *includes,
            *libraries,
            *shlex.split(kwds),
            "-o",
            str(output_file),
        ])

        print(f"DEBUG: Executing command: {' '.join(cmd)}", file=sys.stderr)

        # Run compiler
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise CompilationError(f"Compilation failed:\nCommand: {' '.join(cmd)}\nError: {result.stderr}")

        return output_file

COMPILER_FLAGS_DB = {
    "gcc": {
        "optimization": {
            "-O0": "No optimization (best for debugging).",
            "-O2": "Standard optimization (recommended for deployment).",
            "-O3": "Aggressive optimization (may increase binary size).",
            "-Ofast": "Disregard strict standards compliance for speed."
        },
        "debugging": {
            "-g": "Generate debug information.",
            "-Wall": "Enable all common warnings.",
            "-fsanitize=address": "Enable AddressSanitizer (memory error detector)."
        },
        "dialect": {
            "-std=c++17": "Use C++17 standard.",
            "-std=c++20": "Use C++20 standard."
        }
    },
    "nvcc": {
        "gpu_arch": {
            "-arch=sm_70": "Target Volta architecture.",
            "-arch=sm_80": "Target Ampere architecture."
        },
        "optimization": {
            "-O3": "Generate optimized code.",
            "--use_fast_math": "Make use of fast math library."
        }
    },
    "cgeist": {
        "polyhedral": {
            "-raise-scf-to-affine": "Raise loops to affine representation.",
            "-polyhedral-opt": "Enable polyhedral optimizations."
        }
    }
}
