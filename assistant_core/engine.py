"""Provider-neutral orchestration with allowlisted tools and explicit write confirmation."""

from __future__ import annotations

import secrets
from typing import Any, Mapping, Sequence

from .models import HostAdapter, LLMProvider, ToolDefinition


CONTRACT_VERSION = "1.0"


class AssistantEngine:
    """Orchestrate model output without importing a host framework or database."""

    def __init__(self, llm: LLMProvider, host: HostAdapter) -> None:
        self._llm = llm
        self._host = host
        # In-memory only: appropriate for unit tests, not production multi-worker use.
        self._pending: dict[str, tuple[ToolDefinition, dict[str, Any], dict[str, Any]]] = {}

    def handle(
        self,
        *,
        request_id: str,
        conversation_id: str,
        message: str,
        conversation: Sequence[Mapping[str, str]] = (),
        user_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = user_context or {}
        if not isinstance(message, str) or not message.strip():
            return self._error(request_id, conversation_id, "INVALID_REQUEST",
                               "message must be a non-empty string")

        tools = list(self._host.get_tools())
        result = self._llm.generate(
            message=message,
            conversation=conversation,
            tools=[self._public_tool(tool) for tool in tools],
        )
        base = {
            "contract_version": CONTRACT_VERSION,
            "request_id": request_id,
            "conversation_id": conversation_id,
        }

        if result.needs_clarification:
            return {
                **base,
                "type": "clarification",
                "message": {"role": "assistant", "content": result.text},
            }

        if result.tool_call is None:
            return {
                **base,
                "type": "message",
                "message": {"role": "assistant", "content": result.text},
            }

        tool = next((item for item in tools if item.name == result.tool_call.name), None)
        if tool is None:
            return self._error(request_id, conversation_id, "UNKNOWN_TOOL",
                               "The requested tool is not registered")

        validation_error = self._validate_arguments(
            result.tool_call.arguments, tool.parameters
        )
        if validation_error:
            return self._error(request_id, conversation_id, "INVALID_TOOL_ARGUMENTS",
                               validation_error)

        args = dict(result.tool_call.arguments)
        if tool.requires_confirmation:
            confirmation_id = secrets.token_urlsafe(24)
            self._pending[confirmation_id] = (tool, args, dict(context))
            return {
                **base,
                "type": "confirmation_required",
                "confirmation_id": confirmation_id,
                "action": {"tool": tool.name, "arguments": args},
                "message": {
                    "role": "assistant",
                    "content": result.text or "Please confirm before I make this change.",
                },
            }

        try:
            data = tool.handler(args, context)
        except Exception:
            return self._error(request_id, conversation_id, "TOOL_FAILED",
                               "The requested operation could not be completed")
        return {
            **base,
            "type": "tool_result",
            "tool": tool.name,
            "data": data,
            "message": {"role": "assistant", "content": result.text},
        }

    def confirm(
        self,
        *,
        request_id: str,
        conversation_id: str,
        confirmation_id: str,
        approved: bool,
    ) -> dict[str, Any]:
        base = {
            "contract_version": CONTRACT_VERSION,
            "request_id": request_id,
            "conversation_id": conversation_id,
        }
        pending = self._pending.pop(confirmation_id, None)
        if pending is None:
            return self._error(request_id, conversation_id, "CONFIRMATION_NOT_FOUND",
                               "This confirmation is invalid, expired, or already used")
        if not approved:
            return {
                **base,
                "type": "message",
                "message": {"role": "assistant", "content": "Action cancelled."},
            }

        tool, args, context = pending
        try:
            data = tool.handler(args, context)
        except Exception:
            return self._error(request_id, conversation_id, "TOOL_FAILED",
                               "The requested operation could not be completed")
        return {
            **base,
            "type": "tool_result",
            "tool": tool.name,
            "data": data,
            "message": {"role": "assistant", "content": "Confirmed action completed."},
        }

    @staticmethod
    def _public_tool(tool: ToolDefinition) -> dict[str, Any]:
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": dict(tool.parameters),
            "requires_confirmation": tool.requires_confirmation,
        }

    @classmethod
    def _validate_arguments(
        cls, arguments: Any, schema: Mapping[str, Any]
    ) -> str | None:
        if not isinstance(arguments, dict):
            return "Tool arguments must be an object"
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        if not isinstance(required, list) or not isinstance(properties, Mapping):
            return "Tool schema is invalid"
        missing = [key for key in required if key not in arguments]
        if missing:
            return "Missing required argument(s): " + ", ".join(map(str, missing))
        if schema.get("additionalProperties") is False:
            extra = [key for key in arguments if key not in properties]
            if extra:
                return "Unexpected argument(s): " + ", ".join(map(str, extra))
        for key, value in arguments.items():
            definition = properties.get(key)
            if definition is None:
                continue
            expected = definition.get("type")
            valid = {
                "string": lambda v: isinstance(v, str),
                "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
                "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
                "boolean": lambda v: isinstance(v, bool),
                "object": lambda v: isinstance(v, dict),
                "array": lambda v: isinstance(v, list),
            }.get(expected)
            if valid and not valid(value):
                return f"Argument '{key}' must be of type {expected}"
        return None

    @staticmethod
    def _error(request_id: str, conversation_id: str, code: str,
               message: str) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "request_id": request_id,
            "conversation_id": conversation_id,
            "type": "error",
            "error": {"code": code, "message": message},
        }
