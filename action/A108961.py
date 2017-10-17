import os
from Action import Action

# Get mecc supertest

class A108961(Action):
  dir_supertest_source     = os.path.join ('testsuites', 'supertest')
  dir_cadese               = os.path.join ('/user', 'local_cosy')
  dir_cadese_repository    = os.path.join (dir_cadese, 'CoSy3202', 'repository')
  file_product             = os.path.join (dir_cadese, 'product', 'bin', 'product');
  file_supertest_component = os.path.join (dir_cadese_repository, 'local', 'components_supertest')

  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 108961
    self.name = "Get mecc supertest"

  # Execute the action.
  def run(self):
    env = { 'PATH': '%s/product/bin:%s/cadese/bin:%s/sccs/bin:%s' % (self.dir_cadese, self.dir_cadese, self.dir_cadese, os.getenv ('PATH') ) }
    
    # Get all the directories involved
    work_dir = self.getWorkPath()
    self.dir_supertest_source = os.path.join (work_dir, self.dir_supertest_source)

    if self.debug_verbose:
      print "Inputs:"
      print "Working:"
      print "\tWork dir:      %s" % (work_dir)
      print "\tSupertest dir: %s" % (self.dir_supertest_source)

    self.config.setVariable ('SUPERTEST_INST_ROOT', self.dir_supertest_source)

    if self.testrun.debug_allow_skipping and os.path.exists (self.dir_supertest_source):
      self.testrun.skip ("Checkout supertest")
    else:
      result = self.execute(env=env, command=[self.file_product, "extract", "-c", self.file_supertest_component], workdir=self.dir_supertest_source)
      if not result == 0:
        self.error("Checkout supertest")

    return self.success()
