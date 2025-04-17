import os
import asyncio
import logging
from dotenv import load_dotenv
from llama_index.core.workflow import Context
from llama_index.tools.tavily_research import TavilyToolSpec
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.agent.workflow import ReActAgent, FunctionAgent, AgentWorkflow
from tools import get_pinecone_content

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

load_dotenv()

if not os.getenv("GOOGLE_API_KEY") or not os.getenv("TAVILY_API_KEY"):
    logger.error("Missing GOOGLE_API_KEY or TAVILY_API_KEY in environment variables")
    raise ValueError("Missing GOOGLE_API_KEY or TAVILY_API_KEY in environment variables")

logger.info("Environment variables loaded successfully")

tavily_tool = TavilyToolSpec(api_key=os.getenv("TAVILY_API_KEY"))
search_web = tavily_tool.to_tool_list()[0]

llm = GoogleGenAI(
    model="models/gemini-1.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
)

logger.info("GoogleGenAI LLM configured successfully")

search_agent = ReActAgent(
    name="SearchAgent",
    description="Useful for searching for schemes from the database.",
    system_prompt=(
        "You are the SearchAgent who searches for schemes. "
        "You search for schemes and structure them properly. "
        "You ensure that you provide schemes with their proper descriptions. "
        "You should provide all the relevant details of each scheme."
        """
        Example:
        1. Maha DBT (Maharashtra Direct Benefit Transfer) - Agricultural Machinery Subsidies
            - Eligibility: Farmers in Maharashtra. You are eligible as you farm in Maharashtra. Specific subsidy eligibility varies by program.
            - Benefits: Subsidies on agricultural machinery. Reduces the cost of purchasing essential equipment for your wheat farm.
            - Steps: Explore available schemes at https://mahadbt.mahaonline.gov.in/. Look for agricultural equipment subsidies. Check individual program requirements.
        2. SMAM (Sub-Mission on Agricultural Mechanization)
            - Eligibility: Small and marginal farmers. Your farm size likely qualifies; check specific eligibility criteria.
            - Benefits: Subsidies on agricultural machinery. Reduces the cost of equipment, improving efficiency and yield.
            - Steps: Contact your local agricultural department. They can provide information on available subsidies and the application process. Check your state's Department of Agriculture website for more details.
        3. Soil Health Card Scheme
            - Eligibility: All farmers. You are eligible.
            - Benefits: Free soil testing to understand nutrient levels in your soil. Allows for tailored fertilizer use, improving crop yields and reducing costs.
            - Steps: Contact your local agricultural department to obtain your Soil Health Card.
        4. Crop Diversification Scheme (Example - Specific scheme details vary by state)
            - Eligibility: Farmers interested in diversifying crops. This depends on your state's specific program.
            - Benefits: Financial assistance and training to grow alternative crops alongside wheat. Reduces reliance on a single crop and increases income potential.
            - Steps: Contact your local agricultural extension office for information on available crop diversification programs in your area.
        Disclaimer: Eligibility criteria and benefits can change. Always check with official sources for the latest information. Contact your local agricultural department for personalized advice and assistance.
        """
    ),
    llm=llm,
    tools=[get_pinecone_content],
    can_handoff_to=["RecommendAgent"]
)

recommend_agent = ReActAgent(
    name="RecommendAgent",
    description="Useful for recommending schemes according to the profile.",
    system_prompt=(
        "You are the RecommendAgent who recommends schemes to farmers. "
        "You recommend schemes according to the farmer's profile. "
        "You suggest the best schemes from the given schemes. "
        "You can use SearchAgent to get the schemes from the database. "
        "You ensure that each farmer will get the highest benefit possible."
        "Provide the schemes in the list format with the their proper descriptions."
        "Remember that you have to suggest only schemes, nothing else."
    ),
    llm=llm,
    can_handoff_to=["SearchAgent", "ReviewAgent"]
)

review_agent = FunctionAgent(
    name="ReviewAgent",
    description="Useful for reviewing the schemes for farmers.",
    system_prompt=(
        "You are the ReviewAgent who reviews the suggested schemes for the given farmer profile. "
        "You review the schemes to ensure the farmer gets the highest benefits for themselves and their family."
    ),
    llm=llm,
    can_handoff_to=["RecommendAgent"]
)

agent_workflow = AgentWorkflow(
    agents=[search_agent, recommend_agent, review_agent],
    root_agent=recommend_agent.name,
    initial_state={
        "pinecone_results": []
    }
)

logger.info("Agent workflow initialized successfully")

async def run_workflow():
    try:
        result = await agent_workflow.run(
            user_msg=""" 
                Suggest me the schemes for the given farmer:
                "basic_information": {
                    "state": "Haryana",
                    "district": "Karnal",
                    "village": "Bahlolpur"
                },
                "farm_information": {
                    "land_size": "2 hectares",
                    "main_crop": "wheat, rice"
                },
                "land_irrigation": {
                    "land_ownership": "Owned",
                    "irrigation_type": "Rain-fed",
                    "annual_income": 145000
                },
                "personal_details": {
                    "caste_category": "General",
                    "bank_account": "Yes",
                    "current_schemes": "none"
                }
            """
        )
        logger.info("Workflow executed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during workflow execution: {str(e)}")
        raise

if __name__ == "__main__":
    result = asyncio.run(run_workflow())
    print(result)
