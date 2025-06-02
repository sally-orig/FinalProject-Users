from fastapi import FastAPI
from .routes import router

app = FastAPI(title="User Management API", version="1.0.0")

app.include_router(router, prefix="/users", tags=["users"])

