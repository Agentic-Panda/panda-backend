import asyncio

from langgraph.graph import StateGraph, END

from panda.agents.nodes.supervisor import supervisor_node
from panda.models.agents.state import MasterState
from langchain_core.messages import HumanMessage, AIMessage


async def productivity_node(state: MasterState):
    print("   --> [PRODUCTIVITY] Scheduling task...")
    await asyncio.sleep(0.1)
    return {
        "messages": state["messages"] + [
            AIMessage("Meeting scheduled successfully.")
        ]
    }


async def operations_node(state: MasterState):
    print("   --> [OPERATIONS] Performing system operation...")
    await asyncio.sleep(0.1)
    return {
        "messages": state["messages"] + [
            AIMessage("System operation completed.")
        ]
    }


async def health_node(state: MasterState):
    print("   --> [HEALTH] Analyzing health data...")
    await asyncio.sleep(0.1)
    return {
        "messages": state["messages"] + [
            AIMessage("Health check complete. All good.")
        ]
    }


async def scribe_node(state: MasterState):
    print("   --> [SCRIBE] Writing content...")
    await asyncio.sleep(0.1)
    return {
        "messages": state["messages"] + [
            AIMessage("Document drafted successfully.")
        ]
    }


async def build_and_run_graph():
    workflow = StateGraph(MasterState)

    workflow.add_node("SUPERVISOR", supervisor_node)
    workflow.add_node("PRODUCTIVITY", productivity_node)
    workflow.add_node("OPERATIONS", operations_node)
    workflow.add_node("HEALTH", health_node)
    workflow.add_node("SCRIBE", scribe_node)

    workflow.set_entry_point("SUPERVISOR")

    workflow.add_conditional_edges(
        "SUPERVISOR",
        lambda state: state["next_step"],
        {
            "PRODUCTIVITY": "PRODUCTIVITY",
            "OPERATIONS": "OPERATIONS",
            "HEALTH": "HEALTH",
            "SCRIBE": "SCRIBE"
        }
    )

    workflow.add_edge("PRODUCTIVITY", END)
    workflow.add_edge("OPERATIONS", END)
    workflow.add_edge("HEALTH", END)
    workflow.add_edge("SCRIBE", END)

    app = workflow.compile()

    print("=== STARTING ASYNC GRAPH TESTS ===")

    tests = [
        ("Book a meeting with Alice", "PRODUCTIVITY"),
        ("Restart the server", "OPERATIONS"),
        ("I feel tired and stressed", "HEALTH"),
        ("Write an email to my manager", "SCRIBE"),
    ]

    for i, (prompt, expected) in enumerate(tests, 1):
        print(f"\n--- Test {i}: {expected} ---")

        inputs = {
            "messages": [HumanMessage(prompt)]
        }

        result = await app.ainvoke(inputs)

        print("Final Messages:")
        for msg in result["messages"]:
            print(" ", msg)