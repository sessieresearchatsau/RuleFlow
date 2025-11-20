"""Sequential Substitution System"""
from typing import Sequence
from copy import deepcopy, copy
from core.engine import (
    Flow,
    SpaceState1D as StateSpace,
    Cell,
    Rule as RuleABC,
    RuleSet as RuleSetBase,
    DeltaSpace
)

class Constructor:
    def __init__(self, rule_str: str, op_symbol: str):
        match, op, replace = rule_str.split(' ')
        if op != op_symbol: raise ValueError(f'Invalid replacement rule format: {rule_str}')
        self.match_cells = tuple(Cell(c) for c in match.strip())
        self.replace_cells = tuple(Cell(c) for c in replace.strip())


class ReplacementRule(RuleABC, Constructor):
    def __init__(self, rule_str: str):
        RuleABC.__init__(self)
        Constructor.__init__(self, rule_str, '->')
        self.break_RuleSet_application_on_success = True  # set flags to modify the RuleSet behavior

    def apply(self, to_spaces: Sequence[StateSpace]) -> tuple[DeltaSpace]:
        old_space: StateSpace = to_spaces[0]
        new_space: StateSpace = copy(old_space)
        cell_deltas = new_space.replace(self.match_cells, deepcopy(self.replace_cells))
        return (DeltaSpace(old_space, new_space if cell_deltas else None, cell_deltas),)


class MultiwayReplacementRule(RuleABC, Constructor):
    def __init__(self, rule_str: str):
        RuleABC.__init__(self)
        Constructor.__init__(self, rule_str, '-->')
        self.break_RuleSet_application_on_success = True  # set flags to modify the RuleSet behavior

    def apply(self, to_spaces: Sequence[StateSpace]) -> tuple[DeltaSpace, ...]:
        modified_spaces: tuple[DeltaSpace, ...] = tuple()
        for space in to_spaces:
            matches: list[int] = space.find(self.match_cells, instances=-1)
            for pos in matches:
                new_space: StateSpace = copy(space)
                cell_deltas = new_space.replace_at(self.match_cells, deepcopy(self.replace_cells), at_pos=pos)
                modified_spaces += (DeltaSpace(space, new_space, cell_deltas),)
        return modified_spaces


class RuleSet(RuleSetBase):
    def __init__(self, rules: list[str | RuleABC]):
        for i in range(len(rules)):
            if not isinstance(rules[i], str): continue
            for ro in (ReplacementRule, MultiwayReplacementRule):
                try: rules[i] = ro(rules[i]); break
                except ValueError: continue
        super().__init__(rules)


class SSS(Flow):
    def __init__(self, rule_set: list[str] | RuleSet,
                 initial_state: str | StateSpace):
        if isinstance(rule_set, list): rule_set = RuleSet(rule_set)
        if isinstance(initial_state, str): initial_state = StateSpace([Cell(s) for s in initial_state])
        super().__init__(rule_set, initial_state)


if __name__ == "__main__":
    sss = SSS(["ABA -> AAB", "A -> ABA"], "AB")
    sss.evolve_n(8)
    string = sss.print(show_causally_connected_events=False, show_causal_distance_to_creation=False,
                       collapse_causally_connected_events_into_set=True, space_idx=-1, exclude=('None',))
    from core.graph import CausalityGraph, create_causal_graph
    g = CausalityGraph(sss)
    create_causal_graph(g)


