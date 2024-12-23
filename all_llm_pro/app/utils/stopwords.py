with open("stop_words.txt", "r", encoding="utf-8") as file:
    STOP_WORDS = set(eval(file.read()))  
def remove_stopwords(text):
    """
    텍스트에서 불용어를 제거하는 함수
    """
    text_lst = text.split()
    
    filtered_words = [word for word in text_lst if word not in STOP_WORDS]
    
    cleaned_text = ' '.join(filtered_words)
    
    return cleaned_text
