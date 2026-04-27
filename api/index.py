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
def get_home_data():
    try:
        # Limit to 5 "Shelves" (rows) to keep the API lightning fast
        home_data = yt.get_home(limit=5)
        
        formatted_modules = []
        
        for shelf in home_data:
            title = shelf.get('title', 'Discover')
            contents = shelf.get('contents', [])
            
            mapped_contents = []
            for item in contents:
                # YT Music uses different ID keys depending on what the item is
                item_id = item.get('videoId') or item.get('playlistId') or item.get('browseId')
                
                # If there's no ID, skip it (sometimes YT sends weird promotional banners)
                if not item_id:
                    continue
                    
                # Figure out what kind of media this is so your React Native app knows how to handle clicks
                if item.get('videoId'):
                    item_type = "song"
                elif item.get('playlistId'):
                    item_type = "playlist"
                else:
                    item_type = "album" # 'browseId' usually belongs to albums or artists
                    
                # Grab the highest quality thumbnail available
                thumbnails = item.get('thumbnails', [])
                image_url = thumbnails[-1]['url'] if thumbnails else "https://via.placeholder.com/500"
                
                # Clean up the YouTube image URL to be a high-res perfect square
                if "=" in image_url:
                    image_url = image_url.split('=')[0] + "=w500-h500-l90-rj"

                mapped_contents.append({
                    "id": item_id,
                    "title": item.get('title', 'Unknown Title'),
                    # Subtitle usually contains the Artist name or "Playlist • YouTube Music"
                    "subtitle": item.get('subtitle', ''), 
                    "type": item_type,
                    "image": image_url
                })
            
            # Only send the row to the app if it actually has items inside it
            if mapped_contents:
                formatted_modules.append({
                    "title": title,
                    "items": mapped_contents
                })
                
        return {
            "success": True,
            "data": formatted_modules
        }
        
    except Exception as e:
        return {
            "success": False, 
            "error": "Failed to fetch home data", 
            "details": str(e)
        }
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
