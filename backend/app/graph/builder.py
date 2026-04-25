from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import traceable

load_dotenv()


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0.7,
    max_output_tokens=100
)

@traceable
def chatbot_node(state: ChatState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def build_graph(checkpointer=None):
    builder = StateGraph(ChatState)
    builder.add_node("chatbot", chatbot_node)
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)

   
    return builder.compile(checkpointer=checkpointer)

