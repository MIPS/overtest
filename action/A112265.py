import os
from Action import Action

# META Linux BusyBox

class A112265(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112265
    self.name = "META Linux BusyBox"

  # Execute the action.
  def run(self):
    """
    Just make a Buildroot compatible patch and pass the patchfile location on
    """
    host = self.getResource("Execution Host")
    cvsroot = host.getAttributeValue("LEEDS CVSROOT")
    env = {"CVSROOT":cvsroot};
    patchfile = os.path.join(self.getSharedPath(), "busybox-metag.patch")

    if self.version == "Latest":
      tag = "HEAD"
    else:
      tag = self.version

    exitcode = self.execute(env=env,
                            command=["cvs -q rdiff -ko -u -r busybox_1_2_1 -r %s metag-busybox/modutils/insmod.c | " % tag +\
                                     "filterdiff -# 1,4- > %s" % patchfile],
                            shell=True)

    if exitcode == 0:
      exitcode = self.execute(env=env,
                              command=["cvs -q rdiff -ko -u -r busybox_1_2_1 -r %s metag-busybox | " % tag +\
                                       "filterdiff -x '*/insmod.c' | "+\
                                       "filterdiff -x '*/.config' | "+\
                                       "filterdiff -x '*/Rules.mak' >> %s" % patchfile],
                              shell=True)
    else:
      self.error("Failed to create initial single hunk patch")
     
    return (exitcode == 0)
