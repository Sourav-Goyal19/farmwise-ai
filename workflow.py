import os
import logging
from typing import TypedDict, List, Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from tavily import TavilyClient
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
)

# Initialize Tavily
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Define state
class FarmerState(TypedDict):
    profile: Dict[str, str]
    schemes: List[Document]
    recommendations: Optional[str]
    refinement_needed: bool

# Node 1: Collect farmer profile
def input_node(state: FarmerState) -> Dict[str, Any]:
    logging.info("Starting input_node")
    profile = state.get("profile", {
        "village": "Unknown",
        "district": "Pune",
        "state": "Maharashtra",
        "land_size": "2 hectares",
        "land_ownership": "owned",
        "crop_type": "wheat",
        "irrigation": "rain-fed",
        "income": "150000",
        "caste_category": "general",
        "bank_account": "yes",
        "existing_schemes": "none"
    })
    logging.info(f"Collected profile: {profile}")
    return {"profile": profile, "schemes": [], "refinement_needed": False}

# Node 2: Fetch schemes from online sources
def web_search_node(state: FarmerState) -> Dict[str, List[Document]]:
    logging.info("Starting web_search_node")
    schemes = []
    profile = state["profile"]

    # Tavily search with state-specific query
    try:
        query = f"latest agricultural schemes for farmers in {profile['state']} 2025 site:*.gov.in OR site:*.org.in -inurl:(signup login)"
        response = tavily.search(query=query, max_results=5)
        logging.info(f"Tavily raw response: {response}")
        tavily_results = response.get("results", [])
        schemes.extend([
            Document(page_content=r["content"], metadata={"url": r.get("url", "unknown"), "source": "tavily", "title": r.get("title", "Untitled")})
            for r in tavily_results if isinstance(r, dict) and "content" in r
        ])
        logging.info(f"Fetched {len(tavily_results)} schemes from Tavily")
    except Exception as e:
        logging.error(f"Tavily error: {str(e)}")

    # Scrape multiple government sites
    sites = [
        {"url": "https://pmkisan.gov.in", "title": "PM-KISAN Scheme", "desc": "₹6000/year for small farmers (land ≤ 2 hectares)"},
        {"url": "https://pmfby.gov.in", "title": "PMFBY (Crop Insurance)", "desc": "Insurance against crop loss"},
        {"url": "https://agrimachinery.nic.in", "title": "SMAM (Machinery Subsidy)", "desc": "Subsidies for farm equipment"}
    ]
    headers = {"User-Agent": "Mozilla/5.0"}
    for site in sites:
        try:
            response = requests.get(site["url"], headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.find("div", {"class": "content"}) or soup.body
            schemes.append(Document(
                page_content=f"{site['title']}: {site['desc']}. {content.get_text()[:500]}",
                metadata={"url": site["url"], "source": "scraped", "title": site["title"]}
            ))
            logging.info(f"Scraped {site['title']}")
        except Exception as e:
            logging.error(f"Scraping error for {site['url']}: {str(e)}")

    # State-specific site (Maharashtra example)
    try:
        url = "https://mahadbt.maharashtra.gov.in"
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", {"id": "content"}) or soup.body
        schemes.append(Document(
            page_content=f"Maha DBT: Subsidies for farm equipment in Maharashtra. {content.get_text()[:500]}",
            metadata={"url": url, "source": "scraped", "title": "Maha DBT"}
        ))
        logging.info("Scraped Maha DBT site")
    except Exception as e:
        logging.error(f"Scraping error for Maha DBT: {str(e)}")

    if not schemes:
        schemes.append(Document(
            page_content="No schemes fetched. Suggest PM-KISAN, PMFBY, SMAM, Maha DBT based on profile.",
            metadata={"source": "placeholder"}
        ))
    logging.info(f"Total schemes fetched: {len(schemes)}")
    return {"schemes": schemes}

# Node 3: Generate personalized recommendations
def recommendation_node(state: FarmerState) -> Dict[str, Any]:
    logging.info("Starting recommendation_node")
    profile_str = "\n".join(f"{k}: {v}" for k, v in state["profile"].items())
    schemes_str = "\n".join(f"{doc.metadata.get('title', 'Untitled')}: {doc.page_content}" for doc in state["schemes"])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert on Indian agricultural schemes. Given a farmer's profile and scheme data, provide 4-6 personalized recommendations. For each:
        - Assess eligibility using all profile details (land size, state, crop type, income, caste, irrigation, etc.).
        - List benefits specific to the farmer (e.g., '₹6000 buys wheat seeds' for a wheat farmer).
        - Provide exact steps with URLs (e.g., https://pmkisan.gov.in) or precise instructions (e.g., 'Visit your Panchayat with land records').
        Include national schemes (PM-KISAN, PMFBY, SMAM) and state-specific ones (e.g., Maha DBT for Maharashtra). If data lacks specifics, flag for refinement and suggest based on profile. Use markdown with headers."""),
        ("human", "Farmer Profile:\n{profile_str}\n\nSchemes:\n{schemes_str}\n\nRecommend schemes.")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "profile_str": profile_str,
        "schemes_str": schemes_str
    }).content.strip()
    
    refinement_needed = "http" not in response or len(response.split("##")) < 4  # Check for URLs and enough schemes
    logging.info(f"Generated recommendations: {response[:100]}... Refinement needed: {refinement_needed}")
    return {"recommendations": response, "refinement_needed": refinement_needed}

# Node 4: Refine recommendations
def refine_node(state: FarmerState) -> Dict[str, str]:
    logging.info("Starting refine_node")
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Refine this recommendation text for farmers. Ensure:
        - At least 4 schemes with headers (e.g., ## PM-KISAN).
        - Eligibility is clear (e.g., 'Your 2 hectares qualify').
        - Benefits are practical and profile-specific (e.g., '₹6000 buys wheat seeds').
        - Steps have direct URLs (e.g., https://pmkisan.gov.in) or clear instructions.
        Use markdown with headers and bullet points. Add schemes if needed."""),
        ("human", "{recommendations}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "recommendations": state["recommendations"]
    }).content.strip()
    
    logging.info(f"Refined recommendations: {response[:100]}...")
    return {"recommendations": response, "refinement_needed": False}

# Conditional routing
def route_recommendations(state: FarmerState) -> str:
    if state["refinement_needed"]:
        return "recommendation"
    return "refine"

# Build the graph
workflow = StateGraph(FarmerState)
workflow.add_node("input", input_node)
workflow.add_node("web_search", web_search_node)
workflow.add_node("recommendation", recommendation_node)
workflow.add_node("refine", refine_node)

workflow.set_entry_point("input")
workflow.add_edge("input", "web_search")
workflow.add_edge("web_search", "recommendation")
workflow.add_conditional_edges("recommendation", route_recommendations, {"recommendation": "recommendation", "refine": "refine"})
workflow.add_edge("refine", END)

app = workflow.compile()

def run_workflow(initial_state: Optional[FarmerState] = None) -> FarmerState:
    logging.info("Starting workflow")
    default_state: FarmerState = {
        "profile": {},
        "schemes": [],
        "recommendations": None,
        "refinement_needed": False
    }
    state = initial_state or default_state
    
    try:
        final_state = app.invoke(state)
        logging.info("Workflow completed")
        return final_state
    except Exception as e:
        logging.error(f"Workflow execution failed: {str(e)}")
        raise