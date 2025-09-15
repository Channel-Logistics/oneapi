# Shared fixtures: HTTP client + wait until /health is up.

import os
import time
import pytest
import httpx


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("STORAGE_BASE_URL", "http://localhost:9000")


@pytest.fixture(scope="session")
def client(base_url: str):
    with httpx.Client(base_url=base_url, timeout=20) as c:
        # wait for service to come up (fast retry loop)
        deadline = time.time() + 10
        last_err = None
        while time.time() < deadline:
            try:
                r = c.get("/health")
                if r.status_code == 200:
                    break
            except Exception as e:
                last_err = e
            time.sleep(0.5)
        if last_err:
            # final probe; if it fails, let tests error out with a clear message
            c.get("/health")
        yield c
