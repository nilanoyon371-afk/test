
import asyncio
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.limiter import rate_limit_middleware, rate_limiter

app = FastAPI()
app.middleware("http")(rate_limit_middleware)

@app.get("/")
async def root():
    return {"message": "Hello World"}

client = TestClient(app)

def test_rate_limiter():
    # Clear limiter
    rate_limiter.requests.clear()
    
    print("Testing Rate Limiter...")
    
    # Send 60 requests (allowed)
    for i in range(60):
        response = client.get("/", headers={"X-Forwarded-For": "1.2.3.4"})
        if response.status_code != 200:
            print(f"Request {i+1} failed: {response.status_code}")
            return
            
    print("✅ First 60 requests allowed")
    
    # Send 61st request (should fail)
    response = client.get("/", headers={"X-Forwarded-For": "1.2.3.4"})
    if response.status_code == 429:
        print("✅ Limit enforced (429 Too Many Requests received)")
    else:
        print(f"❌ Limit FAILED. Status: {response.status_code}")

if __name__ == "__main__":
    test_rate_limiter()
