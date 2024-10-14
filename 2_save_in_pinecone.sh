#!/bin/bash
# lawfastapi 디렉토리로 이동
cd ./lawfastapi

# 메시지 출력
echo "Run pinecone_module"

# poetry를 사용하여 Python 스크립트 실행
poetry run python ./pinecone_module/write.py

# 일시 정지
read -p "Press [Enter] key to continue..."