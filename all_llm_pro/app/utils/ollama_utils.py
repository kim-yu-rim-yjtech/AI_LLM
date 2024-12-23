import requests
import json
import re

def ensure_list(value):
    """
    입력값이 리스트가 아니면 리스트로 변환하고, 입력값이 None이면 빈 리스트를 반환합니다.
    """
    if value is None:
        return []
    return [value] if not isinstance(value, list) else value

def validate_keywords(original_text, extracted_keywords):
    """
    원문에 포함된 키워드인지 검증합니다.
    모든 키워드(time, location, smell_type, smell_intensity)에 대해 원문에서 명시적으로 존재하는 경우만 반환합니다.
    """
    validated_keywords = {}
    for key, values in extracted_keywords.items():
        if isinstance(values, list):
            # 키워드가 리스트일 경우: 원문에 존재하는 단어만 필터링
            validated_keywords[key] = [val for val in values if val in original_text]
        elif isinstance(values, str):
            # 키워드가 문자열일 경우: 원문에 포함된 경우에만 유지
            validated_keywords[key] = values if values in original_text else None
    return validated_keywords


def extract_information(maf_idx, spacing_spelling_res):
    """
    Ollama API를 호출하여 문장에서 시간, 장소, 냄새 종류, 냄새 장소, 냄새 강도 등을 추출합니다.
    """
    result = {
        'maf_idx': maf_idx, 
        'voice_to_text': spacing_spelling_res['voice_to_text'], 
        'keywords': None
    }
    
    # Ollama API URL
    url = "http://61.37.153.212:11434/api/generate"
    
    # Request payload
    payload = {
        "model": "llama3:70b",
        "temperature": 0.0,  # 완전히 결정적으로 설정
        "top_p": 1.0,       # 확률 분포 전체 사용
        "seed": 42,  # seed 값을 추가하여 결정적 결과를 강제
        "prompt": f"""
            너는 민원 데이터를 사용해 중요한 키워드를 추출하는거야
            문장에서 시간, 장소, 냄새 종류, 냄새 강도를 JSON 형식으로 추출해주세요.
            [문장]: "{spacing_spelling_res['spacing_and_spelling_res']}"

            형식:
            {{
                "time": ["시간표현1", "시간표현2"],
                "location": ["장소"],
                "smell_type": ["냄새종류1", "냄새종류2"],
                "smell_intensity": ["강도표현1", "강도표현2"]
            }}

            규칙:
            1. [시간 추출 규칙]:
            - 문장에서 직접적으로 언급된 시간 표현만 포함.
            - 절대적 시간: "오전 9시", "저녁 7시"
            - 상대적 시간: "퇴근", "아침", "저녁"
            - 문장 내에 복합적으로 표현된 시간도 모두 포함.
            - 추론하지 말 것.
            2. [장소 추출 규칙]:
            - 구체적인 위치나 거주지 정보만 포함.
            - 아파트명, 동, 호수 등 상세 정보 포함.
            - 문장 내 민원인의  위치를 추출
            - 예를 들어 힐스테이트 포항, 아이파크, 오천 힐스테이트 등
            3. [냄새 종류 추출 규칙]:
            - 냄새 종류를 추출
            - 냄새 종류에 대한 발생 위치가 포함되어 있다면 같이 추출
            - 문장 내 냄새 종류와 발생 위치를 추출
            4. [냄새 강도 추출 규칙]:
            - 강도를 나타내는 형용사 또는 부사 표현 포함.
            - 문장 내 냄새 강도를 나타내는 표현을추출
            """
    }

    try:
        # API call
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()  # HTTP 오류 상태 코드 확인
        
        # API 응답 처리
        full_response = ""
        for line in response.iter_lines(decode_unicode=True):
            if line:
                data = json.loads(line)
                full_response += data.get("response", "")
        
        # JSON 포맷을 추출하는 정규 표현식
        json_match = re.search(r'```json\n(.*?)\n```', full_response, re.DOTALL)
        if json_match:
            try:
                # JSON 문자열을 파싱하여 키워드 추출
                keywords = json.loads(json_match.group(1))
                validated_keywords = validate_keywords(spacing_spelling_res['spacing_and_spelling_res'], {
                    'time': ensure_list(keywords.get('time', [])),
                    'location': ensure_list(keywords.get('location', ''))[0],
                    'smell_type': ensure_list(keywords.get('smell_type', [])),
                    'smell_intensity': ensure_list(keywords.get('smell_intensity', []))
                })
                result['keywords'] = validated_keywords
            except json.JSONDecodeError:
                result['keywords'] = {
                    'error': 'Failed to parse JSON',
                    'raw_response': full_response
                }
        else:
            # 만약 JSON이 백틱(```)으로 감싸져 있지 않다면 일반적인 JSON 객체로 시도
            json_match = re.search(r'\{[^}]+\}', full_response)
            if json_match:
                try:
                    keywords = json.loads(json_match.group(0))
                    
                    validated_keywords = validate_keywords(spacing_spelling_res['spacing_and_spelling_res'], {
                        'time': ensure_list(keywords.get('time', [])),
                        'location': ensure_list(keywords.get('location', ''))[0],
                        'smell_type': ensure_list(keywords.get('smell_type', [])),
                        'smell_intensity': ensure_list(keywords.get('smell_intensity', []))
                    })
                    result['keywords'] = validated_keywords
                except json.JSONDecodeError:
                    result['keywords'] = {
                        'error': 'Failed to parse JSON',
                        'raw_response': full_response
                    }
            else:
                result['keywords'] = {
                    'error': 'No JSON found',
                    'raw_response': full_response
                }
        return result
    

    except Exception as e:
        result['keywords'] = {
            'error': str(e)
        }
        return result