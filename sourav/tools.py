import os
import logging
from dotenv import load_dotenv
from langchain.tools import tool
from data_feed import vector_store
from llama_index.core.workflow import Context
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from langchain.tools import tool
from llama_index.core.workflow import Context

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    logger.error("GOOGLE_API_KEY is not set in environment variables")
    raise ValueError("GOOGLE_API_KEY is not set in environment variables")

logger.info("GOOGLE_API_KEY environment variable loaded successfully")

Settings.embed_model = GoogleGenAIEmbedding(
    model_name="models/embedding-001",
    api_key=os.getenv("GOOGLE_API_KEY"),
)

logger.info("GoogleGenAIEmbedding model configured successfully")

try:
    vector_index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    logger.info("Vector index created successfully")
except Exception as e:
    logger.error(f"Failed to create vector index: {str(e)}")
    raise

retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=10)
logger.info("Retriever configured successfully")

@tool
def pinecone_content(query: str) -> list[dict]:
    """Retrieve the top 5 scheme results from the pinecone according to the upcoming query."""
    query = "Top 5 schemes for farmer"
    try:
        if not query or not isinstance(query, str):
            logger.error("Query must be a non-empty string")
            return []

        nodes = retriever.retrieve(query)
        results = []
        for i, node in enumerate(nodes, 1):
            results.append({
                "result": i,
                "score": round(node.score, 4),
                "text": node.get_content(),
                "metadata": node.metadata
            })

        logger.info(f"Retrieved {len(nodes)} nodes for query: {query}")
        return results

    except Exception as e:
        logger.error(f"Error during retrieval: {str(e)}")
        return []

async def get_pinecone_content(ctx:Context, query: str):
    """Retrieve the top scheme results from the pinecone according to the upcoming query."""
    # query = "All schemes for farmer"
    try:
        if not query or not isinstance(query, str):
            logger.error("Query must be a non-empty string")
            return []

        nodes = retriever.retrieve(query)
        results = []
        for i, node in enumerate(nodes, 1):
            results.append({
                "result": i,
                "score": round(node.score, 4),
                "text": node.get_content(),
                "metadata": node.metadata
            })

        logger.info(f"Retrieved {len(nodes)} nodes for query: {query}")
        return results

    except Exception as e:
        logger.error(f"Error during retrieval: {str(e)}")
        return []
