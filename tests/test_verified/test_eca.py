import pytest
from implementations.eca import ECA


def test_eca_rule_90_snapshot_verification(snapshot_loader, serialize_flow_events):
    """
    Runs Wolfram's Rule 90 elementary cellular automaton and compares
    its serialized evolution against the human-verified JSON snapshot.
    """
    # Initialize Rule 90 with a small symmetric initial state
    system = ECA(rule_index=90, initial_space=[0, 0, 1, 0, 0])
    system.evolve(3)

    # Serialize live events using the conftest fixture
    serialized_events = serialize_flow_events(system.events)

    # Load the expected snapshot
    expected_snapshot = snapshot_loader("eca_rule90_step3.json")

    assert serialized_events == expected_snapshot
