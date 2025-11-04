"""Sequential Substitution System"""
from typing import Sequence
from engine import Flow, StateSpace1D as StateSpace, Cell, Rule as RuleABC, RuleSet as RuleSetABC
from copy import deepcopy, copy


class ReplacementRule(RuleABC):
    def __init__(self, rule_str: str):
        super().__init__()
        if '->' not in rule_str: raise ValueError(f'Invalid replacement rule format: {rule_str}')
        match, replace = rule_str.split('->')
        self.match_cells = [Cell(c) for c in match.strip()]
        self.replace_cells = [Cell(c) for c in replace.strip()]
        self.break_RuleSet_application_on_success = True  # set flags to modify the RuleSet behavior

    def apply(self, to_space: Sequence[StateSpace]) -> tuple[StateSpace, ...]:
        modified_states: tuple[StateSpace, ...] = tuple()
        new_state_space: StateSpace = copy(to_space[0])
        if new_state_space.replace(self.match_cells, deepcopy(self.replace_cells)):
            modified_states += (new_state_space,)
        return modified_states


class MultiwayReplacementRule(RuleABC):
    def __init__(self, rule_str: str):
        super().__init__()
        if '-->' not in rule_str: raise ValueError(f'Invalid replacement rule format: {rule_str}')
        match, replace = rule_str.split('-->')
        self.match_cells = [Cell(c) for c in match.strip()]
        self.replace_cells = [Cell(c) for c in replace.strip()]
        self.break_RuleSet_application_on_success = True  # set flags to modify the RuleSet behavior

    def apply(self, to_space: Sequence[StateSpace]) -> tuple[StateSpace, ...]:
        modified_states: tuple[StateSpace, ...] = tuple()
        for space in to_space:
            matches: list[int] = space.find(self.match_cells, instances=-1)
            for pos in matches:
                new_state_space: StateSpace = copy(space)
                if new_state_space.replace_at(self.match_cells, deepcopy(self.replace_cells), at_pos=pos):
                    modified_states += (new_state_space,)
        return modified_states


class RuleSet(RuleSetABC):
    def __init__(self, rules: list[str]):
        super().__init__([ReplacementRule(rule_str) if rule_str == '->' else MultiwayReplacementRule(rule_str) for rule_str in rules])


class SSS(Flow):
    def __init__(self, rule_set: list[str] | RuleSet,
                 initial_state: str | StateSpace):
        if isinstance(rule_set, list): rule_set = RuleSet(rule_set)
        if isinstance(initial_state, str): initial_state = StateSpace([Cell(s) for s in initial_state])
        super().__init__(rule_set, initial_state)


if __name__ == "__main__":
    sss = SSS(["ABA->AAB", "A-->ABA"], "AB")
    sss.evolve_n(100)
    print(sss)
