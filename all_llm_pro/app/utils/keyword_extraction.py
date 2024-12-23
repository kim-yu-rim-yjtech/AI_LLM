import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import logging
import re
logging.basicConfig(level=logging.INFO, format="\t\t[%(asctime)s] - %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class ModelLoader:
    _instance = None
    _models = {}

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance

    def load_models(self, model_paths):
        """
        여러 모델을 동시에 로딩하고 캐싱하는 메서드
        
        :param model_paths: 모델 경로들의 딕셔너리 
        {
            'location': 'yurim111/bart-location-keyword-finetuning',
            'smell': 'model_path_for_smell',
            'intensity': 'model_path_for_intensity'
        }
        :return: 로딩된 모델들의 딕셔너리
        """
        loaded_models = {}

        for model_type, model_path in model_paths.items():
            # 이미 로딩된 모델이 있다면 캐시에서 반환
            if model_path in self._models:
                loaded_models[model_type] = self._models[model_path]
                continue

            try:
                # 새 모델 로딩
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to("cpu")
                
                # 모델 캐싱
                self._models[model_path] = (tokenizer, model)
                loaded_models[model_type] = (tokenizer, model)
                
                logger.info(f"{model_type} 모델 로딩 완료: {model_path}")

            except Exception as e:
                logger.error(f"{model_type} 모델 로딩 실패: {e}")
                loaded_models[model_type] = None

        return loaded_models

def extract_dates_and_times(text):
    """
    문장에서 다양한 날짜와 시간 형식을 추출하는 함수
    """
    # 날짜 및 시간 패턴 정의
    patterns = [
        # 날짜 패턴
        r"\d{1,2}월 \d{1,2}일",            # 11월 3일
        r"\d{1,2}월",                      # 11월
        r"\d{1,2}일",                      # 3일
        r"\d{1,2}년 \d{1,2}월 \d{1,2}일", # 2023년 11월 3일
        r"\d{1,2}년",                      # 2023년
        # 상대적 날짜 패턴
        r"오늘", r"어제", r"내일", r"모레", r"글피",  # 상대 날짜
        r"\d+일 전", r"\d+일 후",             # 3일 전, 3일 후
        r"\d+개월 전", r"\d+개월 후",         # 3개월 전, 3개월 후
        r"\d+년 전", r"\d+년 후",             # 3년 전, 3년 후

        # 시간 패턴
        r"\d{1,2}시",                      # 3시
        r"\d{1,2}시 \d{1,2}분",            # 3시 15분
        r"\d{1,2}:\d{2}",                  # 03:15
        r"오전 \d{1,2}시",                 # 오전 9시
        r"오후 \d{1,2}시",                 # 오후 3시
        r"새벽 \d{1,2}시",                 # 새벽 2시
        r"정오", r"자정",                  # 정오, 자정

        # 복합 날짜와 시간
        r"\d{1,2}월 \d{1,2}일 \d{1,2}시",     # 11월 3일 3시
        r"\d{1,2}월 \d{1,2}일 오전 \d{1,2}시", # 11월 3일 오전 9시
        r"\d{1,2}월 \d{1,2}일 오후 \d{1,2}시"  # 11월 3일 오후 3시
    ]

    # 패턴 컴파일 및 검색
    combined_pattern = "|".join(patterns)
    matches = re.findall(combined_pattern, text)
    
    unique_matches = set(matches)
    result_str = ", ".join(unique_matches)
    
    return result_str

def extract_keywords(maf_idx, spelling_text_res):
    # 모델 로더 인스턴스 생성 (싱글톤)
    model_loader = ModelLoader()

    # 모델 경로 정의
    model_paths = {
        'location': "yurim111/bart-location-keyword-finetuning",
        'smell': "yurim111/bart-smell-keyword-finetuning"
        # 'intensity': 'intensity_model_path'  # 실제 모델 경로로 대체
    }
    
    # 모든 모델 한 번에 로딩
    loaded_models = model_loader.load_models(model_paths)
    
    # 결과 저장용 딕셔너리
    result = {'maf_idx': maf_idx, 'voice_to_text': None, 'keywords': None}

    text = spelling_text_res['spelling_text']
    try:
        # 1. 장소 모델 추론
        if loaded_models['location']:
            tokenizer, model = loaded_models['location']
            inputs = tokenizer(
                f"키워드 추출: {text}",
                return_tensors = "pt",
                max_length = 128,
                truncation = True
            ).to("cpu")

            outputs = model.generate(
                inputs["input_ids"],
                max_length = 128,
                num_beams = 5,
                length_penalty = 0.7,
                repetition_penalty = 1.2,
                early_stopping = True
            )
            location_result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        else:
            location_result = "모델 로딩 실패"

        # 2. 냄새 모델 추론 
        if loaded_models['smell']:
            tokenizer, model = loaded_models['smell']
            inputs = tokenizer(
                f"키워드 추출: {text}",
                return_tensors = "pt",
                max_length = 128,
                truncation = True
            ).to("cpu")

            outputs = model.generate(
                inputs["input_ids"],
                max_length = 128,
                num_beams = 5,
                length_penalty = 0.7,
                repetition_penalty = 1.2,
                early_stopping = True
            )
            smell_result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        else:
            smell_result = "모델 로딩 실패"

        # 3. 강도 모델 추론 (유사한 방식)
        # if loaded_models['intensity']:
        #     tokenizer, model = loaded_models['intensity']
        #     inputs = tokenizer(
        #         f"키워드 추출: {text}",
        #         return_tensors = "pt",
        #         max_length = 128,
        #         truncation = True
        #     ).to("cpu")

        #     outputs = model.generate(
        #         inputs["input_ids"],
        #         max_length = 128,
        #         num_beams = 5,
        #        length_penalty = 0.7,
        #         repetition_penalty = 1.2,
        #         early_stopping = True
        #     )
        #     intensity_result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # else:
        #     intensity_result = "모델 로딩 실패"

        # 3. 시간 추출
        time_result = extract_dates_and_times(text)
        
        result['maf_idx'] = maf_idx
        result['voice_to_text'] = text
        result['keywords'] = {
            'location': location_result,
            'smell_type': smell_result,
            'time': time_result
            # 'intensity': intensity_result
        }
        
    except Exception as e:
        logger.error(f"Error occurred for maf_idx {maf_idx}: {e}")
        logger.debug(f"Problematic text: {text}")
        result['maf_idx'] = maf_idx
        result['voice_to_text'] = text
        result['keywords'] = {
            'location': "Error",
            'smell_type': "Error",
            'time': "Error"
            # 'intensity': "Error"
        }
    return result