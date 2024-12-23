import re

def text_clean(maf_idx, voice_to_text_res):
    '''
    텍스트에서 기본적인 전처리 작업을 실행하는 함수
    '''
    result = {
        'maf_idx': maf_idx, 
        'voice_to_text': voice_to_text_res['voice_to_text'], 
        'cleaned_text': None
    }
    
    text = voice_to_text_res['voice_to_text']
    
    if not isinstance(text, str):
        text = str(text)  # 문자열이 아닌 경우 변환
        
    # 한글 자음, 모음 제거
    pattern = '([ㄱ-ㅎㅏ-ㅣ]+)'
    text = re.sub(pattern, '', text)
    
    # 특수기호 제거: 점(.), 물음표(?), 쉼표(,)는 제외
    pattern = r'(?<!\d)-|\b(?!\d+-\d)\d+\b|[^\w\s.,?\-]'
    text = re.sub(pattern, '', text)

    # 쉼표가 2개 이상 반복될 경우 하나로 축소
    pattern = r',,{1,}'
    text = re.sub(pattern, ',', text)

    # 중복 공백 제거
    pattern = '\s{2, }'
    text = re.sub(pattern, ' ', text).strip()

    # 줄 바꿈 제거
    pattern = '\n'
    text = re.sub(pattern, '', text)

    # `.이 2개 이상` 제거하는 패턴
    pattern = r'\.{2,}'  # 점(.)이 2개 이상인 경우 제거
    text = re.sub(pattern, '', text)
    
    result['cleaned_text'] = text

    return result
