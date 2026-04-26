from fastapi import FastAPI, Query
from ytmusicapi import YTMusic
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
yt = YTMusic()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)