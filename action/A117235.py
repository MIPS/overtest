import os
import re
import collections
from Action import Action
from Perforce import PerforceConnection
from Config import CONFIG
from utils.Utilities import versionCompare

# TicketRegression

class A117235(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 117235
    self.name = "TicketRegression"

  # Execute the action.
  def run(self):
    host = self.getResource('Execution Host')
    p4port = str(host.getAttributeValue('P4PORT'))

    # Extract configuration data for this testrun
    MECC_INST_ROOT = self.config.getVariable("MECC_INST_ROOT")
    METAG_INST_ROOT = self.config.getVariable("METAG_INST_ROOT")
    METAG_FSIM_ROOT = self.config.getVariable("METAG_FSIM_ROOT")
    COBIT_INST_ROOT = self.config.getVariable("COBIT_INST_ROOT")

    root = self.getWorkPath ()

    env = { 'PATH' : CONFIG.makeSearchPath([CONFIG.getProgramDir(CONFIG.neo),
                                            os.path.join(COBIT_INST_ROOT, 'bin'),
                                            os.environ['PATH']]),
            'LM_LICENSE_FILE' : os.path.join(os.path.expanduser("~"), "licenses", "uncounted.lic"),
            'MECC_INST_ROOT' : MECC_INST_ROOT,
            'METAG_INST_ROOT' : METAG_INST_ROOT,
            'METAG_FSIM_ROOT' : METAG_FSIM_ROOT,
            'P4PORT' : p4port,
            'P4USER' : 'xbuild.meta',
          }

    command = ['p4_cmp', 'fetch', 'TicketRegression']
    if self.version == 'CHANGELIST':
        changelist = self.config.getVariable('MECCTICKETS_FETCH_CHANGELIST')
        command.append('--changeset=%s' % changelist)
        command.append('--location=//meta/swcore/cosy/code/ticket_regression/MAIN/mecc/tickets/xyTicketRegression.xyf')
    else:
        command[-1] = command[-1] + ':%s' % self.version
    command.append(root)

    if self.execute(env=env, command=command):
      self.error("Failed to fetch source")

    command = ["./all_tickets.sh"]

    if self.config.getVariable("MECCTICKETS_VERBOSE"):
      command.append('--verbose')

    if self.execute(workdir=os.path.join(root, "mecc", "tickets"), 
                    env=env,
                    command=command):
      self.error("Failed to execute all_tickets.sh")

    summary = collections.defaultdict(lambda:0)
    output = self.fetchOutput().splitlines()

    # Parse each line of the last command's output
    anything_failed = False

    for line in output:
      passed = False

      if re.match('\w+ *: *(PASS|FAIL) *: *.*$', line):
        line = re.split(' *: *', line)
        ticketid = line[0]
        result = line[1]
        ext_result = line[2]

        summary[ext_result] += 1
  
        passed = False
  
        if result == 'PASS':
          passed = True
        else:
          anything_failed = True
  
        self.testsuiteSubmit(ticketid, passed, {"Result":ext_result})

    if anything_failed:
      return self.failure(summary)

    return self.success(summary)
