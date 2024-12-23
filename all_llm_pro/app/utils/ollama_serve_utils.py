import os

def start_ollama():
    """Ollama 서비스를 시작"""
    os.system("sudo systemctl start ollama")
    print("Ollama 서비스를 시작했습니다.")

def stop_ollama():
    """Ollama 서비스를 중지"""
    os.system("sudo systemctl stop ollama")
    print("Ollama 서비스를 중지했습니다.")