"""Provides all the tools for optimized and rigorous graph analysis."""
from engine import Flow

class Graph:
    @property
    def adjacency_matrix(self) -> Graph:
        return self

class CausalityGraph(Graph):
    pass


def create_causal_graph(flow: Flow, filename: str = "causal_network.html", collapse_multiple_edges: bool = False):
    """
    Uses pyvis to render the causal network from a Flow object.
    """
    print(f"Generating causal graph for {len(flow.events)} events...")
    from pyvis.network import Network
    net = Network(height="800px", width="100%", directed=True, notebook=True, cdn_resources='remote')
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "hierarchicalRepulsion": {
          "nodeDistance": 150
        }
      }
    }
    """)
    # 1. Add Nodes
    for event in flow.events:
        net.add_node(
            event.time,
            label=str(event.time),
        )
    # 2. Add Edges
    for event in flow.events:
        if event.time == 0:  # Skip the initial event (no parents)
            continue
        parent_event_indices = set(event.causally_connected_events) if collapse_multiple_edges else event.causally_connected_events
        for parent_time in parent_event_indices:
            if parent_time is not None:
                net.add_edge(parent_time, event.time)
    try:
        net.save_graph(filename)
        print(f"Successfully generated '{filename}'!")
        print("Open this file in your browser to view the interactive graph.")
    except Exception as e:
        print(f"Error generating graph: {e}")
