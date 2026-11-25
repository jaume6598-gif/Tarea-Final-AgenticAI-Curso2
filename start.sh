
#!/usr/bin/env bash
set -e

# Iniciar Gerardo A2A (comunicacion interna)
python -m uvicorn servidor_a2a:app --host 127.0.0.1 --port 8001 &

# Iniciar FastAPI + Jaime (acceso publico)
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-10000}"
