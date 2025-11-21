"""Provides all the tools for optimized and rigorous graph analysis."""
from core.engine import Flow
from networkx import MultiDiGraph as __MultiDiGraph
from pyvis.network import Network


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

        # TODO - maybe add option to collapse edges
        # construct causal graph - because each node is literally the time, and thus index, it can be used to query to the actual event for more granular information.
        for event in flow.events:
            if event.time == 0: continue  # Skip the initial event (no parents)
            self.add_node(event.time, label=f'{event.time}', title=f'Causal Distance: {event.causal_distance_to_creation}\nSpace: {event}')  # add the node
            for parent_time in event.causally_connected_events:
                if parent_time is not None:
                    self.add_edge(parent_time, event.time)

    def render_in_browser(self, filename: str = "causal_network.html", show_controls: list[str] | bool | None = None):
        """
        Uses pyvis to render the causal network from a Flow object.
        """

        net = Network(height="500px", width="100%", directed=True, notebook=True, cdn_resources='remote', filter_menu=True, select_menu=True)
        if show_controls:
            net.show_buttons(filter_=['physics'])
        else:
            net.set_options("""
                    {
                      "edges": {
                        "color": {
                          "inherit": true
                        },
                        "selfReferenceSize": null,
                        "selfReference": {
                          "angle": 0.7853981633974483
                        },
                        "smooth": {
                          "forceDirection": "none"
                        }
                      },
                      "interaction": {
                        "navigationButtons": true
                      },
                      "physics": {
                        "minVelocity": 0.75
                      }
                    }
                    """)
        net.from_nx(self)
        try:
            net.save_graph(filename)
            print(f"Successfully generated '{filename}'!")
            print("Open this file in your browser to view the interactive graph.")
        except Exception as e:
            print(f"Error generating graph: {e}")
