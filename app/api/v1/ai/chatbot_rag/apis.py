from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import FileResponse
from app.api.v1.ai.chatbot_rag.models import AskQuestionRequest
from app.api.v1.ai.chatbot_rag.services import *
from app.api.v1.utils.vector_db_manager import VectorDBManager
from app.api.v1.utils.azure_sql_manager import AzureSQLManager
from langchain_community.document_loaders import Docx2txtLoader
from app.api.v1.utils.config import Config
from typing import List
import os
import json



rag_router = APIRouter(prefix= "/chatbot-rag")


@rag_router.post("/file-upload")
async def upload_files(session_id: str, user_id: str, files: List[UploadFile] = File(...)):
    """
    Endpoint to upload multiple files.
    Files are stored in the `temp_data` directory.
    """
    try:
        uploaded_file_names = []
        folder_base_path = f"temp_data/{session_id}"
        os.makedirs(folder_base_path, exist_ok = True)
        vector_db = VectorDBManager(Config())
        sql_db = AzureSQLManager(Config())
        for file in files:
            file_location = f"{folder_base_path}/{file.filename}"
            with open(file_location, "wb") as f:
                f.write(await file.read())
            uploaded_file_names.append(file.filename)

            loader = Docx2txtLoader(file_location)
            document = loader.load()
            vector_db.add_document_if_not_exist(document, session_id)
            params = (session_id, user_id, file.filename, user_id)
            status = sql_db.insert_file_metadata(params)
            sql_db.disconnect()
            if not status:
                raise Exception("Insertion to Azure SQL failed.")
        return {"uploaded_files": uploaded_file_names, "message": "Files uploaded successfully!"}
    except Exception as e:
        return {"uploaded_files": [], "message": "Files upload failed!"}


@rag_router.post("/ask-question")
async def ask_question(request: AskQuestionRequest):
    vector_db_manager = VectorDBManager(Config())
    response = vector_db_manager.query_with_document(
                        request.user_question
                        ,request.session_id)
    return response