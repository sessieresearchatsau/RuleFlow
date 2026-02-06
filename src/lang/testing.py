from core.engine import SpaceState1D, Cell
def space(string: str) -> SpaceState1D:
    return SpaceState1D([Cell(s) for s in string])
def seq(string: str) -> list[Cell]:
    return [Cell(s) for s in string]
s = space('ABBABBAabc123xyz456abc')


# ==== Regex Tests ====
a = []
a.extend(s.find(r'ABBA'))
print(a)


pass
# ==== Modifier Tests ====
# Good
# s.substitute((3, 6), seq('ABC'))
# s.substitute((-6, -3), seq('ABC'))

# Good
# s.overwrite(-3, seq('A_C'))

# Good
# s.insert(1, seq('ABC'))

# Good
# s.delete((3, 6))
# s.delete((-6, -3))

# Good
# s.shift((3, 6), 1)
# s.shift((3, 6), -1)
# s.shift((-6, -3), 1)
# s.shift((-6, -3), -1)

# Good
# s.swap((3, 6), (-6, -3))
# s.swap((-6, -4), (3, 6))
# s.swap((-100, -3), (-3, 100))

# Good
# s.reverse((3, 6))
# s.reverse((-6, -3))

# print(s)
