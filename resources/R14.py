from Resource import Resource
import os

class R14(Resource):
  """
  A class to manage the ARM Board resources
  """
  RESOURCETYPEID=14

  def __init__(self, data):
    """
    Initialise the class
    """
    Resource.__init__(self, data)

  def initialise(self):
    """
    Run the initialisation commands
    """
    return True
