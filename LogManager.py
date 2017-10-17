from Config import CONFIG
import os

class LogManager:
  def __init__(self, logname, display=False, local=False, subdir=None):
    """
    Open a handle to the relevant log file
    """
    self.log = None

    if logname != None:
      location = CONFIG.logdir
      if local:
        location = "."
      if subdir is not None:
	location = os.path.join(location, str(subdir))
      try:
        os.makedirs(location)
      except OSError:
        pass

      self.log = open(os.path.join(location, "%s.log" % logname), "a")
    self.display = display

  def __del__(self):
    """
    Clean up the log file
    """
    if self.log != None:
      self.log.close()

  def write(self, message):
    """
    Write a message to the log and optionally to the screen
    """
    if self.log != None:
      self.log.write("%s\n"% message)
      self.log.flush()
    if self.display:
      print message
