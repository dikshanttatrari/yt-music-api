import os
import json
from fastapi import FastAPI, Query
from ytmusicapi import YTMusic
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
print("Initializing YTMusic for India Region...")
yt = YTMusic(location="IN", language="en")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/search/songs")
def search_songs(q: str = Query(...)):
    results = yt.search(q, filter="songs")
    
    mapped_results = []
    
    for item in results:
        video_id = item.get('videoId')
        mapped_item = {
            "id": video_id,
            "name": item.get('title'),
            "type": "song",
            "year": item.get('year', "2024"),
            "duration": item.get('duration_seconds', 0),
            "album": {
                "name": item.get('album', {}).get('name', 'Single'),
                "id": item.get('album', {}).get('id', '')
            },
            "artists": {
                "primary": [
                    {
                        "name": a.get('name'),
                        "id": a.get('id'),
                        "role": "primary_artists"
                    } for a in item.get('artists', [])
                ]
            },
            "image": [
                {"quality": "50x50", "url": item['thumbnails'][0]['url']},
                {"quality": "150x150", "url": item['thumbnails'][-1]['url']},
                {"quality": "500x500", "url": item['thumbnails'][-1]['url'].replace('w120-h120', 'w500-h500')}
            ],
            "downloadUrl": [
                {"quality": "320kbps", "url": f"https://www.youtube.com/watch?v={video_id}"}
            ]
        }
        mapped_results.append(mapped_item)

    return {
        "success": True,
        "data": {
            "results": mapped_results
        }
    }
@app.get("/api/home")
def get_home():
    try:
        # Instead of get_home(), we explicitly request the Indian Charts
        # This completely ignores Vercel's US IP address
        charts = yt.get_charts(country="IN")
        
        formatted_modules = []
        
        # --- SHELF 1: Trending in India ---
        if 'trending' in charts and charts['trending'].get('items'):
            mapped_trending = []
            for item in charts['trending']['items'][:10]: # Get top 10
                thumbnails = item.get('thumbnails', [])
                image_url = thumbnails[-1]['url'] if thumbnails else "https://via.placeholder.com/500"
                if "=" in image_url: image_url = image_url.split('=')[0] + "=w500-h500-l90-rj"
                
                mapped_trending.append({
                    "id": item.get('videoId'),
                    "title": item.get('title'),
                    "subtitle": item.get('artists', [{}])[0].get('name', 'Unknown Artist'),
                    "type": "song",
                    "image": image_url
                })
            formatted_modules.append({"title": "Trending in India", "items": mapped_trending})

        # --- SHELF 2: Top Songs India ---
        if 'songs' in charts and charts['songs'].get('items'):
            mapped_songs = []
            for item in charts['songs']['items'][:10]: 
                thumbnails = item.get('thumbnails', [])
                image_url = thumbnails[-1]['url'] if thumbnails else "https://via.placeholder.com/500"
                if "=" in image_url: image_url = image_url.split('=')[0] + "=w500-h500-l90-rj"

                mapped_songs.append({
                    "id": item.get('videoId'),
                    "title": item.get('title'),
                    "subtitle": item.get('artists', [{}])[0].get('name', ''),
                    "type": "song",
                    "image": image_url
                })
            formatted_modules.append({"title": "Top Songs India", "items": mapped_songs})

        # --- SHELF 3: Top Music Videos India ---
        if 'videos' in charts and charts['videos'].get('items'):
            mapped_videos = []
            for item in charts['videos']['items'][:10]:
                thumbnails = item.get('thumbnails', [])
                image_url = thumbnails[-1]['url'] if thumbnails else "https://via.placeholder.com/500"
                if "=" in image_url: image_url = image_url.split('=')[0] + "=w500-h500-l90-rj"

                mapped_videos.append({
                    "id": item.get('videoId'),
                    "title": item.get('title'),
                    "subtitle": item.get('artists', [{}])[0].get('name', ''),
                    "type": "song",
                    "image": image_url
                })
            formatted_modules.append({"title": "Top Music Videos", "items": mapped_videos})

        return {
            "success": True,
            "data": formatted_modules
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
