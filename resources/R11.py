from Resource import Resource

class R11(Resource):
  """
  A class to manage the Example Resource resources
  """
  RESOURCETYPEID=11

  def __init__(self, data):
    """
    Initialise the class
    """
    Resource.__init__(self, data)

  def initialise(self):
    """
    Run the initialisation commands
    """
    self.execute(command=["touch", "ressy"])
    return True
