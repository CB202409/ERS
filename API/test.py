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
genai.configure(api_key="")

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
            내가 정보를 주면 태그별로 모아줬으면 좋겠어
            그리고 firstName, lastName도 나누어 주어야하는데 만약에 한글이름이 홍길동이면 홍=firstName, 길=lastName 이야
            그런데 firstName,lastName을 따로 적지않고 이름 만 있는경우는  firstName,lastName을 합쳐서 출력해 줘
            personalInfo는 기본정보, education은 교육정보, certifications는 자격증정보, workExperience는 경력사항이야
            정보가 있는 경우는 CSS Selector 형식으로 나오지않고, 무조건 값이 출력되었으면 좋겠어 
            하지만 값이 없는경우에는 CSS Selector 형식으로 출력이 되었으면 좋겠어
            특히 null은 절대 출력하지말고 빈칸으로 출력해주거나 CSS Selector 형식으로 출력해줘
            빈칸인 경우는 "" 이렇게 출력되거나 비어있었으면 좋겠어
            또한 cetification의 경우 경력이 하나면 cetificatin:[] 이렇게 하나, 
            두개이상이면 {
                            cetification:[],
                            cetification:[]
                } 이런식으로 줄 단위로 나왔으면 좋겠어

            형식은 다음과 같아 

            personalInfo{
                "firstName":"input[name='first-name']",
                "lastName":"input[name='last-name']",
                "dateOfBirth":"input[name='birth date'],
                "age":"input[name='age']",
                "email":"input[name='email']",
                "phoneNumber":"input[name='phone-number']",
                "address":"input[name='address']",
            }
            education":[
            {
                "schoolName":"input[name='schoolName']",
                "major":"input[name='major']",
                "period":"input[name='period']",
                "location":"input[name='location']",
                "gpa":"input[name='gpa']",
                "status":"input[name='status']"
            }
            ],
            "certifications":[{
                "cerificationName":"input[name='certificationName']",
                "acquisitionDate":"input[name='acquisitionDate']",
                "issuingOrganization":"input[name='issuingOrganization']",
                "score":"input[name='score']",
                "category":"input[name='category']"
            }],
            "workExperience":[{
                "companyName":"input[name='companyName']",
                "position":"input[name='position']",
                "employmentPeriod":"input[name='employmentPeriod']",
                "location":"input[name='location']"
            }]
        
            이런 형식으로 출력되었으면 좋겠어 
           
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