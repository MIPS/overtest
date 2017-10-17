import os
from Action import Action

# Build mecc toolkit

class A108957(Action):
  dir_cadese       = os.path.join ('/user', 'local_cosy')
  dir_mecc_source  = os.path.join ('source', 'mecc')
  dir_mecc_build   = os.path.join (dir_mecc_source, 'mecc', 'release')
  dir_mecc_output  = os.path.join (dir_mecc_source, 'mecc', 'outputs')
  file_mecc_build  = os.path.join (dir_mecc_build, 'scripts', 'build.sh')

  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108957
    self.name = "Build mecc toolkit"

  # Execute the action.
  def run(self):
    env = {}
    
    # Get all the directories involved
    work_dir = self.getWorkPath()
    self.dir_mecc_source = os.path.join (work_dir, self.dir_mecc_source)
    self.dir_mecc_build  = os.path.join (work_dir, self.dir_mecc_build )
    self.file_mecc_build = os.path.join (work_dir, self.file_mecc_build)

    # Get the variables we need
    metag_inst_root = self.config.getVariable("METAG_INST_ROOT")
    env['METAG_INST_ROOT'] = metag_inst_root

    if self.debug_verbose:
      print "Inputs:"
      print "METAG_INST_ROOT: %s" % (metag_inst_root)
      print "Working:"
      print "\tWork dir:      %s" % (work_dir)
      print "\tMECC source dir: %s" % (self.dir_mecc_source)

    self.logHelper("Starting MECC build")
    if self.testrun.debug_allow_skipping and os.path.exists (self.dir_mecc_output):
      self.testrun.skip ("Build MECC")
    else:
      result = self.execute (env=env, command=['%s --no-win' % self.file_mecc_build], shell=True, workdir=self.dir_mecc_build)
      if not result == 0:
        self.error("Couldn't build MECC")

    return self.success ()
