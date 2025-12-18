#!/usr/bin/env python3
"""
Minimal test of the backend without full dependencies
"""
import os
os.environ['MYSQL_HOST'] = ''
os.environ['MYSQL_USER'] = ''
os.environ['MYSQL_PASSWORD'] = ''

from fastapi import FastAPI
from datetime import datetime
import uvicorn

app = FastAPI(title="Minimal Test API")

@app.get("/")
async def root():
    return {"message": "Hello World", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting minimal test API...")
    uvicorn.run(app, host="127.0.0.1", port=8003)