import unittest
from src.core.vec import PVec
from src.core.engine import Cell


class TestPVec(unittest.TestCase):
    def setUp(self):
        # Initial state: "ABCDE"
        self.initial_chars = "ABCDE"
        self.cells = [Cell(c) for c in self.initial_chars]
        self.vec = PVec(self.cells)

    def test_initialization(self):
        """Verify initial sync between pvec and search_buffer."""
        self.assertEqual(len(self.vec), 5)
        self.assertEqual(self.vec.search_buffer, bytearray(b"ABCDE"))
        self.assertEqual(self.vec[0].quanta, "A")

    def test_point_update_int(self):
        """Test __setitem__ with integer index (triggers evolver)."""
        new_cell = Cell("X")
        self.vec[2] = new_cell

        # Verify buffer and temporary state
        self.assertEqual(self.vec.search_buffer, bytearray(b"ABXDE"))
        self.assertIsNotNone(self.vec.evolver)

        # Commit and verify persistence
        self.vec.commit()
        self.assertEqual(self.vec.pvec[2].quanta, "X")
        self.assertIsNone(self.vec.evolver)

    def test_point_update_slice_same_length(self):
        """Test slice __setitem__ with same length (triggers evolver)."""
        updates = [Cell("Y"), Cell("Z")]
        self.vec[1:3] = updates

        self.assertEqual(self.vec.search_buffer, bytearray(b"AYZDE"))
        self.assertIsNotNone(self.vec.evolver)
        self.vec.commit()
        self.assertEqual(self.vec.pvec[1].quanta, "Y")
        self.assertEqual(self.vec.pvec[2].quanta, "Z")

    def test_structural_change_insertion(self):
        """Test slice __setitem__ with different length (triggers sandwich)."""
        # "ABCDE" -> "ABXYZCDE" (Insert 3 cells)
        xyz = [Cell(c) for c in "XYZ"]
        self.vec[2:2] = xyz

        self.assertEqual(len(self.vec), 8)
        self.assertEqual(self.vec.search_buffer, bytearray(b"ABXYZCDE"))
        # Structural change should have forced a commit
        self.assertIsNone(self.vec.evolver)
        self.assertEqual(self.vec[5].quanta, "C")

    def test_structural_change_deletion(self):
        """Test __delitem__ (triggers sandwich)."""
        del self.vec[1:4]  # Delete "BCD"

        self.assertEqual(len(self.vec), 2)
        self.assertEqual(self.vec.search_buffer, bytearray(b"AE"))
        self.assertEqual(self.vec[1].quanta, "E")

    def test_append_and_extend(self):
        """Test list-like growth methods."""
        self.vec.append(Cell("F"))
        self.vec.extend([Cell("G")])

        self.assertEqual(self.vec.search_buffer, bytearray(b"ABCDEFG"))
        self.assertIsNotNone(self.vec.evolver)

    def test_branching_and_copy(self):
        """Test persistence and structural sharing via branching."""
        # Modify vec
        self.vec[0] = Cell("Z")

        # Branch it
        new_vec = self.vec.branch()

        # Verify they share underlying pvec data but have distinct buffers (once modified)
        self.assertEqual(new_vec.search_buffer, self.vec.search_buffer)

        # Modify original, should not affect branch pvec
        self.vec[1] = Cell("Q")
        self.assertEqual(new_vec[1].quanta, "B")  # Original branch preserved

    def test_buffer_reconstruction(self):
        """Test manual search buffer sync."""
        # Force the buffer out of sync manually for testing
        self.vec.search_buffer = bytearray(b"XXXXX")
        self.vec.branch_search_buffer(reconstruct_from_pvec=True)

        # Should be back to "ABCDE"
        self.assertEqual(self.vec.search_buffer, bytearray(b"ABCDE"))

    def test_finditer_pattern_matching(self):
        """Test regex pattern matching via finditer on the search buffer."""
        chars = "ABABA"
        self.vec = PVec([Cell(c) for c in chars])

        # 1. Test basic pattern match for "ABA"
        # Should find two overlapping matches if using regex,
        # but standard finditer usually finds non-overlapping.
        matches = list(self.vec.finditer(b"ABA"))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].start(), 0)

        # 2. Test after a point update (buffer sync check)
        # Change "ABABA" -> "ABXBA"
        self.vec[2] = Cell("X")
        matches = list(self.vec.finditer(b"BX"))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].start(), 1)

        # 3. Test structural change
        # "ABXBA" -> "ABX_Y_BA" (Insert Y)
        self.vec[3:3] = [Cell("Y")]
        matches = list(self.vec.finditer(b"XBA"))
        # In "ABXYBA", "XBA" should not exist, but "XYB" should
        self.assertEqual(len(list(self.vec.finditer(b"XBA"))), 0)

        xyb_matches = list(self.vec.finditer(b"XYB"))
        self.assertEqual(len(xyb_matches), 1)
        self.assertEqual(xyb_matches[0].start(), 2)


if __name__ == '__main__':
    unittest.main()
