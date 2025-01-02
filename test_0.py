from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain_openai import ChatOpenAI

from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(api_key="ollama",model="mistral",base_url="http://localhost:11434/v1",)

tools = [TavilySearchResults(max_results=1)]

llm_with_tools = llm.bind_tools(tools)

prompt = hub.pull("wfh/react-agent-executor")
prompt.pretty_print()

agent_executor = create_react_agent(llm_with_tools, tools, messages_modifier=prompt)

response=agent_executor.invoke({"messages": [("user", "What is Oracle database")]})

for message in response['messages']:
    print(message.content)