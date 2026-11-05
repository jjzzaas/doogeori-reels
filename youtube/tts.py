# 나레이션 생성(선택). edge-tts가 안 되면 조용히 건너뛰고 자막+음악만으로 제작된다.
# usage: python3 tts.py config.json  -> out_dir/tts/{intro,item0..,outro}.mp3 + durations.json
import asyncio, json, os, subprocess, sys
CFG = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = os.path.join(CFG["out_dir"], "tts"); os.makedirs(OUT, exist_ok=True)
VOICE = CFG.get("voice", "ko-KR-SunHiNeural"); RATE = CFG.get("voice_rate", "+8%")
jobs = [("intro", CFG.get("intro_say", ""))] + [(f"item{i}", it.get("say", "")) for i, it in enumerate(CFG["items"])] + [("outro", CFG.get("outro_say", ""))]
def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode())
async def main():
    import edge_tts
    proxy = os.environ.get("HTTPS_PROXY") or None
    out = {}
    for key, text in jobs:
        if not text.strip(): continue
        p = os.path.join(OUT, key + ".mp3")
        await edge_tts.Communicate(text, VOICE, rate=RATE, proxy=proxy).save(p)
        out[key] = dur(p)
    json.dump(out, open(os.path.join(OUT, "durations.json"), "w"), indent=1)
    print("tts ok", out)
try: asyncio.run(main())
except Exception as e:
    print("나레이션 생성 실패 → 자막만으로 진행:", type(e).__name__, e)
    p = os.path.join(OUT, "durations.json")
    if os.path.exists(p): os.remove(p)
    sys.exit(0)
