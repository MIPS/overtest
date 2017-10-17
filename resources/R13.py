from Resource import Resource

class R13(Resource):
  """
  A class to manage the MIPS Board resources
  """
  RESOURCETYPEID=13

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
