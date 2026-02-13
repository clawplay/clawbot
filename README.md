<div align="center">
  <img src="assets/Bai.png" alt="baibo" width="500">
  <h1>baibo: Lightweight Personal AI Assistant with more infrastructure</h1>
</div>

**baibo** is a **lightweight** personal AI assistant built on top of [baibo](https://github.com/HKUDS/baibo). It adds production-grade infrastructure (PostgreSQL + pgvector + pgmq), a hybrid memory system, and multi-channel support while keeping the core agent simple.

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
│       │        │ Memory Layer │                                     │
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

## Quick Start

```bash
# Clone
git clone https://github.com/clawplay/baibo.git
cd baibo

# Install
uv sync

# Configure
uv run baibo onboard

# Start gateway
uv run baibo gateway
```

## Documentation

- **[Memory System](docs/memory_system.md)** - Hybrid memory architecture and storage strategies
- **[Deployment Guide](docs/deploy.md)** - Deployment options and configuration

## License

Based on [baibo](https://github.com/HKUDS/baibo) — see LICENSE for details.
