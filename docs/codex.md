# Codex setup and role contracts

Target environment: Codex CLI. The inventory for this task found version
`0.167.0`. Record the version when validating configuration; hosted tools and
future releases can differ.

Codex reads repository instructions from `AGENTS.md`. The files in
`.codex/agents/*.md` are plain role contracts for explicit delegation. They are
not automatically registered merely because they exist. The old
`.codex/settings.json` used another tool's hook and permission syntax and is
archived under `docs/archive/`; do not rely on its enforcement claims.

Native custom roles are declared in `.codex/config.toml` with an
`agents.<name>` table containing `description` and `config_file`. Each role's
config file is TOML. The bootstrap spec covers adding and verifying those
files against the installed CLI. In environments exposing generic delegation
instead, the leader passes the role contract explicitly. If delegation is
unavailable, report that limitation; a second self-check is not independent review.

An intended launch after bootstrap is installed is:

```bash
uv sync --extra dev
./init.sh
codex
```

Example task prompt:

```text
Read AGENTS.md and progress/current.md. Work on feature <name> using the
leader, spec_author, implementer, and reviewer contracts. Present the spec
revision for my approval before implementation. After checks and independent
review pass, open the PR. Do not merge.
```

Use existing authentication and machine permissions. Do not commit credentials
or weaken the sandbox through project defaults. Confirm project trust through
the normal Codex workflow. A role's instruction text is not a filesystem or
network security boundary.

Current official references, checked 2026-11-06:

- [Repository instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)

The official configuration reference describes TOML role declarations and
user-level telemetry routing. Consult the installed CLI as well as the docs
before adopting version-sensitive keys. Local checks and CI provide executable
verification; prompts and stop messages alone do not enforce successful tests.
