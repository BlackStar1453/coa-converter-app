#!/usr/bin/env bash
# Quick launcher for development
cd "$(dirname "$0")"
exec .venv/bin/python -m src.main
