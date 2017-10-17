import os
from Action import Action

# %actionname%

class A%actionid%(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = %actionid%
    self.name = "%actionname%"

  # Execute the action.
  def run(self):
    # Sample usage of the framework. Some actions will utilise more than others pick and choose.
    # A full listing and description of the supported features is available in the API reference
    # which is self-documented in the python module action/Action.py and HTML formatted on the
    # web interface in the API help.

    # Find the resources that have been allocated
    # da = self.getResource("Debug Adapter")
    # Extract any useful attributes associated with the resource
    # da_name = da.getAttributeValue("DA Name")

    # Extract configuration data for this testrun
    # METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")
    # env = {}
    # env['PATH'] = METAG_INST_ROOT+"/bin:"+os.environ['PATH']

    # Execute a command overriding some environment variables
    # result = self.execute(env=env, command=["command", "arg1", "arg2", da_name])

    # Find the correct CVSROOT for a given repository when accessed from this host 
    # host = self.getResource("Execution Host")
    # cvsroot = host.getAttributeValue("KL metag CVSROOT")

    # Check out a cvs module and put it in a subdirectory of the automatically allocated working directory
    # result = self.cvsCheckout("module", workdir=os.path.join(self.getWorkPath(),"mysubdir"), tag="tag", cvsroot=cvsroot)

    # Store the path to this action's work area so other actions can find it
    # self.config.setVariable("Some Shared Path", self.getWorkPath())

    # If something goes wrong with any part of this run simply raise an error immediately. This
    # will throw an exception which you should not catch.
    # self.error("What went wrong")

    # Always signal success with self.success() you can "return self.success()" as it returns True
    # if result:
    #   return self.success()

    # Success takes an argument of additional information about the 'success'
    # For example a testsuite may succeed in its execution but there may be some aggregated data to store
    # return self.success({"PASS":2000, "FAIL":10, "NOTRUN":34})

    # For actions that run a testsuite each test result can be submitted individually. This allows
    # detailed analysis of results at a later stage.
    # 
    # Use the following function to submit individual results, this can be called multiple times with
    # different test names.
    # self.testsuiteSubmit("name of test", <True|False>, {"field":"value"})

    self.error("NOT IMPLEMENTED")
