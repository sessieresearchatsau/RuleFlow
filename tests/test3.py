from array import array
a = bytearray('ABCD', 'utf-8')
a[1:3] = bytes(ord(c) for c in 'ab')
print(a)
