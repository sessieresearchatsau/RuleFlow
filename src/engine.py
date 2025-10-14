from typing import Any, Union, Callable
from abc import ABC, abstractmethod
from copy import copy

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
    """A single mutable unit within a universe/string (a.k.a. Quanta). However, it is usually treated as immutable
    A cell is analogous to a discrete spacial-unit and quanta is the matter that fills up that unit of space.

    Policies:
    - The Cell class should not contain any fields other than the quanta and the metadata. This is so copies can be made easily.

    Future Considerations:
    - Add additional metadata fields such as tags.
    """
    def __init__(self, quanta: Any):
        self.quanta: Any = quanta

        # metadata (specific to each Cell instance)
        self.created_at: Event | None = None
        self.destroyed_at: Event | None = None

    def __str__(self):
        """String representation of quanta"""
        return str(self.quanta)

    def __eq__(self, other: Cell):
        """Semantic equality (use is for true equality)"""
        return self.quanta == other.quanta


DeltaSet = tuple[tuple[Cell, ...], tuple[Cell, ...]]  # in the format (new_cells, destroyed_cells)
class CellString:
    """Mutable string made up of `Cells` (a.k.a. Universe State). Higher dimensional strings should be considered.

    Policies:
    - All modifier methods (methods that create/destroy cells) should return bool if successful and emit any changes as DeltaSets in the .on_change signal

    TODO:
    - Flesh out helper methods such __contains__() and others that str has.
    - What other modifiers should we have?

    Future Considerations:
    - What about higher dimensions?
    """

    def __init__(self, cells: list[Cell]):
        self.cells: list[Cell] = cells
        self.on_change: Signal = Signal()

        # property for cell concatenation upon printing
        self.string_delineator: str = ''
        # plugins
        self.quanta_str_translator: Callable[[Any], str] = lambda q: str(q)

    def __str__(self):
        return self.string_delineator.join([self.quanta_str_translator(c) for c in self.cells])

    def __eq__(self, other: CellString):
        """Semantic equality (use is for true equality)"""
        for sc, oc in zip(self.cells, other.cells):
            if sc.quanta != oc.quanta:
                return False
        return True

    def new_state(self) -> CellString:
        """Copies the CellString, but does not copy the cells themselves (it retains references to them)."""
        new_string: CellString = object.__new__(self.__class__)  # create new object without init
        for k, v in self.__dict__.items():
            setattr(new_string, k, copy(v))
        return new_string

    # ==== Utilities ====
    def find(self, sub_string: CellString) -> int | None:
        """Find the first occurrence of sub_string in self.cells and return the starting index, or -1 if not found."""
        sub_len: int = len(sub_string.cells)
        for i in range(len(self.cells) - sub_len + 1):
            if all(self.cells[i + j] == sub_string.cells[j] for j in range(sub_len)):
                return i
        return -1

    # ==== Modifiers ====
    def replace(self, old: CellString, new: CellString) -> bool:
        """Replace the first occurrence of old with new. Emits a DeltaSet if successful."""
        idx: int = self.find(old)
        if idx == -1:
            return False
        destroyed = tuple(self.cells[idx:idx + len(old.cells)])
        self.cells[idx:idx + len(old.cells)] = new.cells
        created = tuple(new.cells)
        self.on_change.emit((created, destroyed))
        return True

    def insert(self, new: CellString, at_pos: int) -> bool:
        """Insert new at the specified position. Emits a DeltaSet if successful."""
        if not (0 <= at_pos <= len(self.cells)):
            return False
        self.cells[at_pos:at_pos] = new.cells
        created = tuple(new.cells)
        self.on_change.emit((created, tuple()))
        return True


class Rule(ABC):
    def __init__(self):
        """This should be implemented by subclasses.
        It should take arguments that define the rule behavior. For instance, ``SubstitutionRule(match: string, replace: string)`` should be for a rule that finds a matching substring and replaces it.
        ``InsertionRule(insert: string, at_idx: string)`` should be a rule that inserts a string at the specified index. Whatever the init arguments are, they must be created as fields internally in an elegant format.
        """
        self.on_applied: Signal = Signal()  # emitted when a rule is successfully applied.

    @abstractmethod
    def apply(self, to_string: CellString) -> bool:
        """This should be implemented by subclasses.
        It should apply the rule to the given ``string: CellString``. Upon success, return true."""
        raise NotImplementedError


class RuleSet(ABC):
    def __init__(self):
        """This should be implemented by subclasses.
        This should ideally accept a list of Rules either as objects or as strings that should then be parsed into their corresponding rules. The rules should be stored in array."""
        self.rules: list[Rule] = []
        self.on_rules_applied: Signal = Signal()

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
        self.inert: bool = False  # if true, the new event caused no changes to the system


class Flow:
    """The base class for a rule flow, additional behavior should be implemented by subclassing this class.

    Future Considerations:
    - Add a clone() method?
    """

    def __init__(self, rule_set: RuleSet,
                 initial_state: CellString):
        self.events: list[Event] = [Event(0)]  # time steps
        self.states: list[CellString] = [initial_state]  # remembered states
        self.rule_set: RuleSet = rule_set
        self.pending_deltas: list[DeltaSet] = []

        # make sure the first state is connected to the creation event.
        for cell in initial_state.cells:
            cell.created_at = self.current_event
        # make sure any deltas are detected
        initial_state.on_change.connect(self.on_deltas_detected)

    @property
    def current_state(self) -> CellString:
        return self.states[-1]

    @property
    def current_event(self) -> Event:
        return self.events[-1]

    def on_deltas_detected(self, delta: DeltaSet):
        self.pending_deltas.append(delta)

    def evolve(self) -> None:
        """ Evolve the system by one step.

        This can be reimplemented by subclasses to modify behavior. As it stands, it does the following:
        - create a new current Event
        - create new current state
        - apply ruleset to new current state
        - Update event and state metadata (important for tracking causality)
            - the .apply() function should return the applied rule(s)
            - process the self.pending_deltas (update the cell's created_by and destroyed_by fields)
        """
        self.events.append(Event(self.current_event.step + 1))
        self.states.append(self.current_state.new_state())
        self.current_event.applied_rules = self.rule_set.apply(self.current_state)
        if not self.current_event.applied_rules:  # if no rules were applied
            self.current_event.inert = True
            return
        for delta in self.pending_deltas:
            for new_cells in delta[0]:
                new_cells.created_at = self.current_event
            for destroyed_cells in delta[1]:
                destroyed_cells.destroyed_at = self.current_event
                self.current_event.causally_connected_events.append(destroyed_cells.created_at)
        self.current_event.affected_cells = self.pending_deltas
        self.pending_deltas.clear()

    def evolve_n(self, n_steps: int) -> None:
        """Evolve the system n steps."""
        for _ in range(n_steps):
            self.evolve()

    def to_graphviz(self):
        raise NotImplementedError

    def to_networkx_graph(self):
        raise NotImplementedError

    def __str__(self) -> str:
        return '\n'.join((str(state) for state in self.states))


if __name__ == '__main__':
    pass
