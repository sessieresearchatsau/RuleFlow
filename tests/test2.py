from pyrsistent import pvector, v

v = pvector([1, 2, 3])
# e = v.evolver()
# e[1] = 2
# s = e.persistent()
s = v[:1] + pvector([1, 2]) + v[-1:]
print(v, s, type(s), sep='\n')
