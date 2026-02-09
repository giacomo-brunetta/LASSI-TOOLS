import torch
import torch_mlir
# Note the specific import for the older API
import torch_mlir.torchscript 

# 1. Load the ScriptModule
model_path = "3mm_model.pt"
module = torch.jit.load(model_path)

# 2. Define inputs
A = torch.randn(16, 16, dtype=torch.float64)
B = torch.randn(16, 16, dtype=torch.float64)
C = torch.randn(16, 16, dtype=torch.float64)
D = torch.randn(16, 16, dtype=torch.float64)

# 3. Use the version-specific API
# In your version, the function is tucked inside .torchscript
tosa_mlir = torch_mlir.torchscript.compile(
    module, 
    [A, B, C, D], # Note: Some versions expect a list of tuples for inputs
    output_type="tosa"
)

# 4. Save to file
output_path = "3mm_tosa.mlir"
with open(output_path, "w") as f:
    f.write(str(tosa_mlir))

print(f"Successfully compiled to TOSA MLIR: {output_path}")