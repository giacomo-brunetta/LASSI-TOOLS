# LLM correctness gate

Configure a separate reviewer at the top level of a run configuration:

```yaml
judge:
  model:
    model: your-reviewer-model
    provider: your-provider
    # Use the same provider/credential options as the other model entries:
    # base_url: https://your-endpoint/v1
    # api_key_env: REVIEWER_API_KEY
    max_tokens: 8192
    turn_timeout_s: 120
    turn_retries: 0
  timeout_s: 180
  max_source_chars: 200000
  instructions: |
    Pay particular attention to boundary conditions and input-dependent behavior.
```

Omit `judge` (or set it to `null`) to retain numerical validation alone.
Choose an independently configured reviewer; a different model from the generator
can reduce shared blind spots, but independence is not enforced.

The order is numerical validation (the mandatory primary workload and every
configured correctness test), then semantic review. Both must pass. The judge
cannot override a failed test. It reviews every numerically passing revision,
including revisions validated during compensation and compatibility repair.

The reviewer receives the task, reference source, explicitly configured
`kernel.context` files, candidate module, tested dataset names, numerical
tolerances, precision policy, and suite report when present. Include relevant
headers and helper definitions in `kernel.context`; dependencies are not collected
automatically. Review input is sent to the configured model provider.

Each review uses a fresh Hermes session with no tools, no long-term memory, and
no generation conversation. Source comments and strings are treated as untrusted
evidence. The review checks algorithm fidelity, input consumption, initialization,
bounds and iteration counts, hardcoded answers and special cases, omitted work,
reference-output reads, and precision policy. These instructions reduce the risk
of misleading reviews; they do not eliminate prompt injection or model mistakes.

## Outcomes

- **Passed:** a completed response explicitly approves, with a nonempty explanation
  and no unresolved findings.
- **Failed:** an explicit rejection with concrete findings blocks acceptance and
  returns an `llm_judge` diagnostic to the existing correction loop. The complete
  numerical suite and review must pass again after repair.
- **Inconclusive:** uncertainty, missing evidence, oversized context, malformed
  response, incomplete turn, provider failure, or timeout blocks acceptance.
  Evaluation raises an infrastructure/review error rather than asking the
  generator to repair code based on unavailable evidence.
- **Not run:** numerical tests failed or did not complete successfully; their
  existing diagnostic remains the feedback.

The judge has its own wall-clock budget, separate from the numerical suite budget.
Model retries remain bounded by that judge budget. Oversized review context fails
closed rather than silently truncating source.

## Artifacts and limits

Each validation attempt writes `judge/report.json`. Reviews also save
`evidence.json`, `system.txt`, and the raw `response.txt` when available.
The report includes the configured model/provider, source and evidence hashes,
verdict, findings, and token/cost usage when returned. Credentials are not copied
into the report. Judge usage is recorded separately; it is not currently added
to candidate generation token totals.

This is a probabilistic source review, not a correctness proof or a performance
gate. It does not execute additional tests, inspect unprovided dependencies,
establish GPU compatibility, or predict GPU timeouts. Use it alongside input
contracts, multiple numerical workloads, and accelerator validation.
