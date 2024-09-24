@echo off
start cmd /k "cd /d .\react && npm run start"
start cmd /k "cd /d .\rag_fastapi && python rag.py"
