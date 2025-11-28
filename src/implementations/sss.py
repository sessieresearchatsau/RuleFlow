"""Sequential Substitution System"""
from typing import Sequence
from copy import deepcopy, copy
from core.engine import (
    Flow,
    SpaceState1D as SpaceState,
    Cell,
    Rule as RuleABC,
    RuleMatch,
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
        self.group_break = True  # set flags to modify the RuleSet behavior

    def match(self, spaces: Sequence[SpaceState]) -> Sequence[RuleMatch]:
        output = ()
        if matches:=spaces[0].find(self.match_cells, instances=1):
            output += (RuleMatch(space=spaces[0], matches=matches, conflicts=()),)
        return output

    def apply(self, matches: Sequence[RuleMatch]) -> Sequence[DeltaSpace]:
        selector: tuple[int, int] = matches[0].matches[0]
        old_space: SpaceState = matches[0].space
        new_space: SpaceState = copy(old_space)
        cell_deltas = new_space.substitute(selector, deepcopy(self.replace_cells))
        return (DeltaSpace(old_space, new_space, cell_deltas),)


# class MultiwayReplacementRule(RuleABC, Constructor):
#     def __init__(self, rule_str: str):
#         RuleABC.__init__(self)
#         Constructor.__init__(self, rule_str, '-->')
#         self.group_break = True  # set flags to modify the RuleSet behavior
#
#     def match(self, spaces: Sequence[SpaceState]) -> Sequence[RuleMatch]:
#         # TODO use the selector to find matches.
#         pass
#
#     def apply(self, rule_matches: Sequence[RuleMatch]) -> Sequence[DeltaSpace]:
#         modified_spaces: tuple[DeltaSpace, ...] = tuple()
#         for space in to_spaces:
#             matches: list[int] = space.find(self.match_cells, instances=-1)
#             for pos in matches:
#                 new_space: SpaceState = copy(space)
#                 cell_deltas = new_space.replace_at(self.match_cells, deepcopy(self.replace_cells), at_pos=pos)
#                 modified_spaces += (DeltaSpace(space, new_space, cell_deltas),)
#         return modified_spaces


class RuleSet(RuleSetBase):
    def __init__(self, rules: list[str | RuleABC]):
        for i in range(len(rules)):
            if not isinstance(rules[i], str): continue
            for ro in (ReplacementRule,):
                try: rules[i] = ro(rules[i]); break
                except ValueError: continue
        super().__init__(rules)


class SSS(Flow):
    def __init__(self, rule_set: list[str] | RuleSet,
                 initial_state: str | SpaceState):
        if isinstance(rule_set, list): rule_set = RuleSet(rule_set)
        if isinstance(initial_state, str): initial_state = SpaceState([Cell(s) for s in initial_state])
        super().__init__(rule_set, initial_state)


if __name__ == "__main__":
    sss = SSS(["ABA -> AAB", "A -> ABA"], "AB")
    sss.evolve_n(10)
    sss.print()
    from core.graph import CausalGraph
    g = CausalGraph(sss)
    g.render_in_browser()
