# from utils.install_module_utils import check_and_install_packages
# check_and_install_packages()

from app.utils.db_import_voice_utils import aws_server
from app.utils.voice_to_text import fetch_file_from_aws, execute_on_mac
from app.utils.listener import listen_for_unchecked_maf_chk
from app.utils.text_cleaning import text_clean
# from app.utils.spacing_correction import correct_spacing
# from app.utils.spelling_correction import correct_spelling
from app.utils.ollama_spelling import spacing_and_spelling
from app.utils.ollama_utils import extract_information
from app.utils.db_update_text_utils import update_processed_status

from datetime import datetime
from tqdm import tqdm


def process_complaints(ids):
    """
    특정 민원 ID를 처리하는 함수
    """
    
    _now_time = datetime.now().__str__()
    print(f'[{_now_time}] -------------------------------------------------- 음성 민원 처리 시스템 시작 --------------------------------------------------')

    # 1. 음성 데이터를 텍스트로 변경
    print(f'[{_now_time}] -------------------- 1. 음성 데이터를 텍스트로 변경 --------------------')
    
    # 1.1 DB에서 감지된 음성 데이터 경로 가져와 aws에서 파일 가져오기
    print(f'[{_now_time}] ---- 1.1 음성 데이터 불러오기 시작 ----')
    
    voice_datas = aws_server()  # 결과는 사전({'maf_idx': , 'file_path': })
   
    _now_time = datetime.now().__str__()
    print(f'[{_now_time}] ---- 1.1 음성 데이터 불러오기 완료 ----')
    
    for maf_idx, file_path in zip(voice_datas['maf_idx'], voice_datas['file_path']):
        # 1.2 음성 데이터를 텍스트 데이터로 변경
        print(f'[{_now_time}] ---- 1.2 음성 데이터를 텍스트 데이터로 변경 시작 ----')
        local_temp_dir = "/all_llm_pro/aws_file"
        local_file_path = fetch_file_from_aws(file_path, local_temp_dir)
        voice_to_text_res = execute_on_mac(maf_idx, local_file_path) # 결과는 사전({'maf_idx': , 'voice_to_text': })
        print(" \t\t", voice_to_text_res)
        
        _now_time = datetime.now().__str__()
        print(f'[{_now_time}] ---- 1.2 음성 데이터를 텍스트 데이터로 변경 완료 ----')

        # 2. 민원 데이터 처리
        print(f'[{_now_time}] -------------------- 2. 민원 데이터 처리 --------------------')

        # 2.1 텍스트 처리
        print(f'[{_now_time}] ---- 2.1 텍스트 처리 시작 ----')

        # 2.2 텍스트 클리닝, 띄어쓰기 교정, 맞춤법 교정, 키워드 추출
        print(f'[{_now_time}] ---- 2.2 텍스트 처리 세부 작업 시작 ----')

        print(f' \t\t ---- 2.2.1 텍스트 클리닝 ----')
        cleaned_text_res = text_clean(maf_idx, voice_to_text_res)  # 텍스트 클린 {'maf_idx': maf_idx, 'cleaned_text': None}

        print(f' \t\t ---- 2.2.2 띄어쓰기 및 ㅁ자춤법법 교정 ----')
        spacing_spelling_res = spacing_and_spelling(maf_idx, cleaned_text_res)
        print(" \t\t 맞춤법 교정 결과: ", spacing_spelling_res)
        
        print(f' \t\t ---- 2.2.3 키워드 추출 ----')
        # keywords_res = extract_keywords(maf_idx, spelling_text_res) # 결과는 사전({'maf_idx': , 'voice_to_text':, 'keywords': {'location': , 'smell_type':, ..}})
        keywords_res = extract_information(maf_idx, spacing_spelling_res)
        print(" \t\t 키워드 추출 결과: ", keywords_res)

        _now_time = datetime.now().__str__()
        print(f'[{_now_time}] ---- 2.2 텍스트 처리 세부 작업 완료 ----')

        # 2.3 처리 상태 업데이트
        print(f'[{_now_time}] ---- 2.3 DB 상태 업데이트 시작 ----')
        update_processed_status(keywords_res)
        
        _now_time = datetime.now().__str__()
        print(f'[{_now_time}] ---- 2.3 DB 상태 업데이트 완료 ----')

        print(f'[{_now_time}] -------------------- 2. 민원 데이터 처리 완료 --------------------')

        print(" ===================== 모든 작업이 완료되었습니다. =====================")


def main():
    """
    실시간 음성 민원 감지 및 처리 메인 함수
    """
    _now_time = datetime.now().__str__()
    print(f'[{_now_time}] ==================================== 음성 민원 키워드 추출 시스템 시작 ====================================')

    try:
        # 민원 감지 시작
        while True:
            ids = listen_for_unchecked_maf_chk()
            if ids:
                process_complaints(ids)

    except KeyboardInterrupt:
        print(" ==================================== 음성 민원 키워드 추출 시스템이 종료되었습니다. ====================================")


if __name__ == "__main__":
    main()
