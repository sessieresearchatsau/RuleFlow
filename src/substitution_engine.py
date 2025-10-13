from typing import Any, Union, Callable
from abc import ABC, abstractmethod

# helper
class Signal:
    """Implements a QT-like signal system using traditional callbacks."""
    __slots__ = 'callables', 'callables_count'
    def __init__(self) -> None:
        self.callables: list[Callable] = []
        self.callables_count: int = 0

    def emit(self, *args, **kwargs) -> None:
        for c in self.callables: c(*args, **kwargs)

    def connect(self, func: Callable) -> None:
        if func in self.callables: return
        self.callables.append(func)
        self.callables_count = len(self.callables)

    def disconnect(self, func: Callable) -> None:
        self.callables.remove(func)
        self.callables_count = len(self.callables)



class Cell:
    """A single mutable unit within a universe (a.k.a. Quanta)."""
    def __init__(self, quanta: Any):
        self.quanta: Any = quanta
        self.created_by: Event | None = None
        self.destroyed_by: Event | None = None

        # Plugins
        self.quanta_str_translator: Callable[[Any], str] = lambda q: str(q)

    def __str__(self):
        return self.quanta_str_translator(self.quanta)

    def __eq__(self, other: Cell | Any):
        return self.quanta == (other.quanta if isinstance(other, Cell) else other)


DeltaSet = tuple[tuple[Cell, ...], tuple[Cell, ...]]  # in the format (new_cells, destroyed_cells)
class CellString:
    """Mutable string made up of `Cells` (a.k.a. Universe State)."""

    def __init__(self, cells: list[Cell]):
        self.cells: list[Cell] = cells
        self.on_change: Signal = Signal()

    def __str__(self):
        return ''.join([str(c) for c in self.cells])

    def find(self, sub_string: CellString):
        pass

    # ==== Modifiers ==== (all modifiers should return bool if successful and emit any changes as DeltaSets in the .on_change signal)
    def replace(self, old: CellString, new: CellString) -> bool:
        pass

    def insert(self, new: CellString, at_pos: int) -> bool:
        pass

    def __eq__(self, other: CellString):
        pass


class Rule(ABC):
    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any):
        """This should be implemented by subclasses.
        It should take arguments that define the rule behavior. For instance, ``SubstitutionRule(match: string, replace: string)`` should be for a rule that finds a matching substring and replaces it.
        ``InsertionRule(insert: string, at_idx: string)`` should be a rule that inserts a string at the specified index. Whatever the init arguments are, they must be created as fields internally in an elegant format."""
        raise NotImplementedError

    @abstractmethod
    def apply(self, to_string: CellString) -> bool:
        """This should be implemented by subclasses.
        It should apply the rule to the given ``string: CellString``. Upon success, return true."""
        raise NotImplementedError


class RuleSet(ABC):
    @abstractmethod
    def __init__(self, *args: Any, **kwargs: Any):
        """This should be implemented by subclasses.
        This should ideally accept a list of Rules either as objects or as strings that should then be parsed into their corresponding rules. The rules should be stored in array."""
        self.rules: list[Rule]
        raise NotImplementedError

    @abstractmethod
    def apply(self, to_string: CellString) -> list[Rule]:
        """This should be implemented by subclasses.
        This should try to apply the RuleSet to the given ``string: CellString``.
        The rules that have been successfully applied should be returned in a list."""
        raise NotImplementedError


class Event:
    def __init__(self, step: int, applied_rules: list[Rule]):
        self.step: int  # also known as time
        self.applied_rules: list[Rule]



class SS(ABC):
    """The abstract substitution engine that operates on string of quanta using rulesets."""

    def __init__(self, rule_set: RuleSet,
                 initial_state: CellString):
        self.rule_set: RuleSet = rule_set
        self.states: list[CellString] = [initial_state]
        self.events: list[Event] = [Event(step=0, applied_rules=[])]  # time states
        self.pending_deltas: list[DeltaSet] = []
        initial_state.on_change.connect(self.on_deltas_detected)

    @property
    def current_state(self) -> CellString:
        return self.states[-1]

    @abstractmethod
    def evolve(self):
        """This should be implemented by subclasses.
        - create a new Event
        - duplicate current state
        - apply ruleset to state
        - the .apply() function should return the applied rule(s) which should be added to the new event
        - process the pending deltas (update the cells created_by and destroyed_by fields)
        """
        pass

    def rollback(self):
        """This should be implemented by subclasses.
        Undo the last evolve"""
        pass

    def on_deltas_detected(self, delta: DeltaSet):
        self.pending_deltas.append(delta)

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass



# ================================ Substitution System Implementation ================================
class SSS(SS):  # this should implement the features specific to SSS
    def __init__(self, rule_set: list[Rule | str],
                 initial_state: CellString | str):
        pass

    def evolve(self):
        # create Event objects
        pass


if __name__ == '__main__':
    pass
    # sss = SSS(["ABA->AAB", "A->ABA"], "AB", 5, RulePlacement='Left')
    # sss.worldGen()
    # sss.worldGenNested()
    # sss.generate_causal_diagram()

    # print(SSS(["ABA->AAB", "A->ABA"], "AB", 10).ruleSet)
    # print(SSS(["ABA->AAB", "A->ABA"], "AB", 10).ruleSet['A'])
    # SSS(["ABA->AAB", "A->ABA", "BB->C"], "AB", 10).worldGen()
    # SSS(["BB->C", "ABA->AAB","A->ABA"], "AB", 10, RulePlacement='Left').worldGenNested()
