"""Sequential Substitution System"""
from typing import Sequence
from engine import Flow, SpaceState1D as StateSpace, Cell, Rule as RuleABC, RuleSet as RuleSetABC, DeltaSpace
from copy import deepcopy, copy


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
        return (DeltaSpace(old_space, new_space if cell_deltas else (), cell_deltas),)


# class MultiwayReplacementRule(RuleABC, Constructor):
#     def __init__(self, rule_str: str):
#         RuleABC.__init__(self)
#         Constructor.__init__(self, rule_str, '-->')
#         self.break_RuleSet_application_on_success = True  # set flags to modify the RuleSet behavior
#
#     def apply(self, to_spaces: Sequence[StateSpace]) -> tuple[StateSpace, ...]:
#         modified_spaces: tuple[StateSpace, ...] = tuple()
#         for space in to_spaces:
#             matches: list[int] = space.find(self.match_cells, instances=-1)
#             for pos in matches:
#                 new_state_space: StateSpace = copy(space)
#                 if new_state_space.replace_at(self.match_cells, deepcopy(self.replace_cells), at_pos=pos):
#                     modified_spaces += (new_state_space,)
#         return modified_spaces
#
#
# class StochasticReplacementRule(RuleABC, Constructor):
#     def __init__(self, rule_str: str):
#         RuleABC.__init__(self)
#         Constructor.__init__(self, rule_str, '-.->')
#         self.break_RuleSet_application_on_success = True  # set flags to modify the RuleSet behavior
#         self.prob = 0.3
#
#     def apply(self, to_spaces: Sequence[StateSpace]) -> tuple[StateSpace, ...]:
#         """
#
#         :param to_spaces:
#         :return:
#         """
#         # TODO assign a certain probability to the assignment.
#         # TODO What about multi-way systems?
#         # TODO what are some ways in which this could work.
#         # TODO must all probabilities add up to 1?
#         from random import random
#         modified_states: tuple[StateSpace, ...] = tuple()
#         new_state_space: StateSpace = copy(to_spaces[0])
#         if new_state_space.replace(self.match_cells, deepcopy(self.replace_cells)):
#             modified_states += (new_state_space,)
#         return modified_states


class RuleSet(RuleSetABC):
    def __init__(self, rules: list[str | RuleABC]):
        for i in range(len(rules)):
            if not isinstance(rules[i], str): continue
            for ro in (ReplacementRule,):  # MultiwayReplacementRule, StochasticReplacementRule
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
    sss = SSS(["AB -> BA", "BA -> AB"], "AB")
    sss.evolve_n(1)
    print(sss)
    print(sss.current_event)
