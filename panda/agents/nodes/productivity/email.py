from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from panda.core.llm.factory import LLMFactory, LLMProvider
from panda.core.llm.prompts import EMAIL_AGENT_PROMPT
from panda.models.agents.state import ProductivityState
from panda.models.agents.response import 



llm_client = LLMFactory.create_client(
    provider=LLMProvider.GEMINI,
    model_name="gemini-2.5-flash",
)

email_llm = llm_client.with_structured_output()

email_prompt = ChatPromptTemplate.from_messages([
        ("system", EMAIL_AGENT_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])

chain = email_prompt | email_llm

async def email_node(state: ProductivityState):
    decision = await chain.ainvoke({
        "messages": state["messages"]
    })

    return {"next_step": decision.next_step}