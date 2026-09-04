from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.videos import router as videos_router
from app.api.v1.feed import router as feed_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(videos_router, prefix=settings.API_V1_STR + "/videos", tags=["videos"])
app.include_router(feed_router, prefix=settings.API_V1_STR, tags=["feed"])

@app.get("/")
def root():
    return {"message": "Welcome to the Video Viewer API"}
