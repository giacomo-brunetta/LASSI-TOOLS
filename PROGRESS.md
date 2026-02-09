# Directions
---

## Skills vs. MCP

| Aspect               | Skills                                 | MCP Server                       |
| -------------------- | -------------------------------------- | -------------------------------- |
| **Description**          | Library of few-shot examples for tasks | Server exposing function calls   |
| **Expandability**        | Easy to expand                         | Harder to expand                 |
| **Input Format**         | Bash shell command (string)            | JSON                             |
| **Flexibility**          | High (free shell usage)                | Rigid                            |
| **Validation**           | None by default                        | Input validated before execution |
| **Environment Handling** | Managed at shell level by the model    | Managed at server level          |
| **Adoption Status**      | Widely used but abandoned by Anthropic | New Anthropic standard           |

---


## Single Agent vs. Multi-Agent

| Aspect                    | Single Agent          | Multi-Agent                             |
| ------------------------- | --------------------- | --------------------------------------- |
| **Implementation Complexity** | Simple                | Harder                                  |
| **Context Handling**         | No inheritance issues | Context inheritance / forgetting issues |
| **Reusability**             | Limited               | High                                    |
| **Context Size**             | Can grow large        | Smaller, scoped contexts                |
| **Model Usage**              | Single model          | Potentially multiple models             |

---

