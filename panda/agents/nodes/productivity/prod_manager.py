from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from panda.core.llm.factory import LLMFactory, LLMProvider
from panda.core.llm.prompts import PRODUCTIVITY_MANAGER_PROMPT
from panda.models.agents.state import ProductivityState
from panda.models.agents.response import ProductivityRouterResponse


llm_client = LLMFactory.create_client(
    provider=LLMProvider.GEMINI,
    model_name="gemini-2.5-flash",
)

manager_llm = llm_client.with_structured_output(ProductivityRouterResponse)
manager_prompt = ChatPromptTemplate.from_messages([
    ("system", PRODUCTIVITY_MANAGER_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])
manager_chain = manager_prompt | manager_llm

async def productivity_manager_node(state: ProductivityState):
    decision = await manager_chain.ainvoke({"messages": state["messages"]})
    return {"next_step": decision.next_step}