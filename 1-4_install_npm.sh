#!/bin/bash

# 스크립트 실행 중 발생하는 모든 오류를 즉시 중단하도록 설정
set -e

# 스크립트의 현재 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 'lawreact' 디렉토리로 이동
PROJECT_DIR="./lawreact"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: 디렉토리 '$PROJECT_DIR'을(를) 찾을 수 없습니다."
    exit 1
fi

cd "$PROJECT_DIR"

# 의존성 설치 메시지 출력
echo "Installing dependencies..."

# npm을 사용하여 의존성 설치 실행 및 오류 처리
if npm install; then
    echo "Dependencies installed successfully."
else
    echo "Error: Failed to install dependencies."
    exit 1
fi

echo "Task completed successfully."