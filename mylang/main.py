from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.websocket_handler import websocket_endpoint
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

app.add_api_websocket_route("/ws", websocket_endpoint)

if __name__ == "__main__":

    load_dotenv()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)