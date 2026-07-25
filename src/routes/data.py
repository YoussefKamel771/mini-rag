from fastapi import FastAPI, APIRouter, Depends, Request, UploadFile, status
from fastapi.responses import JSONResponse
from helpers.config import Settings, get_settings
from controllers import DataController, ProjectController, ProcessController
from models import ResponseSignal, ProjectModel, DataChunk, ChunkModel
from models.ChunkModel import ChunkModel
from .schemas.data import ProcessRequest
import os
import aiofiles
import logging

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile, 
                      app_settings: Settings = Depends(get_settings)):
    
    project_model = ProjectModel(db_client=request.app.state.database)

    project = await project_model.get_project_or_create_one(project_id=project_id)
    
    # Validata the file properties
    data_controller = DataController()
    is_valid, response_signal = data_controller.validate_uploaded_file(file=file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, 
            content={"message": response_signal})
    

    # Get the project path
    project_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_file_path(
        orig_file_name=file.filename, 
        project_id=project_id
        )

    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, 
            content={"message": ResponseSignal.FILE_UPLOAD_FAILED.value})

    return JSONResponse(
        status_code=status.HTTP_200_OK, 
        content={
            "message": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id,
            # "project_id": str(project.id)
            }
    )


@data_router.post("/process/{project_id}")
async def process_data(request: Request, project_id: str, process_request: ProcessRequest):
    # Placeholder for processing logic
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.chunk_overlap
    do_reset = process_request.do_reset

    project_model = ProjectModel(
        db_client=request.app.state.database
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    process_controller = ProcessController(project_id=project_id, logger=logger)

    try:
        file_content = process_controller.get_file_content(file_id=file_id)
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, 
            content={"message": ResponseSignal.FILE_PROCESSING_FAILED.value}
        )

    file_chunks = process_controller.process_file_content(
        file_content=file_content,
        file_id=file_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_PROCESSING_FAILED.value
            }
        )
    
    file_chunks_records = [
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i+1,
            chunk_project_id=project.id,
        )
        for i, chunk in enumerate(file_chunks)
    ]

    chunk_model = ChunkModel(
        db_client=request.app.state.database
    )

    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(
            project_id=project.id
        )


    no_records  = await chunk_model.insert_many_chunks(
        chunks=file_chunks_records
    )   

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records 
        }
    )
