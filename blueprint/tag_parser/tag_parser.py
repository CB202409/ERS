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
                When uploading an HTML file, I would like it to be output in the form of a CSS Selector.
                For example,
                {
                "name":"name"
                "birth":"date of birth"
                "phone":"phone number"
                ...
                }
                I would like it to be output like this.

                And the existing data should be output as is, and only the part where new information is entered should be filled in.
                Please display the missing information as an empty string ("").
                Replace the required information.
                The previously extracted information will be replaced with the new information.

                The new required information is as follows.
                {
                "Name": "Jang Bogo",
                "Phone": "010-1111-1111",
                "Email": "woja@cas.com"
                ...
                }
                You must enter the information as above.
            
    
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
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)