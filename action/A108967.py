import os
from Action import Action

# Build GCC 4 based test toolkit

class A108967(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108967
    self.name = "Build GCC 4 based test toolkit"

  # Execute the action.
  def run(self):
    # Find where the source was checked out to
    source = self.config.getVariable("METAG_SOURCE_ROOT")
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")
    if METAG_INST_ROOT == "":
      METAG_INST_ROOT=self.getWorkPath()
      self.config.setVariable("METAG_INST_ROOT", METAG_INST_ROOT)

    self.config.setVariable("GCC build path", os.path.join(source, "target", "gcc2"))

    # Construct the path to the build directory
    dir_build = os.path.join(source, "metag", "tools", "gcc2testing", "build")

    # Specify the current work directory as the destination
    env = {"METAG_INST_ROOT":METAG_INST_ROOT}

    # Build the toolkit (this will modify the working area from the source fetch
    # stage! 
    result = self.execute(command=["make", "-j4", "install"], env=env, workdir=dir_build)

    if result == 0:
      return self.success()
    else:
      self.error("Build failed")
