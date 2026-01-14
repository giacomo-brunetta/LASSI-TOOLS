from __future__ import annotations

from typing import Union, Optional, Iterable
import subprocess
from enum import Enum

import subprocess
import shlex
from pathlib import Path

from pydantic import BaseModel, Field

from enum import Enum


class InvalidLanguage(Exception):
    pass

class Language(Enum):
    C = 'C'
    CPP = 'C++'
    CUDA = 'CUDA'
    OMP = 'OMP'
    HIP = 'HIP'
    SYCL = 'SYCL'
    MLIR = 'MLIR'

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
    POLYGEIST = "polygeist-opt"

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

    def get_version(self) -> str:
        # Show compiler version
        return subprocess.run(
            [self.compiler.value, "--version"],
            capture_output=True,
            text=True
        )

    def compile(
        self,
        file: Path,
        kwds: Optional[Union[str, Iterable]] = None,
        output_file: Optional[Path] = None
    ) -> Path:

        kwds = kwds if kwds is not None else self.default_kwds

        if isinstance(kwds, (list, tuple, set)):
            kwds = " ".join(str(x) for x in kwds)
        elif not isinstance(kwds, str):
            raise TypeError("kwds must be a string or iterable of strings/numbers")

        # Normalize file paths
        file = file.resolve()
        if output_file is None:
            output_file = file.with_suffix("")  # remove extension
        else:
            output_file = output_file.resolve()

        lang_info = f" for language {self.language.value}" if self.language else ""
        print(f"Compiling {file} using {self.compiler.value}{lang_info}...")

        # Build command
        cmd = [
            self.compiler.value,
            str(file),
            *shlex.split(kwds),
            "-o",
            str(output_file),
        ]

        print(f"Compiling with command: {' '.join(cmd)}")

        # Run compiler
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise CompilationError(f"Compilation failed:\n{result.stderr}")

        return output_file
