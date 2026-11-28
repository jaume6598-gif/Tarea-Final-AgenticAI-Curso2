#!/usr/bin/env bash
set -e

# Gerardo A2A specialist (internal)
python -m uvicorn servidor_a2a:app --host 127.0.0.1 --port 8001 &

# MCP server: suppliers and cold-room temperatures (internal)
python -m uvicorn servidor_mcp:app --host 127.0.0.1 --port 8002 &

# FastAPI + Jaime (public)
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-10000}"
