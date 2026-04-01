import subprocess
import os

MAX_DURATION = 300  # 5 minutes

def get_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def split_audio(file_path, output_dir="/tmp"):
    duration = get_duration(file_path)

    if duration <= MAX_DURATION:
        return [file_path]

    print(f"Long audio detected ({duration}s), splitting...")

    output_pattern = f"{output_dir}/chunk_%03d.wav"

    subprocess.run([
        "ffmpeg",
        "-i", file_path,
        "-f", "segment",
        "-segment_time", str(MAX_DURATION),
        "-c", "copy",
        output_pattern
    ])

    chunks = sorted([
        f"{output_dir}/{f}" for f in os.listdir(output_dir)
        if f.startswith("chunk_")
    ])

    return chunks
