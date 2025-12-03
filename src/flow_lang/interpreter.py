"""  TODO: work here 👈👈👈
- Take the AST and construct rulesets.
    - define rules.
        - change rules by adding a find(selector) method to match positions and the apply(matches).
    - modify ruleset behavior
    - construct the rules.
"""
from typing import Any, Type, Iterator
import re

# Import the base engine classes
from core.engine import Flow, SpaceState1D, Cell
from implementation import (
    BaseRule, Selector, SubstitutionRule, InsertionRule, OverwriteRule,
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
    s_type = selector_data["type"]
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


def interpret_instructions(instructions: list[dict], global_flags: dict[str, Any]) -> Iterator[BaseRule]:
    """
    Iterates over the flat list of instructions, instantiates the correct
    Rule subclass, merges flags, and initializes fields.
    """
    for instruction in instructions:
        operator = instruction["operator"]
        RuleClass = RULE_MAPPER.get(operator)
        if not RuleClass:
            print(f"Warning: Unknown operator '{operator}'. Skipping rule.")
            continue

        # 1. Prepare Selectors and Targets
        if not instruction["selector"]:
            print(f"Warning: All rules must have a selector. Skipping rule.")
            continue
        selectors = [interpret_selector(sd) for sd in instruction["selector"]]

        # The target may be a selector dict, an int (for shifting), or None (for deleting)
        target_data = instruction.get("target")
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
        rule_flags = instruction.get("flags", {})
        final_flags.update(rule_flags)  # Apply rule/group flags (overwrites global)
        # Apply flags to the rule instance
        for key, value in final_flags.items():
            # Map shorthand keys (e.g., 'pl' for 'parallel_processing_limit') to full attribute names
            setattr(rule_instance, rule_instance.FLAG_ALIAS.get(key, key), value)

        yield rule_instance


def interpret_directives(objects: list[object], directives: dict[str, Any]) -> None:
    """Use the directives to modify (call) the `objects`. The provided objects can be functions or objects on which the directives are applied."""
    pass
