from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.modules.assistant.router import router as assistant_router

app = FastAPI(title="AI Sales Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # вынести
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    assistant_router,
    prefix="/api/v1",
)
