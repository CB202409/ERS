#!/bin/bash
# lawfastapi 디렉토리로 이동
cd ./lawfastapi

# 로딩 메시지 출력
echo "loading. . . ."

# Poetry를 사용하여 FastAPI 서버 실행
poetry run python app/main.py