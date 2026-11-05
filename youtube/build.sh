#!/usr/bin/env bash
# usage: ./build.sh config.json  -> out_dir/video.mp4 + out_dir/thumb.jpg
set -e
cd "$(dirname "$0")"
CFG="$1"
OUT=$(python3 -c "import json;print(json.load(open('$CFG',encoding='utf-8'))['out_dir'])")
mkdir -p "$OUT"
python3 tts.py "$CFG"
python3 render_brief.py "$CFG"
TOTAL=$(python3 -c "import json;print(json.load(open('$OUT/timeline.json'))['total'])")
python3 make_music.py "$OUT/music.wav" "$TOTAL"
# 나레이션을 장면 시작 시각에 배치
VO="$OUT/voice.wav"
python3 - "$OUT" <<'PY'
import json, os, subprocess, sys
out = sys.argv[1]; tl = json.load(open(f"{out}/timeline.json"))
ins, flt, k = [], [], 0
names = ["intro"] + [f"item{i}" for i in range(len(tl["scenes"]) - 2)] + ["outro"]
for name, sc in zip(names, tl["scenes"]):
    p = f"{out}/tts/{name}.mp3"
    if os.path.exists(p) and os.path.exists(f"{out}/tts/durations.json"):
        ins += ["-i", p]; ms = int((sc["start"] + 0.25) * 1000)
        flt.append(f"[{k}:a]adelay={ms}|{ms},aresample=44100[v{k}]"); k += 1
if k == 0: sys.exit(0)
fc = ";".join(flt) + ";" + "".join(f"[v{i}]" for i in range(k)) + f"amix=inputs={k}:normalize=0,apad,atrim=0:{tl['total']}[vo]"
subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-map", "[vo]", "-ac", "2", f"{out}/voice.wav"])
PY
if [ -f "$VO" ]; then
  # 음성이 있으면 음악을 낮게 깔고 음성 구간에서 더 줄인다(사이드체인 덕킹)
  ffmpeg -y -loglevel error -i "$OUT/silent.mp4" -i "$VO" -i "$OUT/music.wav" -filter_complex \
   "[2:a]volume=0.35[m];[1:a]asplit=2[v][sc];[m][sc]sidechaincompress=threshold=0.03:ratio=8:release=400[md];[v][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]" \
   -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/video.mp4"
else
  ffmpeg -y -loglevel error -i "$OUT/silent.mp4" -i "$OUT/music.wav" \
   -filter_complex "[1:a]loudnorm=I=-16:TP=-1.5:LRA=7[a]" -map 0:v -map "[a]" \
   -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/video.mp4"
fi
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 "$OUT/video.mp4"
