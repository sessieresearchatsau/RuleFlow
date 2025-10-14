"""
in order to do have the program run, you need to enter for following string of code:
the rulsets, initial string, and number of iterations. currenlty SSSSize and NetSize currently do nothing.

Example:
SSS(["ABA->AAB", "A->ABA"], "AB", 10).worldGen()
will output:

AB
ABAB
AABB
ABAABB
AABABB
ABAABABB
AABABABB
ABAABABABB
AABABABABB
ABAABABABABB
AABABABABABB
ABAABABABABABB
AABABABABABABB
ABAABABABABABABB
AABABABABABABABB
ABAABABABABABABABB
AABABABABABABABABB
ABAABABABABABABABABB
AABABABABABABABABABB
ABAABABABABABABABABABB
"""

import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter


class SSS(object):
    def __init__(self, ruleSet, Init: str, n: int, SSSSize: int = 10, NetSize: int = 300, RulePlacement: str = "Left"):
        self.ruleSet = self._transform(ruleSet)
        self.Init = Init
        self.n = n
        self.SSSSize = SSSSize
        self.NetSize = NetSize
        self.RulePlacement = RulePlacement
        self.world = self.Init
        self.letter_order = {}
        self.global_index = 0
        self.count = 0

        # Build letter order from initial world
        for c in self.world:
            if c not in self.letter_order:
                self.letter_order[c] = self.count
                self.count += 1

        # Also add letters from rules
        for before, after in self.ruleSet.items():
            for c in before + after:
                if c not in self.letter_order:
                    self.letter_order[c] = self.count
                    self.count += 1

        self.converted_ruleSet = {}
        self.before = []
        self.after = []
        self.nested = []
        self.original_ruleSet = ruleSet  # Keep original order

    def __str__(self) -> str:
        return f"{self.world}"

    def __repr__(self) -> str:
        return f"SSS('{self.world}')"

    def _count(self):
        self.global_index += 1
        return self.global_index

    def _transform(self, rules: list) -> dict:
        rule_dict = {}
        for rule in rules:
            if "->" in rule:
                before, after = rule.split("->")
                rule_dict[before.strip()] = after.strip()
        return rule_dict

    def worldGen(self):
        print(self.world)
        for i in range(self.n):
            new_world = self.world
            # Apply rules based on RulePlacement
            if self.RulePlacement == "Left":
                rule_items = list(self.ruleSet.items())
            else:  # Right
                rule_items = list(reversed(list(self.ruleSet.items())))

            # Find first matching rule
            for before, after in rule_items:
                if before in self.world:
                    new_world = self.world.replace(before, after, 1)
                    break
            self.world = new_world
            print(self.world)

    def worldGenNested(self):
        # Initialize nested structure for initial world
        self.nested = []
        self.global_index = 0

        # Create initial nested structure
        for c in self.Init:
            self.nested.append([self.letter_order[c], self._count()])

        print(self.nested)

        current_world = self.Init
        # Track each individual nested list with unique ID
        self.list_tracking = []  # List of {"id": unique_id, "created": step, "destroyed": step, "content": [letter, causal_index]}

        # Record initial state (step 1)
        for element in self.nested:
            list_id = f"list_{len(self.list_tracking)}"
            self.list_tracking.append({
                "id": list_id,
                "created": 1,
                "destroyed": None,
                "content": list(element)
            })

        # Apply rules step by step
        for step in range(1, self.n):  # Steps 1 to n-1
            # Determine rule order based on RulePlacement
            if self.RulePlacement == "Left":
                rule_items = list(self.ruleSet.items())
            else:  # Right
                rule_items = list(reversed(list(self.ruleSet.items())))

            # Find first matching rule
            applied = False
            for before_pattern, after_pattern in rule_items:
                if before_pattern in current_world:
                    # Find the position of the match
                    pos = current_world.find(before_pattern)

                    # Convert patterns to numeric form
                    before_numeric = [self.letter_order[c] for c in before_pattern]
                    after_numeric = [self.letter_order[c] for c in after_pattern]

                    # Find the corresponding positions in nested structure
                    pattern_start_idx = -1
                    for i in range(len(self.nested) - len(before_numeric) + 1):
                        if [self.nested[i + j][0] for j in range(len(before_numeric))] == before_numeric:
                            pattern_start_idx = i
                            break

                    if pattern_start_idx != -1:
                        # Get the elements that will be removed
                        removed_elements = self.nested[pattern_start_idx:pattern_start_idx + len(before_numeric)]

                        # Mark these elements as destroyed at this step (step + 1)
                        for i, element in enumerate(removed_elements):
                            # Find the corresponding tracked list and mark as destroyed
                            for tracked_list in self.list_tracking:
                                if (tracked_list["content"][0] == element[0] and
                                        tracked_list["content"][1] == element[1] and
                                        tracked_list["destroyed"] is None):
                                    tracked_list["destroyed"] = step + 1
                                    break

                        # Remove the matched elements
                        del self.nested[pattern_start_idx:pattern_start_idx + len(before_numeric)]

                        # Insert new elements with new causal indices
                        new_elements = []
                        for num in after_numeric:
                            new_causal_index = self._count()
                            new_element = [num, new_causal_index]
                            new_elements.append(new_element)

                            # Track new list
                            list_id = f"list_{len(self.list_tracking)}"
                            self.list_tracking.append({
                                "id": list_id,
                                "created": step + 1,
                                "destroyed": None,
                                "content": list(new_element)
                            })

                        # Insert at the same position
                        for i, element in enumerate(reversed(new_elements)):
                            self.nested.insert(pattern_start_idx, element)

                        # Update current_world
                        current_world = current_world[:pos] + after_pattern + current_world[pos + len(before_pattern):]

                        print(self.nested)
                        applied = True
                        break

            if not applied:
                break

    def draw_multigraph_edges(self, g, pos, edges_with_counts):
        """Draw edges with appropriate curvature based on how many times they appear"""

        # Draw single edges (straight)
        single_edges = [edge for edge, count in edges_with_counts.items() if count == 1]
        if single_edges:
            nx.draw_networkx_edges(g, pos, edgelist=single_edges, arrows=True,
                                   arrowsize=20, edge_color='black', alpha=0.6)

        # Handle multiple edges
        multi_edges = [(edge, count) for edge, count in edges_with_counts.items() if count > 1]

        for edge, count in multi_edges:
            # Calculate curvature values - spread them evenly
            if count % 2 == 1:
                # Odd number: include 0, then symmetric around 0
                curvatures = [0.3 * i for i in range(-(count // 2), count // 2 + 1)]
            else:
                # Even number: symmetric around 0, no 0
                curvatures = [0.3 * (i - (count - 1) / 2) * 2 / (count - 1) for i in range(count)] if count > 1 else [
                    0.3]

            # Draw each edge with its curvature
            for i in range(count):
                curvature = curvatures[i] if i < len(curvatures) else 0.3 * (i - count // 2)
                # Create a temporary graph with one edge to draw with specific curvature
                temp_graph = nx.DiGraph()
                temp_graph.add_edge(*edge)
                nx.draw_networkx_edges(temp_graph, pos, edgelist=[edge], arrows=True,
                                       arrowsize=20, edge_color='black', alpha=0.6,
                                       connectionstyle=f'arc3,rad={curvature}')

    def generate_causal_diagram(self):
        # Ensure worldGenNested has been called
        if not hasattr(self, 'list_tracking'):
            raise ValueError("Call worldGenNested() first to generate list tracking.")

        # Build the causal graph as a MultiDiGraph to handle multiple edges
        g = nx.MultiDiGraph()

        # Add nodes for each step (1 to n)
        for step in range(1, self.n + 1):
            g.add_node(step)

        # Collect all edges
        edges = []
        for list_info in self.list_tracking:
            created_step = list_info["created"]
            destroyed_step = list_info["destroyed"]

            # If destroyed, add edge from creation to destruction
            if destroyed_step is not None and destroyed_step <= self.n:
                edges.append((created_step, destroyed_step))

        # Add all edges to the graph
        g.add_edges_from(edges)

        # Layout the graph using spring_layout
        pos = nx.spring_layout(g, k=0.5)
        pos = nx.planar_layout(g)
        # Draw the graph
        plt.figure(figsize=(12, 8))

        # Draw nodes
        nx.draw_networkx_nodes(g, pos, node_size=800, node_color="skyblue", alpha=0.7)

        # Count edge occurrences
        edge_counts = Counter(edges)

        # Draw edges with appropriate styling
        self.draw_multigraph_edges(g, pos, edge_counts)

        # Draw labels
        nx.draw_networkx_labels(g, pos, font_size=10, font_weight="bold")

        plt.title("Causal Diagram - Evolutionary Steps")
        plt.axis('off')  # Hide axis
        plt.show()


# Example usage
sss = SSS(["ABA->AAB", "A->ABA"], "AB", 5, RulePlacement='Left')
sss.worldGen()
sss.worldGenNested()
sss.generate_causal_diagram()

# print(SSS(["ABA->AAB", "A->ABA"], "AB", 10).ruleSet)
# print(SSS(["ABA->AAB", "A->ABA"], "AB", 10).ruleSet['A'])
# SSS(["ABA->AAB", "A->ABA", "BB->C"], "AB", 10).worldGen()
# SSS(["BB->C", "ABA->AAB","A->ABA"], "AB", 10, RulePlacement='Left').worldGenNested()