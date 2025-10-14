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
    """A single mutable unit within a universe/string (a.k.a. Quanta).
    A cell is analogous to a discrete spacial-unit and quanta is the matter that fills up that unit of space."""
    def __init__(self, quanta: Any):
        self.quanta: Any = quanta
        self.created_at: Event | None = None
        self.destroyed_at: Event | None = None
        self.tags: list[str] = []  # optional additional tags can be added for more nuance rules

        # Plugins
        self.quanta_str_translator: Callable[[Any], str] = lambda q: str(q)

    def __str__(self):
        """String representation of quanta"""
        return self.quanta_str_translator(self.quanta)

    def __eq__(self, other: Cell):
        """Semantic equality (use is for true equality)"""
        return self.quanta == other.quanta


DeltaSet = tuple[tuple[Cell, ...], tuple[Cell, ...]]  # in the format (new_cells, destroyed_cells)
class CellString:
    """Mutable string made up of `Cells` (a.k.a. Universe State). Higher dimensional strings should be considered."""

    def __init__(self, cells: list[Cell]):
        self.cells: list[Cell] = cells  # 👉👉👉 TODO what about higher dimensions?
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

    # 👉👉👉 TODO implement modifiers (what are some others I should have?)

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
        raise NotImplementedError

    @abstractmethod
    @property
    def rule(self) -> list[Rule]:
        """This should be implemented by subclasses."""
        raise NotImplementedError

    @abstractmethod
    def apply(self, to_string: CellString) -> list[Rule]:
        """This should be implemented by subclasses.
        This should try to apply the RuleSet to the given ``string: CellString``.
        The rules that have been successfully applied should be returned in a list."""
        raise NotImplementedError


class Event:
    def __init__(self, step: int):
        self.step: int = step  # also known as time

        # optional metadata for each new event (must be managed by Flow.evolve())
        self.applied_rules: list[Rule] = []  # rules applied at this event
        self.affected_cells: list[DeltaSet] = []  # cells affected by this event
        self.causally_connected_events: list[Event] = []  # events whose created cells were destroyed by this event



class FlowABC(ABC):
    pass  # 👉👉👉 TODO define behavior


class Flow(FlowABC):
    """The base class for a rule flow, additional behavior should be implemented by subclassing this class of the FlowABC class."""

    def __init__(self, rule_set: RuleSet,
                 initial_state: CellString):
        self.events: list[Event] = [Event(0)]  # time steps
        self.states: list[CellString] = [initial_state]  # remembered states
        self.rule_set: RuleSet = rule_set
        self.pending_deltas: list[DeltaSet] = []
        initial_state.on_change.connect(self.on_deltas_detected)

    @property
    def current_state(self) -> CellString:
        return self.states[-1]

    def on_deltas_detected(self, delta: DeltaSet):
        self.pending_deltas.append(delta)

    # 👉👉👉 TODO implement these function the generic Flow class (what are some others I should have?)

    def evolve(self) -> None:
        """This should be implemented by subclasses.
        - create a new Event
        - create new current state
        - apply ruleset to current state
        - Add this to event metadata
            - the .apply() function should return the applied rule(s)
            - process the self.pending_deltas (update the cell's created_by and destroyed_by fields)
        """
        pass

    def evolve_n(self, n_steps: int):
        pass

    def rollback(self, n_steps: int = 1):
        """This should be implemented by subclasses.
        Undo the last evolve."""
        pass

    def to_graphviz(self):
        pass

    def to_networkx_graph(self):
        pass

    def __str__(self) -> str:
        return '\n'.join((str(state) for state in self.states))


if __name__ == '__main__':
    pass
