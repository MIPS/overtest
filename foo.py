class Foo:
  def __init__(self, a):
    self.a =a

  def __radd__(self, other):
    return self.a + other

a = {}
a[2] = Foo(3)
a[3] = Foo(4)
print sum(a.values())

