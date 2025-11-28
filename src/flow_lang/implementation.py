"""The pure python implementation of the language for 1D space.

Future Considerations:
- We may need to create different implementations for higher dimensions spaces.
- TODO: maybe make a CompositeRule object for rule merger directives to construct (defined in then Future Directives section of the Language Specification).
"""
from typing import Sequence, NamedTuple
from copy import deepcopy, copy
from core.engine import (
    Flow,
    SpaceState1D as SpaceState,
    Cell,
    Rule as RuleABC,
    RuleMatch,
    RuleSet as RuleSetBase,
    DeltaSpace
)


class BaseRule(RuleABC):
    def __init__(self):
        super().__init__()
        # Functionality Fields
        self.selector: dict  # use the "type" key to differentiate between selector types
        self.target: dict  # use the "type" key to differentiate between selector types

        # ==== Flags (that modify the internal rule behavior) ====
        self.nct: bool = False  # no cellular causality tracking (don't return delta cells)
        self.nns: bool = False  # no new space per event (don't create a copy of last space)
        self.m: tuple[int, int, int] = (0, -1, 1)  # the range of matches if there are multiple matches. Step can determine order.
        self.pl: int = 1  # parallel processing limit (how many times the rule can be applied per run without breaking into another branch).
        self.bl: int = 0  # branch limit per run (how many branches can be created).
        self.bo: str = 'last'  # branch origin. The origin of the branch can either be the last state or the current state (after any parallel/async modifications).
        self.crp: str = 'branch'  # conflict resolution protocol.
        self.tso: str = 'last'  # target selector origin. If the target involves a selector, choose where to pull characters from. To keep causality clean, the selected cells are always copied as new cells.
        self.offset: int = 0  # the offset to index the selectors return.
        self.input_range: tuple[int, int] | None = None  # maximum number of input spaces that a rule can process per event.
        self.lifespan: int = -1  # how many times this rule is allowed to run. Overall effect a rule can have before it dies.
        # Note that additional flags can be set in the syntax, however, they will have no meaning unless included in the control flow by subclassing and modifying particular rule.

    def match(self, spaces: Sequence[SpaceState]) -> Sequence[RuleMatch]:
        # TODO use the selector to find matches.
        pass

    def apply(self, matches: Sequence[RuleMatch]) -> Sequence[DeltaSpace]:
        raise NotImplementedError("Must be implemented in a subclass")



class InsertionRule(BaseRule):
    pass


class SubstitutionRule(BaseRule):
    pass


class OverwriteRule(BaseRule):
    pass


class DeletionRule(BaseRule):
    pass


class ShiftingRule(BaseRule):
    pass


class SwappingRule(BaseRule):
    pass
