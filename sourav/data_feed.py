import os
import logging
from dotenv import load_dotenv
from pinecone import Pinecone, NotFoundException
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import StorageContext, VectorStoreIndex, SimpleDirectoryReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

load_dotenv()

if not os.getenv("COHERE_API_KEY") or not os.getenv("PINECONE_API_KEY"):
    logger.error("Missing COHERE_API_KEY or PINECONE_API_KEY in environment variables")
    raise ValueError("Missing COHERE_API_KEY or PINECONE_API_KEY in environment variables")
else:
    logger.info("Environment variables loaded successfully")

embed_model = GoogleGenAIEmbedding(
    model_name="models/embedding-001", 
    api_key=os.getenv("GOOGLE_API_KEY"), 
)
logger.info("Embedding model initialized")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
logger.info("Pinecone client initialized")

index_name = "farmwise-ai"
try:
    pinecone_index = pc.Index(index_name)
    logger.info(f"Index '{index_name}' found.")
except NotFoundException:
    logger.warning(f"Index '{index_name}' not found, creating a new one.")
    try:
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}, 
        )
        pinecone_index = pc.Index(index_name)
        logger.info(f"Index '{index_name}' created successfully.")
    except Exception as e:
        logger.error(f"Failed to create Pinecone index: {str(e)}")
        raise

# try:
#     documents = SimpleDirectoryReader("./docs").load_data()
#     logger.info(f"{len(documents)} documents loaded successfully.")
# except Exception as e:
#     logger.error(f"Failed to load documents: {str(e)}")
#     raise

vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
logger.info("Storage context and vector store set up successfully")

# def safe_embed_request(embed_model, documents_batch):
#     try:
#         return embed_model.get_text_embedding_batch(documents_batch)
#     except Exception as e:
#         logger.warning("Rate limit exceeded. Retrying after 60 seconds...")
#         time.sleep(60) 
#         return safe_embed_request(embed_model, documents_batch)

# try:
#     index = VectorStoreIndex.from_documents(
#         documents=documents,
#         embed_model=embed_model,
#         storage_context=storage_context
#     )
#     logger.info("Index created successfully.")
# except Exception as e:
#     logger.error(f"Failed to create index: {str(e)}")
#     raise
