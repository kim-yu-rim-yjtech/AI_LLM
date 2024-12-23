import psycopg2
import select
from datetime import datetime

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

    
def listen_for_unchecked_maf_chk():
    try:
        conn = connect_db()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("LISTEN unchecked_maf_chk;")
        print("Listening for unchecked maf_chk notifications...")

        while True:
            if select.select([conn], [], [], 5) == ([], [], []):
                continue

            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                print(f"새로운 데이터 감지: ID {notify.payload}")
                return notify.payload  # 알림 받은 ID 반환
            
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()