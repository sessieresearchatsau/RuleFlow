import pytest
from implementations.sss import SSS


def test_sss_system_snapshot_verification(snapshot_loader, serialize_flow_events):
    """
    Runs a Sequential Substitution System (SSS) and compares
    its serialized evolution against the human-verified JSON snapshot.
    """
    # Initialize SSS with standard substitution rules and initial string 'AB'
    system = SSS(rule_set=["ABA -> AAB", "A -> ABA"], initial_space='AB')
    system.evolve(2)

    # Serialize live events using the conftest fixture
    serialized_events = serialize_flow_events(system.events)

    # Load the expected snapshot
    expected_snapshot = snapshot_loader("sss_simple_step3.json")

    assert serialized_events == expected_snapshot
