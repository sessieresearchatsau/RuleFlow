"""Elementary Cellular Automaton with Bit-Flip Causality Filtering"""
from typing import Sequence, cast
import numpy as np
from core.engine import (
    Flow,
    Rule as RuleABC,
    RuleMatch,
    RuleSet,
    DeltaSpace,
    DeltaCell
)
from core.topologies.nd_space import SpaceState1D as SpaceState


class ECARule(RuleABC):
    def __init__(self, rule_index: int):
        super().__init__()
        self.rule_index = rule_index

        # Convert the integer rule index into an 8-bit binary pattern string
        rule_bits = f'{rule_index:08b}'

        # Map the 3-cell neighborhood binary value (7 down to 0) to its resulting bit
        self.mapping = {
            7 - i: int(bit) for i, bit in enumerate(rule_bits)
        }

    def match(self, spaces: Sequence[SpaceState]) -> Sequence[RuleMatch]:
        space = spaces[0]
        return (RuleMatch(space=space, matches=((0, len(space.vec)),), conflicts=frozenset()),)

    def apply(self, rule_matches: Sequence[RuleMatch]) -> Sequence[DeltaSpace]:
        old_space = cast(SpaceState, rule_matches[0].space)
        data = old_space.vec.data.logical_data
        length = len(data)
        new_data = data.copy()  # Start with a copy of the old data (defaulting to no changes)
        destroyed_cells_list = []
        for i in range(length):
            left = data[i - 1] if i > 0 else 0
            center = data[i]
            right = data[i + 1] if i < length - 1 else 0

            # Calculate the integer index of the neighborhood pattern
            idx = (left << 2) | (center << 1) | right
            target_bit = self.mapping[idx]

            if target_bit != center:
                new_data[i] = target_bit
                destroyed_cells_list.append(old_space.vec.get_cell(i))

        new_space = old_space.next_gen()
        new_space.vec[:] = new_data

        # Gather the corresponding new cells only for the indices that actually flipped
        new_cells_list = [
            new_space.vec.get_cell(i)
            for i in range(length)
            if new_data[i] != data[i]
        ]

        # Build the DeltaCell containing strictly the flipped cells
        dc = DeltaCell(tuple(destroyed_cells_list), tuple(new_cells_list))

        return (DeltaSpace(old_space, (new_space,), (dc,), self),)


class ECA(Flow):
    def __init__(self, rule_index: int, initial_space: Sequence[int]):
        super().__init__()
        self.set_initial_space([SpaceState(np.array(initial_space, dtype=np.uint8))])
        self.set_ruleset(RuleSet([ECARule(rule_index)]))


if __name__ == "__main__":
    # Test Rule 90: Sierpinski Triangle with bit-flip filtered causality
    system = ECA(rule_index=90, initial_space=[0, 0, 0, 1, 0, 0, 0])
    system.evolve(3)
    print(system.__str__())

    # Evolution Table
    # from analysis.prettier import SpaceState1DFormatter
    # from rich.console import Console
    # formatter = SpaceState1DFormatter()
    # console = Console(width=1000)
    # for event in system.events:
    #     console.print(formatter(next(event.spaces)))
