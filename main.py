from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import engine
import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="LeadGen API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import businesses, messages, website_checker, scraper, pipeline

app.include_router(businesses.router, prefix="/api/businesses", tags=["businesses"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(website_checker.router, prefix="/api/check", tags=["website-checker"])
app.include_router(scraper.router, prefix="/api/scrape", tags=["scraper"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
