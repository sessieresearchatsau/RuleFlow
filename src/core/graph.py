"""Provides all the tools for optimized and rigorous graph analysis."""
from core.engine import Flow
from networkx import MultiDiGraph as __MultiDiGraph, DiGraph as __DiGraph
import networkx


class Graph(__MultiDiGraph):
    """This simply adds additional (can be custom) methods for analysis of directed graphs.

    - add support for printing in markdown compatible form.
    """

    @property
    def adjacency_matrix(self):
        return None

    @property
    def dijkstra_algorithm(self):
        return None


class CausalityGraph(Graph):
    def __init__(self, flow: Flow) -> None:
        super().__init__()
        self.flow: Flow = flow

        # construct causal graph - because each node is literally the time, and thus index, it can be used to query to the actual event for more granular information.
        for event in flow.events:
            if event.time == 0: continue  # Skip the initial event (no parents)
            self.add_node(event.time, label=f'{event.time}', title=f'Distance {event.causal_distance_to_creation}')  # add the node
            for parent_time in event.causally_connected_events:
                if parent_time is not None:
                    self.add_edge(parent_time, event.time)



def create_causal_graph(G: CausalityGraph, filename: str = "causal_network.html", collapse_multiple_edges: bool = False):
    """
    Uses pyvis to render the causal network from a Flow object.
    """
    from pyvis.network import Network
    net = Network(height="800px", width="100%", directed=True, notebook=True, cdn_resources='remote', filter_menu=True, select_menu=True)
    # net.set_options("""
    # {
    #   "physics": {
    #     "enabled": true,
    #     "hierarchicalRepulsion": {
    #       "nodeDistance": 150
    #     }
    #   }
    # }
    # """)
    net.show_buttons(filter_=True)
    net.from_nx(G)
    try:
        net.save_graph(filename)
        print(f"Successfully generated '{filename}'!")
        print("Open this file in your browser to view the interactive graph.")
    except Exception as e:
        print(f"Error generating graph: {e}")
