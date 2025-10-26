"""Sequential Substitution System"""
from engine import Flow, StateSpace, Cell, Rule as RuleABC, RuleSet as RuleSetABC, Rule


class InsertionRule(RuleABC):
    def __init__(self, rule_str: str):
        super().__init__()
        if ".>" not in rule_str:
            raise ValueError(f"Invalid insertion rule format: {rule_str}")
        quanta_str, pos_str = rule_str.split(".>")
        self.insert_cells = StateSpace([Cell(c) for c in quanta_str.strip()])
        self.insert_pos = int(pos_str.strip())

    def apply(self, to_space: StateSpace) -> bool:
        success = to_space.insert(self.insert_cells, self.insert_pos)
        if success:
            self.on_applied.emit()
        return success

    def __str__(self):
        return f"{''.join(str(c) for c in self.insert_cells.cells)}.>{self.insert_pos}"



class ReplacementRule(RuleABC):
    def __init__(self, rule_str: str):
        super().__init__()
        if "->" not in rule_str:
            raise ValueError(f"Invalid replacement rule format: {rule_str}")
        match, replace = rule_str.split("->")
        self.match = match.strip()
        self.replace = replace.strip()

        self.match_cells = [Cell(c) for c in self.match]
        self.replace_cells = [Cell(c) for c in self.replace]

    def match(self): pass

    def apply(self, to_space: StateSpace) -> bool:
        success = to_space.replace(self.match_cells, self.replace_cells)
        if success:
            self.on_applied.emit()
        return success

    def __str__(self):
        return f"{self.match}->{self.replace}"



class RuleSet(RuleSetABC):
    def __init__(self, rules: list[str]):
        super().__init__()
        for rule_str in rules:
            rule_str = rule_str.strip()
            if "->" in rule_str:
                self.rules.append(ReplacementRule(rule_str))
            elif ".>" in rule_str:
                self.rules.append(InsertionRule(rule_str))
            else:
                raise ValueError(f"Unrecognized rule format: {rule_str}")

    def match(self) -> list[Rule]:  # TODO must implement or pass
        pass

    def apply(self, to_space: StateSpace) -> list[RuleABC]:
        applied = []
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
