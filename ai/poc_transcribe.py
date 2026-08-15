import os
import subprocess
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def extract_audio(video_path: str, audio_path: str):
    
    print(f"Извлекаем аудио из {video_path}...")
    
    command = [
        "ffmpeg",
        "-i", video_path,       
        "-vn",                  
        "-acodec", "libmp3lame", 
        "-b:a", "128k",         
        "-y",                   
        audio_path
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Ошибка FFmpeg:\n{result.stderr}")
        raise Exception("Не удалось извлечь аудио")
        
    print(f"Аудио успешно сохранено в {audio_path}")

def transcribe_audio(audio_path: str) -> dict:
    """
    Отправляет аудио в OpenAI Whisper и получает транскрипт с таймкодами.
    """
    print("Отправляем аудио в OpenAI Whisper...")
    
    with open(audio_path, "rb") as audio_file:
        
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            response_format="verbose_json",
        )
    
    return transcript.model_dump()

if __name__ == "__main__":
    INPUT_VIDEO_A = "camera_a.mp4" 

    OUTPUT_AUDIO = "temp_audio.mp3"
    OUTPUT_JSON = "transcript.json"

    if not os.path.exists(INPUT_VIDEO_A):
        print(f"Положи файл {INPUT_VIDEO_A} в папку со скриптом!")
        exit(1)

    try:
        extract_audio(INPUT_VIDEO_A, OUTPUT_AUDIO)
        
        result_data = transcribe_audio(OUTPUT_AUDIO)
        
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
            
        print(f"Готово! Результат сохранен в {OUTPUT_JSON}")
        
    finally:
        if os.path.exists(OUTPUT_AUDIO):
            os.remove(OUTPUT_AUDIO)
            print("Временный аудиофайл удален.")