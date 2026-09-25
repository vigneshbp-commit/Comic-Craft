#!/usr/bin/env python3
"""Convenience launcher for ComicCraft FastAPI server."""
import os
import sys
import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"🚀 Starting {settings.APP_NAME} on http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Interactive Swagger docs at http://{settings.HOST}:{settings.PORT}/docs")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
