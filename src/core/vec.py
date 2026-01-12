"""Vector Implementation (Custom fit for engine) to be OPTIONALLY used as the Sequence of Cells for the StateSpace.

==== Policy ====
- The API for all vectors should be cross-compatible. If a specific vector implementation is switched, the client code should still work just fine.

==== FUTURE CONSIDERATIONS ====
- Add a new backend for persistent vectors (using Rope or Finger data structures) to solve the structural edit problem
with the current trie-based pvector data structure.
This would likely be a significant time commitment to implement properly... so do this in the future only when truly needed.
    - Consider implementing these in pure C and making a python interface for maximum performance.
"""
from pyrsistent import PVector, pvector
from pyrsistent.typing import PVectorEvolver
from typing import MutableSequence, Sequence, Literal, Iterator, Any, overload
from copy import copy
from core.engine import Cell


# ================================ Target Bytes Cache ================================
# IMPORTANT NOTE: Sequence[Cell] must really be tuple[Cell] for there to be any benefit to using the Cache!!! Because tuple is hashable.
__bytes_cache_size__: int = 0
__bytes_cache__ = {  # FIFO cache
    # globally cached bytes will go here where the key is an immutable array of Cells and the value is the compiled bytes
}
def __retrieve_bytes__(key: Sequence[Cell]) -> bytes:
    """Used to retrieve the pre-compiled bytearrays from the global cache (fills up quickly for our application)."""
    pass
def enable_global_cache(b: bool, cache_size: int = 1024):
    """Enable the use of the global bytes cache. Consider disabling the cache if there is an unknown number of bytes sequences to be used."""
    if b:
        global __bytes_cache_size__
        __bytes_cache_size__ = cache_size
        def retrieve_bytes(key: Sequence[Cell]) -> bytes:
            global __bytes_cache__
            try:  # we use this because the cache "hit" is most common for L-Systems... so a bit faster than doing an if statement when key exists in the cache already.
                return __bytes_cache__[key]
            except KeyError:
                if len(__bytes_cache__) >= __bytes_cache_size__:  # ensure that the cache stays within limits
                    try:
                        del __bytes_cache__[next(iter(__bytes_cache__))]  # use the fact that dicts keep element order to follow FIFO caching principles
                    except (StopIteration, RuntimeError, KeyError):
                        pass
                __bytes_cache__[key] = (r := bytes(ord(c.quanta) for c in key))
                return r
            except TypeError:  # if key is not hashable:  # but it really-really ought to be!
                return retrieve_bytes(tuple(key))
    else:
        def retrieve_bytes(key: Sequence[Cell]) -> bytes:
            return bytes(ord(c.quanta) for c in key)
    globals()['__retrieve_bytes__'] = retrieve_bytes
enable_global_cache(True)


# ================================ Regex Backend ================================
import re
import regex
from regex import finditer as _finditer  # this the default (can be changed with the `set_regex_backend` function below)
def set_regex_backend(m: Literal['re', 'regex']):
    """Set the regex backend to either the builtin `re` or the more versatile `regex` (default)"""
    if m == 'regex':
        globals()['_finditer'] = regex.finditer
    elif m == 're':
        globals()['_finditer'] = re.finditer
__pattern_cache__: dict[str | bytes, re.Pattern | regex.Pattern]
def finditer():
    pass



# ================================ Vector Implementation ================================
class Vec(MutableSequence):
    __slots__ = ('vec', 'search_buffer')

    def __init__(self, elems: Sequence[Cell]):
        self.vec: MutableSequence[Cell] = elems if isinstance(elems, MutableSequence) else list(elems)
        self.search_buffer: bytearray = bytearray((ord(c.quanta) for c in elems))

    def __str__(self):
        return str(self.vec)

    def __repr__(self):
        return str(self)

    # ================ Persistence Method Placeholders ================
    def edit(self):
        """Enter edit mode (for immutable/persistent internal vectors)."""

    def commit(self):
        """Commit changes made while in edit mode (for immutable/persistent internal vectors)."""

    # ================ Branching Methods ================
    def branch_search_buffer(self, reconstruct_from_cells: bool = False) -> None:
        """Create new search buffer (useful for multi-ways). If using from_pvec, it will be reconstructed directly from the cells, otherwise just copied."""
        if reconstruct_from_cells:
            self.search_buffer = bytearray((ord(c.quanta) for c in self.vec))  # O(n log_32 n)
        else:
            self.search_buffer = self.search_buffer.copy()  # O(n)

    def branch(self) -> Vec:
        """Branch the current vector into a new vector"""
        nv: Vec = object.__new__(Vec)
        nv.vec = copy(self.vec)
        nv.search_buffer = self.search_buffer  # note: becomes out-of-date on self after branch (use branch_search_buffer(rfp=True) to reconstruct clean buffer for self)
        return nv

    def __copy__(self):
        return self.branch()

    def __deepcopy__(self, memo):  # force it to use self.branch for safety
        return self.branch()

    # ================ Viewer Methods ================
    def __len__(self):
        return len(self.vec)

    @overload
    def __getitem__(self, index: int) -> Cell: ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[Cell]: ...

    def __getitem__(self, index):
        return self.vec[index]

    def finditer(self, pattern: bytes, *args, **kwargs) -> Iterator[tuple[int, int]]:
        for m in finditer(pattern, self.search_buffer, *args, **kwargs):
            yield m.span()

    # ================ Modifiers ================
    @overload
    def __setitem__(self, index: int, value: Cell) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Sequence[Cell]) -> None:
        ...

    def __setitem__(self, index, value):
        self.vec[index] = value
        self.search_buffer[index] = ord(value.quanta) if isinstance(value, Cell) else __retrieve_bytes__(value)

    def __delitem__(self, index: int | slice):
        del self.vec[index]
        del self.search_buffer[index]

    def append(self, value: Cell):
        """Append value to end"""
        self.vec.append(value)
        self.search_buffer.append(ord(value.quanta))

    def extend(self, values: Sequence[Cell]):
        """Extend with values"""
        self.vec.extend(values)
        self.search_buffer.extend(__retrieve_bytes__(values))

    def insert(self, index: int, value: Cell):
        """Insert value at index"""
        self.vec.insert(index, value)
        self.search_buffer.insert(index, ord(value.quanta))


class TrieVec(Vec):
    __slots__ = ('evolver',)

    def __init__(self, elems: Sequence[Cell]):
        object.__init__(super())
        self.vec: PVector[Cell] = pvector(elems)
        self.search_buffer: bytearray = bytearray((ord(c.quanta) for c in elems))
        self.evolver: PVectorEvolver[Cell] | None = None

    def __str__(self):
        return 'Vec' + str(self.vec)[7:]

    # Persistence Methods
    def edit(self):  # we use this rather than .is_dirty() to minimize space use of an evolver object.
        if self.evolver is None:
            self.evolver = self.vec.evolver()

    def commit(self):
        if self.evolver is not None:
            self.vec = self.evolver.persistent()
            self.evolver = None

    # Branching Methods
    def branch(self) -> TrieVec:
        """Branch the current vector into a new vector"""
        self.commit()  # flush any changes
        nv: TrieVec = object.__new__(TrieVec)
        nv.vec = self.vec  # we don't need to copy as edit() will do that for us
        nv.evolver = None
        nv.search_buffer = self.search_buffer  # note: becomes out-of-date on self after branch (use branch_search_buffer(rfp=True) to reconstruct clean buffer for self)
        # we could auto enter edit mode here... however, that is not necessary as this should work just fine.
        return nv

    # ================ Modifiers ================
    @overload
    def __setitem__(self, index: int, value: Cell) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Sequence[Cell]) -> None: ...

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value: Sequence[Cell]
            start, stop, _ = index.indices(len(self.vec))
            if len(value) == stop - start:  # if we can do point updates
                self.edit()
                for i, val in enumerate(value):
                    self.evolver[start + i] = val
            else: # Structural Change: because the evolver cannot handle length changes (deletions or insertions)
                self.commit()  # flush any existing point-updates to the pvec
                self.vec = self.vec[:start] + pvector(value) + self.vec[stop:]  # does not use the Evolver object as this creates a new node.
            self.search_buffer[start:stop] = __retrieve_bytes__(value)
            return
        # if isinstance(index, int):
        value: Cell
        self.edit()
        self.evolver[index] = value
        self.search_buffer[index] = ord(value.quanta)

    def __delitem__(self, index: int | slice):
        if isinstance(index, int):
            self[index:index+1] = ()
        else:  # if index is a slice
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
        self.search_buffer.extend(__retrieve_bytes__(values))

    def insert(self, index, value):
        """Insert value at index"""
        self[index:index] = (value,)


if __name__ == '__main__':
    pass
