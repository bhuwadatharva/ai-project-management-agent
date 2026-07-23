import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config.settings import settings
from backend.app.api.endpoints import router as api_router
from backend.app.db.session import engine, Base

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="DevPilot AI - Engineering Project Manager Agent Framework",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Allow requests from React clients
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event handler to compile DB tables
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

# Include Routers
app.include_router(api_router, prefix=settings.API_PREFIX)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to DevPilot AI Engine REST Server API",
        "documentation": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
