import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from fastapi import FastAPI, File, UploadFile, HTTPException
import json
import tempfile

from fastapi.middleware.cors import CORSMiddleware

# FastAPI 앱 생성
app = FastAPI()

# Google Gemini API 키 설정
genai.configure(api_key="AIzaSyAsPTSBN5PUXbafzKMYLo-H6jwlCf5Am9k")

# 파일을 Gemini에 업로드하는 함수
def upload_to_gemini(file_path, mime_type=None):
    """Gemini에 파일 업로드"""
    file = genai.upload_file(file_path, mime_type=mime_type)
    return file

@app.get("/test")
def analyze_image():
    return "안녕"

# 업로드된 파일을 처리하여 이력서 정보 비교 및 두 프롬프트 처리
@app.post("/test")
async def process_resumes(file1: UploadFile = File(...)):
    temp_file_path_1 = None
    try:
        # 첫 번째 파일을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file_1:
            temp_file_1.write(await file1.read())
            temp_file_path_1 = temp_file_1.name

        # Google Gemini에 파일 업로드
        gemini_file_1 = upload_to_gemini(temp_file_path_1, mime_type=file1.content_type)

        # 첫 번째 프롬프트: HTML 파일에서 CSS Selector 추출
        generation_config_1 = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        model_1 = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config_1,
            system_instruction="""
            해당파일을 올리면 태그별로 모아줬으면 좋겠어
            특히 기본정보인 userInfo{ firstname,lastname,email,phone_number,address,bitrhday,gender...} 는 userInfo객체에 넣을거고
            pageInfo객체도 만들어서 내부에 {edu, persnalInfo, cetificatin ... } 정보를 출력해줬으면 좋겠어
            특히, cetification에는 경력 정보를 넣어줬으면 좋겠어
            그리고 firstname, lastname도 나누어 주어야하는데 만약에 한글이름이 홍길동이면 홍=firstname, 길동=lastname 이야
            그런데 성,이름을 따로 적지않고 이름 만 있는경우는 그대로 name만 출력해 주면돼
            또한 형식은 
            userInfo{
                "FirstName":"input[name='first-name']",
                "LirstName":"input[name='last-name']",
                "dateOfBirth":"input[name='birth date'],
                "age":"input[name='age']",
                "email":"input[name='email']",
                "phoneNumber":"input[name='phone-number']",
                "address":"input[name='address']",
                ...
            }
            pageTagInfo{
               "education":"input[name='education']",
               "personalInfo":"input[name='personal-info']",
                "cetificatin":"input[name='certification']"
                ...
                }
            이런 형식으로 출력되었으면 좋겠어 
            빈칸인 경우는 "" 이렇게 출력되거나 비어있었으면 좋겠어 
            또한 cetification의 경우 경력이 하나면 cetificatin:[] 이렇게 하나, 
            두개이상이면 {
                            cetification:[],
                            cetification:[]
                } 이런식으로 줄 단위로 나왔으면 좋겠어 
            
    
            """
        )

        # 첫 번째 프롬프트 실행
        response_1 = model_1.generate_content(
            [gemini_file_1],
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
            }
        )

        # 응답을 JSON으로 변환
        response_content_1 = response_1.candidates[0].content.parts[0].text
        css_selector_data = json.loads(response_content_1)

       
        # 임시 파일 삭제
        os.remove(temp_file_path_1)

        # 결과 반환
        return {
            "css_selector": css_selector_data,
        }

    except Exception as e:
        if temp_file_path_1 and os.path.exists(temp_file_path_1):
            os.remove(temp_file_path_1)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
