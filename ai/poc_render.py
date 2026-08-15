import json
import subprocess
import os

def render_video(plan_path: str, output_path: str):
    print("Читаем план монтажа...")
    with open(plan_path, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    segments = plan.get('segments', [])
    if not segments:
        print("План пуст! Нечего рендерить.")
        return

    sources = {
        "camera_a": 0,
        "camera_b": 1
    }

    filter_complex = []
    concat_inputs = ""

    print("Генерируем заклинание для FFmpeg...")
    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        source_name = seg['source']
        file_idx = sources.get(source_name, 0)

        v_filter = f"[{file_idx}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v{i}]"
        
        a_filter = f"[{file_idx}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]"

        filter_complex.append(v_filter)
        filter_complex.append(a_filter)
        
        concat_inputs += f"[v{i}][a{i}]"

    filter_complex.append(f"{concat_inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]")

    filter_str = ";".join(filter_complex)

    command = [
        "ffmpeg",
        "-y",                   # Перезаписывать файл без спроса
        "-i", "camera_a.mp4",   # Файл с индексом 0
        "-i", "camera_b.mp4",   # Файл с индексом 1
        "-filter_complex", filter_str,
        "-map", "[outv]",       # Берем результат склейки (видео)
        "-map", "[outa]",       # Берем результат склейки (аудио)
        "-c:v", "libx264",      # Надежный кодек для видео
        "-preset", "fast",      # Чтобы не ждать вечность при тесте
        "-c:a", "aac",          # Надежный кодек для аудио
        output_path
    ]

    print(f"Запускаем рендер! (Это может занять от пары секунд до минуты)")
    
    result = subprocess.run(command)
    
    if result.returncode == 0:
        print(f"\n✅ УСПЕХ! Готовое видео сохранено в: {output_path}")
    else:
        print("\n❌ ОШИБКА при рендере! Смотри логи FFmpeg выше.")

if __name__ == "__main__":
    if not os.path.exists("camera_a.mp4") or not os.path.exists("camera_b.mp4"):
        print("Ошибка: не найдены исходники camera_a.mp4 и camera_b.mp4")
        exit(1)
        
    render_video("edit_plan.json", "final_shorts.mp4")