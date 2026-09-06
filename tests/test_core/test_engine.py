import pytest
from core.engine import (
    Flow, Event, DeltaSpace, DeltaCell, Coordinate,
    RuleSet, Rule, RuleMatch
)


class MockFlow(Flow):
    def __init__(self, space_factory):
        super().__init__()
        self.set_initial_space([space_factory([1, 2, 3])])


def test_flow_event_architecture(space_1d_factory):
    flow = MockFlow(space_1d_factory)

    assert flow.current_event_idx == 0
    assert flow.current_event.time == 0

    # Mock a manual rule application
    space_0 = tuple(flow.current_event.spaces)[0]
    space_1 = space_0.next_gen()

    # Create a DeltaCell manually representing a deletion
    dc = DeltaCell(destroyed_cells=[space_0.topology.get_cell(1)], new_cells=[])

    ds = DeltaSpace(
        input_space=space_0,
        output_space=(space_1,),
        cell_deltas=(dc,),
        rule=None
    )

    # Inject new event
    new_event = Event(time=1, space_deltas=[ds])
    flow.events.append(new_event)

    # Ensure properties extract correctly
    assert len(list(new_event.affected_cells)) == 1
    assert list(new_event.spaces) == [space_1]
    # Check that causally_connected_events extracts the 'gen' from the destroyed cell
    assert list(new_event.causally_connected_events) == [0]


def test_walk_branch(space_1d_factory):
    flow = MockFlow(space_1d_factory)

    # Setup dummy tree
    s0 = tuple(flow.current_event.spaces)[0]
    s1a = s0.next_gen()
    s1b = s0.next_gen()

    # Event 1 creates two branches
    ds1a = DeltaSpace(s0, (s1a,), (DeltaCell((), ()),), None, parent_delta=flow.current_event.space_deltas[0])
    ds1b = DeltaSpace(s0, (s1b,), (DeltaCell((), ()),), None, parent_delta=flow.current_event.space_deltas[0])
    flow.events.append(Event(1, [ds1a, ds1b]))

    # Walk up branch 1b
    coord = Coordinate(event_idx=-1, space_idx=1)
    history = list(flow.walk_branch(coord))

    # Should yield s1b, then s0
    assert history == [s1b, s0]


class DummyRule(Rule):
    def __init__(self, group=(0,), group_break=True, always_apply=False, disabled=False):
        super().__init__()
        self.group = group
        self.group_break = group_break
        self.always_apply = always_apply
        self.disabled = disabled
        self.matched = False
        self.applied = False

    def match(self, spaces):
        self.matched = True
        return [RuleMatch(space=spaces[0], matches=((0, 1),), conflicts=set())]

    def apply(self, rule_matches):
        self.applied = True
        space = rule_matches[0].space
        next_s = space.next_gen()
        dc = DeltaCell(destroyed_cells=(), new_cells=())
        return [DeltaSpace(input_space=space, output_space=(next_s,), cell_deltas=(dc,), rule=self)]


def test_ruleset_group_break(space_1d_factory):
    space = space_1d_factory([1, 2, 3])

    # Both rules share group 0; rule 1 has group_break=True
    r1 = DummyRule(group=(0,), group_break=True)
    r2 = DummyRule(group=(0,))

    rs = RuleSet([r1, r2])
    deltas = rs.apply([space])

    assert len(deltas) == 1
    assert r1.applied is True
    assert r2.matched is False
    assert r2.applied is False


def test_ruleset_always_apply(space_1d_factory):
    space = space_1d_factory([1, 2, 3])

    # r1 breaks group 0, but r2 has always_apply=True
    r1 = DummyRule(group=(0,), group_break=True)
    r2 = DummyRule(group=(0,), always_apply=True)

    rs = RuleSet([r1, r2])
    deltas = rs.apply([space])

    assert len(deltas) == 2
    assert r1.applied is True
    assert r2.applied is True


def test_ruleset_disabled_rule(space_1d_factory):
    space = space_1d_factory([1, 2, 3])

    r1 = DummyRule(disabled=True)
    rs = RuleSet([r1])
    deltas = rs.apply([space])

    assert len(deltas) == 0
    assert r1.matched is False
    assert r1.applied is False
