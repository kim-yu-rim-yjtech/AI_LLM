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

def spacing_and_spelling(maf_idx, cleaned_text_res):
    """
    Ollama API를 호출하여 문장에서 띄어쓰기 및 맞춤법 교정을 하는 함수
    """
    result = {
        'maf_idx': maf_idx, 
        'voice_to_text': cleaned_text_res['voice_to_text'], 
        'spacing_and_spelling_res': None
    }
    
    # Ollama API URL
    url = "http://61.37.153.212:11434/api/generate"
    
    # Request payload
    payload = {
        "model": "gemma2",
        "prompt": f"""
        너는 한국어 맞춤법 검사 도우미야. 주어진 문장을 분석하여 맞춤법과 띄어쓰기를 수정해주세요.
        설명은 괜찮고 수정한 문장만 보내주세요.

        문장: "{cleaned_text_res['cleaned_text']}"

        형식:
        "맞춤법 및 띄어쓰기 수정 결과": "맞춤법과 띄어쓰기를 수정한 문장"
        """
    }

    try:
        # API call
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            result['spacing_and_spelling_res'] = {
                'error': f"API Error {response.status_code}: {response.text}"
            }
            return result

        full_response = ""
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    data = json.loads(line)
                    full_response += data.get("response", "")
                except json.JSONDecodeError:
                    continue
        
        # JSON 추출 정규 표현식
        json_match = re.search(r'(?:"맞춤법 및 띄어쓰기 수정 결과": ".*?")', full_response, re.DOTALL)
        if json_match:
            corrected_text = json_match.group(0)
            result['spacing_and_spelling_res'] = corrected_text.split(': ')[1].strip('"')
            
        else:
            result['spacing_and_spelling_res'] = {
                'error': 'No matching corrected text found',
                'raw_response': full_response
            }
        
        return result
    
    except Exception as e:
        result['spacing_and_spelling_res'] = {
            'error': str(e)
        }
        return result
