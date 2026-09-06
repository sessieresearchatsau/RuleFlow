from ruleflow.lang.interpreter import FlowLang


def test_flowlang_eca(snapshot_loader, serialize_flow_events):
    """
    Evolves an Elementary Cellular Automaton using the FlowLang interpreter
    and verifies the trajectory matches expected execution.
    """
    script = """
# initial state
@init("A" * 10 + "B" + 10 * "A");

# define the rules
@macro("/lang/ca.preset");
@macro("/lang/eca.pflow", "AB", 30);

# run n times
@evolve(9);
    """

    flow = FlowLang()
    flow.interpret(script)

    # Ensure it evolved 9 steps (plus the initial event = 10 total events)
    assert len(flow.events) == 10
    assert flow.current_event_idx == 9

    # Serialize events to verify structure
    serialized = serialize_flow_events(flow.events)
    expected_snapshot = snapshot_loader("eca_rule30_step10.json")
    assert serialized == expected_snapshot


def test_flowlang_sss(snapshot_loader, serialize_flow_events):
    """
    Evolves a Sequential Substitution System (SSS) using the FlowLang interpreter
    and ensures the rewrite mechanics operate correctly over 10 generations.
    """
    script = """
# set the initial state
@init("AB");

# define the sequential rules
AAAB -> BAA;
AAA -> BB;
B -> AAB;

# evolve
@evolve(9);
    """

    flow = FlowLang()
    flow.interpret(script)

    # Verify events were successfully tracked and generated
    assert len(flow.events) == 10

    # Serialize events to verify structure
    serialized = serialize_flow_events(flow.events)
    expected_snapshot = snapshot_loader("sss_complex_step10.json")
    assert serialized == expected_snapshot
