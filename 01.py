# Imports and Setup
import os,json
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph ,END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage ,HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq

# Environment and API Setup
# Load environment variables
load_dotenv()

# Get API keys from environment
groq_api_key = os.getenv("GROQ_API_KEY")

# LLM Initialization
#Shared LLM Instance
llm=ChatGroq(model="llama3-8b-8192", api_key=groq_api_key)

# State Schema Definition
#---shared state schema --
class AgentState(TypedDict):
    goal : str
    tasks  :List[str]
    results : List[str]
    critique : str
    approved : bool
    iterations : int

# Tool Initialization
#Search Tool called by the agents
search = DuckDuckGoSearchRun()

# Planner Function
def planner(state: AgentState) -> AgentState:
    system = """You are a planning agent. Break the user's goal into
at most 5 concrete, actionable tasks. Respond ONLY with a
valid JSON array of strings. No preamble, no markdown."""

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=f"Goal: {state['goal']}")
    ]

    response = llm.invoke(messages).content.strip()

    try:
        clean = response.replace("```json", "").replace("```", "").strip()
        tasks = json.loads(clean) 
    except json.JSONDecodeError:
        tasks = [response]  # fallback: treat whole response as one task

    print(f"\n[Planner] Generated {len(tasks)} tasks:")
    for i, t in enumerate(tasks):
        print(f" {i+1}. {t}") 

    return {**state, "tasks": tasks}
