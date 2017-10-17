import os

from Action import Action
from Perforce import PerforceConnection

# Fetch

class A117805(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117805
    self.name = "Fetch"

  # Execute the action.
  def run(self):
    host = self.getResource('Execution Host')
    p4port = str(host.getAttributeValue('P4PORT'))

    changelist = int(self.config.getVariable('LLVM_P4_CHANGELIST'))
    workspace_template = 'MAIN_LLVM_WS'

    root = self.getWorkPath ()

    conn = PerforceConnection(p4user='xbuild.meta', p4port=p4port)

    clientdef = conn.make_temporary_client_def(workspace_template, root=root)

    with clientdef as client:
      client.sync('@%d' % changelist)

    self.config.setVariable('LLVM_AUTO_SRC_DIR', root)

    return True
