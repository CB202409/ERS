cd .\rag_fastapi

IF NOT EXIST .venv (
  python -m venv .venv
)

call .venv\Scripts\activate

pip install -r requirements.txt

python rag.py