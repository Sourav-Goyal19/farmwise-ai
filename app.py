import os
import streamlit as st
from dotenv import load_dotenv
from workflow import run_workflow, FarmerState

# Load environment variables
load_dotenv()

# Streamlit configuration
st.set_page_config(page_title="Agricultural Subsidy Advisor", page_icon="🌾", layout="wide")

# Header
st.title("🌾 Agricultural Subsidy & Scheme Advisor")
st.markdown("""
    Provide your farm details below to get tailored scheme recommendations, including eligibility, benefits, and steps to apply.
""")

# Sidebar form with validation
st.sidebar.header("Your Farm Details")
with st.sidebar.form(key="farmer_form"):
    st.markdown("**Required Fields**")
    district = st.text_input("District *", value="Pune", help="Enter your district (e.g., Pune)")
    state = st.text_input("State *", value="Maharashtra", help="Enter your state (e.g., Maharashtra)")
    land_size = st.text_input("Land Size (e.g., 2 hectares) *", value="2 hectares", help="Include units like 'hectares' or 'acres'")
    crop_type = st.text_input("Crop Type (e.g., wheat) *", value="wheat", help="Main crop you grow")

    st.markdown("**Optional Fields** (More details = Better results)")
    village = st.text_input("Village", value="", help="Your village name for local schemes")
    ownership = st.selectbox("Land Ownership", ["Owned", "Leased"], index=0)
    irrigation = st.selectbox("Irrigation", ["Irrigated", "Rain-fed"], index=1)
    income = st.text_input("Annual Income (e.g., 150000)", value="150000", help="In rupees")
    caste_category = st.selectbox("Caste Category", ["General", "OBC", "SC", "ST"], index=0)
    bank_account = st.selectbox("Bank Account?", ["Yes", "No"], index=0)
    existing_schemes = st.text_input("Current Schemes (if any, else 'none')", value="none", help="E.g., PM-KISAN")

    submit_button = st.form_submit_button(label="Get Recommendations")

# Main content
if submit_button:
    # Input validation
    if not all([district, state, land_size, crop_type]):
        st.error("Please fill all required fields (marked with *)!")
    else:
        with st.spinner("Fetching your personalized recommendations..."):
            initial_state: FarmerState = {
                "profile": {
                    "village": village,
                    "district": district,
                    "state": state,
                    "land_size": land_size,
                    "land_ownership": ownership.lower(),
                    "crop_type": crop_type,
                    "irrigation": irrigation.lower(),
                    "income": income,
                    "caste_category": caste_category.lower(),
                    "bank_account": bank_account.lower(),
                    "existing_schemes": existing_schemes.lower()
                },
                "schemes": [],
                "recommendations": None,
                "refinement_needed": False
            }

            try:
                result = run_workflow(initial_state=initial_state)
                st.subheader("Your Personalized Scheme Recommendations")

                # Split recommendations into sections for expanders
                sections = result["recommendations"].split("##")[1:]  # Skip empty first split
                for section in sections:
                    if section.strip():
                        title = section.split("\n")[0].strip()
                        content = "\n".join(section.split("\n")[1:]).strip()
                        with st.expander(title, expanded=True):
                            st.markdown(content)

                st.info("Tip: Add your village name or update details for more local schemes!")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.write("Check your inputs or API keys and try again.")
