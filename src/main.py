from fastapi import FastAPI
from routes import data, base
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings

# 1. Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    settings = get_settings()
    # We attach the client to the app state so it's accessible in routes
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    app.database = app.mongodb_client[settings.MONGODB_DATABASE]
    
    print("Connected to MongoDB")
    
    yield  # This is where the application "lives" and handles requests
    
    # --- Shutdown Logic ---
    app.mongodb_client.close()
    print("Disconnected from MongoDB")

# 2. Pass the lifespan to the FastAPI constructor
app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
