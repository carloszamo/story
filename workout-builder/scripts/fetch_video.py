#!/usr/bin/env python3
"""
Download a workout video (TikTok / Instagram / YouTube) and extract
candidate screenshot frames for reviewing exercise steps.

Usage:
  python3 fetch_video.py <video_url> [--outdir DIR] [--mode scene|interval]
                          [--interval SECONDS] [--scene-threshold FLOAT]
                          [--max-frames N]

Output (written to --outdir, default: ../output/<slug>):
  video.mp4          the downloaded video
  frames/frame_*.jpg  candidate screenshots with timestamps
  manifest.json       metadata + frame list, used by build_page.py
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def slugify(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return (text or "workout")[:max_len]


def check_dependency(name: str, hint: str) -> None:
    if shutil.which(name) is None:
        sys.exit(f"error: '{name}' not found on PATH. {hint}")


def get_video_info(url: str) -> dict:
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--no-playlist", url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"error: yt-dlp failed to read video info:\n{result.stderr.strip()}")
    return json.loads(result.stdout)


def download_video(url: str, dest: Path) -> Path:
    video_path = dest / "video.mp4"
    cmd = [
        "yt-dlp", "--no-playlist",
        "-f", "mp4/bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", str(video_path),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not video_path.exists():
        sys.exit(f"error: yt-dlp failed to download video:\n{result.stderr.strip()}")
    return video_path


def extract_frames_scene(video_path: Path, frames_dir: Path, threshold: float, max_frames: int):
    """Grab one frame per detected scene/cut -- good for edited workout clips."""
    pattern = str(frames_dir / "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr", "-q:v", "3",
        pattern,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    timestamps = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", result.stderr)]
    frame_files = sorted(frames_dir.glob("frame_*.jpg"))
    frames = [
        {"file": f.name, "timestamp": round(ts, 2)}
        for f, ts in zip(frame_files, timestamps)
    ]
    return frames[:max_frames]


def extract_frames_interval(video_path: Path, frames_dir: Path, interval: float, max_frames: int):
    """Grab a frame every `interval` seconds -- reliable fallback."""
    pattern = str(frames_dir / "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"fps=1/{interval}",
        "-q:v", "3",
        pattern,
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    frame_files = sorted(frames_dir.glob("frame_*.jpg"))
    frames = [
        {"file": f.name, "timestamp": round(i * interval, 2)}
        for i, f in enumerate(frame_files)
    ]
    return frames[:max_frames]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", help="TikTok, Instagram, or YouTube video URL")
    parser.add_argument("--outdir", help="output directory (default: workout-builder/output/<slug>)")
    parser.add_argument("--mode", choices=["scene", "interval"], default="scene",
                         help="frame extraction mode (default: scene)")
    parser.add_argument("--interval", type=float, default=2.0,
                         help="seconds between frames in interval mode (default: 2.0)")
    parser.add_argument("--scene-threshold", type=float, default=0.35,
                         help="scene-change sensitivity, lower = more frames (default: 0.35)")
    parser.add_argument("--max-frames", type=int, default=60,
                         help="cap on number of extracted frames (default: 60)")
    args = parser.parse_args()

    check_dependency("yt-dlp", "Install with: pip install yt-dlp")
    check_dependency("ffmpeg", "Install with your OS package manager, e.g. apt-get install ffmpeg")

    print(f"Fetching video info for {args.url} ...")
    info = get_video_info(args.url)

    slug = slugify(info.get("title") or info.get("id") or "workout")
    base = Path(args.outdir) if args.outdir else Path(__file__).resolve().parent.parent / "output" / slug
    frames_dir = base / "frames"
    base.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading video to {base}/video.mp4 ...")
    video_path = download_video(args.url, base)

    print(f"Extracting frames (mode={args.mode}) ...")
    if args.mode == "scene":
        frames = extract_frames_scene(video_path, frames_dir, args.scene_threshold, args.max_frames)
        if len(frames) < 3:
            print("Too few scene-change frames detected, falling back to interval mode ...")
            for f in frames_dir.glob("frame_*.jpg"):
                f.unlink()
            frames = extract_frames_interval(video_path, frames_dir, args.interval, args.max_frames)
    else:
        frames = extract_frames_interval(video_path, frames_dir, args.interval, args.max_frames)

    manifest = {
        "source_url": args.url,
        "platform": info.get("extractor_key", "unknown"),
        "title": info.get("title", ""),
        "uploader": info.get("uploader", ""),
        "duration_seconds": info.get("duration"),
        "video_path": video_path.name,
        "frames_dir": "frames",
        "frames": frames,
    }
    manifest_path = base / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\nDone. {len(frames)} candidate frames extracted.")
    print(f"  video:    {video_path}")
    print(f"  frames:   {frames_dir}/")
    print(f"  manifest: {manifest_path}")
    print("\nNext: review the frames and draft workout.json (see build_page.py --help).")


if __name__ == "__main__":
    main()
