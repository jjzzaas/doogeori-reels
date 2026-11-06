# 내 채널 최근 업로드 목록 + 조회수 (중복 게시 확인·성장 체크용)
# usage: python3 yt_recent.py econ [개수=10]
import os, sys, requests
name = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
rt = os.environ.get(f"YT_REFRESH_TOKEN_{name.upper()}") or open(f"secrets/{name}.token").read().strip()
tok = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
    "refresh_token": rt, "grant_type": "refresh_token"}).json()
H = {"Authorization": f"Bearer {tok['access_token']}"}
API = "https://www.googleapis.com/youtube/v3"
ch = requests.get(f"{API}/channels", params={"part": "snippet,contentDetails,statistics", "mine": "true"}, headers=H).json()["items"][0]
print(f"채널: {ch['snippet']['title']} / 구독자 {ch['statistics'].get('subscriberCount')} / 영상 {ch['statistics'].get('videoCount')}")
pl = requests.get(f"{API}/playlistItems", params={"part": "contentDetails", "playlistId": ch["contentDetails"]["relatedPlaylists"]["uploads"],
                  "maxResults": n}, headers=H).json().get("items", [])
ids = ",".join(i["contentDetails"]["videoId"] for i in pl)
if not ids: print("업로드 없음"); sys.exit(0)
vs = requests.get(f"{API}/videos", params={"part": "snippet,status,statistics", "id": ids}, headers=H).json()["items"]
for v in vs:
    s, st = v["status"], v["statistics"]
    when = s.get("publishAt") or v["snippet"]["publishedAt"]
    print(f"{when} | {s['privacyStatus']:8} | 조회 {st.get('viewCount', 0):>6} | 좋아요 {st.get('likeCount', 0):>4} | {v['snippet']['title']} | https://youtu.be/{v['id']}")
