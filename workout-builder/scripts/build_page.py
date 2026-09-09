#!/usr/bin/env python3
"""
Turn a workout.json spec into a single portable, voice-guided timer
HTML page (same engine as the original hand-built workout-timer.html),
with per-exercise screenshots embedded inline.

workout.json schema:
{
  "title": "Warm-Up Workout",
  "source_url": "https://... (optional, shown as a credit link)",
  "default_duration": 45,                 // seconds, used when an exercise omits "duration"
  "exercises": [
    {"name": "Body hops", "duration": 60, "image": "frames/frame_0007.jpg"},
    {"name": "Squats"}                     // image/duration optional
  ]
}

Image paths are resolved relative to the workout.json file's directory
and inlined as base64 data URIs, so the resulting HTML is a single
self-contained file you can open anywhere.

Usage:
  python3 build_page.py workout.json [--out workout.html]
"""
import argparse
import base64
import json
import mimetypes
import sys
from pathlib import Path

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "workout_template.html"


def image_to_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def build(workout_path: Path, out_path: Path):
    spec = json.loads(workout_path.read_text())
    base_dir = workout_path.parent
    default_duration = spec.get("default_duration", 45)

    exercises = []
    for ex in spec.get("exercises", []):
        entry = {
            "name": ex["name"],
            "duration": int(ex.get("duration", default_duration)),
        }
        image = ex.get("image")
        if image:
            image_path = (base_dir / image).resolve()
            if not image_path.exists():
                sys.exit(f"error: image not found for '{ex['name']}': {image_path}")
            entry["image"] = image_to_data_uri(image_path)
        exercises.append(entry)

    if not exercises:
        sys.exit("error: workout.json has no exercises")

    title = spec.get("title", "Workout")
    source_url = spec.get("source_url")
    source_link_html = (
        f'<a class="source-link" href="{source_url}" target="_blank" rel="noopener">source video ↗</a>'
        if source_url else ""
    )

    template = TEMPLATE_PATH.read_text()
    html = (
        template
        .replace("__TITLE__", title)
        .replace("__SOURCE_LINK__", source_link_html)
        .replace("__COUNT__", str(len(exercises)))
        .replace("__EXERCISES_JSON__", json.dumps(exercises))
    )
    out_path.write_text(html)
    print(f"Wrote {out_path} ({len(exercises)} exercises, {sum(e['duration'] for e in exercises)}s total)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("workout_json", type=Path, help="path to workout.json")
    parser.add_argument("--out", type=Path, help="output HTML path (default: <workout_json dir>/workout.html)")
    args = parser.parse_args()

    if not args.workout_json.exists():
        sys.exit(f"error: {args.workout_json} not found")

    out_path = args.out or args.workout_json.parent / "workout.html"
    build(args.workout_json, out_path)


if __name__ == "__main__":
    main()
