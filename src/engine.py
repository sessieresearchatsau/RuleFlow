from typing import Any, Union, Callable, Sequence
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
    """A single mutable unit within a universe/string (a.k.a. Quanta). However, it is usually treated as immutable using copy().
    A cell is analogous to a discrete spacial-unit and quanta is the matter that fills up that unit of space.
    It is at this smallest unit of space that we care about causality.

    Policies:
    - The Cell class should not contain any fields other than the quanta and the metadata. This is so copies can be made easily.

    Future Considerations:
    - Add additional metadata fields such as tags.
    """
    def __init__(self, quanta: Any):
        self.quanta: Any = quanta

        # metadata (specific to each Cell instance) (NOTE: this should NOT be copied in copy operations)
        self.created_at: Event | None = None
        self.destroyed_at: Event | None = None

    def __str__(self):
        """String representation of quanta"""
        return str(self.quanta)

    def __eq__(self, other: Cell):
        """Semantic equality (use is for true equality)"""
        return self.quanta == other.quanta

    def __copy__(self) -> Cell:
        """Copies the Cell (self), but does not copy the quanta itself (it retains the reference to it). It is a shallow copy."""
        return Cell(self.quanta)  # for now this is all that is necessary for an efficient shallow clone... metadata is not copied.

    def __deepcopy__(self, memo) -> Cell:  # force it to use __copy__ in case the rule programmer is not competent
        return self.__copy__()


# Delta type definition for cells in the format (new_cells, destroyed_cells)
DeltaSet = tuple[Sequence[Cell], Sequence[Cell]]


class StateSpace(ABC):
    """Mutable container made up of `Cells` (a.k.a. Universe State of Space).

    Policies:
    - Should NOT be used as a simple container for Cells (in a replacement rule for instance), it should only be used for actual space states in events/time. Any other container should be in the form Sequence[Cell].
    - All modifier methods must make sure to create new cells or cell copies if causality is to be tracked properly using the DeltaSets.
    - All modifier methods (methods that create/destroy cells) should return bool if successful and emit any changes as DeltaSets in the .on_change signal
    - All official StateSpaces must be created in this engine.py file. If one wants to create a 4D StateSpace, for instance, they must inherit from this, implement the methods, etc.
    - All StateSpaces that inherit from this class must implement the modifier methods. If `find`, `len`, etc. are not sufficient helpers, additional helpers may be created here (if they are general enough), or in the subclasses ideally.
    """

    def __init__(self) -> None:
        if not hasattr(self, 'cells'):  # this insures that cells is properly created in inherited classes
            raise NotImplementedError('The self.cells field must be set in the constructor of classes inheriting from BaseStateSpace BEFORE the BaseStateSpace constructor is called.')

        # Signals (gets propagated throughout the lifetime of the class and all copies)
        self.on_change: Signal = Signal()

        # Plugins
        self.quanta_str_translator: Callable[[Any], str] = lambda q: str(q)

    @abstractmethod
    def __str__(self) -> str:
        """Returns a string representation of the state space. May use the quanta_str_translator() plugin function is necessary."""

    def __repr__(self):
        """Simply calls the self.__str__() implementation so that if self is in another container, it will be used by python when printing the container. This can be overridden to change behavior."""
        return self.__str__()

    @abstractmethod
    def __eq__(self, other: StateSpace) -> bool:
        """Semantic equality (use `is` for true equality)"""

    @abstractmethod
    def __len__(self) -> int | Any:
        """Should return the *size* of a container... whatever that may mean for N^1 or N^2 or N^3 spaces."""

    @abstractmethod
    def __copy__(self) -> StateSpace | Any:
        """Copies the StateSpace (self), but does not copy the cells (internal fields) themselves
        (it only retains references to them). It is a shallow copy.
        """
        """
        Implementation example:
        ```
        new_space = object.__new__(self.__class__)  # create new object without using init
        for k, v in self.__dict__.items():  # copy all fields only once
            setattr(new_space, k, copy(v) if isinstance(v, list) else v)  # only if the field itself is mutable and must be copied (but not deep copied)
        return new_space
        ```
        """

    @abstractmethod
    def __getitem__(self, item: int | slice) -> Cell | Sequence[Cell] | Any:
        """Enables getting subspaces with slicing: space[0][1] of an N^2 space for instance."""

    @abstractmethod
    def get_all_cells(self) -> Sequence[Cell]:
        """Returns all the cells that live in the StateSpace... regardless of the spaces dimensions.
        This is useful for modifying all the cells in the StateSpace."""

    @abstractmethod
    def find(self, subspace: Cell | Sequence[Cell] | Any, instances: int = 1) -> Sequence[int | Any]:
        """Find the `instances` number of occurrences of subspaces in the space (in any order desired) and return a
        sequence of index positions or more complex positions. An empty set is returned if no matches are found.
        If `instances` is -1, all subspaces should be matched.
        Note that `instances` are useful for creating multi-way systems for example."""

    # ==== optional unimplemented modifiers ====
    def replace_at(self, old: Sequence[Cell] | Any, new: Sequence[Cell] | Any, at_pos: int | Any) -> bool:
        """Replace old with new at a position. Emits a DeltaSet and returns True if successful."""
        raise NotImplementedError

    def replace(self, old: Sequence[Cell] | Any, new: Sequence[Cell] | Any) -> bool:
        """Replace the first occurrence of old with new. Emits a DeltaSet and returns True if successful."""
        raise NotImplementedError

    def overwrite_at(self, at_pos: int | Any, new: Sequence[Cell] | Any) -> bool:
        """Overwrite the subspace at `at_pos`. Emits a DeltaSet and returns True if successful."""
        raise NotImplementedError

    def insert(self, new: Sequence[Cell] | Any, at_pos: int | Any) -> bool:
        """Insert new at the specified position. Emits a DeltaSet and returns True if successful."""
        raise NotImplementedError

    def append(self, new: Sequence[Cell] | Any) -> bool:
        """Append the last occurrence of self.cells[-1]. Returns True if successful."""
        raise NotImplementedError


class StateSpace1D(StateSpace):
    """A StateSpace for a single dimensions (string) of space units (cells)."""

    def __init__(self, cells: list[Cell] | Sequence[Cell] | Any) -> None:
        self.cells: list[Cell] = cells
        super().__init__()

        self.string_delimiter: str = ''  # just empty by default.

    def __str__(self) -> str:
        return self.string_delimiter.join([self.quanta_str_translator(c) for c in self.cells])

    def __eq__(self, other: StateSpace1D) -> bool:
        for sc, oc in zip(self.cells, other.cells):
            if sc.quanta != oc.quanta:
                return False
        return True

    def __len__(self) -> int:
        return len(self.cells)

    def __copy__(self) -> StateSpace1D:
        new_space: StateSpace1D = object.__new__(self.__class__)  # create new object without using init
        for k, v in self.__dict__.items():  # copy all fields only once
            setattr(new_space, k, copy(v) if isinstance(v, list) else v)
        return new_space

    def __getitem__(self, item: int | slice) -> Cell | Sequence[Cell]:
        return self.cells[item]

    def get_all_cells(self) -> Sequence[Cell]:
        return self.cells

    def find(self, subspace: Sequence[Cell], instances: int = 1) -> list[int]:
        subspace_len: int = len(subspace)
        matches: list[int] = []
        for i in range(len(self.cells) - subspace_len + 1):  # we use left-to-right search
            if instances == 0:
                break
            if all(self.cells[i + j] == subspace[j] for j in range(subspace_len)):
                matches.append(i)
            if instances != -1:
                instances -= 1
        return matches

    # ==== Modifiers ====
    def replace_at(self, old: Sequence[Cell], new: Sequence[Cell], at_pos: int) -> bool:
        destroyed: tuple[Cell, ...] = tuple(self.cells[at_pos:at_pos+len(old)])
        self.cells[at_pos:at_pos+len(old)] = new
        self.on_change.emit((new, destroyed))
        return True

    def replace(self, old: Sequence[Cell], new: Sequence[Cell]) -> bool:
        pos: list[int] = self.find(old, instances=1)
        if not pos:
            return False
        return self.replace_at(old, new, pos[0])

    def overwrite_at(self, at_pos: int, new: Sequence[Cell]) -> bool:
        destroyed: tuple[Cell, ...] = tuple(self.cells[at_pos:at_pos + len(new)])
        self.cells[at_pos:at_pos + len(new)] = new
        self.on_change.emit((new, destroyed))
        return True

    def insert(self, new: Sequence[Cell], at_pos: int) -> bool:
        if not (0 <= at_pos <= len(self)):
            return False
        self.cells[at_pos:at_pos] = new
        self.on_change.emit((new, tuple()))
        return True

    def append(self, new: Sequence[Cell]) -> bool:
        self.cells.extend(new)
        self.on_change.emit((new, tuple()))
        return True


class StateSpace2D(StateSpace):
    """It is here that we implement the 2D StateSpace."""
    pass


class Rule(ABC):
    def __init__(self):
        """Should take arguments that define the rule behavior. For instance, ``SubstitutionRule(match: string, replace: string)`` should be for a rule that finds a matching substring and replaces it.
        ``InsertionRule(insert: string, at_idx: string)`` should be a rule that inserts a string at the specified index. Whatever the init arguments are, they must be created as fields internally in an elegant format.

        The Rule should be responsible for duplicating (or not) the StateSpace(s) when applying itself. This way,
        multi-way systems are supported because the Rule can apply multiple different modifications to multiple
        different StateSpaces if necessary.

        Note that all the code is assuming that multi-way systems take place for multiple modifications. However, if we want to modify a StateSpace, without creating branches, we must do that in the Rule itself (i.e. having entire "rulesets" within rules).
        """
        # Metadata to modify how RuleSet applies rules. Additional flags for more complex behavior can be added if RuleSet is subclassed and modified for such behavior.
        self.disabled = False  # in case we want to temporarily disable the rule while the program is running.
        self.break_RuleSet_application_on_success: bool = True  # this tells RuleSet whether to keep applying rules or not if this rule was successfully applied.

    @abstractmethod
    def apply(self, to_space: Sequence[StateSpace]) -> Sequence[StateSpace]:
        """Applies the rule to the given ``StateSpace(s)``. Modified StateSpaces are returned.
        Important for implementation: *new/copied* StateSpaces must be created, modified, and returned.
        """

    # ==== optional unimplemented methods ====
    def match(self, *args, **kwargs) -> bool | int | Any:
        """Should return information about how this rule has been matched: could be a simple bool or a position."""
        raise NotImplementedError


class RuleSet:
    """This contains the Rules that can be applied. Additional, more complex, behavior can be implemented by subclassing it.

    Note that all the code is engineered around assuming multi-way systems for more than one rule being applied.
    """

    def __init__(self, rules: list[Rule]):
        """This should be implemented by subclasses.
        This should ideally accept a list of Rules either as objects or as strings that should then be parsed into their corresponding rules. The rules should be stored in array."""
        self.rules: list[Rule] = rules

    def apply(self, to_space: Sequence[StateSpace]) -> list[tuple[Rule, Sequence[StateSpace]]]:
        """The rules that have been successfully applied along with their associated newly created/altered StateSpaces
        are returned in pairs."""
        applied_rules: list[tuple[Rule, Sequence[StateSpace]]] = []
        for rule in self.rules:
            if rule.disabled:
                continue
            created_spaces: Sequence[StateSpace] = rule.apply(to_space)
            if created_spaces:
                applied_rules.append((rule, created_spaces))
                if rule.break_RuleSet_application_on_success:
                    break
        return applied_rules

    # ==== optional unimplemented methods ====
    def match(self, *args, **kwargs) -> Sequence[Rule]:
        """Should return information about how this rule has been matched: could be a simple bool or a position."""
        raise NotImplementedError


class Event:
    def __init__(self, step: int):
        self.step: int = step  # also known as time
        self.statespace: list[StateSpace] = []  # these are all the StateSpaces that are a result of a successfully applied rule. Usually, there is only one StateSpace that lives here, but in multi-way systems, multiple StateSpaces live here.

        # optional metadata for each new event (must be managed by Flow.evolve())
        self.applied_rules: list[tuple[Rule, Sequence[StateSpace]]] = []  # rules along with the associated StateSpace(s) they created that were applied at this event
        self.affected_cells: list[DeltaSet] = []  # cells affected by this event
        self.causally_connected_events: list[Event] = []  # events whose created cells were destroyed by this event
        self.inert: bool = False  # if true, the new event caused no changes to the system


class Flow:
    """The base class for a rule flow, additional behavior should be implemented by subclassing this class."""

    def __init__(self, rule_set: RuleSet,
                 initial_state: StateSpace | Sequence[StateSpace]):
        self.events: list[Event] = [
            Event(0)
        ]
        self.rule_set: RuleSet = rule_set
        self.pending_deltas_buffer: list[DeltaSet] = []

        # make sure the initial space is connected to the creation event.
        self.current_event.statespace.extend(initial_state if isinstance(initial_state, Sequence) else (initial_state,))

        # make sure the initial cells in the space is connected to the creation event.
        for cell in initial_state.get_all_cells():
            cell.created_at = self.current_event

        # make sure all deltas are detected
        initial_state.on_change.connect(self.on_deltas_detected)

    @property
    def current_event(self) -> Event:
        return self.events[-1]

    def on_deltas_detected(self, delta: DeltaSet):
        self.pending_deltas_buffer.append(delta)

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
        applied_rules = self.rule_set.apply(self.current_event.statespace)
        if not applied_rules:  # if no rules were applied
            self.current_event.inert = True
            return

        # Create a new event and process it
        self.events.append(
            Event(self.current_event.step + 1)  # create a new event
        )
        self.current_event.applied_rules = applied_rules
        for rule in applied_rules:  # process all StateSpaces that Rule created
            self.current_event.statespace.extend(rule[1])
        for delta in self.pending_deltas_buffer:
            for new_cell in delta[0]:
                new_cell.created_at = self.current_event
            for destroyed_cell in delta[1]:
                destroyed_cell.destroyed_at = self.current_event
                self.current_event.causally_connected_events.append(destroyed_cell.created_at)
        self.current_event.affected_cells = self.pending_deltas_buffer
        self.pending_deltas_buffer.clear()

    def evolve_n(self, n_steps: int) -> None:
        """Evolve the system n steps."""
        for _ in range(n_steps):
            self.evolve()

    def evolve_until_inert(self, limit_steps: int = 100000) -> None:
        """Evolve the system until the events become inert."""
        while not self.current_event.inert and limit_steps:
            self.evolve()
            limit_steps -= 1

    def to_graphviz(self):
        raise NotImplementedError

    def to_networkx_graph(self):
        raise NotImplementedError

    def __str__(self) -> str:
        return '\n'.join((str(event.statespace) for event in self.events))


if __name__ == '__main__':
    pass
