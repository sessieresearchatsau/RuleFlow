from ruleflow.core.numlib import INF
from ruleflow.lang.parser import parse, parse_callable_args


# ================ Exhaustive Grammar Test ================

def test_parser_exhaustive_grammar_coverage():
    """
    Tests an extremely complex, exhaustive FlowLang snippet.
    This guarantees that the Lark grammar and the FlowLangTransformer correctly parse:
    - Macro expansions and nested AST merges.
    - Multiple mixed selectors and targets in a single instruction.
    - Missing range boundaries falling back to 0 and INF.
    - Operator definitions (->, -->, >, ><).
    - Evaluated literal tuples, dictionary flag arguments, and callable signatures.
    - Block-scoped flag distribution.
    """
    complex_flow = r'''
# 1. Directives (Includes a macro that will unpack)
@macro("/lang/ca.preset");
@test(1, "12", (2,2), k=2);
@test2.all()[0].yup(1, 2, 3);

# 2. Global Flags
-test[slice(1, 1, 1)]
-globalDict[{"key": "value"}]

# 3. Block with grouped flags
(-a -j[2])(
    # Multiple mixed selectors and targets
    "AAB" AB -> ABA CBA (1, 2);

    # Function term selector and Literal target with nested tuple structures
    fn<1, 2> -> (1, 2, 3, "A") -ttt;

    # Ranges with open ends, infinities, and empty brackets
    [-inf, inf] --> AB;
    [, 5] > AB;
    [5, ] >< ;
    [] -> ();

    # Literal term with negative integers
    (1, 2, -3, 4) --> AB;
)

# 4. Standalone instruction outside the block
(1, 2) ->;

# This is an example of a single line comment!
"""
This is an example of multiline comment.
It is a cool feature!
"""
    '''

    ast = parse(complex_flow)

    # ================ Assert Directives ================

    # @macro("stat.ca.preset") injects 4 directives into the AST.
    assert 'self.regex_searcher.set_find_args(overlapped=True)' in ast['directives']
    assert 'self.literal_searcher.set_overlapping_mode(True)' in ast['directives']
    assert 'compress(0)' in ast['directives']
    assert 'merge(0)' in ast['directives']

    # Our explicit directives.
    assert 'test(1, "12", (2,2), k=2)' in ast['directives']
    assert 'test2.all()[0].yup(1, 2, 3)' in ast['directives']

    # ================ Assert Global Flags ================

    g_flags = ast['global_flags']

    # The macro also injects -pl[inf] and -mr[0,inf] into the global flags.
    assert g_flags['pl'] is INF
    assert g_flags['mr'] == (0, INF)

    # Our explicit global flags.
    assert g_flags['test'] == slice(1, 1, 1)
    assert g_flags['globalDict'] == {"key": "value"}

    # ================ Assert Instructions ================

    insts = ast['instructions']

    # 7 instructions inside the block, 1 outside = 8 total instructions.
    assert len(insts) == 8

    # --- Instruction 1: Multiple mixed selectors and targets ---
    # "AAB" AB -> ABA CBA (1, 2);
    inst1 = insts[0]
    assert inst1['operator']['symbol'] == '->'
    assert inst1['flags'] == {'a': True, 'j': 2}  # Inherited from block

    # Selectors
    assert inst1['selector'][0]['selector_type'] == 'regex'
    assert inst1['selector'][0]['value'] == b'AAB'
    assert inst1['selector'][1]['selector_type'] == 'literal_chars'
    assert inst1['selector'][1]['value'] == b'AB'

    # Targets
    assert inst1['target'][0]['target_type'] == 'literal_chars'
    assert inst1['target'][0]['value'] == b'ABA'
    assert inst1['target'][1]['target_type'] == 'literal_chars'
    assert inst1['target'][1]['value'] == b'CBA'
    assert inst1['target'][2]['target_type'] == 'literal'
    assert inst1['target'][2]['value'] == (1, 2)

    # --- Instruction 2: Function terms and Literal eval mapping ---
    # fn<1, 2> -> (1, 2, 3, "A") -ttt;
    inst2 = insts[1]
    assert inst2['flags'] == {'a': True, 'j': 2, 'ttt': True}  # -ttt appended/overwrote block flags

    assert inst2['selector'][0]['selector_type'] == 'function'
    assert inst2['selector'][0]['name'] == 'fn'
    assert inst2['selector'][0]['args'] == ((1, 2), {})  # parsed via parse_callable_args

    assert inst2['target'][0]['target_type'] == 'literal'
    # "A" evaluates to ord("A") which is 65 in literal_term.
    assert inst2['target'][0]['value'] == (1, 2, 3, 65)

    # --- Instruction 3: Range Term Infinities ---
    # [-inf, inf] --> AB;
    inst3 = insts[2]
    assert inst3['operator']['symbol'] == '-->'
    assert inst3['selector'][0]['selector_type'] == 'range'
    assert inst3['selector'][0]['value'] == (-INF, INF)

    # --- Instruction 4: Range Term Missing Start ---
    # [, 5] > AB;
    inst4 = insts[3]
    assert inst4['operator']['symbol'] == '>'
    assert inst4['selector'][0]['selector_type'] == 'range'
    assert inst4['selector'][0]['value'] == (0, 5)  # Fallback start to 0

    # --- Instruction 5: Range Term Missing End and Delete Operator ---
    # [5, ] >< ;
    inst5 = insts[4]
    assert inst5['operator']['symbol'] == '><'
    assert inst5['selector'][0]['selector_type'] == 'range'
    assert inst5['selector'][0]['value'] == (5, INF)  # Fallback end to INF
    assert len(inst5['target']) == 0

    # --- Instruction 6: Empty Range Term ---
    # [] -> ();
    inst6 = insts[5]
    assert inst6['selector'][0]['selector_type'] == 'range'
    assert inst6['selector'][0]['value'] == (0, 0)
    assert inst6['target'][0]['target_type'] == 'literal'
    assert inst6['target'][0]['value'] == ()

    # --- Instruction 7: Negative Literal Integers ---
    # (1, 2, -3, 4) --> AB;
    inst7 = insts[6]
    assert inst7['selector'][0]['selector_type'] == 'literal'
    assert inst7['selector'][0]['value'] == (1, 2, -3, 4)

    # --- Instruction 8: Un-grouped Instruction ---
    # (1, 2) -> ;
    inst8 = insts[7]
    assert inst8['flags'] == {}  # Did not inherit block flags
    assert inst8['selector'][0]['selector_type'] == 'literal'
    assert inst8['selector'][0]['value'] == (1, 2)
    assert len(inst8['target']) == 0


# ================ Helper Parsing Tests ================

def test_parse_callable_args_helper():
    """Verify that Python callable signatures parse correctly using the parser's eval wrapper."""
    args, kwargs = parse_callable_args('1, "test", x=5, y=INF')
    assert args == (1, "test")
    assert kwargs == {'x': 5, 'y': INF}
