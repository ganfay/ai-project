import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def prepare_transcript_for_llm(transcript_path: str) -> str:
    """
    Чистим транскрипт от мусора. Оставляем только время и текст.
    """
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    segments = data.get("segments", [])
    
    clean_text = ""
    for seg in segments:
        start = round(seg.get("start", 0), 2)
        end = round(seg.get("end", 0), 2)
        text = seg.get("text", "").strip()
        clean_text += f"[{start} - {end}] {text}\n"
        
    return clean_text

def generate_edit_plan(clean_transcript: str) -> str:
    
    print("Думаем над монтажом...")
    
    system_prompt = """
    Ты профессиональный режиссер монтажа. У тебя есть 2 камеры:
    - "camera_a": показывает лицо спикера (используй для вступления, заключения и эмоций).
    - "camera_b": показывает экран/проект (используй, когда спикер объясняет технические детали или говорит 'посмотрите сюда', 'вот код' и т.д.).

    Я дам тебе транскрипт с таймкодами. Твоя задача - нарезать видео, переключаясь между камерами.
    
    ВЕРНИ ТОЛЬКО ВАЛИДНЫЙ JSON в таком формате:
    {
      "segments": [
        {
          "start": 0.0,
          "end": 2.5,
          "source": "camera_a",
          "reason": "Спикер здоровается"
        },
        ...
      ]
    }
    Правила:
    1. Сегменты должны идти строго по порядку.
    2. Конец предыдущего сегмента должен быть началом следующего (без дыр).
    3. Не добавляй никаких рассуждений вне JSON.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Вот транскрипт:\n{clean_transcript}"}
        ],
        response_format={"type": "json_object"}, 
        temperature=0.2 
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    INPUT_TRANSCRIPT = "transcript.json"
    OUTPUT_PLAN = "edit_plan.json"
    
    if not os.path.exists(INPUT_TRANSCRIPT):
        print(f"Не найден файл {INPUT_TRANSCRIPT}!")
        exit(1)
        
    clean_text = prepare_transcript_for_llm(INPUT_TRANSCRIPT)
    print("Очищенный транскрипт:")
    print(clean_text)
    print("-" * 30)
    
    plan_json_str = generate_edit_plan(clean_text)
    
    with open(OUTPUT_PLAN, "w", encoding="utf-8") as f:
        plan_dict = json.loads(plan_json_str)
        json.dump(plan_dict, f, ensure_ascii=False, indent=2)
        
    print(f"План монтажа успешно сохранен в {OUTPUT_PLAN}")