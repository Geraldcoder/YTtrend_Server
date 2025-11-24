# Original script

# from googleapiclient.discovery import build
# from datetime import datetime, timedelta, timezone


# API_KEY = "AIzaSyDR2k7lR165zUFshzNcElb2zG6mpDGXekA"
# youtube = build('youtube', 'v3', developerKey=API_KEY)

# keyword = input("What niche do you wish to check trending?: ")
# since = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

# # find recent videos for the keyword, sorted by viewCount
# search = youtube.search().list(
#     part="id",
#     q= keyword,
#     type="video",
#     regionCode="US",
#     publishedAfter= since,
#     order="viewCount",
#     maxResults= 20
# ).execute()

# video_ids = [item["id"]["videoId"] for item in search["items"]]

# # pull stats to compute trend "velocity"
# videos = youtube.videos().list(
#     part="snippet,statistics,contentDetails",
#     id=",".join(video_ids)
# ).execute()

# def views_per_hour(item):
#     views = int(item["statistics"].get("viewCount", 0))
#     published = datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z","+00:00"))
#     hours = max((datetime.now(timezone.utc) - published).total_seconds()/3600, 1/60)
#     return views / hours


# ranked = sorted(videos["items"], key=views_per_hour, reverse=True)
# for v in ranked[:10]:
#     print(f'{v["snippet"]["title"]} | {views_per_hour(v):.0f} views/hr | https://youtu.be/{v["id"]} | Total Views: {v["statistics"]["viewCount"]}')


# fastapi code 

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone

# YouTube API setup
API_KEY = "AIzaSyDR2k7lR165zUFshzNcElb2zG6mpDGXekA"
youtube = build('youtube', 'v3', developerKey=API_KEY)

app = FastAPI()

# CORS setup to allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, etc.
    allow_headers=["*"],  # Content-Type, etc.
)

# In-memory storage for the last search results
last_results = []

# Pydantic model for POST request
class SearchRequest(BaseModel):
    keyword: str

# Helper function to compute views per hour
def views_per_hour(item):
    views = int(item["statistics"].get("viewCount", 0))
    published = datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00"))
    hours = max((datetime.now(timezone.utc) - published).total_seconds() / 3600, 1/60)
    return views / hours

# POST endpoint to perform search
@app.post("/search")
def search_videos(request: SearchRequest):
    global last_results
    keyword = request.keyword
    since = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

    # Search YouTube videos
    search = youtube.search().list(
        part="id",
        q=keyword,
        type="video",
        regionCode="US",
        publishedAfter=since,
        order="viewCount",
        maxResults=20
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search.get("items", [])]

    if not video_ids:
        last_results = []
        return {"message": "No videos found", "results_count": 0}

    # Get video details
    videos = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids)
    ).execute()

    # Rank videos by views per hour
    ranked = sorted(videos.get("items", []), key=views_per_hour, reverse=True)

    # Store top 10 results
    last_results = [
        {
            "title": v["snippet"]["title"],
            "views_per_hour": round(views_per_hour(v)),
            "url": f'https://youtu.be/{v["id"]}',
            "total_views": v["statistics"]["viewCount"]
        }
        for v in ranked[:10]
    ]

    return {"message": f"Search completed for '{keyword}'", "results_count": len(last_results)}

# GET endpoint to fetch last results
@app.get("/results")
def get_results():
    return {"results": last_results}