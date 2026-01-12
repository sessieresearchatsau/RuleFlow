from typing import Any, Type, Iterator, Sequence, cast
from llm_module import LLMSelector

# Import the base engine classes
from core.engine import Cell, Flow, RuleSet, SpaceState1D as SpaceState
from parser import FlowLangParser
from implementation import (
    Selector, Target, BaseRule, SubstitutionRule, InsertionRule, OverwriteRule,
    DeletionRule, ShiftingRule, ReverseRule
)


RULE_MAPPER: dict[str, Type[BaseRule]] = {
    "->": SubstitutionRule,
    ">": InsertionRule,
    "-->": OverwriteRule,
    "><": DeletionRule,
    ">>": ShiftingRule,
    "<<": ShiftingRule,
    ">><<": ReverseRule,
}


def interpret_selector(selector_data: dict[str, Any], llm_selector: LLMSelector | None = None) -> Selector:
    """Converts AST selector data into a clean Selector NamedTuple."""
    s_type = selector_data["selector_type"]
    s_value = selector_data["value"]
    if s_type == "literal":
        return Selector(type=s_type, selector=s_value.replace('_', '.'))  # replace '_' with the regex wildcard '.' because we use regex for matching literals as well.
    elif s_type == "regex":
        return Selector(type=s_type, selector=s_value)
    elif s_type == "range":
        return Selector(type=s_type, selector=s_value)
    elif s_type == "llm_prompt" and llm_selector:
        return Selector(type='regex', selector=llm_selector.prompt(s_value))
    raise ValueError(f"Unknown selector type: {s_type}")


def interpret_target(selector_data: dict[str, Any]) -> Target:
    """Converts AST selector data into a clean Target NamedTuple."""
    t_type = selector_data["target_type"]
    t_value = selector_data["value"]
    if t_type == "literal":
        return Target(
            type=t_type,
            target=t_value if isinstance(t_value, int) else tuple(Cell(c) for c in t_value)
        )
    # add more conditionals if additional types are added to the terminal for target
    raise ValueError(f"Unknown target type: {t_type}")


def interpret_instructions(instructions: Sequence[dict], global_flags: dict[str, Any], llm_selector: LLMSelector) -> Iterator[BaseRule]:
    """
    Iterates over the flat list of instructions, instantiates the correct
    Rule subclass, merges flags, and initializes fields.
    """
    for instruction in instructions:
        operator = instruction['operator']['symbol']
        RuleClass = RULE_MAPPER.get(operator)
        if not RuleClass:
            print(f"Warning: Unknown operator '{operator}'. Skipping rule.")
            continue

        # 1. Prepare Selectors and Targets
        if not instruction['selector']:
            print(f'Warning: All rules must have a selector. Skipping rule.')
            continue
        selectors = [interpret_selector(sd, llm_selector) for sd in instruction['selector']]
        target = [interpret_target(td) for td in instruction['target']]

        # 2. Instantiate Rule
        rule_instance: BaseRule = RuleClass(selectors, target)

        # 3. Merge and Assign Flags (Global < Rule/Group)
        # Start with global defaults
        final_flags = global_flags.copy()
        rule_flags = instruction.get('flags', {})
        final_flags.update(rule_flags)  # Apply rule/group flags (overwrites global)
        # Apply flags to the rule instance
        for key, value in final_flags.items():
            # Map shorthand keys (e.g., 'pl' for 'parallel_processing_limit') to full attribute names
            setattr(rule_instance, rule_instance.FLAG_ALIAS.get(key, key), value)

        yield rule_instance


def interpret_directives(objects: dict[str, Any], directives: list[tuple[str, Any]]) -> dict[str, Any]:
    """
    Use the directives to modify (call) the `objects`.
    """
    returns: dict[str, Any] = {}
    for path, args in directives:
        parts = path.split('.')
        root_name = parts[0]
        root_obj = objects.get(root_name)
        if not root_obj:
            continue
        current_obj = root_obj
        try:
            for part in parts[1:]:
                current_obj = getattr(current_obj, part)
        except AttributeError:
            # noinspection PyUnboundLocalVariable
            print(f"Error: Could not traverse '{part}' in path '{path}'.")
            continue
        returns[path] = current_obj(*args)
    return returns


class FlowLang(Flow):
    """The main interpreter object, it is what actually runs any given code."""

    def __init__(self, lang: str, init_space: Sequence[
                                                  str] | str | None = None):  # init_space can be none if the @init directive is defined.
        self.ast: dict[str, Any] = cast(dict[str, Any], cast(object, FlowLangParser().parse(lang)))  # a bunch of stupid casting due to the Lark.parse() hinting at Tree[Token] return instead of what the transformer returns.
        if isinstance(init_space, str):
            init_space = (init_space,)
        if init_space is None:
            r: dict[str, Any] = interpret_directives({'init': lambda *args: tuple(map(str, args))},
                                                     self.ast['directives'])
            try:
                init_space = r['init']
            except KeyError:
                raise ValueError(
                    "An `@init(<space>)` directive must be present if the `init_space` argument is not provided.")
        self.llm_selector: LLMSelector = LLMSelector()
        super().__init__(RuleSet(list(interpret_instructions(self.ast['instructions'], self.ast['global_flags'],
                                                             llm_selector=self.llm_selector))),
                         [SpaceState([Cell(s) for s in string]) for string in init_space])
        interpret_directives({
            'print': self.print,
            'evolve': self.evolve_n,
            'merge': self.__merge_group,
            'compress': self.__compress_group
        }, self.ast['directives'])

    def __merge_group(self, identifier: int | str):
        """A directive to merge a particular group into a chain (a composite rule)"""
        rules: list[BaseRule] = cast(list[BaseRule], self.rule_set.rules)
        for i in range(len(rules)):
            if rules[i].disabled:
                 continue
            if rules[i].group == identifier:
                head = rules[i]
                for j in range(i + 1, len(rules)):
                    if rules[j].group == identifier:
                        head.chain.append(rules[j])
                        rules[j].is_in_chain = True
                break

    def __compress_group(self, identifier: int | str):
        """Compress a Rule Group such that causality is preserved (no cellular change if the characters look the same)"""
        rules: list[BaseRule] = [rule for rule in cast(list[BaseRule], self.rule_set.rules)
                                 if rule.group == identifier and not rule.disabled]
        # If any rule makes no changes, disable it.
        for rule in rules:
            if type(rule) != OverwriteRule:  # we only care about this type of rule... for obvious reasons
                continue
            rule_is_active: bool = False
            for selector in rule.selectors:
                for s_char, t_char in zip(selector.selector, rule.target[0].target):  # we only care about the first/primary target... (we can't determine how multiple targets will behave on different matches sets)
                    if t_char.quanta == '_':
                        continue
                    if s_char != t_char.quanta:
                        rule_is_active = True
            if not rule_is_active:
                rule.disabled = True

    @classmethod
    def from_file(cls, path: str):
        """opens `.flow` files and constructs a FlowLang object."""
        with open(path, 'r') as f:
            return cls(f.read())


if __name__ == "__main__":
    # "All them Bs at the end of the sequence, but only if there are more than 2."
    code = """
    @init(AB);
    @evolve(30);

    ABA -> AAB;
    A -> ABA;
    """
    flow = FlowLang.from_file('sss.flow')
    flow.print()
    from core.graph import CausalGraph
    g = CausalGraph(flow)
    g.render_in_browser()
