import json
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer
from tqdm import tqdm
import pandas as pd
import re
from difflib import SequenceMatcher
from datetime import datetime

import warnings
warnings.filterwarnings('ignore')

# 모델 정의
tokenizer = AutoTokenizer.from_pretrained("fiveflow/roberta-base-spacing")
model = AutoModelForTokenClassification.from_pretrained("fiveflow/roberta-base-spacing")

# GPU 사용 가능시 GPU 사용
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

# 레이블 정의
label = ["UNK", "PAD", "O", "B", "I", "E", "S"]
    
print("띄어쓰기 모델과 토크나이저 불러오기 완료!")

def correct_spacing(maf_idx, cleaned_text_res):
    
    text = cleaned_text_res['cleaned_text']
    
    result = {
        'maf_idx': maf_idx, 
        'voice_to_text': cleaned_text_res['voice_to_text'], 
        'spacing_text': None
    }


    if not isinstance(text, str):
        return ""
    
    try:
        # 최대 토큰 길이 설정
        max_token_length = 512-2 # CLS와 SEP 토큰을 위한 자리
        
        # 공백 제거된 텍스트
        clean_complaint = text.replace(" ", "")
        correct_spacing_sentences = []
        logits_record = []  # 로짓 저장 리스트 추가
        
        # 512 토큰 단위로 나누기
        for start_idx in range(0, len(clean_complaint), max_token_length):
            chunk = clean_complaint[start_idx:start_idx + max_token_length]
            token_lst = [tokenizer.cls_token_id]
            
            for char in chunk:
                token_lst.extend(tokenizer.encode(char)[1:-1]) # CLS, SEP 토큰 제외
            token_lst.append(tokenizer.sep_token_id)
            
            tkd = torch.tensor(token_lst).unsqueeze(0).to(device)
            
            # 모델 예측
            with torch.no_grad():
                outputs = model(tkd)
                logits = outputs.logits.squeeze(0).cpu().numpy()  # 로짓 저장
                logits_record.append(logits)  # 로짓 기록
                pred_idx = torch.argmax(outputs.logits, dim=-1)
            
            # 예측 결과를 문자열로 변환
            pred_sent = ""
            for char_idx, spc_idx in enumerate(pred_idx.squeeze()[1:-1]):
                if char_idx >= len(chunk): # 인덱스 범위 체크
                    break
                curr_label = label[spc_idx]
                if curr_label in ["E", "S"]:  # E나 S 태그가 있으면 띄어쓰기 추가
                    pred_sent += chunk[char_idx] + " "
                else:
                    pred_sent += chunk[char_idx]
            
            correct_spacing_sentences.append(pred_sent.strip())
            
        # 모든 청크를 다시 합치기
        final_text = " ".join(correct_spacing_sentences)
        result["spacing_text"] = final_text.strip()
        
        return result
        
    except Exception as e:
        print(f"Error processing text: {text}")
        print(f"Error message: {str(e)}")
        return text  # 에러 발생시 원본 텍스트 반환