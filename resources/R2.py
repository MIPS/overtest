from Resource import Resource
from Config import CONFIG
import os
from OvertestExceptions import ResourceException, TimeoutException

class R2(Resource):
  """
  A class to manage the Debug Adapter resources
  """
  RESOURCETYPEID=2

  def __init__(self, data):
    """
    Initialise the class
    """
    Resource.__init__(self, data)

  def initialise(self):
    """
    Run the initialisation commands
    """
    try:
      da_name = self.getAttributeValue("DA Name")
    except ResourceException:
      self.error("Debug Adapter has no DA Name attribute")

    command = [CONFIG.neo, 'run_dascript', 'da_init.py', "-D", da_name]
    try:
      result = self.execute(timeout=100,command=command)
    except TimeoutException:
      return self.transientError("Timeout when initialising DA")

    if result != 0:
      self.logHelper("Warning: Could not initialise DA")
      #self.error("Failed to initialise DA, check logs")

    return True
