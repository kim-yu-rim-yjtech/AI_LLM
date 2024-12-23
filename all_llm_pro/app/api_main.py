from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel # type: ignore
import uvicorn # type: ignore
from datetime import datetime
import logging
import threading
import pytz

from app.utils.db_import_voice_utils import aws_server
from app.utils.voice_to_text import fetch_file_from_aws, execute_on_mac
from app.utils.listener import listen_for_unchecked_maf_chk
from app.utils.text_cleaning import text_clean
from app.utils.ollama_spelling import spacing_and_spelling
from app.utils.ollama_utils import extract_information
from app.utils.db_update_text_utils import update_processed_status

# 로그 시간대를 KST로 설정하는 Formatter
class KSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        kst = pytz.timezone("Asia/Seoul")
        record_time = datetime.fromtimestamp(record.created, tz=kst)
        return record_time.strftime(datefmt or "%Y-%m-%d %H:%M:%S")

# 로그 설정
def setup_logging():
    handler = logging.StreamHandler()
    formatter = KSTFormatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]  # 기존 핸들러 제거 후 새 핸들러 설정

# FastAPI 앱 생성
app = FastAPI(
    title="Voice Complaint Processing API",
    description="API for processing voice complaints and extracting keywords",
    version="1.0.0"
)

# 전역적으로 logger 선언
setup_logging()
logger = logging.getLogger(__name__)

def process_complaints(ids):
    """
    특정 민원 ID를 처리하는 함수
    """
    
    voice_datas = aws_server()
    
    for maf_idx, file_path in zip(voice_datas['maf_idx'], voice_datas['file_path']):
        try:
            logger.info(f"{'-'*10} [민원 ID: {maf_idx}] 처리 시작 {'-'*10}\n")
            logger.info(f"음성을 텍스트로 변경")
            # 음성 -> 텍스트 변환
            local_temp_dir = "/all_llm_pro/aws_file"
            local_file_path = fetch_file_from_aws(file_path, local_temp_dir)

            voice_to_text_res = execute_on_mac(maf_idx, local_file_path)
            
            logger.info(f"텍스트 데이터 처리 및 키워드 추출")
            # 텍스트 처리 파이프라인
            cleaned_text_res = text_clean(maf_idx, voice_to_text_res)

            spacing_spelling_res = spacing_and_spelling(maf_idx, cleaned_text_res)
            keywords_res = extract_information(maf_idx, spacing_spelling_res)

            logger.info(f"DB 상태 업데이트")
            # DB 업데이트
            update_processed_status(keywords_res)
            logger.info(f"{'-'*10} [민원 ID: {maf_idx}] 처리 완료 {'-'*10}\n")
        except Exception as e:
            logger.error(f"Error processing complaint ID {maf_idx}: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """
    서버가 시작될 때 백그라운드 작업 시작
    """
    logger.info("Application has started. Starting background DB listener...")
    threading.Thread(target=background_listen_and_process, daemon=True).start()
    
def background_listen_and_process():
    """
    데이터베이스 변경 감지 및 민원 처리
    """
    while True:
        try:
            ids = listen_for_unchecked_maf_chk()
            if ids:
                logger.info(f"New complaints detected: {ids}")
                process_complaints([ids])
        except Exception as e:
            logger.error(f"Error in background processing: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting API server...")
    uvicorn.run("app.api_main:app", host="0.0.0.0", port=8888, reload=True)
