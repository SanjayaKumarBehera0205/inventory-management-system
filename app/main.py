from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.routes import auth, inventory


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Secure inventory, supplier, and stock movement REST API.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(inventory.router, prefix=settings.api_prefix)


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "healthy"}
