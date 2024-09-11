import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import google.generativeai as genai
from pydantic import BaseModel

# gemini 세팅
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
  "temperature": 0.2,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  system_instruction="해당파일을 올리면 태그별로 모아줬으면 좋겠어\n특히 기본정보인 userInfo{ firstname,lastname,email,phone_number,address,bitrhday,gender...} 는 userInfo객체에 넣을거고\npageInfo객체도 만들어서 내부에 {edu, persnalInfo, cetificatin ... } 정보를 출력해줬으면 좋겠어\n특히, cetification에는 경력 정보를 넣어줬으면 좋겠어\n그리고 firstname, lastname도 나누어 주어야하는데 만약에 한글이름이 홍길동이면 홍=firstname, 길동=lastname 이야\n그런데 성,이름을 따로 적지않고 이름 만 있는경우는 그대로 name만 출력해 주면돼\n또한 형식은 \npersonalInfo{\n    \"firstName\":\"input[name='first-name']\",\n    \"lastName\":\"input[name='last-name']\",\n    \"dateOfBirth\":\"input[name='birth date'],\n    \"age\":\"input[name='age']\",\n    \"email\":\"input[name='email']\",\n    \"phoneNumber\":\"input[name='phone-number']\",\n    \"address\":\"input[name='address']\",\n    ...\n}\neducation\":[\n{\n    \"schoolName\":\"input[name='schoolName']\",\n    \"major\":\"input[name='major']\",\n    \"period\":\"input[name='period']\",\n    \"location\":\"input[name='location']\",\n    \"gpa\":\"input[name='gpa']\",\n    \"status\":\"input[name='status']\"\n}\n],\n\"certifications\":[{\n    \"cerificationName\":\"input[name='certificationName']\",\n    \"acquisitionDate\":\"input[name='acquisitionDate']\",\n    \"issuingOrganization\":\"input[name='issuingOrganization']\",\n    \"score\":\"input[name='score']\",\n    \"category\":\"input[name='category']\"\n}],\n\"workExperience\":[{\n    \"companyName\":\"input[name='companyName']\",\n    \"position\":\"input[name='position']\",\n    \"employmentPeriod\":\"input[name='employmentPeriod']\",\n    \"location\":\"input[name='location']\"\n}\n이런 형식으로 출력되었으면 좋겠어 \n빈칸인 경우는 \"\" 이렇게 출력되거나 비어있었으면 좋겠어 \n또한 cetification의 경우 경력이 하나면 cetificatin:[] 이렇게 하나, \n두개이상이면 {\n                cetification:[],\n                cetification:[]\n    } 이런식으로 줄 단위로 나왔으면 좋겠어 ",
)

chat_session = model.start_chat(
  history=[
  ]
)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestModel(BaseModel):
    param1: str

@app.get("/")
async def root():
    return {"message": "Hello World"}
  

@app.post("/")
async def tag_parser(request: RequestModel):
    response = chat_session.send_message(request.param1)
    my_json = json.loads(response.text)
    return my_json
    
  
  
  
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="127.0.0.1", port=8001)
    
    