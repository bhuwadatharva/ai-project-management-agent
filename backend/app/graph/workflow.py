from langgraph.graph import StateGraph, END
from app.agents.graph_state import AgentState
from app.agents.agent_definitions import (
    supervisor_agent,
    planner_agent,
    repository_agent,
    rag_agent,
    coding_assistant_agent,
    reviewer_agent,
    project_manager_agent
)

def build_workflow():
    # Initialize the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("planner", planner_agent)
    workflow.add_node("repository", repository_agent)
    workflow.add_node("rag", rag_agent)
    workflow.add_node("coding", coding_assistant_agent)
    workflow.add_node("reviewer", reviewer_agent)
    workflow.add_node("pm", project_manager_agent)
    
    # Set the starting node
    workflow.set_entry_point("supervisor")
    
    # Add conditional transitions from Supervisor
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state["next_agent"],
        {
            "PLANNER": "planner",
            "REPO": "repository",
            "RAG": "rag",
            "CODING": "coding",
            "REVIEWER": "reviewer",
            "PM": "pm",
            "FINISH": END
        }
    )
    
    # Connect other nodes back to Supervisor for next round of evaluation
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("repository", "supervisor")
    workflow.add_edge("rag", "supervisor")
    workflow.add_edge("coding", "supervisor")
    workflow.add_edge("reviewer", "supervisor")
    workflow.add_edge("pm", "supervisor")
    
    # Compile the graph
    return workflow.compile()

# Instantiated compiled graph
compiled_graph = build_workflow()
