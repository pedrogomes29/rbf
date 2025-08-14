value = 0x0
value = bytes(str("%"+str(4)+"s") % value, "ascii")
print(value)
print(bytes(value.hex(), 'ascii'))