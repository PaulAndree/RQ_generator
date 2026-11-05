# Agent workflow

Choose the applicable parts of this workflow for the requested task. It governs
this repo and can be copied into other repos with their checks and conventions.

- Read-only reviews, explanations, and investigations need no worktree, commit,
  PR, or Greptile run. If an investigation leads to edits, isolate those edits.
- Code changes use isolation, relevant architecture guidance, checks, and
  evidence of the behavior changed. Capture a failure before fixing it.
- Small documentation edits use an isolated branch and relevant content or link
  checks. Do not manufacture runtime evidence or require a bot review for them.
- Ship when the task calls for a PR or a completed repository change. A request
  for a plan, review, or local experiment does not imply publishing it.

## Workflow

1. **Isolate.** Use `/new-feature` before repository edits. Start from
   `origin/main`, or preserve a worktree already assigned to this task.
   Never build on `main`.
2. **Build.** Use `/code-structure` when extracting shared operations or
   choosing boundaries. Follow the project's existing architecture; the
   service layer pattern is a default for projects without a convention.
3. **Prove.** Run relevant checks. Use `/evidence-driven-testing` for changed
   runtime behavior: record the failure before fixing it and the success
   afterward. For documentation, inspect the changed instructions and verify
   runnable examples and links as applicable.
4. **Ship.** Open the PR with evidence appropriate to the change. Use
   `/before-and-after` when screenshots help; use output pairs for CLI changes.
   Run `/greploop` for code or executable workflow changes, or when requested.
   Aim for **5/5 with zero unresolved actionable Greptile findings** on the
   current commit. Stop at the configured iteration cap, a review timeout, or
   an unavailable integration and report the actual score and remaining work.
   Do not claim success or raise the cap automatically. Present the PR URL.

Ship-beat notes:

- `/before-and-after` drives the `@vercel/before-and-after` CLI. `--markdown`
  uploads the pair and prints a PR-ready table; it also accepts existing
  PNGs, so evidence gathered while developing can be reused as-is.
- In containers/VMs where Chrome fails with "No usable sandbox", set
  `AGENT_BROWSER_ARGS="--no-sandbox"` for the capture command.
- The default upload host (0x0.st) is public — fine for ordinary UI shots;
  pass `--upload-url` for anything sensitive.

## Writing for humans

Run `/unslop` over anything a person will read, before you commit, post, or
send it: commit messages, the PR title and body, README and doc edits, code
comments, and the closing reply. It strips AI tells (em dashes, filler,
hedging, chatbot phrases, puffery, bold-label lists) and replaces fancy
words with plain ones and passive voice with active. Apply it to text you
wrote or changed, not to prose you didn't touch.

## Multi-agent rules

- Never commit directly to `main`.
- One worktree and one branch per task and per agent — never reuse or modify
  another agent's worktree, branch, or uncommitted work.
- **Scope check** before starting: skim open PRs' changed files
  (`gh pr list`, `gh pr diff <n> --name-only`) and look for uncommitted work
  in shared checkouts. Inspect overlapping diffs: independent edits to the same
  file may proceed in your own worktree. Ask only when changes conflict in
  behavior, depend on unfinished work, or ownership is unclear. Do not modify
  another task's checkout.
- Never force-push to `main` — and never plain `--force` anywhere; only
  `--force-with-lease`, only on your own task branch.
- Resolve lockfile conflicts by regenerating, never by hand-merging.
- Worktrees don't isolate shared resources: confirm a dev-server port
  answers *your* process before trusting it, and don't run schema
  experiments against a shared database.
- If a conflict can't be resolved confidently, stop and report instead of
  guessing.

## Logging and observability

When creating an application or changing runtime behavior, include
observability appropriate to its complexity use /observability. Follow existing project
conventions and use the observability skill when available.

### Shared infrastructure

- Reuse our shared Grafana instance: http://127.0.0.1:3013/.
- Use our existing metrics backend: Prometheus:	127.0.0.1:9094
- Use our existing logs backend: Loki 127.0.0.1:3101.
- Use the shared Pushgateway for metrics from short-lived batch jobs, Pushgateway: 	127.0.0.1:9095

- Do not deploy separate monitoring stacks for each application.
- Keep endpoints and port mappings in deployment configuration.
- Read credentials from environment variables or the existing secret manager.

### Application instrumentation

- Emit structured logs using the project's logging framework.
- Include service name, environment, severity, and request or trace
  identifiers where applicable.
- For APIs, measure request counts, errors, and latency.
- For background jobs, measure executions, failures, and duration.
- Never log credentials or tokens. Follow project privacy rules for
  user content.

### Dashboards

- Create or update dashboards in the shared Grafana instance.
- Identify telemetry by application and environment.
- Keep dashboard definitions and provisioning configuration in version
  control where supported.

### LLM applications

- Use Langfuse for LLM tracing.
- Configure its endpoint and credentials through environment variables.
- Trace model calls and relevant retrieval or tool steps.
- Capture model name, latency, token usage, and cost when available.
- Make prompt and response capture configurable and follow project
  privacy rules.

### Verification

- Generate a representative request or job execution.
- Verify that the expected logs, metrics, and applicable LLM traces arrive.
- Report what was verified and any unavailable integrations.
- Configure telemetry failures so they do not fail user requests unless
  the project explicitly requires otherwise.

## Completing a task that ships

1. Keep changes limited to the assigned task.
2. Run the applicable checks listed below.
3. Assemble applicable evidence into before/after pairs or content-check results.
4. Commit with a clear message, rebase onto the latest `origin/main`, and
   rerun the checks.
5. Push (`git push -u origin <branch>`; after rebasing an already-pushed
   branch, `--force-with-lease`).
6. Open the PR. The body must explain what changed, how it was tested (every
   claim backed by evidence), before/after proof, and any risks or follow-up
   work. Run the title and body through `/unslop` before posting.
7. Run `/greploop` when applicable, with the success and stopping conditions
   above. `/greploop-apps` selects the alternate trigger in that same workflow.
8. End by presenting the PR URL.

Do not merge the PR unless explicitly instructed. Keep the worktree until
the PR is merged or closed.


## AI and document-processing services

- Use the existing Ollama service for local LLM inference.
- Use the existing OCR and embedding services when required.
- Reuse the project's existing clients and integration patterns.
- Read endpoints and model names from configuration:
  - OLLAMA_BASE_URL=http://localhost:11436
  - CHUNKING_URL=http://localhost:8085
  - OLLAMA_MODEL=qwen3:14b
  - OCR_BASE_URL=http://127.0.0.1:8084
  - EMBEDDING_MODEL=http://127.0.0.1:8089/embed
  
- Verify connectivity before running integration checks.
- Report unavailable services; do not silently substitute another provider.
- Preserve compatibility between embedding models and existing indexes.
  Changing the embedding model may require reindexing.

## Checks in this repo

- `python3 -m pytest tests/ -q` runs the recorder and workflow regression tests.
  Requires Python 3.10+, pytest, ffmpeg and ffprobe with libx264 and the ass filter.
- `git diff --check` checks whitespace in the change.
- For changes to headless capture, run the documented Playwright example in an
  isolated directory and verify its output. Node, npm, and Chromium are needed.
- Validate edited skill frontmatter and local references. The installed
  skill-creator validator does not recognize the existing `compatibility` field;
  report that validator limitation instead of removing useful metadata.

Tests use synthetic recorder input and local API fixtures. They do not prove
native desktop capture on every OS, live uploads, or a live Greptile review.
Keep generated evidence under the ignored `.artifacts/` directory.

## Skill sources

| Skill | Source |
|---|---|
| `new-feature`, `code-structure`, `evidence-driven-testing` | this repo |
| `before-and-after` | this repo, vendored from [vercel-labs/before-and-after](https://github.com/vercel-labs/before-and-after) (or `npx skills add vercel-labs/before-and-after`) |
| `greploop` | this repo, vendored from [greptileai/skills](https://github.com/greptileai/skills) |
| `greploop-apps` | this repo, compatibility entrypoint requiring `greploop` |
| `unslop` | this repo, vendored from [cursor/plugins (pstack)](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop); frontmatter edited so agents apply it unprompted (`disable-model-invocation` dropped, description scoped to text the agent writes or edits for people), body untouched |
