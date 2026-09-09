# Workout Timer

A voice-guided interval timer for follow-along workouts, plus a pipeline that
builds one automatically from a TikTok, Instagram, or YouTube video link.

## What's in here

```
workout-timer.html          standalone timer — hand-write your own exercise list
workout-builder/             pipeline that generates a timer from a video link
  scripts/fetch_video.py     downloads a video and extracts candidate screenshots
  scripts/build_page.py      turns a workout.json + screenshots into a timer page
  templates/workout_template.html   the generated page's HTML/CSS/JS engine
  output/                    per-video working directories (git-ignored)
```

## 1. `workout-timer.html` — standalone timer

Open it directly in any browser. No install, no server, no dependencies.

- Cycles through a fixed list of exercises, 60 seconds each
- Big circular countdown per exercise
- Speaks the exercise name aloud when it starts
- Announces "10 seconds — next up: X" before switching
- Beeps on every transition (works even with voice off)
- Start / Pause / Reset controls, voice on/off toggle

To reuse it for a different routine, edit the `EXERCISES` array near the top
of the `<script>` block.

**Note:** browsers only allow speech synthesis after a user gesture, so tap
**Start** once — the rest of the routine narrates itself.

## 2. `workout-builder/` — generate a timer from a video

Turns "I saw a workout on TikTok" into a voice-guided timer page, screenshots
included, without transcribing the moves by hand.

### Requirements (run these locally, not in a sandboxed environment)

```bash
pip install yt-dlp
# ffmpeg must be on PATH
brew install ffmpeg        # macOS
apt-get install ffmpeg     # Debian/Ubuntu
```

### Step 1 — download the video and pull candidate screenshots

```bash
python3 workout-builder/scripts/fetch_video.py "<tiktok-or-instagram-or-youtube-url>"
```

This downloads the video and extracts frames into
`workout-builder/output/<slug>/`:

```
output/<slug>/
  video.mp4
  frames/frame_0001.jpg, frame_0002.jpg, ...
  manifest.json       video metadata + frame timestamps
```

By default it uses **scene-change detection** — one frame per cut, which
usually lines up with one frame per exercise in an edited workout clip.
Useful flags:

| Flag | Purpose |
|---|---|
| `--mode interval` | sample every N seconds instead of scene cuts |
| `--interval 2.0` | seconds between frames in interval mode |
| `--scene-threshold 0.35` | lower = more sensitive to cuts, more frames |
| `--max-frames 60` | cap on extracted frames |
| `--outdir DIR` | override the output directory |

Run `python3 workout-builder/scripts/fetch_video.py --help` for the full list.

### Step 2 — write `workout.json`

Look through `output/<slug>/frames/` and identify each exercise, its
duration, and which frame best represents it (or hand the frames to Claude
and ask it to draft this file for you). Save it alongside the frames as
`output/<slug>/workout.json`:

```json
{
  "title": "Warm-Up Workout (from TikTok)",
  "source_url": "https://www.tiktok.com/...",
  "default_duration": 45,
  "exercises": [
    { "name": "Body hops", "duration": 60, "image": "frames/frame_0001.jpg" },
    { "name": "Squats" },
    { "name": "Marches", "duration": 45, "image": "frames/frame_0009.jpg" }
  ]
}
```

- `duration` and `image` are optional per exercise; missing `duration` falls
  back to `default_duration`.
- `image` paths are relative to the `workout.json` file itself.
- The clip's on-screen pace usually isn't how long you actually want to hold
  each move — set real durations here, not the video's cut length.

### Step 3 — build the timer page

```bash
python3 workout-builder/scripts/build_page.py output/<slug>/workout.json
```

Produces `output/<slug>/workout.html` — a single self-contained file (images
inlined as base64) with the same voice/timer engine as `workout-timer.html`,
plus a screenshot behind the countdown ring and thumbnails in the exercise
list. Open it in a browser and tap Start.

## Known limitations

- **Instagram** frequently requires a logged-in session for `yt-dlp` to fetch
  a post; TikTok and YouTube usually work for public videos without auth. If
  you hit this, `yt-dlp --cookies-from-browser <browser>` can be added to
  `fetch_video.py`'s download command.
- Exercise identification from screenshots is a manual (or Claude-assisted)
  review step, not fully automatic — video edits vary too much to reliably
  auto-label every move.
- Downloading video content is subject to the source platform's Terms of
  Service; this tool is meant for personal, single-user routines built from
  videos you already have permission to save.
