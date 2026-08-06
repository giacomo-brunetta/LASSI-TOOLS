"""LASSI-X: a Hermes-powered scientific translation and compensation arena."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import RunConfig

__all__ = ["RunConfig"]
__version__ = "0.1.0"


def __getattr__(name: str) -> Any:  # noqa: ANN401
    """Resolve top-level exports lazily.

    Importing :class:`RunConfig` eagerly pulls in pydantic, which measurement
    workers do not have. A compensation candidate that calls a helper such as
    ``lassi_x.precision.pairwise_sum`` runs inside the accelerator's own
    environment -- groqflow, where torch is the only shared dependency -- and
    must not be forced to import the configuration stack to reach it.

    Args:
        name: Attribute requested from the package namespace.

    Returns:
        The resolved attribute.

    Raises:
        AttributeError: If the package does not export ``name``.
    """
    if name == "RunConfig":
        from .config import RunConfig  # noqa: PLC0415  (deferred on purpose)

        return RunConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
