# Day 30
# Structured Output with Pydantic

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_snowflake import ChatSnowflake
from pydantic import BaseModel, Field
from typing import Literal

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Define output schema
class PlantRecommendation(BaseModel):
    name: str = Field(description="Plant name")
    water: Literal["Low", "Medium", "High"] = Field(description="Water requirement")
    light: Literal["Low", "Medium", "High"] = Field(description="Light requirement")
    difficulty: Literal["Beginner", "Intermediate", "Expert"] = Field(description="Care difficulty level")
    care_tips: str = Field(description="Brief care instructions")

# Create parser
parser = PydanticOutputParser(pydantic_object=PlantRecommendation)

# Create template with format instructions
template = ChatPromptTemplate.from_messages([
    ("system", "You are a plant expert. {format_instructions}"),
    ("human", "Recommend a plant for: {location}, {experience} experience, {space} space")
])

# Create LLM and chain
llm = ChatSnowflake(model="claude-3-5-sonnet", session=session)
chain = template | llm | parser

# UI
st.title(":material/potted_plant: Plant Recommender")
location = st.text_input("Location:", "Apartment in Seattle")
experience = st.selectbox("Experience:", ["Beginner", "Intermediate", "Expert"])
space = st.text_input("Space:", "Small desk")

if st.button("Get Recommendation"):
    result = chain.invoke({
        "location": location,
        "experience": experience,
        "space": space,
        "format_instructions": parser.get_format_instructions()
    })

    st.subheader(f":material/eco: {result.name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Water", result.water)
    col2.metric("Light", result.light)
    col3.metric("Difficulty", result.difficulty)
    st.info(f"**Care:** {result.care_tips}")

    with st.expander(":material/description: See raw JSON response"):
        st.json(result.model_dump())

st.divider()
st.caption("Day 30: Structured Output with Pydantic | 30 Days of AI with Streamlit")
