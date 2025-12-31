from pyrsistent import pvector, v

v = pvector([1, 2, 3, 4, 5, 6, 7, 8])
v1 = v[:2] + pvector([0, 0]) + v[-2:]
print(v, v1, sep='\n')

