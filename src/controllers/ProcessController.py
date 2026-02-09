from .BaseController import BaseController
from .ProjectController import ProjectController
from models import ProcessingEnum
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

import os

class ProcessController(BaseController):
    def __init__(self, project_id: str, logger=None):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
        self.logger = logger

    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]
    
    def get_file_loader(self, file_id: str):
        file_extension = self.get_file_extension(file_id=file_id)
        file_path = os.path.join(self.project_path, file_id)

        # self.logger.info(f"Attempting to load file with extension: {file_extension}")

        if file_extension == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        
        if file_extension == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path) 
        
        return None
    
    def get_file_content(self, file_id: str):
        loader = self.get_file_loader(file_id=file_id)

        return loader.load() # Returns a list of Document objects, each with page_content and metadata attributes.
    

    def process_file_content(self, file_content: list, file_id: str,
                             chunk_size: int = 1000, chunk_overlap: int = 200):
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, 
                                                       chunk_overlap=chunk_overlap,
                                                       length_function=len)
        
        file_content_texts = [doc.page_content for doc in file_content]
        file_content_metadatas = [doc.metadata for doc in file_content]

        chunks = text_splitter.create_documents(
            file_content_texts, 
            metadatas=file_content_metadatas
        )
        return chunks


