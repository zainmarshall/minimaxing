from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import bots, matches

app = FastAPI(title="MiniMaxing API")

# Add CORS middleware to allow communication from SvelteKit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bots.router, prefix="/api/bots", tags=["bots"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])

@app.get("/")
async def root():
    return {"message": "MiniMaxing API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
