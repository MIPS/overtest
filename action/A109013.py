import os
from Action import Action

# Example Testsuite

class A109013(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 109013
    self.name = "Example Testsuite"

  # Execute the action.
  def run(self):
    self.testsuiteSubmit("My First Test", True, {"stringres":"fred", "intres":1, "floatres":1.1, "boolres":False})
    self.testsuiteSubmit("My Second Test", True, {"stringres":"fred2", "intres":2, "floatres":2.2, "boolres":True}, "1.1")
    self.success({"mystr":"bar", "myint":10, "myfloat":3.5, "mybool":True})
    return True
