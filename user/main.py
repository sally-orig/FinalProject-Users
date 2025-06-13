from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .routes import router
from .auth.auth import token_router

app = FastAPI(title="User Management API", version="1.0.0")

@app.get("/", include_in_schema=False)
async def read_root():
    return RedirectResponse(url="/docs")

app.include_router(token_router, prefix="/auth", tags=["authentication"])
app.include_router(router, prefix="/users", tags=["users"])

