import os
import subprocess
import sys
import time
import shutil
import json
from pathlib import Path
import argparse
from moviepy import *

# ============================================================
# STEP 1: Overlay logo watermark on all videos in input folder
# ============================================================
def overlay_logo_on_videos(logo_path, intro_seconds, input_dir, temp_dir):
    input_dir = Path(input_dir)
    logo_path = Path(logo_path)
    temp_dir = Path(temp_dir)

    if not logo_path.exists():
        raise FileNotFoundError(f"Logo file not found: {logo_path}")
    if not input_dir.exists():
        raise FileNotFoundError(f"Videos folder not found: {input_dir}")

    temp_dir.mkdir(parents=True, exist_ok=True)
    processed_files = []

    total_start = time.time()
    for video_file in input_dir.glob("*.*"):
        if video_file.suffix.lower() not in [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"]:
            continue  # skip non-video files

        print(f"\n🔹 Watermarking: {video_file.name}")
        start_time = time.time()

        output_file = temp_dir / video_file.name
        overlay_cmd = [
            "ffmpeg", "-y",
            "-i", str(video_file),
            "-i", str(logo_path),
            "-filter_complex",
            f"[1:v][0:v]scale2ref=w=iw*0.05:h=ow/mdar[logo][base];"
            f"[base][logo]overlay=5:5:enable='gte(t,{intro_seconds})'",
            "-c:a", "copy",
            str(output_file)
        ]
        subprocess.run(overlay_cmd, check=True)

        elapsed = time.time() - start_time
        print(f"✅ Done: {output_file.name} (time: {elapsed:.2f} sec)")
        processed_files.append(str(output_file))

    print(f"\n✅ All videos watermarked. Time taken: {time.time() - total_start:.2f} sec")
    return processed_files

# ============================================================
# STEP 2: Split video
# ============================================================
def _fmt_time(t):
    if isinstance(t, (int, float)):
        return str(t)
    return str(t)

def split_video(input_file, timestamps, temp_dir, crf=18, preset="veryfast"):
    temp_dir = Path(temp_dir); temp_dir.mkdir(parents=True, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(input_file))
    split_files = []

    for i, (start, end) in enumerate(timestamps, 1):
        dur = (end - start) if isinstance(start, (int, float)) and isinstance(end, (int, float)) else None
        if dur is None:
            ss_args = ['-ss', _fmt_time(start)]
            t_args  = ['-to', _fmt_time(end)]
        else:
            ss_args = ['-ss', _fmt_time(start)]
            t_args  = ['-t',  _fmt_time(dur)]

        out = temp_dir / f"{base}_part{i}{ext}"
        cmd = [
            'ffmpeg','-hide_banner','-y',
            '-i', input_file,
            *ss_args, *t_args,
            '-c:v','libx264','-preset',preset,'-crf',str(crf),
            '-c:a','aac','-b:a','192k',
            '-movflags','+faststart',
            '-avoid_negative_ts','make_zero',
            '-map_chapters', '-1', 
            '-map_metadata', '-1',
            str(out)
        ]
        print(f"➡️ Splitting {input_file} ({start} → {end}) -> {out}")
        subprocess.run(cmd, check=True)
        split_files.append(str(out))

    return split_files

# ============================================================
# STEP 3: Prepend intro
# ============================================================
def combine_videos(intro_path, split_path, output_path):
    try:
        intro = VideoFileClip(intro_path)
        split = VideoFileClip(split_path)
        print(f"Intro FPS: {intro.fps}, Split FPS: {split.fps}")
        fps = split.fps or intro.fps
        if fps is None:
            print("Warning: FPS is None for both intro and split videos. Using default FPS of 30.")
            fps = 30.0 
        
        final = concatenate_videoclips([intro, split], method="compose")

        final.fps = fps
        print(f"Final clip FPS after concatenation: {final.fps}")
        if final.fps is None:
            raise ValueError(f"Final clip FPS is None after setting to {fps}")

        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=float(fps),  
            preset="fast",
            threads=4
        )
        print(f"Successfully wrote video to {output_path}")

        intro.close()
        split.close()
        final.close()

    except Exception as e:
        print(f"Error in combine_videos: {str(e)}")
        raise

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline: watermark → split → intro")
    parser.add_argument("--input_dir", default="inputs/videos", help="Folder with input videos")
    parser.add_argument("--logo", required=True, help="Path to logo image")
    parser.add_argument("--intro_seconds", type=int, default=0, help="Delay before showing logo")
    parser.add_argument("--intro_video", required=True, help="Intro video to prepend")
    parser.add_argument("--output_dir", default="outputs", help="Final outputs folder")
    parser.add_argument("--temp_dir", default="temp", help="Temporary working folder")
    parser.add_argument(
    "--splits",
    type=str,
    required=True,
    help=(
            "JSON string of split ranges, e.g. '[[10,300],[300,600]]'. "
            "Each start-end pair can be in seconds (e.g., 120) or HH:MM:SS format (e.g., '00:02:00'). "
            "Example: '[[\"00:00:10\",\"00:05:00\"],[300,600]]' "
            "– multiple splits separated as list of pairs."
        )
    )

    args = parser.parse_args()

    # Parse splits JSON
    try:
        splits = json.loads(args.splits)
        if not isinstance(splits, list) or not all(isinstance(r, list) and len(r) == 2 for r in splits):
            raise ValueError
    except Exception:
        print("[ERROR] --splits must be a JSON list of [start,end] pairs")
        sys.exit(1)

    # Step 1: Watermark
    watermarked_files = overlay_logo_on_videos(args.logo, args.intro_seconds, args.input_dir, args.temp_dir)

    all_final_outputs = []
    # Step 2: Split + Step 3: Prepend intro
    for wm_file in watermarked_files:
        split_files = split_video(wm_file, splits, args.temp_dir)
        for split_file in split_files:
            base = os.path.splitext(os.path.basename(split_file))[0]
            output_file = os.path.join(args.output_dir, f"{base}_final.mp4")
            combine_videos(args.intro_video, split_file, output_file)
            all_final_outputs.append(output_file)

    # Cleanup
    if Path(args.temp_dir).exists():
        shutil.rmtree(args.temp_dir)
        print(f"\n🧹 Cleaned up temporary folder: {args.temp_dir}")

    print("\n🎉 Pipeline complete! Final videos:")
    for f in all_final_outputs:
        print(f)

#python3 process-video-1.py --logo inputs/logo.png --intro_video inputs/pre-video.mp4  --splits '[[10,300],[300,600]]'