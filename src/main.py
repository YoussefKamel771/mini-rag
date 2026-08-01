from fastapi import FastAPI
from routes import data, base
from stores.llm import LLMProviderFactory
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from contextlib import asynccontextmanager

# 1. Define the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup Logic ---
    settings = get_settings()
    # We attach the client to the app state so it's accessible in routes
    app.state.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    app.state.database = app.state.mongodb_client[settings.MONGODB_DATABASE]
    
    print("Connected to MongoDB")

    llm_provider_factory = LLMProviderFactory(settings)

    # generation client
    app.state.generation_client = llm_provider_factory.create(settings.GENERATION_BACKEND)
    app.state.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    # embedding client
    app.state.embedding_client = llm_provider_factory.create(settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, 
                                                   settings.EMBEDDING_MODEL_SIZE)
    
    yield  # This is where the application "lives" and handles requests
    
    # --- Shutdown Logic ---
    app.state.mongodb_client.close()
    print("Disconnected from MongoDB")

# 2. Pass the lifespan to the FastAPI constructor
app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
