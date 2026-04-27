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
        # 1. Try to fetch the official "Top 50 India" Playlist directly
        # This ID is public and works globally.
        playlist_id = "RDCLAK5uy_n9FByws7cwzST9m6_S_On_9zR_vA776Sg" 
        
        try:
            playlist_data = yt.get_playlist(playlist_id, limit=20)
            items = playlist_data.get('tracks', [])
        except:
            items = []

        # 2. If the playlist failed (or is empty), fallback to a high-quality search
        if not items:
            print("Playlist fetch failed, falling back to search...")
            search_results = yt.search("Top Indian Songs 2024", filter="songs")
            items = search_results[:20]

        formatted_modules = []
        mapped_items = []

        for item in items:
            # Handle different key names between Playlist tracks and Search results
            item_id = item.get('videoId')
            if not item_id: continue

            thumbnails = item.get('thumbnails', [])
            image_url = thumbnails[-1]['url'] if thumbnails else "https://via.placeholder.com/500"
            if "=" in image_url: image_url = image_url.split('=')[0] + "=w500-h500-l90-rj"

            # Get artist name safely
            artists = item.get('artists', [])
            artist_name = artists[0].get('name', 'Unknown Artist') if artists else 'Unknown'

            mapped_items.append({
                "id": item_id,
                "title": item.get('title'),
                "subtitle": artist_name,
                "type": "song",
                "image": image_url
            })

        # Put everything into a "Trending in India" category
        if mapped_items:
            formatted_modules.append({
                "title": "Trending in India",
                "items": mapped_items
            })

        return {
            "success": True,
            "data": formatted_modules
        }

    except Exception as e:
        return {"success": False, "error": str(e), "data": []}
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
