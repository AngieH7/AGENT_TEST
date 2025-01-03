from dotenv import load_dotenv

_ = load_dotenv()

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage

memory = SqliteSaver.from_conn_string(":memory:")

class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revisions: int

from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

MANAGER_PROMPT = """You are a senior client service manager tasked with creating the detail plans \
to answer customer's questions or requirments. The detailed plans should include all the information needed to be \
from the database. Ask questions back to the customers until the requirments are clear"""

AGENT_PROMPT = """You are a junior customer service agent.\
Generate the concise answer for the customer's questions based on the initial plan step by step. \
If the quality assurance person provides critique, respond with a revised version of your previous attempts.\
The answer needs to include the information and follow up questions if needed.\
Do not include the wording from the critiques. The answer should be precise. \
Utilize all the information below as needed: 

------

{content}"""

QUALITYA_PROMPT = """You are a customer service quality assurance person validating the customer \
service agent answer to the customer. \
Generate critique and recommendations for the agent's answer. \
The requirements include the answer if helpful, concise and accurate. \
Provide detailed recommendations, including requests for tones, wording, detail level, etc."""

POLICY_PROMPT = """You are an expert with the apple product policy. \
Generate the answers based on the policy and the customer questions:
-----
{content}"""

SAGENT_PROMPT = """You are a senior customer service agent.\
Generate the revised answer to the customer's questions, criticques and the initial plan step by step. \
Utilize all the information below as needed: 

------

{content}"""


from langchain_core.pydantic_v1 import BaseModel

class Queries(BaseModel):
    queries: List[str]

from tavily import TavilyClient
import os
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def plan_node(state: AgentState):
    messages = [
        SystemMessage(content=MANAGER_PROMPT), 
        HumanMessage(content=state['task'])
    ]
    response = model.invoke(messages)
    return {"plan": response.content}

def research_plan_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=POLICY_PROMPT),
        HumanMessage(content=state['task'])
    ])
    content = state['content'] or []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return {"content": content}

def generation_node(state: AgentState):
    content = "\n\n".join(state['content'] or [])
    user_message = HumanMessage(
        content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}")
    messages = [
        SystemMessage(
            content=AGENT_PROMPT.format(content=content)
        ),
        user_message
        ]
    response = model.invoke(messages)
    return {
        "draft": response.content, 
        "revision_number": state.get("revision_number", 1) + 1
    }


def reflection_node(state: AgentState):
    messages = [
        SystemMessage(content=QUALITYA_PROMPT), 
        HumanMessage(content=state['draft'])
    ]
    response = model.invoke(messages)
    return {"critique": response.content}

def research_critique_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=SAGENT_PROMPT),
        HumanMessage(content=state['critique'])
    ])
    content = state['content'] or []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return {"content": content}

def should_continue(state):
    print(f'current:{state["revision_number"]}')
    print(f'limit:{state["max_revisions"]}')
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "reflect"

builder = StateGraph(AgentState)

builder.add_node("planner", plan_node)
builder.add_node("generate", generation_node)
builder.add_node("reflect", reflection_node)
builder.add_node("research_plan", research_plan_node)
builder.add_node("research_critique_node", research_critique_node)

builder.set_entry_point("planner")

builder.add_conditional_edges(
    "generate", 
    should_continue, 
    {END: END, "reflect": "reflect"}
)

builder.add_edge("planner", "research_plan")
builder.add_edge("research_plan", "generate")
builder.add_edge("reflect", "research_critique_node")
builder.add_edge("research_critique_node", "generate")

graph = builder.compile(checkpointer=memory)

thread = {"configurable": {"thread_id": "1"}}

for s in graph.stream({
    'task': "what is the refund policy of the product apple 16 phone",
    "max_revisions": 2,
    "revision_number": 1,
}, thread):
    print(s)
print(f"Final state: {s['generate']['draft']}")