from typing import Any, Callable, Sequence, NamedTuple
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from copy import copy, deepcopy


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


# ==== engine ====


@dataclass
class Cell:
    """A single mutable unit within a universe/string (a.k.a. Quanta). However, it is usually treated as immutable using copy().
    A cell is analogous to a discrete spacial-unit and quanta is the matter that fills up that unit of space.
    It is at this smallest unit of space that we care about causality.

    Policies:
    - The Cell class should not contain any fields other than the quanta and the metadata. This is so copies can be made easily.

    Future Considerations:
    - Add additional metadata/tags fields.
    """
    quanta: Any

    # NOTE: the metadata is the ONLY thing that makes cells differentiable (other than quanta of course)
    # Metadata regarding the creation and destruction of the cell... stored as indices to the events array.
    created_at: int | None = None
    destroyed_at: int | None = None

    def __str__(self):
        """String representation of quanta"""
        return str(self.quanta)

    def __eq__(self, other: Cell):
        """Semantic equality (use is for true equality)"""
        return self.quanta == other.quanta

    def __copy__(self) -> Cell:
        """Copies the Cell (self), but does not copy the quanta itself (it retains the reference to it). It is a shallow copy."""
        new_cell = object.__new__(self.__class__)
        new_cell.quanta = self.quanta
        new_cell.created_at = self.created_at
        new_cell.destroyed_at = self.destroyed_at
        return new_cell

    def __deepcopy__(self, memo) -> Cell:  # force it to use __copy__
        return self.__copy__()


class SpaceState(ABC):
    """Mutable container made up of `Cells` (a.k.a. Universe State of Space).

    Policies:
    - Should NOT be used as a simple container for Cells (in a replacement rule for instance), it should only be used for actual space states in events/time. Any other container should be in the form Sequence[Cell].
    - All modifier methods must make sure to create new cells or cell copies if causality is to be tracked properly using the DeltaSets.
    - All modifier methods (that create/destroy cells) should return DeltaCellSet containing the destroyed and created cells. The destroyed cells should be cloned/deep-copied before passing to and returning DeltaCellSet... this is so that multiple SpaceState(s) that share the same cells can have different cells destroyed and still track cell causality for each respective universe without overriding the destroyed_at: Event field of the same cell multiple times.
    - All official SpaceStates must be created in this engine.py file. If one wants to create a 4D SpaceState, for instance, they must inherit from this, implement the methods, etc.
    - All SpaceStates that inherit from this class must implement the modifier methods. If `find`, `len`, etc. are not sufficient helpers, additional helpers may be created here (if they are general enough), or in the subclasses ideally.
    """

    def __init__(self) -> None:
        if not hasattr(self, 'cells'):  # this insures that cells is properly created in inherited classes
            raise NotImplementedError('The self.cells field must be set in the constructor of classes inheriting from BaseSpaceState BEFORE the BaseSpaceState constructor is called.')

        # Plugins
        self.quanta_str_translator: Callable[[Any], str] = str

    @abstractmethod
    def __str__(self) -> str:
        """Returns a string representation of the state space. May use the quanta_str_translator() plugin function is necessary."""

    def __repr__(self):
        """Simply calls the self.__str__() implementation so that if self is in another container, it will be used by python when printing the container. This can be overridden to change behavior."""
        return self.__str__()

    @abstractmethod
    def __eq__(self, other: SpaceState) -> bool:
        """Semantic equality (use `is` for true equality)"""

    @abstractmethod
    def __len__(self) -> int | Any:
        """Should return the *size* of a container... whatever that may mean for N^1 or N^2 or N^3 spaces."""

    @abstractmethod
    def __copy__(self) -> SpaceState | Any:
        """Copies the SpaceState (self), but does not copy the cells (internal fields) themselves
        (it only retains references to them). It is a shallow copy.
        """

    @abstractmethod
    def __getitem__(self, item: int | slice) -> Cell | Sequence[Cell] | Any:
        """Enables getting subspaces with slicing: space[0][1] of an N^2 space for instance."""

    @abstractmethod
    def get_all_cells(self) -> Sequence[Cell]:
        """Returns all the cells that live in the SpaceState... regardless of the spaces dimensions.
        This is useful for modifying all the cells in the SpaceState."""

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


class SpaceState1D(SpaceState):
    """A SpaceState for a single dimensions (string) of space units (cells)."""

    def __init__(self, cells: Sequence[Cell] | Any) -> None:
        self.cells: list[Cell] = cells
        super().__init__()

        self.string_delimiter: str = ''  # just empty by default.

    def __str__(self) -> str:
        return self.string_delimiter.join([self.quanta_str_translator(c) for c in self.cells])

    def __eq__(self, other: SpaceState1D) -> bool:
        for sc, oc in zip(self.cells, other.cells):
            if sc.quanta != oc.quanta:
                return False
        return True

    def __len__(self) -> int:
        return len(self.cells)

    def __copy__(self) -> SpaceState1D:
        new_space: SpaceState1D = object.__new__(self.__class__)  # create new object without using init
        for k, v in self.__dict__.items():  # copy all fields only once
            setattr(new_space, k, copy(v) if isinstance(v, list) else v)
        return new_space

    def __getitem__(self, item: int | slice) -> Cell | Sequence[Cell]:
        return self.cells[item]

    def get_all_cells(self) -> Sequence[Cell]:
        return self.cells

    # Great debugging example here:
    # 1. breakpoint in the evolve_n() function and look for the problematic step.
    # 2. Step through the code from there to finally see that this find function is not working properly.
    # 3. Fix this find function by indenting the `instances` decrementer.
    # def find(self, subspace: Sequence[Cell], instances: int = 1) -> list[int]:
    #     subspace_len: int = len(subspace)
    #     matches: list[int] = []
    #     for i in range(len(self.cells) - subspace_len + 1):  # we use left-to-right search
    #         if instances == 0:
    #             break
    #         if all(self.cells[i + j] == subspace[j] for j in range(subspace_len)):
    #             matches.append(i)
    #         if instances != -1:
    #             instances -= 1
    #     return matches

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

    # ==== Custom Modifiers ====
    def replace_at(self, old: Sequence[Cell], new: Sequence[Cell], at_pos: int) -> DeltaCells:
        destroyed: tuple[Cell, ...] = tuple(self.cells[at_pos:at_pos + len(old)])
        self.cells[at_pos:at_pos + len(old)] = new
        return DeltaCells(deepcopy(destroyed), new)

    def replace(self, old: Sequence[Cell], new: Sequence[Cell]) -> DeltaCells:
        pos: list[int] = self.find(old, instances=1)
        if not pos:
            return DeltaCells((), ())
        return self.replace_at(old, new, pos[0])

    def overwrite_at(self, at_pos: int, new: Sequence[Cell]) -> DeltaCells:
        destroyed: tuple[Cell, ...] = tuple(self.cells[at_pos:at_pos + len(new)])
        self.cells[at_pos:at_pos + len(new)] = new
        return DeltaCells(deepcopy(destroyed), new)

    def insert(self, new: Sequence[Cell], at_pos: int) -> DeltaCells:
        if not (0 <= at_pos <= len(self)):
            return DeltaCells((), ())
        self.cells[at_pos:at_pos] = new
        return DeltaCells((), new)

    def append(self, new: Sequence[Cell]) -> DeltaCells:
        self.cells.extend(new)
        return DeltaCells((), new)


class SpaceState2D(SpaceState):
    """It is here that we implement the 2D SpaceState."""
    pass


class Rule(ABC):
    def __init__(self):
        """Should take arguments that define the rule behavior. For instance, ``SubstitutionRule(match: string, replace: string)`` should be for a rule that finds a matching substring and replaces it.
        ``InsertionRule(insert: string, at_idx: string)`` should be a rule that inserts a string at the specified index. Whatever the init arguments are, they must be created as fields internally in an elegant format.

        The Rule should be responsible for duplicating (or not) the SpaceState(s) when applying itself. This way,
        multi-way systems are supported because the Rule can apply multiple different modifications to multiple
        different SpaceStates if necessary.

        Note that all the code is assuming that multi-way systems take place for multiple modifications. However, if we want to modify a SpaceState, without creating branches, we must do that in the Rule itself (i.e. having entire "rulesets" within rules).

        Future Considerations:
        - We may want to track more granular information regarding input spaces being associated with the created space so that exact creations and failures could be tracked... we could use a RuleResult dataclass.
        """
        # Flags to modify how RuleSet applies rules. Additional flags for more complex behavior can be added if RuleSet is subclassed and modified for such behavior.
        self.disabled = False  # in case we want to temporarily disable the rule while the program is running.
        self.break_RuleSet_application_on_success: bool = True  # this tells RuleSet whether to keep applying rules or not if this rule was successfully applied.

    @abstractmethod
    def apply(self, to_spaces: Sequence[SpaceState]) -> Sequence[DeltaSpace]:
        """Applies the rule to the given ``SpaceState(s)``. Modified SpaceStates are returned.
        Important for implementation: *new/copied* SpaceState(s) must be created, modified, and returned.

        Rule is responsible for taking all current states to provide maximum flexibility (so different rules can have different behavior: sessies + messies) (TRUST ME!!! I doubted my past self on this and then wasted a bunch of time... just keep it as-is you crazy future/modern self!)
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
        self.register_unmodified_delta_spaces: bool = False

    def apply(self, to_spaces: Sequence[SpaceState]) -> list[DeltaSpaces]:
        """Applies the Rules to the given spaces, and returns a sequence of the DeltaSpaceSet."""
        applied_rules: list[DeltaSpaces] = []
        for rule in self.rules:
            if rule.disabled:
                continue
            space_deltas: DeltaSpaces = DeltaSpaces(rule.apply(to_spaces), rule)
            if space_deltas:
                applied_rules.append(space_deltas)
                if rule.break_RuleSet_application_on_success:
                    break
            else:
                if self.register_unmodified_delta_spaces:
                    applied_rules.append(space_deltas)
        return applied_rules

    # ==== optional unimplemented methods ====
    def match(self, *args, **kwargs) -> Sequence[Rule]:
        """Should return information about how this rule has been matched: could be a simple bool or a position."""
        raise NotImplementedError


class DeltaCells(NamedTuple):  # the cells that were created and destroyed by some SpaceState.modifier() method.
    destroyed_cells: Sequence[Cell]
    new_cells: Sequence[Cell]

    def __bool__(self) -> bool:
        return bool(self.destroyed_cells) or bool(self.new_cells)  # if any changes occurred, return true.


class DeltaSpace(NamedTuple):  # returned by Rule.apply() in a Sequence[DeltaSpace]
    """Single application of a rule within Rule.apply()."""
    input_space: SpaceState  # we always have this filled so that we know what spaces had what changes (if any) made
    created_space: SpaceState  # will be empty if no changes happened.
    cell_deltas: DeltaCells


class DeltaSpaces(NamedTuple):  # returned by RuleSet.apply() in a Sequence[AppliedRule]
    """All delta spaces that happened under a given rule."""
    space_deltas: Sequence[DeltaSpace]
    rule: Rule | None

    def __bool__(self) -> bool:
        return any((bool(d.cell_deltas) for d in self.space_deltas))  # if any changes were recorded.


@dataclass
class Event:
    # TODO: what about weighted edges?
    time: int  # also known as time
    space_deltas: list[DeltaSpaces]  # all space deltas (organized by the rules they were applied under)

    # metadata
    inert: bool = False  # if true, the new event caused no changes to the system

    @property  # maybe cache this?
    def causally_connected_events(self) -> list[int]:
        """Returns events (stored as indices) whose created cells were destroyed by this event"""
        out: list[int] = []
        for delta in self.affected_cells:
            for cell in delta.destroyed_cells:
                out.append(cell.created_at)
        return out

    @property  # maybe cache this?
    def affected_cells(self) -> list[DeltaCells]:
        """Returns all cell deltas"""
        out: list[DeltaCells] = []
        for r in self.space_deltas:
            for space_delta in r.space_deltas:
                if space_delta.cell_deltas:
                    out.append(space_delta.cell_deltas)
        return out

    @property  # maybe cache this?
    def spaces(self) -> list[SpaceState]:
        """Returns all newly created spaces"""
        out: list[SpaceState] = []
        for r in self.space_deltas:
            for space_delta in r.space_deltas:
                if space_delta.created_space:
                    out.append(space_delta.created_space)
        return out

    @property
    def unmodified_spaces(self) -> list[SpaceState]:
        """Returns all unmodified spaces"""
        out: list[SpaceState] = []
        for r in self.space_deltas:
            for space_delta in r.space_deltas:
                if not space_delta.created_space:
                    out.append(space_delta.input_space)
        return out


class Flow:
    """The base class for a rule flow, additional behavior should be implemented by subclassing this class.

    TODO:
    - Should we make it possible to have a sliding window over the events to save memory?
    - Should we re-implement signals (right now they are not being used)... they could be used as on_new_event to update a dynamic graph visual.
    """

    def __init__(self, rule_set: RuleSet,
                 initial_state: SpaceState | Sequence[SpaceState]):
        self.events: list[Event] = [
            Event(0, [DeltaSpaces((DeltaSpace(initial_state, initial_state, DeltaCells((), ())),), None)])
        ]
        self.rule_set: RuleSet = rule_set
        self.use_unmodified_spaces_in_next_event = False

        # make sure the initial cells in the space is connected to the creation event.
        for cell in initial_state.get_all_cells():
            cell.created_at = 0

    @property
    def current_event(self) -> Event:
        return self.events[-1]

    @property
    def current_event_idx(self) -> int:
        return len(self.events) - 1

    def evolve(self) -> None:
        """ Evolve the system by one step.

        This can be reimplemented by subclasses to modify behavior. As it stands, it does the following:
        - apply the rules to the current space states using RuleSet.apply()
        - if a rule was successfully applied, create a new event and increment the time ``step``
        - Update event and cell metadata (important for tracking causality)
            - set the applied rules (the applied rules are associated with the space states they modified)
            - extract all the modified space states from the applied rules and add them to the space states of the Event.
            - process the self.pending_deltas (update the cell's created_by and destroyed_by fields)
        """
        applied_rules: list[DeltaSpaces] = self.rule_set.apply(self.current_event.spaces + (self.current_event.unmodified_spaces if self.use_unmodified_spaces_in_next_event else []))
        if not any(applied_rules):  # if no rules made any modifications to the spaces
            self.current_event.inert = True
            return

        # Create a new event and process it
        self.events.append(
            Event(self.current_event.time + 1, space_deltas=applied_rules)  # create a new event
        )
        current_event_idx: int = self.current_event_idx
        for ar in applied_rules:
            for sd in ar.space_deltas:
                for cell in sd.cell_deltas.new_cells:
                    cell.created_at = current_event_idx
                for cell in sd.cell_deltas.destroyed_cells:
                    cell.destroyed_at = current_event_idx

    def evolve_n(self, n_steps: int) -> None:
        """Evolve the system n steps."""
        for _ in range(n_steps):
            self.evolve()

    def evolve_until_inert(self, max_steps: int = 1000) -> None:
        """Evolve the system until the events become inert."""
        while not self.current_event.inert and max_steps:
            self.evolve()
            max_steps -= 1

    def __str__(self) -> str:  # TODO: move to Visualizer
        return '\n'.join((f'{event.time} ' + str(event.spaces) + f' {event.causally_connected_events}' for event in self.events))


class Visualizer:
    """Should handle Printing and Visualizing Flows, setting their defaults, etc. This is not to be confused with the Graph Visualizer. This only handles the Flow and internal object display, not graph construction."""
    def __init__(self, flow: Flow):
        pass


if __name__ == '__main__':
    pass
