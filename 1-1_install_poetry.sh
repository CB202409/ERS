#!/bin/bash

# 스크립트 실행 중 발생하는 모든 오류를 즉시 중단하도록 설정
set -e

# 스크립트의 현재 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 'lawfastapi' 디렉토리로 이동
PROJECT_DIR="./lawfastapi"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: 디렉토리 '$PROJECT_DIR'을(를) 찾을 수 없습니다."
    exit 1
fi

cd "$PROJECT_DIR"

# Poetry 설치 메시지 출력
echo "Poetry를 설치 중입니다..."

# Poetry 설치 실행
if pip install poetry; then
    echo "Poetry 설치가 완료되었습니다."
else
    echo "Error: Poetry 설치에 실패했습니다."
    exit 1
fi

echo "작업이 완료되었습니다."