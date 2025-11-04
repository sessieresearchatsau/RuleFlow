"""Sequential Substitution System"""
from numpy.random.mtrand import Sequence

from engine import Flow, StateSpace1D as StateSpace, Cell, Rule as RuleABC, RuleSet as RuleSetABC, Rule
from copy import deepcopy, copy


class ReplacementRule(RuleABC):
    def __init__(self, rule_str: str):
        super().__init__()
        if "->" not in rule_str: raise ValueError(f"Invalid replacement rule format: {rule_str}")
        match, replace = rule_str.split("->")
        self.match_cells = [Cell(c) for c in match.strip()]
        self.replace_cells = [Cell(c) for c in replace.strip()]

    def apply(self, to_space: tuple[StateSpace]) -> bool:
        success: bool = False
        for space in to_space:
            new_state_space: StateSpace = copy(space)
            s: bool = new_state_space.replace(self.match_cells, deepcopy(self.replace_cells))
            if s:
                self.state_space_buffer.append(new_state_space)
                success = True
        return success


class RuleSet(RuleSetABC):
    def __init__(self, rules: list[str]):
        super().__init__()
        for rule_str in rules:
            if "->" in rule_str:
                self.rules.append(ReplacementRule(rule_str))
            else:
                raise ValueError(f"Unrecognized rule format: {rule_str}")

    def apply(self, to_space: tuple[StateSpace]) -> list[RuleABC]:
        applied = []
        for
        for rule in self.rules:
            if rule.apply(to_space):
                applied.append(rule)
                break  # Apply only one rule per step (sequential)
        if applied:
            self.on_rules_applied.emit(applied)
        return applied


class SSS(Flow):
    def __init__(self, rule_set: list[str] | RuleSet,
                 initial_state: str | StateSpace):
        if isinstance(rule_set, list):
            rule_set = RuleSet(rule_set)
        if isinstance(initial_state, str):
            initial_state = StateSpace([Cell(s) for s in initial_state])
        super().__init__(rule_set, initial_state)


if __name__ == "__main__":
    rules = ["ABA->AAB", "AB.>3", "A->ABA"]
    initial = "AB"
    steps = 10

    sss = SSS(rules, initial)
    sss.evolve_n(steps)
    print(sss)
