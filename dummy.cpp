#include <torch/torch.h>
#include <torch/script.h>
#include <iostream>
#include <vector>

// 1. The logic you want to compile
namespace user_logic {
    // This is where your custom C++ function will be injected
    at::Tensor my_custom_function(at::Tensor x, at::Tensor y) {
        // Example logic
        auto z = at::matmul(x, y);
        return at::relu(z);
    }
}

// A wrapper module required for tracing
struct Wrapper : torch::nn::Module {
    at::Tensor forward(at::Tensor x, at::Tensor y) {
        return user_logic::my_custom_function(x, y);
    }
};

int main(int argc, char* argv[]) {
    if (argc != 2) { return 1; }
    std::string output_path = argv[1];

    try {
        auto module = std::make_shared<Wrapper>();
        
        // 2. Create dummy inputs to "trace" the C++ execution
        std::vector<torch::jit::IValue> inputs;
        inputs.push_back(torch::ones({3, 3}));
        inputs.push_back(torch::ones({3, 3}));

        // 3. Trace the function
        auto traced_module = torch::jit::trace(
            [](std::vector<torch::jit::IValue> ins) -> torch::jit::IValue {
                Wrapper m;
                return m.forward(ins[0].toTensor(), ins[1].toTensor());
            }, 
            inputs
        );

        // 4. Save the native logic to a .pt file
        traced_module.save(output_path);
        std::cout << "Successfully traced C++ logic to " << output_path << std::endl;

    } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        return -1;
    }
    return 0;
}