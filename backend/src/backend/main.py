from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.enums import UserRole

from .core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    # Change this to use a list from our env file
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to the Farm Project API!"}