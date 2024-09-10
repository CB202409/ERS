import logging
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import base64
import io
import json
from PIL import Image
import anthropic
import uvicorn
import os


# Project configuration
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

app = FastAPI()
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

def get_mime_type(file_bytes):
    try:
        image = Image.open(io.BytesIO(file_bytes))
        if image.format == 'JPEG':
            return 'image/jpeg'
        elif image.format == 'PNG':
            return 'image/png'
        else:
            return None
    except IOError:
        return None

def process_resume_with_claude(file_bytes):
    file_base64 = base64.b64encode(file_bytes).decode('utf-8')
    mime_type = get_mime_type(file_bytes)
    if not mime_type:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPEG or PNG image.")

    prompt = """
    이력서 이미지에서 다음 JSON 형식에 맞추어 정보를 추출해주세요. 이미지에서 찾을 수 없는 정보는 빈 필드로 남겨두세요. JSON 외의 설명은 하지 말아주세요:

    {
      "personalInfo": {
        "firstName": "First Name",
        "lastName": "Last Name",
        "dateOfBirth": "연-월-일",
        "age": "Age",
        "email": "Email",
        "phoneNumber": "Phone Number",
        "address": "Address"
      },
      "education": [
        {
          "schoolName": "School Name",
          "major": "Major",
          "period": "Period",
          "location": "Location",
          "gpa": "GPA",
          "status": "Status (Graduated/In Progress)"
        }
      ],
      "certifications": [
        {
          "certificationName": "Certification Name",
          "acquisitionDate": "Date Acquired",
          "issuingOrganization": "Issuing Organization",
          "score": "Score (if applicable)",
          "category": "Category (e.g., Language)"
        }
      ],
      "workExperience": [
        {
          "companyName": "Company Name",
          "position": "Position",
          "employmentPeriod": "Employment Period",
          "location": "Location (optional)"
        }
      ]
    }
    """

    try:
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",  # 모델 버전 업데이트
            max_tokens=1000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": file_base64
                            }
                        }
                    ]
                }
            ]
        )
        json_content = json.loads(message.content[0].text)
        return json_content

    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        raise HTTPException(status_code=500, detail=f"Claude API error: {e.message}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to decode JSON response: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("upload_form.html", {"request": request})

@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        result = process_resume_with_claude(file_bytes)
        return JSONResponse(content={"message": "Resume processed successfully", "data": result})
    except HTTPException as e:
        logger.error(f"HTTP exception: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in upload_resume: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
