from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.middleware(
    CORSMiddleware,
    # Change this to use a list from our env file
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app = FastAPI()

@app.get("/")
def home():
    return {"message":"home route"}