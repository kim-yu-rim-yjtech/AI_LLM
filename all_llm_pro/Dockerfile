FROM python:3.8

WORKDIR /all_llm_pro


# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 앱 코드 복사
COPY . .

# 컨테이너 실행 시 uvicorn 실행
CMD ["uvicorn", "app.api_main:app", "--host", "0.0.0.0", "--port", "8888"]