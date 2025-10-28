from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)
with client.stream("GET", "/api/news/stream") as resp:
    print("status", resp.status_code)
    iterator = resp.iter_text()
    for _ in range(3):
        chunk = next(iterator)
        print(chunk.strip())
