# Diagnostic output policy

Keep displayed diagnostics below 100 lines and approximately 8 KiB per response.
Summarize status, counts, aggregate metrics, and the root failure first. Preserve complete
logs, graphs, numerical samples, histories, and large diffs as artifacts; report their paths.
Inspect further data only through a small indexed slice, selected fields, operator histogram,
or source excerpt chosen to resolve a specific question. Do not dump complete tensors or IR.
Read source in relevant sections and reuse unchanged context already available.
