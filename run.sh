#!/usr/bin/env bash
# Convenience script for Replit / local dev: starts FastAPI in the
# background, then Streamlit in the foreground.
set -e

uvicorn backend.main:app --host "${BACKEND_HOST:-0.0.0.0}" --port "${BACKEND_PORT:-8000}" &
BACKEND_PID=$!

sleep 2
trap "kill $BACKEND_PID" EXIT

streamlit run app.py --server.port "${STREAMLIT_PORT:-8501}" --server.address 0.0.0.0
