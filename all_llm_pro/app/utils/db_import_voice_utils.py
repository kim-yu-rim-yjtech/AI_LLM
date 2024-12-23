import psycopg2
from psycopg2 import sql
import paramiko
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
    
def load_voice():
    """
    db(mw_audio_analysis)에서 "maf_chk" 표시가 안 된 maf_idx를 찾아서 db(mw_audio_file)의 maf_idx를 찾아
    "maf_save_file_path"를 가져오는 함수
    """
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # 1. "maf_chk"가 표시되지 않은 maf_idx를 가져옴
        import_idx_query = """
        SELECT maf_idx
        FROM mw_audio_analysis
        WHERE maf_chk = FALSE;
        """
        
        cursor.execute(import_idx_query)
        maf_indices = cursor.fetchall()
        # logger.info("\t\t maf_indices:", maf_indices)
        
        if not maf_indices:
            logger.warning("No maf_idx found with maf_chk = NULL")
            return None
        
        # maf_idx 추출
        maf_indices = [row[0] for row in maf_indices]
        
        # 2. maf_idx에 해당하는 mw_audio_file 테이블에서 maf_idx와 maf_save_file_path 가져옴
        
        import_file_path_query = """
        SELECT maf_idx, maf_save_file_path 
        FROM mw_audio_file 
        WHERE maf_idx = %s;
        """
        
        voice_data = []
        for maf_idx in maf_indices:
            cursor.execute(import_file_path_query, (maf_idx,))
            result = cursor.fetchall()
            voice_data.extend(result)

        # maf_save_file_path와 maf_idx 리스트 반환
        if voice_data:
            return [{"maf_idx": row[0], "maf_save_file_path": row[1]} for row in voice_data]
        else:
            logger.warning("No matching maf_idx found in mw_audio_file")
            return None
        
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return None

    finally:
        cursor.close()
        conn.close()
        
def aws_server():
    # AWS EC2 접속 정보
    ec2_host = '43.200.45.232'  # EC2 퍼블릭 IP
    ec2_user = 'ubuntu'  # EC2 사용자 (보통 ec2-user 또는 ubuntu)
    private_key_path = "/all_llm_pro/key/bems_aws.pem"

    # SSH 클라이언트 설정
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    result = {'maf_idx': [], 'file_path': []}  # 결과 저장용 딕셔너리
    
    try:
        # EC2 서버에 접속
        ssh_client.connect(ec2_host, username=ec2_user, key_filename=private_key_path)

        # 데이터베이스에서 반환된 파일 경로 가져오기
        file_data = load_voice()  # 데이터베이스 함수 호출

        if not file_data:
            logger.warning("No file paths found from the database.")
            return None

        for file_info in file_data:
            maf_idx = file_info['maf_idx']
            file_path = file_info['maf_save_file_path']

            # print(f"Checking file for maf_idx: {maf_idx}, path: {file_path}")

            # EC2에서 파일 존재 여부 확인
            command = f'ls {file_path}'
            stdin, stdout, stderr = ssh_client.exec_command(command)

            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if output:  # 파일이 있는 경우
                # logger.info(f"음성 파일 확인: {output}")
                result['maf_idx'].append(maf_idx)
                result['file_path'].append(file_path)
            elif error:  # 오류가 있는 경우
                logger.warning(f"Error for maf_idx {maf_idx}: {error}")
            else:  # 파일이 없는 경우
                logger.warning(f"No file found for maf_idx {maf_idx} at {file_path}")

    except Exception as e:
        logger.error(f"Error occurred during AWS server interaction: {e}")
    finally:
        ssh_client.close()
        
    return result

