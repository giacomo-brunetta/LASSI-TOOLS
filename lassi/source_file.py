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

        self.compiler_tool = compiler_tool if compiler_tool else CompilerTool(
            Compiler.from_language(self.lang)
        )

    def compile(self, kwds: str = None, output_file: Path = None):
        # Compile the source file using the associated compiler tool
        self.executable = self.compiler_tool.compile(self.full_path, kwds=kwds, output_file=output_file)

    def is_compiled(self):
        # Check whether compilation has produced an executable
        return not self.executable is None

    def execute(self, args: str = "", profiler: Profiler = Timer(), validator : Iterable[FunctionalValidator]|FunctionalValidator = None) -> Report|List[Report]:
        # Execute the compiled binary using ExecTool and optional profiling
        self.exec_tool = ExecTool(
            executable=self.executable,
            arguments=args,
            profiler=profiler)
        
        if validator:
            if type(validator) == FunctionalValidator:
                return self.exec_tool.run(validator = validator)
            else: # list of validators
                passed = 0
                for val in validator:
                    try:
                        self.exec_tool.run(validator = val)
                        passed += 1

                    except Exception as e: 
                        print(e)

                print(f"Passed: {passed} / {len(validator)}")
                return self.exec_tool.get_execution_history()
        else:
            self.exec_tool.run()
            return self.exec_tool.get_last_execution_report()

    def get_last_execution_report(self):
        # Retrieve the execution report from the last execution
        return self.exec_tool.get_last_execution_report() if self.exec_tool else None
    
    def get_execution_history(self):
        # Retrieve the execution report from the last execution
        return self.exec_tool.get_execution_history() if self.exec_tool else None

    def read(self) -> str:
        # Read and return the full contents of the source file
        with open(self.full_path, "r", encoding="utf-8") as f:
            return f.read()

    def write(self, content: str) -> None:
        # Overwrite the source file with the provided content
        with open(self.full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def append(self, content: str) -> None:
        # Append the provided content to the source file
        with open(self.full_path, "a", encoding="utf-8") as f:
            f.write(content)

    def copy(self, file_name : Path = None, folder_path : Path = None) -> "SourceFile":
        # no duplicate
        if file_name is None and folder_path is None:
            stem = self.file_name.stem + "_copy"
            file_name = self.file_name.with_name(stem + self.file_name.suffix)

        new_file =  SourceFile(
            file_name = self.file_name,
            folder_path = self.folder_path,
            lang = self.lang,
            compiler_tool = self.compiler_tool,
        )

        new_file.write(self.read())

        return new_file 

    def __str__(self):
        # String representation for debugging and display
        return self.file_name

    def __repr__(self):
        # Delegate representation to __str__
        return self.__str__()
