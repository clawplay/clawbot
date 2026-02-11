<div align="center">
  <img src="logo.png" alt="clawbot" width="500">
  <h1>clawbot: Lightweight Personal AI Assistant with more infrastructure</h1>
</div>

**clawbot** is a **lightweight** personal AI assistant built on top of [Nanobot](https://github.com/HKUDS/nanobot). It adds production-grade infrastructure (PostgreSQL + pgvector + pgmq), a hybrid memory system, and multi-channel support while keeping the core agent simple.

## Architecture

The system is split into three independent layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Channels                                                           │
│  Telegram · WhatsApp · Slack · Discord · Feishu · DingTalk          │
│  Email · QQ · Mochat · OpenAI-Compatible HTTP API                   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ InboundMessage / OutboundMessage
┌──────────────────────────▼──────────────────────────────────────────┐
│  Agent Core                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌────────┐  ┌──────────────────┐  │
│  │ AgentLoop│──│ContextBuilder│──│ Skills │  │    Subagents     │  │
│  └────┬─────┘  └──────┬───────┘  └────────┘  └──────────────────┘  │
│       │               │                                             │
│       │        ┌──────▼───────┐                                     │
│       │        │ Memory Layer │ (see below)                         │
│       │        └──────────────┘                                     │
│       │                                                             │
│  ┌────▼─────────────────────────────────────────────────────────┐   │
│  │ Tools: save_memory · read_memory · update_long_term_memory   │   │
│  │        exec · read_file · write_file · web_search · ...      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│  Infrastructure                                                     │
│  PostgreSQL (pgvector + pgmq) · Embedding API · LLM Providers       │
└─────────────────────────────────────────────────────────────────────┘
```

**Channels** handle protocol-specific I/O (WebSocket, HTTP polling, etc.) and normalize everything into `InboundMessage` / `OutboundMessage` events on the message bus. Adding a new channel requires no changes to the agent or infra.

**Agent Core** runs the LLM tool-use loop, manages sessions, builds context (memory + skills + history), and orchestrates subagents. It is channel-agnostic and infra-agnostic.

**Infrastructure** provides persistence and compute — PostgreSQL for memory storage and job queuing, external embedding APIs for vectorization, and LLM providers (Anthropic, OpenAI, DeepSeek, etc.) via litellm.

## Memory System

clawbot uses a **hybrid memory** architecture combining two storage strategies and two retrieval strategies:

```
                        ┌──────────────────────────────────────┐
  Every turn            │  memory_conversation                 │
  (auto-ingest) ───────►│  raw user + assistant messages       │──┐
                        └──────────────────────────────────────┘  │
                        ┌──────────────────────────────────────┐  │  Semantic
  save_memory()         │  memory_daily                        │  ├─ Search
  (agent-curated) ─────►│  distilled facts, date-partitioned   │──┤  (pgvector)
                        └──────────────────────────────────────┘  │
                        ┌──────────────────────────────────────┐  │
  update_long_term      │  memory_long_term                    │  │
  _memory()       ─────►│  persistent user profile & context   │──┘
  (consolidated)        └──────────────────────────────────────┘
                                        │
                              async embedding worker
                              (pgmq background jobs)
```

### Hybrid Storage

| Strategy | Table | Trigger | Content |
|---|---|---|---|
| **Async full-capture** | `memory_conversation` | Automatic, every turn | Raw dialogue as-is |
| **Active recording** | `memory_daily` | Agent calls `save_memory` | Curated facts & insights |
| **Active recording** | `memory_long_term` | Agent calls `update_long_term_memory` | Consolidated persistent profile |

Auto-ingest captures everything without blocking the response (fire-and-forget). Active recording captures what the agent judges important.

### Hybrid Retrieval

Every incoming user message triggers a **semantic search** (cosine similarity on pgvector embeddings) across all three tables simultaneously. Results are ranked by relevance and injected into the system prompt. The agent can also call `read_memory` for explicit keyword/date-based lookup.

Embeddings are generated **asynchronously** — a pgmq background worker polls the `memory_embedding` queue and writes vectors back to each row. This means writes are never blocked by embedding API latency.

### Backend Options

| | File backend | Postgres backend |
|---|---|---|
| Daily & long-term memory | Markdown files | PostgreSQL tables |
| Conversation auto-ingest | — | pgvector + pgmq |
| Semantic search | — | pgvector cosine similarity |
| Setup | Zero-config | `docker/pg.Dockerfile` |

## Quick Start

```bash
# Clone
git clone https://github.com/clawplay/clawbot.git
cd clawbot

# Install
uv sync

# Configure
uv run nanobot onboard

# Start gateway
uv run nanobot gateway
```

## Supported Channels

| Channel | Protocol | Config key |
|---|---|---|
| Telegram | Bot API (polling) | `channels.telegram` |
| WhatsApp | WebSocket bridge | `channels.whatsapp` |
| Slack | Socket Mode | `channels.slack` |
| Discord | Gateway WebSocket | `channels.discord` |
| Feishu / Lark | WebSocket | `channels.feishu` |
| DingTalk | Stream Mode | `channels.dingtalk` |
| Email | IMAP + SMTP | `channels.email` |
| QQ | botpy SDK | `channels.qq` |
| Mochat | Socket.IO | `channels.mochat` |
| OpenAI-compatible HTTP | REST API | `channels.openapi` |

## License

Based on [Nanobot](https://github.com/HKUDS/nanobot) — see LICENSE for details.
