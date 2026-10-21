# VendorPro Assistant Contract v1

Status: Phase 1 draft. This contract is framework- and host-independent. It does not connect to VendorPro, PostgreSQL, Gemini, or browser speech APIs.

## Principles

- The transport contract is JSON over HTTP so Python, Node.js, and other hosts can integrate.
- The assistant core must not import Django, Quasar, ORM models, or database drivers.
- Tools are explicitly registered by the host adapter. The model cannot provide arbitrary code or SQL.
- Read-only tools may run through a host-provided handler after schema validation. Any tool that changes business data must require a separate explicit confirmation.
- Tool output is untrusted data. The host adapter is responsible for field allowlists and masking sensitive vendor data before returning results.
- Authentication and authorization are intentionally not changed in Phase 1. Do not connect this prototype to real business data.

## Request

```json
{
  "contract_version": "1.0",
  "request_id": "req-example-001",
  "conversation_id": "conv-example-001",
  "message": {
    "role": "user",
    "content": "Show me open RFQs"
  },
  "context": {}
}
```

Required: `contract_version`, `request_id`, `message.role`, and `message.content`. The role must be `user`; content must be a non-empty string. `conversation_id` and `context` are optional. Context must not be treated as authorization proof.

## Response variants

Assistant message:

```json
{
  "contract_version": "1.0",
  "request_id": "req-example-001",
  "conversation_id": "conv-example-001",
  "type": "message",
  "message": { "role": "assistant", "content": "I found 2 open RFQs." }
}
```

Tool result:

```json
{
  "contract_version": "1.0",
  "request_id": "req-example-001",
  "conversation_id": "conv-example-001",
  "type": "tool_result",
  "tool": "list_rfqs",
  "data": [],
  "message": { "role": "assistant", "content": "There are no matching RFQs." }
}
```

Confirmation required:

```json
{
  "contract_version": "1.0",
  "request_id": "req-example-002",
  "conversation_id": "conv-example-001",
  "type": "confirmation_required",
  "confirmation_id": "opaque-one-time-id",
  "action": { "tool": "create_rfq", "arguments": { "title": "Office supplies" } },
  "message": { "role": "assistant", "content": "Please confirm before I create this RFQ." }
}
```

Clarification:

```json
{
  "contract_version": "1.0",
  "request_id": "req-example-003",
  "conversation_id": "conv-example-001",
  "type": "clarification",
  "message": { "role": "assistant", "content": "Which vendor should I use?" }
}
```

Error:

```json
{
  "contract_version": "1.0",
  "request_id": "req-example-004",
  "conversation_id": "conv-example-001",
  "type": "error",
  "error": { "code": "INVALID_REQUEST", "message": "message.content must be a non-empty string" }
}
```

## Confirmation endpoint contract

A future host may expose `POST /assistant/v1/confirm`:

```json
{
  "contract_version": "1.0",
  "request_id": "req-confirm-001",
  "conversation_id": "conv-example-001",
  "confirmation_id": "opaque-one-time-id",
  "approved": true
}
```

The server must bind confirmation IDs to the original user/session, expire them, consume them once, and revalidate authorization and business constraints immediately before execution. A client-supplied user ID or context is not authorization. Phase 1 uses in-memory confirmations only for isolated tests; it is not production persistence.

## Tool definition

A host registers a tool with a stable name, description, JSON Schema-like argument definition, a read/write classification, and a handler. Only registered tools can run. Tool arguments must be objects and must satisfy the declared required fields and supported primitive types. The model must never execute arbitrary SQL or code.

## Speech

Speech-to-text and text-to-speech are client-side input/output adapters. They send/receive the same message contract; speech does not bypass tool validation or write confirmation.

## Provider boundary

The core consumes an `LLMProvider` interface. Gemini is the planned production provider, but Phase 1 tests use a deterministic mock. Gemini credentials must remain server-side and must never be exposed to the browser.

## Phase 1 exclusions

No database connections, migrations, authentication changes, Django routes, Quasar UI, actual Gemini network calls, actual speech calls, or changes to existing VendorPro files.
