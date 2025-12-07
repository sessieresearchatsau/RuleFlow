"""The implementation for 1D space that supports the language features.

Future Considerations:
- We will need to create different implementations for higher dimensions spaces.
"""
from typing import Sequence, NamedTuple, Literal, cast, Iterator, Any, Callable
from re import Pattern
from copy import deepcopy, copy
from numerical_helpers import INF
from core.engine import (
    SpaceState1D as SpaceState,
    Cell,
    Rule as RuleABC,
    RuleMatch,
    DeltaSpace,
    DeltaCells,
    Signal
)


class Selector(NamedTuple):
    type: Literal["literal", "regex", "range"]
    selector: Sequence[Cell] | Pattern | tuple[int, int]


class BaseRule(RuleABC):
    FLAG_ALIAS: dict[str, str] = {
        # IMPORTANT!!!: these must be kept up-to-date with the actual attributes.
        # ==== basic flags ====
        'd': 'disabled',
        'g': 'group',
        'gb': 'group_break',
        'a': 'always_apply',

        # ==== match() flags ====
        'sr': 'space_range',
        'mr': 'match_range',
        # offset
        # cmp

        # ==== apply() flags ====
        'nct': 'no_causality_tracking',
        'nib': 'no_initial_branch',
        'nds': 'no_delta_submit',
        'pl': 'parallel_execution_limit',
        'bl': 'branch_limit',
        'bo': 'branch_origin',
        # tso
        # crp
        'life': 'lifespan',
    }

    def __init__(self, selector: Sequence[Selector], target: Selector | int | None):
        super().__init__()
        # Functionality Fields
        self.selectors: Sequence[Selector] = selector  # used by self.match()
        self.target: Selector | int | None = target  # used by self.apply()  # Selector is for most operations, Int for operations such as shifting, and None for operations such as delete.

        # Complex Functionality
        self.chain: list[BaseRule] = [self]  # so that multiple rules can be chained to this one. Each rule here is treated as though it is "self".
        self.is_in_chain: bool = False  # if this is true, this rule will be ignored as it is expected to run in a chain.

        # ======== Flags (that modify the internal rule behavior) ========
        # match() flags
        self.space_range: tuple[int, int, int] = (0, 1, 1)  # the range of spaces that are matched
        self.match_range: tuple[int, int] = (0, 1)  # the range of matches if there are multiple matches
        self.offset: int = 0  # the offset to the index that selectors return.
        self.cmp: Literal["both", "og", "this", "ignore"] = "ignore"  # conflict marking protocol (if the second match conflicts with the first match, mark both as conflicts if mode='both', for instance, not only the second one.)

        # apply() flags
        self.no_causality_tracking: bool = False  # no cellular causality tracking (don't return delta cells)
        self.no_initial_branch: bool = False  # no initial branch the last space before executing rule (just modify last space) (can still be branched depending on `-pl` limit)
        self.no_delta_submit: bool = False  # if no new states are to be submitted (even if they do occur)
        self.parallel_execution_limit: int = 1  # parallel execution limit (how many times the rule can be executed per run without breaking into another branch).
        self.branch_limit: int = 0  # branch limit per run (how many branches can be created).
        self.branch_origin: Literal["prev", "current"] = "prev"
        self.crp: Literal["branch", "branch_nbl", "skip", "break", "ignore"] = "ignore"  # conflict resolution protocol. Note: at some point this could be extended to exclude BOTH conflicts, not just the one conflicting with the other.

        # rule life flags
        self.lifespan: int = INF  # how many times this rule is allowed to be successfully applied. This is the overall effect a rule can have before it dies.

        # stochastic flags
        self.p_seed: int | None = None  # determines the seed... if the outcome will be the same every time.
        self.p_match: int | None = None  # probability that a match will be counted.
        self.p_space: int | None = None  # probability that a space will be selected.
        self.p_apply: int | None = None  # probability that a rule will apply() at all.

        # Note that additional flags can be set in the syntax, however, they will have no meaning unless included in the control flow by subclassing and modifying particular rule.


        # ======== Signals ========
        # NOTE: time.sleep() can be used by the client to pause flow execution temporally (or play notes, etc.).
        self.on_applied: Signal = Signal()  # if the apply() function was called. The modified spaces is passed as Sequence[DeltaSpace] so that the client can test if the rule was effective.
        # the three following rules get the RuleMatch along with idx of the current match passed as arguments to the client.
        self.on_execution: Signal = Signal()
        self.on_branch: Signal = Signal()
        self.on_conflict: Signal = Signal()

    def __repr__(self):
        return f"{self.__class__.__name__}({[s.selector for s in self.selectors]}, {self.target.selector})"

    def _conflict_detector(self, current_matches: list[tuple[int, int]], match: tuple[int, int]) -> set[int]:
        """helper that detects collisions between selectors"""
        this_idx: int = len(current_matches)  # the len will be the index of match
        conflicts: set[int] = set()
        start1, end1 = match
        for og_idx, m in enumerate(current_matches):
            start2, end2 = m
            if (start1 < start2 < end1 or start1 < end2 < end1
                    or start2 < start1 < end2 or start2 < end1 < end2):
                if self.crp == "this": conflicts.add(this_idx)
                elif self.crp == "og": conflicts.add(og_idx)
                elif self.cmp == "both":
                    conflicts.add(this_idx)
                    conflicts.add(og_idx)
                else:  # if "ignore"
                    continue
        return conflicts

    # noinspection PyMethodFirstArgAssignment
    def match(self, spaces: Sequence[SpaceState]) -> Sequence[RuleMatch]:
        if self.is_in_chain:
            return ()  # we do not run the rule outside the collective "self"
        spaces: Sequence[SpaceState] = spaces[slice(*self.space_range)]
        out: list[RuleMatch] = []
        for space in spaces:
            chained: list[BaseRule] = []
            matches: list[tuple[int, int]] = []
            conflicts: set[int] = set()
            for self in self.chain:
                for pattern in self.selectors:
                    finds: Iterator[tuple[int, int]]
                    if pattern.type == 'literal':
                        finds = space.find(pattern.selector)  # it is better if the selector is already a Sequence[Cell] because otherwise the raw string has to be converted every time.
                    elif pattern.type == 'regex':
                        finds = space.regex_find(pattern.selector)
                    elif pattern.type == 'range':
                        finds = iter((pattern.selector,))
                    else: continue
                    for idx, span in enumerate(finds):
                        if self.offset:
                            span = (span[0] + self.offset, span[1] + self.offset)
                        if self.match_range[0] > idx:
                            continue
                        if idx >= self.match_range[1]:
                            break
                        if self.cmp != 'ignore':
                            conflicts.update(self._conflict_detector(matches, span))
                        matches.append(span)
                        chained.append(self)  # these "line up" with the matches
            if matches:
                out.append(
                    RuleMatch(
                        space=space,
                        matches=matches,
                        conflicts=conflicts,
                        metadata=chained,  # we simply use this extra (and optional) metadata field to let .apply() know which rule in self.chain is tied to which match.
                    )
                )
        return out

    def _aggregate_DeltaCells(self, delta_cells: list[DeltaCells]) -> DeltaCells:
        """Helper function to aggregate many DeltaCells into a single DeltaCells"""
        if len(delta_cells) == 1:
            return delta_cells[0]
        destroyed_cells: list[Cell] = []
        new_cells: list[Cell] = []
        for delta_cell in delta_cells:
            destroyed_cells.extend(delta_cell.destroyed_cells)
            new_cells.extend(delta_cell.new_cells)
        return DeltaCells(destroyed_cells, new_cells)

    def _call_space_modifier(self, space: SpaceState, selector: tuple[int, int], target: Sequence[Cell] | None) -> DeltaCells:
        raise NotImplementedError('A subclass must implement the correct modifier (e.g. `space.substitute(selector, deepcopy(target))`)')

    # noinspection PyMethodFirstArgAssignment
    def apply(self, rule_matches: Sequence[RuleMatch]) -> Sequence[DeltaSpace]:
        og_self: BaseRule = self.chain[0]  # because self is reassigned when there are self has a chain of followers.
        modified_spaces: list[DeltaSpace] = []
        for rule_match in rule_matches:  # basically loop through all spaces
            prev_space: SpaceState = cast(SpaceState, rule_match.space)
            current_space: SpaceState = prev_space if self.no_initial_branch else copy(prev_space)
            cell_deltas: list[DeltaCells] = []  # stack of the cell deltas that is cleared whenever delta space is submitted
            pl: int = 0  # parallel executions
            bl: int = 0  # branch executions
            matches_bound: int = len(rule_match.matches) - 1
            for idx, selector in enumerate(rule_match.matches):  # a "run" over the matches to the space.
                # noinspection PyTypeHints
                self: BaseRule = rule_match.metadata[idx]  # we need to treat each rule in the chain (specifically those with successful matches which are put in .metadata of the RuleMatch) as though they are "self"

                # make sure the target is in a correct form for all rules (Sequence[Cell] for rewriting or inserting, None for deleting or reversing, and int for shifting)
                target: Sequence[Cell] | int | None = None
                if isinstance(self.target, int):
                    target = self.target
                elif isinstance(t:=self.target, Selector):
                    if t.type == 'literal':
                        target = t.selector
                    elif t.type in ('regex', 'range'):
                        span: tuple[int, int] | None = next(prev_space.regex_find(t.selector), None) \
                        if t.type == 'regex' else t.selector if t.type == 'range' else None
                        if span is None:
                            break
                        target = prev_space[span[0]:span[1]]

                # handle the selector if it is a conflict
                if self.parallel_execution_limit > 1 and self.crp != 'ignore' and idx in rule_match.conflicts:
                    self.on_conflict.emit(rule_match, idx)
                    if self.crp in ('branch', 'branch_nbl'):
                        if self.crp == 'branch' and bl == self.branch_limit:
                            continue
                        branch: SpaceState = copy(prev_space)
                        dc: DeltaCells = self._call_space_modifier(branch, selector, target)
                        modified_spaces.append(DeltaSpace(
                            input_space=prev_space,
                            output_space=branch if not self.no_delta_submit else None,
                            cell_deltas=DeltaCells((), ()) if self.no_causality_tracking else dc
                        ))
                    elif self.crp == 'skip':
                        continue  # just skip this selector
                    elif self.crp == 'break':
                        break
                    continue

                # apply operation
                cell_deltas.append(
                    self._call_space_modifier(current_space, selector, target)
                )
                pl += 1  # increment the parallel execution tracker

                # if pl is at max, submit modified space
                if pl == self.parallel_execution_limit or idx == matches_bound:  # if parallel execution limit is reached OR no more matches for the space
                    modified_spaces.append(DeltaSpace(
                        input_space=prev_space,
                        output_space=current_space if not self.no_delta_submit else None,
                        cell_deltas=DeltaCells((), ()) if self.no_causality_tracking else self._aggregate_DeltaCells(cell_deltas)
                    ))
                    pl = 0
                    cell_deltas.clear()
                    self.on_execution.emit(rule_match, idx)

                    # set the new current space (branch into another universe)
                    if bl != self.branch_limit:
                        current_space = copy(prev_space) if self.branch_origin == 'prev' else copy(current_space)
                        bl += 1
                        self.on_branch.emit(rule_match, idx)
                    else:
                        break  # break out of loop if no branches are supposed to be made.

        self = og_self  # make sure we are referring to the top of the chain version of "self"
        # ensure the lifespan is enforced
        self.lifespan -= 1  # will not affect infinity if so set
        if self.lifespan == 0 and modified_spaces:
            self.disabled = True
        self.on_applied.emit(modified_spaces)
        return modified_spaces


class SubstitutionRule(BaseRule):
    def _call_space_modifier(self, space: SpaceState, selector: tuple[int, int], target: Sequence[Cell]) -> DeltaCells:
        return space.substitute(selector, deepcopy(target))


class InsertionRule(BaseRule):
    def _call_space_modifier(self, space: SpaceState, selector: tuple[int, int], target: Sequence[Cell]) -> DeltaCells:
        return space.insert(selector[0], deepcopy(target))


class OverwriteRule(BaseRule):
    def _call_space_modifier(self, space: SpaceState, selector: tuple[int, int], target: Sequence[Cell]) -> DeltaCells:
        return space.overwrite(selector[0], deepcopy(target))


class DeletionRule(BaseRule):
    def _call_space_modifier(self, space: SpaceState, selector: tuple[int, int], target: None) -> DeltaCells:
        return space.delete(selector)


class ShiftingRule(BaseRule):
    def _call_space_modifier(self, space: SpaceState, selector: tuple[int, int], target: int) -> DeltaCells:
        return space.shift(selector, k=target)


class ReverseRule(BaseRule):
    def _call_space_modifier(self, space: SpaceState, selector: tuple[int, int], target: None) -> DeltaCells:
        return space.reverse(selector)


if __name__ == "__main__":
    pass
