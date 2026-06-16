#!/usr/bin/env python3
"""Quick health check for a vLLM server running on localhost:8000."""
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"


def get(path):
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as r:
        body = r.read().decode()
        return r.status, json.loads(body) if body.strip() else None


def post(path, payload):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, json.loads(r.read().decode())


def main():
    try:
        status, _ = get("/health")
        print(f"[OK] /health -> {status}")
    except urllib.error.URLError as e:
        print(f"[FAIL] /health unreachable: {e}")
        sys.exit(1)

    status, models = get("/v1/models")
    ids = [m["id"] for m in models.get("data", [])]
    print(f"[OK] /v1/models -> {ids}")
    if not ids:
        print("[FAIL] no models loaded")
        sys.exit(1)

    model = ids[0]
    status, resp = post("/v1/completions", {
        "model": model,
        "prompt": "The capital of France is",
        "max_tokens": 16,
        "temperature": 0.0,
    })
    text = resp["choices"][0]["text"]
    print(f"[OK] /v1/completions -> {text!r}")

    status, resp = post("/v1/chat/completions", {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with the single word: pong"}],
        "max_tokens": 8,
        "temperature": 0.0,
    })
    msg = resp["choices"][0]["message"]["content"]
    print(f"[OK] /v1/chat/completions -> {msg!r}")


if __name__ == "__main__":
    main()
