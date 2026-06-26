import uvicorn
from app.config import Config

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="debug" if Config.DEBUG else "info"
    )