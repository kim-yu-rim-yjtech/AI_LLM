import psycopg2
from psycopg2 import sql
import pandas as pd    
import logging
import pytz

#  db 연결
def connect_db():
    try:
        conn = psycopg2.connect(
            host = '15.165.7.44',
            database = 'pohang_ai',
            user = 'postgres',
            password = 'yjtech0701!@#'
        )

        return conn
    
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None
    
from datetime import datetime

import json

def update_processed_status(result):
    logging.basicConfig(level=logging.INFO, format="\t\t[%(asctime)s] - %(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    """
    처리 완료된 데이터의 ID 목록과 텍스트 및 키워드를 받아서 DB를 업데이트합니다.

    Args:
        result = {'maf_idx': , 'voice_to_text':, 'keywords': {'location': , 'smell_type':, ..}} 형식의 처리 결과
    """ 
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # 현재 날짜와 시간
        db_timezone = pytz.timezone('Asia/Seoul')  # 데이터베이스 시간대
        now = datetime.now(pytz.UTC).astimezone(db_timezone)

        maf_idx = result['maf_idx']
        mw_detail = result['voice_to_text']
        keywords = result['keywords']  #  {'location': , 'smell_type': , ..}
        
        # mw_address, mw_odor_knd, mw_ocr_date, mw_odor_div 값 추출
        # mw_address = json.dumps(keywords.get('location', []), ensure_ascii=False) if keywords.get('location') else None
        mw_address = keywords.get('location', None)
        mw_odor_knd = json.dumps(keywords.get('smell_type', []), ensure_ascii=False) if keywords.get('smell_type') else None
        mw_ocr_date = json.dumps(keywords.get('time', []), ensure_ascii=False) if keywords.get('time') else None
        mw_odor_div = json.dumps(keywords.get('smell_intensity', []), ensure_ascii=False) if keywords.get('smell_intensity') else None

        # DB 업데이트 쿼리
        update_query = """
        UPDATE mw_audio_analysis
        SET 
            mw_address = %s,
            mw_detail = %s,
            mw_odor_knd = %s,
            mw_ocr_date = %s,
            mw_odor_div = %s,
            maf_chk = TRUE,
            maf_update_date = %s
        WHERE maf_idx = %s;
        """
        
        cursor.execute(update_query, (
            mw_address,
            mw_detail,
            mw_odor_knd,
            mw_ocr_date,
            mw_odor_div,
            now,
            maf_idx
        ))
        
        # 변경 사항 커밋
        conn.commit()
        # logger.info(f"DB 업데이트 완료: {maf_idx}")
        
    except Exception as e:
        print(f"처리 상태 업데이트 중 오류 발생: {e}")
    finally:
        cursor.close()
        conn.close()
