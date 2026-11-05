# 유튜브 직접 업로드 (YouTube Data API v3, 재개 가능 업로드)
# usage: python3 yt_upload.py econ meta.json
#   meta.json: {"video":"out/.../video.mp4","title":"...","description":"...","tags":[...],
#               "privacy":"private|unlisted|public","publish_at":"2026-11-06T07:30:00+09:00"(선택),
#               "category":"25","thumbnail":"out/.../thumb.jpg"(선택, 롱폼), "made_for_kids":false}
# 토큰: 환경변수 YT_REFRESH_TOKEN_<NAME 대문자> 또는 secrets/<name>.token
import json, os, sys, requests
name, meta = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8"))
rt = os.environ.get(f"YT_REFRESH_TOKEN_{name.upper()}")
if not rt and os.path.exists(f"secrets/{name}.token"): rt = open(f"secrets/{name}.token").read().strip()
if not rt: sys.exit(f"{name} 채널 토큰이 없습니다(yt_auth.py 먼저).")
tok = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
    "refresh_token": rt, "grant_type": "refresh_token"}).json()
if "access_token" not in tok: sys.exit(f"토큰 갱신 실패: {tok}")
H = {"Authorization": f"Bearer {tok['access_token']}"}
status = {"privacyStatus": meta.get("privacy", "private"), "selfDeclaredMadeForKids": meta.get("made_for_kids", False),
          "containsSyntheticMedia": meta.get("synthetic", False)}
if meta.get("publish_at"): status.update(privacyStatus="private", publishAt=meta["publish_at"])  # 예약 공개
body = {"snippet": {"title": meta["title"][:100], "description": meta.get("description", "")[:5000],
                    "tags": meta.get("tags", []), "categoryId": meta.get("category", "25"),
                    "defaultLanguage": "ko", "defaultAudioLanguage": "ko"}, "status": status}
size = os.path.getsize(meta["video"])
init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                     headers={**H, "Content-Type": "application/json; charset=UTF-8",
                              "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                     data=json.dumps(body))
if init.status_code != 200: sys.exit(f"업로드 시작 실패 {init.status_code}: {init.text[:500]}")
with open(meta["video"], "rb") as f:
    up = requests.put(init.headers["Location"], headers={**H, "Content-Type": "video/mp4"}, data=f)
if up.status_code not in (200, 201): sys.exit(f"업로드 실패 {up.status_code}: {up.text[:500]}")
v = up.json(); vid = v["id"]
print(f"업로드 완료: https://youtu.be/{vid}  상태: {v['status'].get('privacyStatus')} / {v['status'].get('uploadStatus')}")
if meta.get("thumbnail"):
    with open(meta["thumbnail"], "rb") as f:
        t = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                          headers={**H, "Content-Type": "image/jpeg"}, data=f)
    print("썸네일:", "완료" if t.ok else f"실패 {t.status_code} {t.text[:200]}")
json.dump({"id": vid, "url": f"https://youtu.be/{vid}", "status": v["status"]},
          open(os.path.join(os.path.dirname(meta["video"]), "upload_result.json"), "w"), indent=1)
