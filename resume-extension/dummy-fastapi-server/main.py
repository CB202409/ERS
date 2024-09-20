from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/")
async def root():
    return {
      "name": "신상범",
      "dateOfBirth": "1992-12-06",
      "email": "abcd@naver.com",
      "address": "서울 강남구 봉은사로",
      "phoneNumber": "010-1234-5678"
      }
  
@app.get("/")
def get_page():
    return FileResponse("dummy-page.html")
    
if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host="127.0.0.1", port=8000)