import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from fastapi import FastAPI, File, UploadFile, HTTPException
import json
import tempfile

from fastapi.middleware.cors import CORSMiddleware

# FastAPI 앱 생성
app = FastAPI()

# # CORS 설정 (모든 도메인 허용)
# origins = ["*"]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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

# 업로드된 두 개의 파일을 처리하여 이력서 정보 비교
@app.post("/test")
async def process_resumes(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    temp_file_path_1 = None
    temp_file_path_2 = None
    try:
        # 첫 번째 파일을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file_1:
            temp_file_1.write(await file1.read())
            temp_file_path_1 = temp_file_1.name

        # 두 번째 파일을 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file_2:
            temp_file_2.write(await file2.read())
            temp_file_path_2 = temp_file_2.name

        # Google Gemini에 두 파일을 업로드
        gemini_file_1 = upload_to_gemini(temp_file_path_1, mime_type=file1.content_type)
        gemini_file_2 = upload_to_gemini(temp_file_path_2, mime_type=file2.content_type)

        # 모델 설정 및 생성
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction="""
                두가지의 .html파일을 비교할거야 
                거기서 출력되는건 비슷하거나 같은값 끼리 묶을거야
                key:value 값으로 출력을 받을건데 중요한건 key:key 값으로 출력을 보내고싶어
                value값은 안나와도 되고 비슷한 key값이 있으면 그걸 받을거야 
                이걸 json형식으로 받고싶어 예를들어
                공통json{
                "사람인name": "잡코리아name",
                "사람인email": "잡코리아email",
                "사람인phone": "잡코리아mobile",
                "사람인address": "잡코리아address",
                "사람인birth": "잡코리아birth_date",
                "사람인career": "잡코리아career",
                "사람인resume_title": "잡코리아resume_title",
                "사람인major": "잡코리아major",
                "사람incompany": "잡코리아company",
                "사람인job_title": "잡코리아position",
                "사람인experience": "잡코리아experience"
                }
                이런식으로 출력을 받고싶어 한가지의 html파일만 내보내지말고 내가 보내준 
            """
        )

        # Gemini API를 호출하여 이력서 정보를 추출
        response = model.generate_content(
            [gemini_file_1, gemini_file_2],
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
            }
        )

        # 응답 데이터를 JSON으로 변환
        response_content = response.candidates[0].content.parts[0].text
        extracted_resume_data = json.loads(response_content)

        # 임시 파일 삭제
        os.remove(temp_file_path_1)
        os.remove(temp_file_path_2)

        return extracted_resume_data

    except Exception as e:
        if temp_file_path_1 and os.path.exists(temp_file_path_1):
            os.remove(temp_file_path_1)
        if temp_file_path_2 and os.path.exists(temp_file_path_2):
            os.remove(temp_file_path_2)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)