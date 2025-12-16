from pathlib import Path

from lassi.profiler import Timer, MultiProfiler, GPUProfiler, CPUProfiler
from lassi.source_file import SourceFile
from lassi.executer import FunctionalValidator
from typing import Annotated

from lassi.compiler import Compiler, CompilerTool, CompilationError

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import subprocess

import dotenv
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

from openai import AsyncOpenAI


dotenv.load_dotenv()
MODEL_NAME = "openai/gpt-oss-120b"
model = GroqModel(MODEL_NAME)

from pydantic_ai import Agent
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

toolset = FastMCPToolset('http://127.0.0.1:8000/mcp')

agent = Agent(
    model=model,
    instructions=(
        "You are an helpful coding assisstant."
    ),
    toolsets=[toolset]
)

from fastmcp import Client

result = agent.run_sync("Compile and run the C program using the tools. Tell me how much time it takes and how much power is consumed.")
print(result)