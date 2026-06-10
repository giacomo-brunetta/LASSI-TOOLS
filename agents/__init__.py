from .analyst import AnalystAgent
from .base import Agent, build_permission_router, render_paths
from .c_optimizer import CCodeOptimizerAgent
from .coder import CoderAgent
from .config_builder import ConfigBuilderAgent
from .dispatch import (
    DispatchBackend,
    get_dispatch_backend,
    set_dispatch_backend,
)
from .model_generator import ModelGeneratorAgent
from .planner import PlannerAgent
from .translator import TranslatorAgent
from .utils import claude_send

AGENT_REGISTRY: dict[str, type[Agent]] = {
    "analyst": AnalystAgent,
    "c-optimizer": CCodeOptimizerAgent,
    "coder": CoderAgent,
    "config-builder": ConfigBuilderAgent,
    "model-generator": ModelGeneratorAgent,
    "planner": PlannerAgent,
    "translator": TranslatorAgent,
}

__all__ = [
    "AGENT_REGISTRY",
    "Agent",
    "AnalystAgent",
    "CCodeOptimizerAgent",
    "CoderAgent",
    "ConfigBuilderAgent",
    "DispatchBackend",
    "ModelGeneratorAgent",
    "PlannerAgent",
    "TranslatorAgent",
    "build_permission_router",
    "claude_send",
    "get_dispatch_backend",
    "render_paths",
    "set_dispatch_backend",
]
