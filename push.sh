#!/bin/bash
set -ex
cd /Users/ktinega/Documents/edusight-africa
git add -A
git status --short | head -5
git commit -m "refactor: migrate to Next.js frontend, FastAPI backend, and ML pipeline"
git push origin main
