import hashlib
from app.api.v1.utils.config import Config
from app.api.v1.utils.llm_manager import LLMManager
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchFieldDataType,
    SearchField,
    SimpleField,
    TextWeights,
)

class VectorDBManager:
    def __init__(self, config: Config):
        self.conf = config

        self.embeddings: AzureOpenAIEmbeddings = AzureOpenAIEmbeddings(
                    azure_deployment= self.conf.embedding_deployment_name,
                    openai_api_version= self.conf.embedding_api_version,
                    azure_endpoint= self.conf.ai_endpoint,
                    api_key= self.conf.ai_api_key,
                )
        self.embedding_function = self.embeddings.embed_query
        self.vector_store: AzureSearch = AzureSearch(
                azure_search_endpoint= self.conf.ai_search_endpoint,
                azure_search_key= self.conf.ai_search_key,
                index_name= self.conf.ai_consumer_sales_index_name,
                embedding_function= self.embedding_function,
                fields=[
                        SimpleField(
                            name="id",
                            type="Edm.String",
                            key=True,
                            filterable=True,
                        ),
                        SearchableField(name="content", type="Edm.String", searchable=True,),
                        SearchField(
                            name="content_vector",
                            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                            searchable=True,
                            vector_search_dimensions=len(self.embedding_function("Text")),
                            vector_search_profile_name="myHnswProfile",
                        ),
                        SearchableField(name="metadata",type="Edm.String",searchable=True,),
                        # Additional field for filtering on document source
                        SimpleField(name="document_hash",type="Edm.String",filterable=True,),
                        SimpleField(name="session_id",type="Edm.String",filterable=True,),
                    ]
            )


    def get_document_hash(self, text):
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def check_doc_exists_in_vector_store(self, doc_hash):
        similar_docs = self.vector_store.similarity_search(query=doc_hash, k=1)

        for doc in similar_docs:
            if doc.metadata.get("document_hash") == doc_hash:
                return True
        return False

    def split_document(self, document, chunk_size=1000, chunk_overlap=100):
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_documents(document)
        return chunks

    def add_document_if_not_exist(self, doc, session_id):
        doc_content = doc[0].page_content
        doc_hash = self.get_document_hash(doc_content)
        if not self.check_doc_exists_in_vector_store(doc_hash):
            print("Got new document, adding to vector store...")

            chunks = self.split_document(doc)
            docs_array, meta_array = [], []
            for chunk in chunks:
                docs_array.append(chunk.page_content)
                meta_array.append({'document_hash' : doc_hash, 'session_id': session_id})

            self.vector_store.add_texts(texts = docs_array, metadatas = meta_array)
        else:
            print("Document already exists, skipping")

    def query_with_document(self, user_question, session_id):

        similar_docs = self.vector_store.similarity_search(
            query = user_question,
            k=5,
            filters=f"session_id eq '{session_id}'"
        )

        context_from_docs = "\n\n".join([doc.page_content for doc in similar_docs])

        prompt_template = """
        You are given the following context from the document:
        {context}

        Using this context, answer the following question:
        "{user_question}"

        Answer:
        """

        enriched_prompt = prompt_template.format(
            context=context_from_docs,
            user_question=user_question
        )
        llm_manager = LLMManager(self.conf)
        llm = llm_manager.connect()
        response = llm.invoke([{"role" : "user", "content": enriched_prompt}])
        answer = response.content

        return answer.strip()




