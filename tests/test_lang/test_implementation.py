import pytest
import random
import numpy as np

from core.engine import RuleMatch, DeltaCell
from core.topologies.tooling.searcher import VectorRegexSearch, VectorSearch
from lang.implementation import (
    Selector, Target, BaseRule, SubstitutionRule, OverwriteRule, InsertionRule, DeletionRule
)


# ================ Base Rule Dependencies Fixture ================

@pytest.fixture
def base_rule_dependencies():
    """Provides standard searchers and a deterministic random engine for rule instantiation."""
    return VectorRegexSearch(), VectorSearch(), random.Random(42)


# ================ Conflict Detection Tests ================

def test_conflict_detector_overlap(base_rule_dependencies):
    """
    Test that overlapping spatial spans are properly marked based on the cmp flag,
    which stands for conflict marking protocol.
    """
    rule = SubstitutionRule([], [], *base_rule_dependencies)

    current_matches = [(0, 3), (4, 7)]
    new_match = (2, 5)

    # cmp = "ignore" ignores conflicts entirely.
    rule.cmp = "ignore"
    assert rule._conflict_detector(current_matches, new_match) == set()

    # cmp = "this" marks only the incoming match as a conflict.
    rule.cmp = "this"
    assert rule._conflict_detector(current_matches, new_match) == {2}

    # cmp = "og" marks only the original match as a conflict.
    rule.cmp = "og"
    assert rule._conflict_detector(current_matches, new_match) == {0, 1}

    # cmp = "both" marks both the original and the new match as conflicts.
    rule.cmp = "both"
    assert rule._conflict_detector(current_matches, new_match) == {0, 1, 2}


# ================ Rule Application Limits & Lifespan ================

def test_rule_application_limits_and_lifespan(space_1d_factory, base_rule_dependencies):
    """
    Test parallel execution limits and lifespan tracking for rule application.
    Ensures that limits properly break execution branches and decrement lifespan.
    """
    rule = SubstitutionRule(
        [Selector("literal", (65,))],
        [Target("literal", (66,))],
        *base_rule_dependencies
    )

    # Restrict to one execution per branch and a total lifespan of two.
    rule.parallel_execution_limit = 1
    rule.lifespan = 2

    space = space_1d_factory([65, 65, 65])

    # Create manual rule matches imitating the matcher output.
    rm = RuleMatch(space=space, matches=[(0, 1), (1, 2), (2, 3)], conflicts=set(), metadata=[rule, rule, rule])

    deltas = rule.apply([rm])

    # With a limit of one, it should branch or submit after applying once.
    assert len(deltas) == 1

    # Check that lifespan decremented and disabled status updated.
    assert rule.lifespan == 1
    assert not rule.disabled

    # Apply again to exhaust lifespan.
    rule.apply([rm])
    assert rule.lifespan == 0
    assert rule.disabled is True


# ================ Probabilistic Match Controls ================

def test_probabilistic_matching(space_1d_factory, base_rule_dependencies):
    """
    Tests p_rule and p_space stochastic flags to ensure matches are
    dropped randomly according to the random engine.
    """
    rule = SubstitutionRule(
        [Selector("literal", (65,))],
        [Target("literal", (66,))],
        *base_rule_dependencies
    )

    # Force the rule to skip matches and spaces by setting impossibly low thresholds.
    rule.p_space = 0.0
    rule.p_rule = 0.0

    space = space_1d_factory([65])

    matches = rule.match([space])
    assert len(matches) == 0


# ================ Delta Cell Aggregation ================

def test_aggregate_delta_cells():
    """
    Tests the static helper function that aggregates many DeltaCells into a single DeltaCell.
    """
    from core.engine import Cell

    dc1 = DeltaCell(destroyed_cells=[Cell(65, 0, 0)], new_cells=[Cell(66, 1, 1)])
    dc2 = DeltaCell(destroyed_cells=[Cell(67, 0, 2)], new_cells=[Cell(68, 1, 3)])

    aggregated = BaseRule._aggregate_DeltaCells([dc1, dc2])

    assert len(aggregated.destroyed_cells) == 2
    assert len(aggregated.new_cells) == 2
    assert aggregated.destroyed_cells[1].quanta == 67


# ================ Modifier Dispatch Tests ================

def test_specific_rule_modifier_dispatch(base_rule_dependencies, space_1d_factory):
    """
    Validates that subclasses properly route _call_space_modifier to the correct SpaceState methods.
    """
    space = space_1d_factory([65, 66, 67])

    # Substitution Rule calls space.substitute
    sub_rule = SubstitutionRule([], [], *base_rule_dependencies)
    sub_rule._call_space_modifier(space, (0, 1), [88])
    assert list(space.vec.data.logical_data) == [88, 66, 67]

    space = space_1d_factory([65, 66, 67])

    # Overwrite Rule calls space.overwrite
    ow_rule = OverwriteRule([], [], *base_rule_dependencies)
    ow_rule._call_space_modifier(space, (1, 2), [88, 89])
    assert list(space.vec.data.logical_data) == [65, 88, 89]

    space = space_1d_factory([65, 66, 67])

    # Insertion Rule calls space.insert
    ins_rule = InsertionRule([], [], *base_rule_dependencies)
    ins_rule._call_space_modifier(space, (1, 2), [88])
    assert list(space.vec.data.logical_data) == [65, 88, 66, 67]

    space = space_1d_factory([65, 66, 67])

    # Deletion Rule calls space.delete
    del_rule = DeletionRule([], [], *base_rule_dependencies)
    del_rule._call_space_modifier(space, (1, 3), None)
    assert list(space.vec.data.logical_data) == [65]
