import pytest
import copy
import numpy as np
from hypothesis import given, strategies as st

# flow imports
from core.topologies.vector import Vector, CellVector
from core.topologies.tooling.searcher import VectorSearch


@given(
    st.lists(st.integers(0, 255), min_size=0, max_size=100),
    st.integers(0, 100),
    st.integers(0, 100),
    st.lists(st.integers(0, 255), min_size=0, max_size=50)
)
def test_vector_slice_assignment_fuzz(base_data, slice_start, slice_end, insert_data):
    """Rigorous property-based testing comparing custom Vector against standard Python lists."""
    slice_start = min(slice_start, len(base_data))
    slice_end = min(slice_end, len(base_data))
    if slice_start > slice_end:
        slice_start, slice_end = slice_end, slice_start

    py_list = list(base_data)
    py_list[slice_start:slice_end] = insert_data

    vec = Vector(base_data)
    vec[slice_start:slice_end] = insert_data

    assert list(vec) == py_list
    assert len(vec) == len(py_list)
    assert vec.logical_length == len(py_list)
    assert vec.capacity >= vec.logical_length


def test_vector_initialization():
    """Verify initial sync between logical_data and capacity."""
    vec = Vector([65, 66, 67, 68, 69])  # A, B, C, D, E
    assert len(vec) == 5
    assert list(vec.logical_data) == [65, 66, 67, 68, 69]
    assert vec[0] == 65


def test_vector_point_update_int():
    """Test __setitem__ with integer index."""
    vec = Vector([65, 66, 67, 68, 69])
    vec[2] = 88  # X
    assert list(vec.logical_data) == [65, 66, 88, 68, 69]


def test_vector_point_update_slice_same_length():
    """Test slice __setitem__ with same length."""
    vec = Vector([65, 66, 67, 68, 69])
    vec[1:3] = [89, 90]  # Y, Z
    assert list(vec.logical_data) == [65, 89, 90, 68, 69]


def test_vector_structural_change_insertion():
    """Test slice __setitem__ with different length (triggers capacity logic)."""
    vec = Vector([65, 66, 67, 68, 69])
    vec[2:2] = [88, 89, 90]  # Insert X, Y, Z
    assert len(vec) == 8
    assert list(vec.logical_data) == [65, 66, 88, 89, 90, 67, 68, 69]


def test_vector_structural_change_deletion():
    """Test __delitem__ with slices."""
    vec = Vector([65, 66, 67, 68, 69])
    del vec[1:4]  # Delete B, C, D
    assert len(vec) == 2
    assert list(vec.logical_data) == [65, 69]


def test_vector_append_and_extend():
    """Test list-like growth methods (inherited from MutableSequence)."""
    vec = Vector([65, 66, 67, 68, 69])
    vec.append(70)  # F
    vec.extend([71])  # G
    assert list(vec.logical_data) == [65, 66, 67, 68, 69, 70, 71]


def test_vector_copy_isolation():
    """Test copying behavior to ensure memory views don't bleed across branches."""
    vec = Vector([65, 66, 67])
    new_vec = copy.copy(vec)
    new_vec[0] = 90
    assert vec[0] == 65
    assert new_vec[0] == 90



# ================ CellVector Tests (Causality & Branches) ====================

def test_cell_vector_initialization():
    """Verify initial setup of data, generations, and IDs."""
    cv = CellVector([65, 66, 67, 68, 69], gen=0, id_start=0)
    assert len(cv) == 5
    assert list(cv.data.logical_data) == [65, 66, 67, 68, 69]

    first_cell = cv.get_cell(0)
    assert first_cell.quanta == 65
    assert first_cell.gen == 0
    assert first_cell.id == 0


def test_cell_vector_point_and_slice_updates():
    """Test that setting data triggers generation and ID tracking correctly."""
    cv = CellVector([65, 66, 67, 68, 69], gen=0, id_start=0)
    cv2 = cv.next_gen()

    # Integer update
    cv2[2] = 88
    assert cv2.gens[2] == 1
    assert cv2.ids[2] == 5  # ID counter increments

    # Slice update
    cv2[1:3] = [89, 90]
    assert list(cv2.gens[1:3]) == [1, 1]
    assert list(cv2.ids[1:3]) == [6, 7]  # Continues incrementing
    assert cv2.id_start == 8


def test_cell_vector_branching():
    """Test persistence and structural sharing via branching (next_gen)."""
    cv = CellVector([65, 66, 67], gen=0)
    cv2 = cv.next_gen()

    # Modify original (simulating an alternate branch context)
    cv[0] = 90
    assert cv2[0] == 65  # Should remain untouched
    assert cv[0] == 90


# ================ Searcher Integration (Pattern Matching) ================

def test_pattern_matching_with_structural_changes():
    """Test exact pattern matching via the new VectorSearch on the logical_data buffer."""
    searcher = VectorSearch(backend='numpy', overlapping=True)
    vec = Vector([65, 66, 65, 66, 65])  # A B A B A
    pattern1 = np.array([65, 66, 65], dtype=np.uint8)  # A B A

    # 1. Test basic pattern match for "ABA" (overlapping)
    matches = list(searcher(pattern1, vec.logical_data))
    assert len(matches) == 2
    assert matches[0] == (0, 3)
    assert matches[1] == (2, 5)

    # 2. Test after a point update (buffer sync check)
    vec[2] = 88  # X (now: A B X B A)
    pattern2 = np.array([66, 88], dtype=np.uint8)  # B X
    matches = list(searcher(pattern2, vec.logical_data))
    assert len(matches) == 1
    assert matches[0] == (1, 3)

    # 3. Test structural change
    vec[3:3] = [89]  # Y (now: A B X Y B A)
    pattern3 = np.array([88, 66, 65], dtype=np.uint8)  # X B A
    matches = list(searcher(pattern3, vec.logical_data))
    assert len(matches) == 0  # Eradicated by Y

    pattern4 = np.array([88, 89, 66], dtype=np.uint8)  # X Y B
    matches = list(searcher(pattern4, vec.logical_data))
    assert len(matches) == 1
    assert matches[0] == (2, 5)
