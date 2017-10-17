import os
from action.Action import Action
from action.IMGAction import IMGAction
from OvertestExceptions import ResourceException

class VerificationSuiteAction(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)

  def group_option(self):
    g = self.groups()
    if g == None:
      return None
    else:
      return str(','.join(g))

  def groups(self):
    return None

  def tests_option(self):
    t = self.tests()
    if t == None:
      return None
    else:
      assert len(t) == 1
      return str(','.join(t))

  def tests(self):
    return None

  def verify_version(self):
    return '.'.join(self.version.split('.')[0:4])

  def verify_template(self):
    return "verify"

  def tools_option(self):
    return str(self.testrun.getVersion("MetaMtxToolkit"))

  def post_process(self):
    return self.success()

  # Execute the action.
  def run(self):
    kwargs = { 'TOOLS' : self.tools_option(),
               'GROUP' : self.group_option(),
               'JUSTONE' : self.tests_option(),
               'VERIFY'  : self.verify_version(),
               'template' : self.verify_template()
             }

    for k, v in kwargs.items():
      if v == None:
        del kwargs[k]

    env = { 'VERBOSE' : '2' }

    try:
      DA = self.getResource("Debug Adapter")
    except ResourceException, e:
      pass
    else:
      DA_NAME = DA.getAttributeValue("DA Name")
      env['METAT_USE_TARGET'] = DA_NAME

    if self.testrun.getVersion("MECCToolkit") != None:
      env['MECC_INST_ROOT'] = self.config.getVariable ("MECC_INST_ROOT")
      env['LM_LICENSE_FILE'] = os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic")
      kwargs['COMPILER'] = "mecc"

    result = self.neoVerify(env=env, **kwargs)

    if not result == 0:
      self.error ("Failed to run command")
    return self.post_process()
