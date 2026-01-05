"""Persistent Vector Implementation (for sparse storage)"""
from pyrsistent import PVector, PVectorEvolver, pvector
from typing import MutableSequence, overload, _T, Iterable, Sequence
from core.engine import Cell


class Vec(MutableSequence):
    __slots__ = ('pvec', 'evolver', 'search_buffer')

    def __init__(self, elems: Sequence[Cell] | Iterable[Cell]):
        self.pvec: PVector[Cell] = pvector(elems)
        self.evolver: PVectorEvolver[Cell] | None = None
        self.search_buffer: bytearray = bytearray(ord(c.quanta) for c in elems)

    # utility functions
    def edit(self):  # we use this rather than .is_dirty() to minimize space use of an evolver object.
        """Enter edit mode."""
        if self.evolver is None:
            self.evolver = self.pvec.evolver()

    def commit(self):
        """Commit changes."""
        if self.evolver is not None:
            self.pvec = self.evolver.persistent()
            self.evolver = None

    def branch(self) -> Vec:
        """Branch the current vector into a new vector"""
        nv: Vec = object.__new__(Vec)
        nv.pvec = self.pvec
        nv.evolver = None
        nv.search_buffer = self.search_buffer
        return nv

    def branch_search_buffer(self, from_pvec: bool = False) -> None:
        """Create new search buffer (useful for multi-ways). If using from_pvec, it will be reconstructed directly from the cells, otherwise just copied."""
        if from_pvec:
            self.search_buffer = bytearray(ord(c.quanta) for c in self.pvec)
        else:
            self.search_buffer = self.search_buffer.copy()

    def __copy__(self):
        return self.branch()

    def __deepcopy__(self, memo):
        return self.branch()

    # ================ Viewers ================
    def __len__(self):
        return len(self.pvec)

    @overload
    def __getitem__(self, index: int) -> Cell: ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[Cell]: ...

    def __getitem__(self, index):
        return self.pvec[index]

    def finditer(self, pattern):
        pass  # use the search_buffer

    # ================ Modifiers ================
    @overload
    def __setitem__(self, index: int, value: Cell) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[Cell]) -> None: ...

    def __setitem__(self, index, value):
        # Ensure we are in edit mode to use the evolver for point updates
        if isinstance(index, int):
            value: Cell
            self.edit()
            self.evolver[index] = value
            self.search_buffer[index] = ord(value.quanta)
            return
        if isinstance(index, slice):
            value: Sequence[Cell]
            start, stop, _ = index.indices(len(self.pvec))
            if len(value) == stop - start:
                self.edit()
                for i, val in enumerate(value):
                    self.evolver[start + i] = val
            else: # Structural Change: Evolver cannot handle length changes
                self.commit()  # flush any existing point-updates to the pvec
                self.pvec = self.pvec[:start] + pvector(value) + self.pvec[stop:]
            self.search_buffer[start:stop] = bytes(ord(c.quanta) for c in value)

    def __delitem__(self, index: int | slice):
        pass

    def append(self, value):
        pass

    def extend(self, values: Iterable[_T]):
        pass

    def insert(self, index, value):
        pass