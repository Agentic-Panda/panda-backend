from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from panda.core.llm.factory import LLMFactory, LLMProvider
from panda.core.llm.prompts import MASTER_SUPERVISOR_PROMPT
from panda.models.agents.state import MasterState
from panda.models.agents.response import SupervisorRouterResponse



llm_client = LLMFactory.create_client(
    provider=LLMProvider.GEMINI,
    model_name="gemini-2.5-flash",
)

supervisor_llm = llm_client.with_structured_output(SupervisorRouterResponse)

supervisor_prompt = ChatPromptTemplate.from_messages([
        ("system", MASTER_SUPERVISOR_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

chain = supervisor_prompt | supervisor_llm

async def supervisor_node(state: MasterState):
    decision = await chain.ainvoke({
        "messages": state["messages"]
    })

    return {"next_step": decision.next_step}