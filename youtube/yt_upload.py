# 유튜브 직접 업로드 (YouTube Data API v3, 재개 가능 업로드)
# usage: python3 yt_upload.py econ meta.json [--force]
#   같은 영상(upload_result.json 있음)·같은 제목(최근 15개)·동시 실행이면 올리지 않고 종료한다.
#   업로드 실패로 종료되면 다시 실행하기 전에 반드시 yt_recent.py로 실제로 올라갔는지 먼저 확인한다.
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
# ---- 중복 업로드 방지 (같은 영상·같은 제목이면 올리지 않는다) ----
FORCE = "--force" in sys.argv
res_path = os.path.join(os.path.dirname(meta["video"]), "upload_result.json")
if not FORCE and os.path.exists(res_path):
    sys.exit(f"중복 방지: 이 영상은 이미 업로드됨 → {json.load(open(res_path))['url']} (다시 올리려면 --force)")
API = "https://www.googleapis.com/youtube/v3"
ch = requests.get(f"{API}/channels", params={"part": "contentDetails", "mine": "true"}, headers=H).json()
up_pl = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
recent = requests.get(f"{API}/playlistItems", params={"part": "snippet", "playlistId": up_pl, "maxResults": 15}, headers=H).json().get("items", [])
want = meta["title"][:100].strip()
for it in recent:
    if it["snippet"]["title"].strip() == want and not FORCE:
        sys.exit(f"중복 방지: 같은 제목 영상이 이미 있음 → https://youtu.be/{it['snippet']['resourceId']['videoId']} (다시 올리려면 --force)")
# 동시에 두 번 실행되는 것 막기(잠금 파일)
lock = res_path + ".lock"
if FORCE and os.path.exists(lock): os.remove(lock)
try: fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd)
except FileExistsError: sys.exit(f"중복 방지: 같은 영상 업로드가 이미 진행 중(잠금 {lock}). 끝난 뒤 yt_recent.py로 확인하세요.")
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
