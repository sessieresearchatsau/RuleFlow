"""  TODO: work here 👈👈👈
- Take the AST and construct rulesets.
    - define rules.
        - change rules by adding a find(selector) method to match positions and the apply(matches).
    - modify ruleset behavior
    - construct the rules.
"""
import flow_lang.implementation as impl

from typing import Sequence, Any, Type, Dict, List, Literal, Tuple, Union
from math import inf
import re

# Import the base engine classes
from core.engine import Flow, SpaceState1D, Cell, Rule as RuleABC
from implementation import (
    BaseRule, Selector, SubstitutionRule, InsertionRule, OverwriteRule,
    DeletionRule, ShiftingRule, ReverseRule
)


RULE_MAPPER: Dict[str, Type[BaseRule]] = {
        "->": SubstitutionRule,
        ">": InsertionRule,
        "-->": OverwriteRule,
        "><": DeletionRule,
        ">>": ShiftingRule,
        "<<": ShiftingRule,
        ">><<": ReverseRule,
}


class FlowLangInterpreter:
    """
    Translates the Flow Lang AST (dictionary structure from the parser)
    into runnable engine objects (Rule, RuleSet, Flow).
    """

    # Maps DSL operators to the concrete Rule class


    # Maps flag keys to their expected type conversion function
    FLAG_CONVERTERS: Dict[str, Any] = {
        # Numeric Limits (float supports inf)
        "pl": float,
        "bl": float,
        "lifespan": float,
        # Boolean Flags (True/False or default True)
        "nct": bool, "nns": bool, "a": bool, "g_break": bool, "d": bool,
        # Multi-part flags (e.g., [start, end, step])
        "m": lambda args: (float(args[0]) if args[0] is not None else 0,
                           float(args[1]) if args[1] is not None else inf,
                           float(args[2]) if args[2] is not None else 1),
        "input_range": lambda args: (float(args[0]) if args[0] is not None else 0,
                                     float(args[1]) if args[1] is not None else inf),
        # Literal/String Flags
        "bo": lambda args: args[0], "crp": lambda args: args[0], "tso": lambda args: args[0],
        "g": lambda args: int(args[0]), "id": lambda args: args[0], "weight": float,
        "offset": int,
        # LLM/Stochastic flags (handled as strings, conversion logic lives in RuleSet)
        "llm_temp": float, "llm_seed": str, "llm_cache": float,
        "p_seed": str, "p_run": float, "p_apply": float,
    }

    def __init__(self, ast_data: Dict[str, Any]):
        self.directives: Dict[str, Any] = ast_data.get("directives", {})
        self.global_flags: Dict[str, Any] = self._convert_flags(ast_data.get("ruleset_flags", {}))
        self.raw_instructions: List[Dict] = ast_data.get("all_instructions", [])

        self.rules: List[RuleABC] = []
        self._interpret_instructions()

    def _convert_flags(self, raw_flags: Dict[str, Any]) -> Dict[str, Any]:
        """Converts raw flag values (from the parser) into their final Python types."""
        converted_flags = {}
        for key, value in raw_flags.items():
            converter = self.FLAG_CONVERTERS.get(key)
            if converter:
                try:
                    # Handle multi-part flags (lists) vs. single values
                    if isinstance(value, list) and key in ("m", "input_range"):
                        converted_flags[key] = converter(value)
                    elif isinstance(value, list) and len(value) == 1:
                        # Single value list (e.g., -g[1])
                        converted_flags[key] = converter(value[0])
                    elif isinstance(value, list):
                        # Multi-value list (e.g., LLM flags or complex strings)
                        converted_flags[key] = [converter(v) for v in value]
                    else:
                        # Boolean or simple scalar value
                        converted_flags[key] = converter(value)
                except Exception as e:
                    print(f"Warning: Failed to convert flag '{key}' with value '{value}'. Error: {e}")
                    converted_flags[key] = value  # Use raw value as fallback
            else:
                converted_flags[key] = value
        return converted_flags

    def _parse_selector(self, selector_data: Dict[str, Any]) -> Selector:
        """Converts AST selector data into a clean Selector NamedTuple."""
        s_type = selector_data["type"]
        s_value = selector_data["value"]

        if s_type == "literal":
            # Convert simple string literal into sequence of Cells
            # Handles the wildcard '_'
            cells = [Cell(c) if c != '_' else '_' for c in s_value]
            return Selector(type=s_type, selector=tuple(cells))

        elif s_type == "regex":
            # Compile the regex pattern once for performance
            pattern = re.compile(s_value)
            return Selector(type=s_type, selector=pattern)

        elif s_type == "range":
            # Range is already a tuple of (start, end)
            start = selector_data["start"] if selector_data["start"] is not None else 0
            end = selector_data["end"] if selector_data["end"] is not None else inf
            return Selector(type=s_type, selector=(start, end))

        # Add LLM prompt handling here when ready (returns a prompt string)
        # elif s_type == "llm_prompt":
        #    return Selector(type=s_type, selector=s_value)

        raise ValueError(f"Unknown selector type: {s_type}")

    def _interpret_instructions(self) -> None:
        """
        Iterates over the flat list of instructions, instantiates the correct
        Rule subclass, merges flags, and initializes fields.
        """
        for instruction in self.raw_instructions:
            operator = instruction["operator"]
            RuleClass = self.RULE_MAPPER.get(operator)

            if not RuleClass:
                print(f"Warning: Unknown operator '{operator}'. Skipping rule.")
                continue

            # 1. Prepare Selectors and Targets
            raw_selector_data = instruction["selector"]
            # The parser output supports multi-selectors (e.g., "A B"), so ensure it's a list.
            if not isinstance(raw_selector_data, list):
                raw_selector_data = [raw_selector_data]

            selectors = [self._parse_selector(sd) for sd in raw_selector_data]

            # The target may be a selector dict, an int (for shifting), or None (for deleting)
            target_data = instruction.get("target")
            target = None
            if isinstance(target_data, dict):
                # Target is a selector (e.g., substitution target)
                target = self._parse_selector(target_data)
            elif target_data is not None:
                # Target is an integer (for shifting)
                try:
                    target = int(target_data)
                except ValueError:
                    # This should not happen if parsing is correct
                    print(f"Warning: Shift target '{target_data}' is not an integer.")

            # 2. Instantiate Rule
            rule_instance: BaseRule = RuleClass(selectors, target)

            # 3. Merge and Assign Flags (Global < Rule/Group)

            # Start with global defaults
            final_flags = self.global_flags.copy()

            # Apply rule/group flags (overwrites global)
            rule_flags = instruction.get("flags", {})
            converted_rule_flags = self._convert_flags(rule_flags)
            final_flags.update(converted_rule_flags)

            # Apply flags to the rule instance
            for key, value in final_flags.items():
                # Map shorthand keys (e.g., 'pl' for parallel_processing_limit) to full attribute names
                # This requires you to know the mapping or use __dict__

                # For this implementation, we will assume flag keys map directly to attributes
                # e.g., 'pl' maps to self.pl, 'bo' maps to self.bo
                try:
                    if hasattr(rule_instance, key):
                        setattr(rule_instance, key, value)
                except Exception as e:
                    print(f"Warning: Could not set attribute {key} on rule. Error: {e}")

            self.rules.append(rule_instance)

    def initialize_flow(self) -> Flow:
        """
        Initializes the Flow engine object, consuming the directives.
        """
        # 1. Get initial state from @Universe directive
        universe_str = self.directives.get("Universe", "")
        if not universe_str:
            raise ValueError("Flow Lang requires an @Universe directive to define the initial state.")

        initial_cells = [Cell(c) for c in universe_str]
        initial_space = SpaceState1D(initial_cells)

        # 2. Configure and Instantiate RuleSet
        # NOTE: A RuleSet class handling group management would be created here.
        # For simplicity, we pass the raw rules to a basic RuleSet (assuming the engine can handle it).

        # Placeholder for RuleSet instantiation (assuming your engine uses a list of rules)
        class SimpleRuleSet:
            def __init__(self, rules):
                self.rules = rules
            # ... (the rest of the RuleSet methods are required here)

        # Assuming the RuleSet handles its own flag logic (e.g., ncd, ncr)
        # and has been designed to accept the simple list of RuleABC objects.
        # We assume the RuleSet class is defined somewhere and is called RuleSetBase

        from core.engine import RuleSet as RuleSetBase  # Re-importing base class

        class FlowRuleSet(RuleSetBase):
            def __init__(self, rules: List[RuleABC]):
                super().__init__(rules)
                # Assign global ruleset flags here (e.g., self.no_cellular_causality = self.global_flags.get("ncr", False))

        ruleset_instance = FlowRuleSet(self.rules)

        # 3. Instantiate and Return Flow
        return Flow(ruleset_instance, initial_space)
