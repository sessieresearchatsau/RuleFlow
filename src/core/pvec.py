"""Persistent Vector Implementation (for sparse storage)"""
from pyrsistent import PVector, pvector
from pyrsistent.typing import PVectorEvolver
from typing import MutableSequence, overload, Sequence
from core.engine import Cell


class PVec(MutableSequence):
    __slots__ = ('pvec', 'evolver', 'search_buffer')

    def __init__(self, elems: Sequence[Cell]):
        self.pvec: PVector[Cell] = pvector(elems)
        self.evolver: PVectorEvolver[Cell] | None = None
        self.search_buffer: bytearray = bytearray((ord(c.quanta) for c in elems))

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

    def branch(self) -> PVec:
        """Branch the current vector into a new vector"""
        self.commit()  # flush any changes
        nv: PVec = object.__new__(PVec)
        nv.pvec = self.pvec
        nv.evolver = None
        nv.search_buffer = self.search_buffer  # note: becomes out-of-date on self after branch (use branch_search_buffer(rfp=True) to reconstruct clean buffer for self)
        return nv

    def branch_search_buffer(self, reconstruct_from_pvec: bool = False) -> None:
        """Create new search buffer (useful for multi-ways). If using from_pvec, it will be reconstructed directly from the cells, otherwise just copied."""
        if reconstruct_from_pvec:
            self.search_buffer = bytearray((ord(c.quanta) for c in self.pvec))  # O(n log_32 n)
        else:
            self.search_buffer = self.search_buffer.copy()  # O(n)

    def __copy__(self):
        return self.branch()

    def __deepcopy__(self, memo):
        return self.branch()

    def __str__(self):
        return 'Vec' + str(self.pvec)[7:]

    def __repr__(self):
        return str(self)

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
    def __setitem__(self, index: slice, value: Sequence[Cell]) -> None: ...

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value: Sequence[Cell]
            start, stop, _ = index.indices(len(self.pvec))
            if len(value) == stop - start:  # if we can do point updates
                self.edit()
                for i, val in enumerate(value):
                    self.evolver[start + i] = val
            else: # Structural Change: because the evolver cannot handle length changes (deletions or insertions)
                self.commit()  # flush any existing point-updates to the pvec
                self.pvec = self.pvec[:start] + pvector(value) + self.pvec[stop:]  # does not use the Evolver object as this creates a new node.
            self.search_buffer[start:stop] = bytes(ord(c.quanta) for c in value)
        elif isinstance(index, int):
            value: Cell
            self.edit()
            self.evolver[index] = value
            self.search_buffer[index] = ord(value.quanta)

    def __delitem__(self, index: int | slice):
        if isinstance(index, int):
            self[index:index+1] = ()
        else:
            self[index] = ()

    def append(self, value: Cell):
        """Append value to end"""
        self.edit()
        self.evolver.append(value)
        self.search_buffer.append(ord(value.quanta))

    def extend(self, values: Sequence[Cell]):
        """Extend with values"""
        self.edit()
        self.evolver.extend(values)
        self.search_buffer.extend(ord(c.quanta) for c in values)

    def insert(self, index, value):
        """Insert value at index"""
        self[index:index] = (value,)


if __name__ == '__main__':
    pass
