"""Provides all the tools for optimized and rigorous graph analysis."""
from core.engine import Flow
from networkx import MultiDiGraph
from pyvis.network import Network


class CausalGraph(MultiDiGraph):
    def __init__(self, flow: Flow) -> None:
        super().__init__()
        self.flow: Flow = flow

        # TODO - maybe add option to collapse edges
        # construct causal graph - because each node is literally the time, and thus index, it can be used to query to the actual event for more granular information.
        for event in flow.events:
            # if event.time == 0: continue  # Skip the initial event (no parents)
            self.add_node(event.time, label=f'{event.time}', title=f'Causal Distance: {event.causal_distance_to_creation}\nSpace: {event}', shape='box')  # add the node
            for parent_time in event.causally_connected_events:
                if parent_time is not None:
                    self.add_edge(parent_time, event.time)

    @property
    def adjacency_matrix(self):
        return None

    @property
    def dijkstra_algorithm(self):
        return None

    # same as the the glxl file...
    def save_to_gephi_file(self):
        pass

    def render_in_browser(self, filename: str = "causal_network.html", show_controls: list[str] | bool | None = None):
        """
        Uses pyvis to render the causal network from a Flow object.
        """

        net = Network(height="800px", width="100%", directed=True, filter_menu=True, select_menu=True, cdn_resources='remote')
        net.from_nx(self)
        if show_controls:
            net.show_buttons(filter_=show_controls)
        else:
            net.set_options("""
            {
                "physics": {
                    "minVelocity": 0.75
                },
                "interaction": {
                    "navigationButtons": true
                }
            }
            """)

        try:
            net.save_graph(filename)
            print(f"Successfully generated '{filename}'!")
            print("Open this file in your browser to view the interactive graph.")
        except Exception as e:
            print(f"Error generating graph: {e}")
