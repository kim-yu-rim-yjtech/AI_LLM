from transformers import T5Tokenizer, T5ForConditionalGeneration
import logging

# 모델과 토크나이저를 전역 변수로 한 번만 불러오기
tokenizer = T5Tokenizer.from_pretrained("yurim111/et5-spelling-correction")
model = T5ForConditionalGeneration.from_pretrained("yurim111/et5-spelling-correction")
print("맞춤법 모델과 토크나이저 불러오기 완료!")

logging.basicConfig(level=logging.INFO, format="\t\t[%(asctime)s] - %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
    
def correct_spelling(maf_idx, spacing_text_res):
    text = spacing_text_res['spacing_text']
    
    result = {
        'maf_idx': maf_idx, 
        'voice_to_text': spacing_text_res['voice_to_text'], 
        'spelling_text': None
    }
    
    if not isinstance(text, str):
        return ""
    
    
    try:
        # 문장 단위로 분리
        sentences = text.split('.')
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
        corrected_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # logger.info(f"분리된 문장 '{sentence}' 맞춤법 교정 중...")
            if len(sentence) == 0:
                continue

            
            # 문장별로 맞춤법 교정
            inputs = tokenizer(
                f"맞춤법 교정: {sentence}",
                return_tensors='pt',
                max_length=128,
                truncation=True
            ).to("cpu")
            
            
            # 모델 예측
            outputs = model.generate(
                inputs["input_ids"],
                max_length=128,
                num_beams=3,
                length_penalty=0.6,
                early_stopping=True
            )
            
            corrected_sentence = tokenizer.decode(outputs[0], skip_special_tokens=True)
            corrected_sentences.append(corrected_sentence)
        
        # 교정된 문장들을 다시 합침 (문장 끝에 마침표 추가)
        final_text = " ".join(corrected_sentences)  # 문장 끝에 마침표 추가
        result["spelling_text"] = final_text.strip()
        
        return result
    
    except Exception as e:
        print(f"Error processing text: {text}")
        print(f"Error message: {str(e)}")
        return text  # 에러 발생시 원본 텍스트 반환
