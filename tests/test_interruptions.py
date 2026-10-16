from lassi_x.interruptions import model_service_interrupted


def test_usage_limit_in_nested_candidate_is_an_interruption() -> None:
    assert model_service_interrupted(
        {
            "candidates": [
                {
                    "diagnostics": [
                        {
                            "gate": "agent",
                            "message": "RuntimeError: HTTP 429: The usage limit has been reached",
                        }
                    ]
                }
            ]
        }
    )
    assert not model_service_interrupted({"status": "crashed", "notes": "CUDA out of memory"})
