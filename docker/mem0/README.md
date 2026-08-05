# Self-hosted Mem0 for LASSI-X agent memory

This compose stack runs the open-source [Mem0](https://github.com/mem0ai/mem0)
server locally so LASSI-X agents (planner, candidates, compensation) can store
and recall long-term memories across runs through the Hermes
[mem0 memory provider](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers#mem0).

## Start the stack

```bash
cd docker/mem0
cp .env.example .env      # set OPENAI_API_KEY (used server-side by Argo)
docker compose up -d --build
curl -s http://localhost:8888/docs >/dev/null && echo "mem0 is up"
```

The checked-in example points the OpenAI client at Argo and selects
`text-embedding-3-large`, whose 3072-dimensional output is matched explicitly
by the pgvector collection. If you select another embedding model, update
`MEM0_DEFAULT_EMBEDDING_DIMS` before creating the collection; an existing
collection cannot mix vector dimensions.

The extraction model is `GPT-5-mini`; Argo model names are case-sensitive, so
do not replace this with Mem0's lowercase upstream default. Its extraction
temperature is set to `1`, the only value this model accepts through Argo.

Because pgvector's HNSW index for the `vector` type is limited to 2000
dimensions, this large-model configuration uses exact search
(`MEM0_PGVECTOR_HNSW=false`). For a large memory corpus where indexed search
matters more than embedding quality, use `text-embedding-3-small`, 1536
dimensions, and enable HNSW.

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
