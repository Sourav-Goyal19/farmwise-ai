import os
import logging
from dotenv import load_dotenv
from langchain_cohere import CohereEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document
from typing import TypedDict, Optional, Dict, Any, List
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from tools import pinecone_content
from tavily import TavilyClient
from langchain.tools import tool

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

pinecone_api_key = os.getenv("PINECONE_API_KEY")
cohere_api_key = os.getenv("COHERE_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")
pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

embeddings = CohereEmbeddings(cohere_api_key=cohere_api_key, model="embed-english-v3.0")
pc = PineconeVectorStore.from_existing_index(
    index_name="farmwise-ai",
    embedding=embeddings
)

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=google_api_key)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def tavily_search(query: str):
    """Searches online for the given query and summarizes them."""
    try:
        search_results = tavily.search(query=query)
        return search_results
    except Exception as e:
        logging.error("Exception caused in tavily search", e);
        return {}

class FarmerState(TypedDict):
    profile: Dict[str, str]
    schemes: List[Document]
    recommendations: Optional[str]
    visuals: Optional[List[str]]

tools = [pinecone_content]
tools2 = [tavily_search]

prompt_template = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt_template)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def profile_analysis_node(state: FarmerState) -> Dict[str, Any]:
    logger.info("[Profile Analysis] Starting analysis of farmer profile.")
    profile = state["profile"]
    derived = {}
    try:
        land_size = float(profile["land_size"].split()[0]) if "hectares" in profile["land_size"] else 0
        derived["farmer_type"] = "small" if land_size <= 2 else "medium" if land_size <= 5 else "large"
        derived["needs_insurance"] = "yes" if profile["irrigation"] == "rain-fed" else "no"
        derived["seed_cost_estimate"] = "24000"  # ₹/hectare for wheat
        logger.info("[Profile Analysis] Successfully derived profile attributes: %s", derived)
    except Exception as e:
        logger.warning("[Profile Analysis] Failed to parse profile: %s", str(e))
        derived["farmer_type"] = "unknown"
        derived["needs_insurance"] = "unknown"
        derived["seed_cost_estimate"] = "unknown"
    profile.update(derived)
    logger.info("[Profile Analysis] Enhanced profile: %s", profile)
    return {"profile": profile, "schemes": [], "recommendations": None, "visuals": []}

def react_agent_node(state: FarmerState) -> Dict[str, Any]:
    logger.info("[ReAct Agent] Starting agent to suggest schemes from Pinecone.")
    profile = state["profile"]
    combined_input = f"""
    You're an expert on Indian agricultural schemes. Given a farmer's profile and scheme data, provide 4-6 detailed recommendations. For each:
        - Confirm eligibility with profile specifics (e.g., '2 hectares = small farmer', 'rain-fed needs insurance').
        - Provide steps with URLs (e.g., https://pmkisan.gov.in) or local instructions (e.g., 'Visit your district office').
        Include national schemes (PM-KISAN, PMFBY, SMAM) and state-specific ones (e.g., Maha DBT for Maharashtra). Use markdown with headers (## Scheme Name).
    If farmer's profile is not provided, then suggest the schemes from the database that are relevant for the farmers.
    Remember that don't suggest only the popular one's that already everybody knows like PM-Kisan, etc.

    **Important Note** - You must have to provide schemes in the end, even they lacks some information. 

    Example:
    
    """ 
    # Farmer-profile: {profile}

    try:
        response = agent_executor.invoke({"input": combined_input})
        logger.info("[ReAct Agent] Agent response: %s", response["output"][:100] if "output" in response else "No output")

        schemes = []
        recommendations = response.get("output", "No recommendations generated due to insufficient Pinecone data.")

        tool_outputs = response.get("intermediate_steps", [])
        for step in tool_outputs:
            if isinstance(step[1], list) and all(isinstance(doc, Document) for doc in step[1]):
                schemes.extend(step[1])

        if not schemes:
            schemes.append(Document(
                page_content="No schemes found in Pinecone. Ensure the database contains relevant data.",
                metadata={"source": "placeholder"}
            ))

        return {
            "schemes": schemes,
            "recommendations": recommendations,
            "visuals": []
        }
    except Exception as e:
        logger.error("[ReAct Agent] Execution failed: %s", str(e))
        return {"schemes": [], "recommendations": "Error generating recommendations.", "visuals": []}

def refine_agent_node(state: FarmerState) -> Dict[str, Any]:
    logger.info("[Refine Agent] Starting refinement of recommendations.")
    agent2 = create_react_agent(llm, tools2, prompt_template)
    agent_executor2 = AgentExecutor(agent=agent2, tools=tools2, verbose=True, handle_parsing_errors=True)

    schemes = state["recommendations"]
    combined_input = f"""
        You're an expert in completing and enhancing agricultural scheme information for Indian farmers.
        Your job is to fill in or verify missing or vague details using reliable online data. Use bullet points for clarity.
        Prefix each scheme with a markdown heading: `# Scheme Name`.
        You have to search for each scheme one by one with your tool. One at a time.

        Even if you can't find much information, provide your best effort using general knowledge. Make sure it's helpful to the farmer.

        <Schemes>
        {schemes}
        </Schemes>
    """

    try:
        response = agent_executor2.invoke({"input": combined_input})
        refined_output = response.get("output", "No detailed information found.")
        logger.info("[Refine Agent] Refined recommendations: %s", refined_output[:100])
        return {
            "profile": state["profile"],
            "schemes": state["schemes"],
            "recommendations": refined_output,
            "visuals": state.get("visuals", [])
        }
    except Exception as e:
        logger.error("[Refine Agent] Execution failed: %s", str(e))
        return {
            "profile": state["profile"],
            "schemes": state["schemes"],
            "recommendations": "Error while refining recommendations.",
            "visuals": state.get("visuals", [])
        } 

workflow = StateGraph(FarmerState)

workflow.add_node("profile_analysis", profile_analysis_node)
workflow.add_node("react_agent", react_agent_node)
workflow.add_node("refine_agent", refine_agent_node)

workflow.set_entry_point("profile_analysis")
workflow.add_edge("profile_analysis", "react_agent")
workflow.add_edge("react_agent", "refine_agent")
workflow.add_edge("refine_agent", END)

app = workflow.compile()

def run_workflow(initial_state: Optional[FarmerState] = None) -> FarmerState:
    logger.info("[Workflow] Starting execution.")
    default_state: FarmerState = {
        "profile": {"village": "hasdar", "district": "Pune", "state": "Maharashtra", "land_size": "2 hectares", "land_ownership": "owned", "crop_type": "wheat", "irrigation": "rain-fed", "income": "150000", "caste_category": "general", "bank_account": "yes", "existing_schemes": "none"},
        "schemes": [],
        "recommendations": None,
        "visuals": []
    }
    state = initial_state or default_state

    try:
        final_state = app.invoke(state)
        logger.info("[Workflow] Execution completed successfully.")
        return final_state
    except Exception as e:
        logger.error("[Workflow] Execution failed: %s", str(e))
        raise

if __name__ == "__main__":
    result = run_workflow()
    print("Final Schemes:", result["schemes"])
    print("Recommendations:", result["recommendations"])