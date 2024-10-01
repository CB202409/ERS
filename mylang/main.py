from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api_handler import router
from langchain_teddynote import logging

from dotenv import load_dotenv
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":

    load_dotenv()
    logging.langsmith("My-First-API-Like-API")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
