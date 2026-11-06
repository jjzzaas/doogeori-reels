# youtube/ — 경제 브리핑 쇼츠·롱폼 자동 제작

```
pip install pillow numpy scipy edge-tts   # apt: ffmpeg fonts-noto-cjk
./build.sh example_config.json            # → out/…/video.mp4, thumb.jpg
```
- `format`: "short"(1080×1920, 60초 이하) / "long"(1920×1080)
- 생활 경제 형식: 항목마다 `wallet`(내 지갑엔 상자) 한 줄로 생활비 영향을 금액으로 보여준다.
- 충격 비교: 항목에 `before`({label,value,pct})를 넣으면 "1년 전 ○원 → 지금 [+N%]" 줄이 나온다.
- 나레이션: edge-tts가 되면 자동으로 넣고, 안 되면 자막+음악만으로 만든다.
- 음악: make_music.py 직접 합성곡(저작권 문제 없음).
- 운영 방법: OPERATING_GUIDE.md, 예약 작업 프롬프트: SCHEDULED_TASK_PROMPT.md
