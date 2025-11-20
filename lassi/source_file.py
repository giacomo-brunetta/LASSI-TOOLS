from pathlib import Path
from lassi.compiler import *
from lassi.executer import *
from lassi.profiler import *


class SourceFile:
    def __init__(self, file_name: Path, folder_path: Path = Path(""), lang: Language = None, compiler_tool: CompilerTool = None):
        # Initialize a SourceFile with paths, language, and compiler settings
        self.file_name = file_name
        self.folder_path = folder_path
        self.full_path = self.folder_path / self.file_name
        self.lang = lang if lang else Language.from_extension(file_name.suffix)
        self.executable = None
        self.exec_tool = None

        if self.lang is None:
            raise InvalidLanguage(f"No supported language has extension {file_name.suffix}")

        self.compiler_tool = compiler_tool if compiler_tool else CompilerTool.from_compiler(
            Compiler.from_language(self.lang)
        )

    def compile(self, kwds: str = None, output_file: Path = None):
        # Compile the source file using the associated compiler tool
        self.executable = self.compiler_tool.compile(self.full_path, kwds=kwds, output_file=output_file)

    def is_compiled(self):
        # Check whether compilation has produced an executable
        return not self.executable is None

    def execute(self, args: str, profiler: Profiler = Timer()) -> Report:
        # Execute the compiled binary using ExecTool and optional profiling
        self.exec_tool = ExecTool(executable=self.executable, arguments=args, profiler=profiler)
        return self.exec_tool.run()

    def get_execution_report(self):
        # Retrieve the execution report from the last execution
        return self.exec_tool.get_execution_report() if self.exec_tool else None

    def read_file(self) -> str:
        # Read and return the full contents of the source file
        with open(self.full_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, content: str) -> None:
        # Overwrite the source file with the provided content
        with open(self.full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def append_to_file(self, content: str) -> None:
        # Append the provided content to the source file
        with open(self.full_path, "a", encoding="utf-8") as f:
            f.write(content)

    def __str__(self):
        # String representation for debugging and display
        return (
            f"Source File:\n"
            f"   file name: {self.file_name},\n"
            f"   folder path: {self.folder_path},\n"
            f"   language:    {self.lang},\n"
            f"   executable:  {self.executable}"
        )

    def __repr__(self):
        # Delegate representation to __str__
        return self.__str__()
