from typing import Any, Type, Iterator, Sequence, cast
import re

# Import the base engine classes
from core.engine import Cell, Flow, RuleSet, SpaceState1D as SpaceState
from parser import FlowLangParser
from implementation import (
    Selector, BaseRule, SubstitutionRule, InsertionRule, OverwriteRule,
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


def interpret_selector(selector_data: dict[str, Any]) -> Selector:
    """Converts AST selector data into a clean Selector NamedTuple."""
    s_type = selector_data["selector_type"]
    s_value = selector_data["value"]
    if s_type == "literal":
        return Selector(type=s_type, selector=tuple((Cell(c) for c in s_value)))
    elif s_type == "regex":
        return Selector(type=s_type, selector=re.compile(s_value))
    elif s_type == "range":
        return Selector(type=s_type, selector=s_value)
    elif s_type == "llm_prompt":
        # TODO: Add LLM prompt handling here when ready (returns a prompt string)
        re_pattern: re.Pattern = re.compile('llm result')
        return Selector(type='regex', selector=re_pattern)
    raise ValueError(f"Unknown selector type: {s_type}")


def interpret_instructions(instructions: Sequence[dict], global_flags: dict[str, Any]) -> Iterator[BaseRule]:
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
        selectors = [interpret_selector(sd) for sd in instruction['selector']]

        # The target may be a selector dict, an int (for shifting), or None (for deleting)
        target_data = instruction.get('target')
        target = None
        if isinstance(target_data, dict):
            target = interpret_selector(target_data)
        elif isinstance(target_data, int):
            target = target_data

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


def interpret_directives(objects: dict[str, Any], directives: dict[str, Any]) -> dict[str, Any]:
    """
    Use the directives to modify (call) the `objects`.
    """
    returns: dict[str, Any] = {}
    for path, args in directives.items():
        parts = path.split('.')
        root_name = parts[0]
        root_obj = objects.get(root_name)
        if not root_obj:
            continue

        current_obj = root_obj
        parent_obj = None  # we must keep track of this in case we want to assign to the attribute.
        target_attr_name = parts[-1]
        try:
            for part in parts[1:]:
                parent_obj = current_obj
                current_obj = getattr(current_obj, part)
        except AttributeError:
            # noinspection PyUnboundLocalVariable
            print(f"Error: Could not traverse '{part}' in path '{path}'.")
            continue

        if len(args) > 1 and args[0] == '=':
            # Assignment Logic
            val_to_assign = args[1:]
            if len(val_to_assign) == 1:
                val_to_assign = val_to_assign[0]
            if parent_obj:
                try:
                    setattr(parent_obj, target_attr_name, val_to_assign)
                except AttributeError:
                    print(f"Error: Cannot set attribute on {parent_obj}.")
            else:
                print(f"Warning: Cannot assign value directly to root object '{root_name}'.")
        else:
            # Function Call Logic
            if callable(current_obj):
                returns[path] = current_obj(*args)
            else:
                print(f"Error: '{path}' is not callable.")
    return returns


class FlowLang(Flow):
    """The main interpreter object, it is what actually runs any given code."""

    def __init__(self, lang: str, init_space: Sequence[str] | str | None = None):  # init_space can be none if the @init directive is defined.
        self.ast: dict[str, Any] = cast(dict[str, Any], cast(object, FlowLangParser().parse(lang)))  # a bunch of stupid casting due to the Lark.parse() hinting at Tree[Token] return instead of what the transformer returns.
        if isinstance(init_space, str):
            init_space = (init_space,)
        if init_space is None:
            r = interpret_directives({'Init': lambda *args: args}, self.ast['directives'])
            try:
                init_space = r['Init']
            except KeyError:
                raise ValueError("An `@Init(<space>)` directive must be present if the `init_space` argument is not provided.")
        super().__init__(RuleSet(list(interpret_instructions(self.ast['instructions'], self.ast['global_flags']))),
                         [SpaceState([Cell(s) for s in string]) for string in init_space])
        interpret_directives({'Flow': self, 'Self': self}, self.ast['directives'])

    @classmethod
    def from_file(cls, path: str):
        """opens `.flow` files and constructs a FlowLang object."""
        with open(path, 'r') as f:
            return cls(f.read())


if __name__ == "__main__":
    code = """
    @Init(AB);
    @Self.evolve_n(20);
    
    ABA -> AAB;
    A -> ABA;
    
    (-g[1] -nib -nds) {
        /B+$/ ><;
        [0,] >><<;
    }
    """
    flow = FlowLang.from_file('sss.flow')
    flow.print()
    from core.graph import CausalGraph
    g = CausalGraph(flow)
    g.render_in_browser()
