from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import ml_services
from .database import Base, SessionLocal, engine
from .routers import auth, cases, dashboard, suspects


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ml_services.load_face_gallery_from_db(db)
        ml_services.load_fir_linker_from_db(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Suspect Tracking & Crime Analysis System", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(suspects.router)
app.include_router(cases.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}
