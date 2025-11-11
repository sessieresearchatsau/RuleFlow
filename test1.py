# from typing import NamedTuple, Sequence
#
# class DeltaCellSet(NamedTuple):  # the cells that were created and destroyed
#     destroyed_cells: Sequence[int]
#     new_cells: Sequence[int]
#
#     def __bool__(self) -> bool:
#         return bool(self.destroyed_cells) or bool(self.new_cells)  # if any changes occurred, return true.
#
#
# a = DeltaCellSet((), ())
# if a:
#     print(True)
# else:
#     print(False)

