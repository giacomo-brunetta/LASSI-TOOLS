# Self-hosted Mem0 for LASSI-X agent memory

This compose stack runs the open-source [Mem0](https://github.com/mem0ai/mem0)
server locally so LASSI-X agents (planner, candidates, compensation) can store
and recall long-term memories across runs through the Hermes
[mem0 memory provider](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers#mem0).

## Start the stack

```bash
cd docker/mem0
cp .env.example .env      # set OPENAI_API_KEY (used server-side for fact extraction)
docker compose up -d --build
curl -s http://localhost:8888/docs >/dev/null && echo "mem0 is up"
```

Optional web UI for browsing memories:

```bash
docker compose --profile dashboard up -d
open http://localhost:3000
```

## Enable memories in a run

Add a `memory` section to the run YAML (absent or `enabled: false` keeps every
memory layer off — agents then run exactly as before):

```yaml
memory:
  enabled: true
  host: http://localhost:8888
  user_id: lassi-x           # shared memory scope across runs
  # api_key_env: MEM0_API_KEY  # only for servers with AUTH_DISABLED=false
```

Per agent role, memories are attributed via the Mem0 `agent_id` (`planner`,
`c1`…`cN`, `compensation-<variant>`), while `user_id` scopes the shared store.

During the run the harness temporarily sets `memory.provider: mem0` in the
Hermes home `config.yaml` (restored afterwards) and configures each worker
process through `MEM0_*` environment variables. Note: a `mem0.json` in the
Hermes home (written by `hermes memory setup`) overrides those variables —
remove it or use a dedicated `HERMES_HOME` if you have one.

## Verify memories are stored

With `AUTH_DISABLED=true` you can query the REST API directly:

```bash
# All memories for the run scope
curl -s "http://localhost:8888/memories?user_id=lassi-x" | python3 -m json.tool

# Semantic search
curl -s -X POST http://localhost:8888/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "kernel translation strategies", "filters": {"user_id": "lassi-x"}}' \
  | python3 -m json.tool
```

The integration test does the same end-to-end through the Hermes plugin
backend (skipped automatically when the stack is not running):

```bash
pytest -m mem0
```
