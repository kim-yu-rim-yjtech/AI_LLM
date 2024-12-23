import os
import uuid
from pathlib import Path
import paramiko
from scp import SCPClient
import json
import logging

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# AWS 서버 정보
AWS_SERVER_HOST = "43.200.45.232"  # AWS 서버 IP
AWS_SERVER_USER = "ubuntu"  # AWS 사용자명
AWS_KEY_PATH = "/all_llm_pro/key/bems_aws.pem"

# Mac 서버 정보
MAC_SERVER_HOST = "61.37.153.212"  # 서버 IP 주소
MAC_SERVER_USER = "yjtech_mac_machine"          # Mac 서버 사용자명
MAC_SERVER_KEY = "/all_llm_pro/key/id_rsa"  # Mac 서버 SSH 키 경로

REMOTE_SCRIPT_PATH = "/Users/yjtech_mac_machine/AI/LLM/code/voice_to_text.py"  # Mac 서버의 스크립트 위치
REMOTE_TEMP_DIR = "/Users/yjtech_mac_machine/AI/LLM/data"  # 서버 임시 디렉토리 (파일 저장 없이 작업 수행)

LOCAL_TEMP_DIR = "/all_llm_pro/aws_file"

def fetch_file_from_aws(aws_file_path, local_temp_dir):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        logger.info("Connecting to AWS...")
        private_key = paramiko.RSAKey.from_private_key_file(AWS_KEY_PATH)
        ssh.connect(hostname=AWS_SERVER_HOST, username=AWS_SERVER_USER, pkey=private_key)
        
        # POSIX 경로 사용
        local_temp_path = Path(local_temp_dir) / Path(aws_file_path).name

        # print(f"Downloading file to: {local_temp_path}")
        with SCPClient(ssh.get_transport()) as scp:
            scp.get(aws_file_path, str(local_temp_path))

        logger.info("Connected to AWS server successfully!")
        # print("File downloaded successfully.")
        return local_temp_path
    finally:
        ssh.close()
        
# 로컬 파일 삭제 함수
def delete_local_file(file_path):
    try:
        if Path(file_path).exists():
            Path(file_path).unlink()
            # print(f"Local file deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"Error deleting local file: {e}")


# Mac에서 파일 실행 및 처리 후 로컬 파일 삭제
def execute_on_mac(maf_idx, file_path):
    ssh = paramiko.SSHClient()
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key = paramiko.RSAKey.from_private_key_file(MAC_SERVER_KEY)

        logger.info("Connecting to Mac server...")
        ssh.connect(hostname=MAC_SERVER_HOST, username=MAC_SERVER_USER, pkey=private_key)
        logger.info("Connected to Mac server successfully!")

        temp_file_name = Path(file_path).name
        remote_temp_path = f"{REMOTE_TEMP_DIR}/{temp_file_name}"

        # 파일 업로드
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(file_path, remote_temp_path)

        command = (
            f"export PATH=/opt/homebrew/bin:$PATH && "
            f"/opt/anaconda3/envs/venv-keyword/bin/python {REMOTE_SCRIPT_PATH} "
            f"--maf_idx {maf_idx} --file_path {remote_temp_path}"
        )

        # 명령 실행
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.recv_exit_status()  # Wait for 명령이 완료되기를 기다림

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if "Error" in error or "Exception" in error:
            logger.warning(f"Error during script execution: {error}")
            raise Exception(f"Error during script execution: {error}")
        
        # JSON 형식으로 변환
        try:
            result_dict = json.loads(output.split("\n")[-1])  # 마지막 줄에서 JSON 추출
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            raise Exception("Failed to parse output as JSON")

        return result_dict

    except Exception as e:
        logger.error(f"Error on Mac server: {e}")
        return {'maf_idx': maf_idx, 'voice_to_text': 'Error occurred'}
    
    finally:
        # 로컬 파일 삭제
        delete_local_file(file_path)

        # 원격 파일 삭제
        try:
            # logger.info(f"Deleting remote file: {remote_temp_path}")
            ssh.exec_command(f"rm -f {remote_temp_path}")
        except Exception as e:
            logger.warning(f"Error deleting remote file: {e}")
        finally:
            ssh.close()
