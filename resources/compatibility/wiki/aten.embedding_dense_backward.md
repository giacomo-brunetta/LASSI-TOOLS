# aten.embedding_dense_backward

- Status: ❌ Unsupported
- Error: Overloaded torch operator invoked from Python failed to match any schema: aten::embedding_dense_backward() is missing value for argument 'indices'. Declaration: aten::embedding_dense_backward(Tensor grad_output, Tensor indices, SymInt num_weights, SymInt padding_idx, bool scale_grad_by_freq) -> Tensor  aten::embedding_dense_backward() is missing value for argument 'indices'. Declaration: aten::embedding_dense_backward.out(Tensor grad_output, Tensor indices, SymInt num_weights, SymInt padding_idx, bool scale_grad_by_freq, *, Tensor(a!) out) -> Tensor(a!)
