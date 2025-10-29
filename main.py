from fastapi import FastAPI
from app.api.v1.spark.apis import spark_router
from app.api.v1.ai.chatbot_rag.apis import rag_router
from app.api.v1.ai.agentic.apis import agentic_router
from dotenv import load_dotenv
        
load_dotenv()

app = FastAPI()

app.include_router(spark_router, tags=["spark"])
app.include_router(rag_router, tags=["chatbot-rag"])
app.include_router(agentic_router, tags=["agentic-bot"])


@app.get("/")
def root():
    return {"Hello": "World"}