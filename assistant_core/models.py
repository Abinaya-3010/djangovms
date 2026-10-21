"""Small, dependency-free contracts for assistant providers and host tools."""

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol, Sequence


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: JsonObject


@dataclass(frozen=True)
class LLMResult:
    """A provider-neutral model result."""

    text: str = ""
    tool_call: ToolCall | None = None
    needs_clarification: bool = False


@dataclass(frozen=True)
class ToolDefinition:
    """A registered host capability; handlers are never supplied by the model."""

    name: str
    description: str
    parameters: Mapping[str, Any]
    handler: Callable[[JsonObject, JsonObject], Any]
    requires_confirmation: bool = False


class LLMProvider(Protocol):
    def generate(
        self,
        *,
        message: str,
        conversation: Sequence[Mapping[str, str]],
        tools: Sequence[Mapping[str, Any]],
    ) -> LLMResult:
        """Return a response or a request to call one registered tool."""
        ...


class HostAdapter(Protocol):
    def get_tools(self) -> Sequence[ToolDefinition]:
        """Return only capabilities intentionally exposed by the host."""
        ...
