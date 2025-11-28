"""Just a showcase of how simple implementation is"""
from typing import Sequence
from copy import deepcopy, copy
from core.graph import create_causal_graph
from core.engine import (
    Flow,
    SpaceState1D as StateSpace,
    Cell,
    Rule as RuleABC,
    RuleSet,
    DeltaSpace
)


class ReplacementRule(RuleABC):
    def __init__(self, rule_str: str):
        super().__init__()
        match, op, replace = rule_str.split(' ')
        if op != '->': raise ValueError(f'Invalid replacement rule format: {rule_str}')
        self.match_cells = tuple(Cell(c) for c in match.strip())
        self.replace_cells = tuple(Cell(c) for c in replace.strip())
        self.break_RuleSet_application_on_success = True

    def apply(self, matches: Sequence[StateSpace]) -> tuple[DeltaSpace]:
        old_space: StateSpace = matches[0]
        new_space: StateSpace = copy(old_space)
        cell_deltas = new_space.replace(self.match_cells, deepcopy(self.replace_cells))
        return (DeltaSpace(old_space, new_space if cell_deltas else None, cell_deltas),)


class SSS(Flow):
    def __init__(self, rule_set: list[str], initial_state: str):
        super().__init__(RuleSet([ReplacementRule(s) for s in rule_set]), StateSpace([Cell(s) for s in initial_state]))


if __name__ == "__main__":
    sss = SSS(["ABA -> AAB", "A -> ABA"], "AB")
    sss.evolve_n(15)
    sss.print(show_causally_connected_events=True, show_time_steps=True)
