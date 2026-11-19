if __name__ == "__main__":
    import uvicorn
    from src.backend.core.config import settings

    uvicorn.run(app="src.backend.main:app", host='localhost', port=8000, reload=True)
    pass