from fastapi import FastAPI
from routes import data, base, nlp
from stores.llm import LLMProviderFactory
from stores.vectordb import VectorDBProviderFactory
from stores import TemplateParser
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

    llm_provider_factory = LLMProviderFactory(settings)
    vector_db_provider_factory = VectorDBProviderFactory(settings)

    # print("GENERATION_BACKEND:", repr(settings.GENERATION_BACKEND))
    # generation client
    app.state.generation_client = llm_provider_factory.create(settings.GENERATION_BACKEND)
    app.state.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    # embedding client
    app.state.embedding_client = llm_provider_factory.create(settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(settings.EMBEDDING_MODEL_ID, 
                                                   settings.EMBEDDING_MODEL_SIZE)

    # Vector DB client
    app.state.vectordb_client = vector_db_provider_factory.create(settings.VECTOR_DB_BACKEND)
    app.state.vectordb_client.connect()    

    app.state.template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG,
    )


    yield  # This is where the application "lives" and handles requests
    
    # --- Shutdown Logic ---
    app.state.mongodb_client.close()
    app.state.vectordb_client.disconnect()


# 2. Pass the lifespan to the FastAPI constructor
app = FastAPI(lifespan=lifespan)

app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)