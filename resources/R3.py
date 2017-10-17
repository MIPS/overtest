from Resource import Resource

class R3(Resource):
  """
  A class to manage the Example Resource resources
  """
  RESOURCETYPEID=3

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
