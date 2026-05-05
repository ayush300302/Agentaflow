# Imports and Setup
import os,json
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, END, START
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
llm=ChatGroq(model="llama-3.1-8b-instant", api_key=groq_api_key)

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


def executor(state: AgentState) -> AgentState:
    results = []
    critique_ctx = ""

    if state["critique"]:
        critique_ctx = f"\n\nYour previous attempt was rejected. Critique: {state['critique']}\n\nImprove your output accordingly."

    for task in state["tasks"]:
        system = f"""You are an execution agent. Complete the task below thoroughly. Use web search if you need current information.{critique_ctx}"""

        # try web search for research tasks
        search_ctx = ""
        try:
            search_result = search.run(task[:100])
            search_ctx = f"\n\nWeb search result for context:\n{search_result[:800]}"
        except:
            pass

        messages = [
            SystemMessage(content=system),
            HumanMessage(content=f"Task: {task}{search_ctx}")
        ]

        result = llm.invoke(messages).content
        results.append(result)

        print(f"\n[Executor] Task: {task[:60]}...\n  Result: {result[:120]}...")

    return {**state, "results": results}


##########Main######
graph =StateGraph(AgentState)
graph.add_node("planner", planner)
graph.add_node("executor", executor)

# Add edges to connect START to planner, planner to executor, and executor to END
graph.add_edge(START, "planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", END)

app =graph.compile()
 
 # ---runit---
initial_state = {
    "goal":  "Research and summarise the top 3 trends in generative AI for 2025",
    "tasks" : [],
    "results": [],
    "critique" : [],
    "approved" : False,
    "iterations" : 0
}

final_state =app.invoke(initial_state)


print("\n FINAL OUTPUT")
for i,(tasks,result) in enumerate(zip(final_state["tasks"],final_state["results"])):
    print(f"\n[Task {i+1}] {tasks}\n{result}")
print(f"\nCompleted in {final_state['iterations']} iterations")

def executor(state: AgentState) -> AgentState:
    results = []
    critique_ctx = ""

    if state["critique"]:
        critique_ctx = f"\n\nYour previous attempt was rejected. Critique: {state['critique']}\n\nImprove your output accordingly."

    for task in state["tasks"]:
        system = f"""You are an execution agent. Complete the task below thoroughly. Use web search if you need current information.{critique_ctx}"""

        # try web search for research tasks
        search_ctx = ""
        try:
            search_result = search.run(task[:100])
            search_ctx = f"\n\nWeb search result for context:\n{search_result[:800]}"
        except:
            pass

        messages = [
            SystemMessage(content=system),
            HumanMessage(content=f"Task: {task}{search_ctx}")
        ]

        result = llm.invoke(messages).content
        results.append(result)

        print(f"\n[Executor] Task: {task[:60]}...\n  Result: {result[:120]}...")

    return {**state, "results": results}