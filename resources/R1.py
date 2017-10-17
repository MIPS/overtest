from Resource import Resource

class R1(Resource):
  """
  A class to manage the Execution Host resources
  """
  RESOURCETYPEID=1

  def __init__(self, data):
    """
    Initialise the class
    """
    Resource.__init__(self, data)

  def initialise(self):
    """
    Run the initialisation commands
    """
    # Debug adapters do not need initialising
    return True
