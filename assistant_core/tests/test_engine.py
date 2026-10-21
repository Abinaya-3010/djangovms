"""Run with: python -m unittest discover -s assistant_core/tests -v"""

import unittest

from assistant_core.engine import AssistantEngine
from assistant_core.models import LLMResult, ToolCall, ToolDefinition


class MockLLM:
    def __init__(self, result):
        self.result = result
        self.last_tools = None

    def generate(self, *, message, conversation, tools):
        self.last_tools = tools
        return self.result


class MockHost:
    def __init__(self, tools):
        self.tools = tools

    def get_tools(self):
        return self.tools


class AssistantEngineTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.read_tool = ToolDefinition(
            name="list_rfqs",
            description="List mock RFQs",
            parameters={
                "type": "object",
                "properties": {"status": {"type": "string"}},
                "required": [],
                "additionalProperties": False,
            },
            handler=lambda args, context: self.calls.append(("read", args, context)) or [],
        )
        self.write_tool = ToolDefinition(
            name="create_rfq",
            description="Create a mock RFQ",
            parameters={
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
                "additionalProperties": False,
            },
            handler=lambda args, context: self.calls.append(("write", args, context)) or {
                "id": 123, "title": args["title"]
            },
            requires_confirmation=True,
        )

    def test_plain_message_does_not_call_tools(self):
        engine = AssistantEngine(MockLLM(LLMResult(text="Hello")), MockHost([self.read_tool]))
        response = engine.handle(request_id="r1", conversation_id="c1", message="Hello")
        self.assertEqual(response["type"], "message")
        self.assertEqual(self.calls, [])

    def test_read_tool_runs_after_allowlist_and_schema_validation(self):
        llm = MockLLM(LLMResult(text="Here are the RFQs.", tool_call=ToolCall("list_rfqs", {"status": "Open"})))
        engine = AssistantEngine(llm, MockHost([self.read_tool]))
        response = engine.handle(
            request_id="r2", conversation_id="c1", message="Show open RFQs",
            user_context={"test_user": "mock"},
        )
        self.assertEqual(response["type"], "tool_result")
        self.assertEqual(response["tool"], "list_rfqs")
        self.assertEqual(self.calls[0][0], "read")
        self.assertEqual(llm.last_tools[0]["name"], "list_rfqs")

    def test_unknown_tool_is_rejected(self):
        engine = AssistantEngine(
            MockLLM(LLMResult(tool_call=ToolCall("run_sql", {"query": "DROP TABLE vendors"}))),
            MockHost([self.read_tool]),
        )
        response = engine.handle(request_id="r3", conversation_id="c1", message="do it")
        self.assertEqual(response["error"]["code"], "UNKNOWN_TOOL")
        self.assertEqual(self.calls, [])

    def test_invalid_arguments_are_rejected(self):
        engine = AssistantEngine(
            MockLLM(LLMResult(tool_call=ToolCall("create_rfq", {"title": 7}))),
            MockHost([self.write_tool]),
        )
        response = engine.handle(request_id="r4", conversation_id="c1", message="create it")
        self.assertEqual(response["error"]["code"], "INVALID_TOOL_ARGUMENTS")
        self.assertEqual(self.calls, [])

    def test_write_requires_explicit_confirmation_and_is_single_use(self):
        engine = AssistantEngine(
            MockLLM(LLMResult(text="Create this RFQ?", tool_call=ToolCall("create_rfq", {"title": "Office supplies"}))),
            MockHost([self.write_tool]),
        )
        pending = engine.handle(
            request_id="r5", conversation_id="c1", message="create RFQ",
            user_context={"mock_user": "test"},
        )
        self.assertEqual(pending["type"], "confirmation_required")
        self.assertEqual(self.calls, [])

        completed = engine.confirm(
            request_id="r6", conversation_id="c1",
            confirmation_id=pending["confirmation_id"], approved=True,
        )
        self.assertEqual(completed["type"], "tool_result")
        self.assertEqual(self.calls[0][0], "write")

        replay = engine.confirm(
            request_id="r7", conversation_id="c1",
            confirmation_id=pending["confirmation_id"], approved=True,
        )
        self.assertEqual(replay["error"]["code"], "CONFIRMATION_NOT_FOUND")
        self.assertEqual(len(self.calls), 1)

    def test_confirmation_cannot_be_used_from_another_conversation(self):
        engine = AssistantEngine(
            MockLLM(LLMResult(tool_call=ToolCall("create_rfq", {"title": "Bound context"}))),
            MockHost([self.write_tool]),
        )
        pending = engine.handle(request_id="r11", conversation_id="original", message="create")
        response = engine.confirm(
            request_id="r12", conversation_id="different",
            confirmation_id=pending["confirmation_id"], approved=True,
        )
        self.assertEqual(response["error"]["code"], "CONFIRMATION_CONTEXT_MISMATCH")
        self.assertEqual(self.calls, [])

    def test_rejected_confirmation_does_not_write(self):
        engine = AssistantEngine(
            MockLLM(LLMResult(tool_call=ToolCall("create_rfq", {"title": "Cancelled"}))),
            MockHost([self.write_tool]),
        )
        pending = engine.handle(request_id="r8", conversation_id="c1", message="create")
        response = engine.confirm(
            request_id="r9", conversation_id="c1",
            confirmation_id=pending["confirmation_id"], approved=False,
        )
        self.assertEqual(response["type"], "message")
        self.assertEqual(self.calls, [])

    def test_empty_message_is_rejected(self):
        engine = AssistantEngine(MockLLM(LLMResult(text="unused")), MockHost([]))
        response = engine.handle(request_id="r10", conversation_id="c1", message=" ")
        self.assertEqual(response["error"]["code"], "INVALID_REQUEST")


if __name__ == "__main__":
    unittest.main()
