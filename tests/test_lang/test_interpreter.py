from ruleflow.lang.interpreter import Interpreter, FlowLang
from ruleflow.lang.implementation import SubstitutionRule, OverwriteRule, Selector, Target


# ================ Interpreter Data Mapping ================

def test_interpreter_literal_conversion_and_wildcards():
    """
    Tests the logic where the interpreter automatically translates dot wildcards
    with ord value 46 into -1 for numerical mapping.
    """
    interp = Interpreter()
    interp.use_regex_for_literal_selectors(False)

    selector_data = {
        "selector_type": "literal_chars",
        "value": b"A.C"
    }

    selector = interp.interpret_selector(selector_data)

    assert selector.type == "literal"
    # Ordinal 'A' is 65, '.' is 46 (which converts to -1), 'C' is 67.
    assert list(selector.selector) == [65, -1, 67]


def test_interpreter_regex_fallback():
    """
    Verifies that Literal Selectors fallback to Regex strings when the global
    interpreter flag commands them to.
    """
    interp = Interpreter()
    interp.use_regex_for_literal_selectors(True)

    selector_data = {
        "selector_type": "literal_chars",
        "value": b"A.C"
    }

    selector = interp.interpret_selector(selector_data)

    # Forces regex mode instead of numerical array processing.
    assert selector.type == "regex"
    assert selector.selector == b"A.C"


# ================ Instruction Compilation & Flag Aliasing ================

def test_interpreter_instruction_compilation(base_rule_dependencies):
    """
    Iterates over a flat list of instructions, instantiates the correct Rule subclass,
    and applies global flags merging them over rule-level flags via FLAG_ALIAS.
    """
    interp = Interpreter()

    instructions = [{
        "selector": [{"selector_type": "literal", "value": [65]}],
        "operator": {"symbol": "->"},
        "target": [{"target_type": "literal", "value": [66]}],
        "flags": {"life": 5}
    }]

    global_flags = {"pl": 3}

    rule_generator = interp.interpret_instructions(
        instructions, global_flags, *base_rule_dependencies
    )

    rule = next(rule_generator)

    # Verify exact Rule type mapping for the substitution operator.
    assert isinstance(rule, SubstitutionRule)

    # Verify flag aliases translated 'pl' to 'parallel_execution_limit' and 'life' to 'lifespan'.
    assert rule.parallel_execution_limit == 3
    assert rule.lifespan == 5


# ================ FlowLang Directives ================

def test_flowlang_initializer_directive():
    """
    Tests FlowLang's internal @init directive implementation, verifying
    it processes tuples and strings correctly while hashing for cache invalidation.
    """
    flow = FlowLang()

    # The @init directive is routed to the internal __init function within the 'program' scope.
    flow.ast = {'directives': [], 'global_flags': {}, 'instructions': []}

    # Trigger __init with string initial state.
    flow._FlowLang__init("ABC")

    assert len(flow.events) == 1
    # Ensures the initial output space properly maps back to the string ordinals.
    assert list(list(flow.current_event.spaces)[0].vec.data.logical_data) == [65, 66, 67]

    # Trigger __init with tuple initial state.
    flow._FlowLang__init((10, 20, 30))
    # It must reset the events if the hash doesn't match.
    assert list(list(flow.current_event.spaces)[0].vec.data.logical_data) == [10, 20, 30]


def test_flowlang_merge_and_compress_directives(base_rule_dependencies):
    """
    Validates FlowLang's @merge and @compress directives.
    @merge links rules together into chains, and @compress disables rules that cause no changes.
    """
    flow = FlowLang()

    # Create dummy rules sharing group 0.
    rule1 = OverwriteRule([Selector("literal", (65,))], [Target("literal", (65,))], *base_rule_dependencies)
    rule2 = OverwriteRule([Selector("literal", (66,))], [Target("literal", (67,))], *base_rule_dependencies)

    from ruleflow.core.engine import RuleSet
    flow.set_ruleset(RuleSet([rule1, rule2]))

    # Execute merge logic to link rules.
    flow._FlowLang__merge_group(0)

    assert rule2 in rule1.chain
    assert rule2.is_in_chain is True

    # Execute compress logic. Rule 1 overwrites "A" with "A", meaning causality is preserved
    # but no structural change occurs. It should be disabled.
    flow._FlowLang__compress_group(0)

    assert rule1.disabled is True
    assert rule2.disabled is False
