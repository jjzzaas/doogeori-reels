# 채널 1개당 1번 실행: 휴대폰에서 google.com/device 에 코드를 넣어 승인 → refresh token 저장
# 필요 환경변수: YT_CLIENT_ID, YT_CLIENT_SECRET  (OAuth 클라이언트 유형: "TV 및 입력 제한 기기")
# usage: python3 yt_auth.py econ   -> secrets/econ.token (git에 올라가지 않음)
import json, os, sys, time, requests
name = sys.argv[1] if len(sys.argv) > 1 else "econ"
cid, csec = os.environ.get("YT_CLIENT_ID"), os.environ.get("YT_CLIENT_SECRET")
if not cid or not csec: sys.exit("환경변수 YT_CLIENT_ID / YT_CLIENT_SECRET 가 없습니다.")
r = requests.post("https://oauth2.googleapis.com/device/code",
                  data={"client_id": cid, "scope": "https://www.googleapis.com/auth/youtube"}).json()
if "device_code" not in r: sys.exit(f"오류: {r}")
print(f"\n휴대폰에서 {r['verification_url']} 접속 → 코드 입력: {r['user_code']}")
print("※ 채널 선택 화면에서 업로드할 채널(브랜드 계정)을 고르세요.\n", flush=True)
deadline = time.time() + r["expires_in"]; wait = r.get("interval", 5)
while time.time() < deadline:
    time.sleep(wait)
    t = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": cid, "client_secret": csec, "device_code": r["device_code"],
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}).json()
    if "refresh_token" in t:
        os.makedirs("secrets", exist_ok=True)
        p = f"secrets/{name}.token"; open(p, "w").write(t["refresh_token"]); os.chmod(p, 0o600)
        ch = requests.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "snippet", "mine": "true"},
                          headers={"Authorization": f"Bearer {t['access_token']}"}).json()
        title = ch.get("items", [{}])[0].get("snippet", {}).get("title", "?")
        print(f"승인 완료 — 채널: {title} / 토큰 저장: youtube/{p}")
        sys.exit(0)
    if t.get("error") == "slow_down": wait += 2
    elif t.get("error") != "authorization_pending": sys.exit(f"오류: {t}")
sys.exit("시간 초과 — 다시 실행하세요.")
