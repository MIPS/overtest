import os
import re
from Action import Action
from common.VerificationSuite import VerificationSuiteAction

# CoreMark

class A117215(VerificationSuiteAction):
  def __init__(self, data):
    VerificationSuiteAction.__init__(self, data)
    self.actionid = 117215
    self.name = "CoreMark"

  def verify_template(self):
    return "ovt_%s" % self.version.split('.')[-1]

  def tests(self):
    if self.verify_template().split('_')[1] == "vhdl":
      return [ "cqdxmark1"  ]
    elif self.verify_template().split('_')[1] == "fpga":
      return [ "fcqdxmark1"  ]
    else:
      assert False

  def post_process(self):
    publish_txt = os.path.join(self.getWorkPath(), ".publish.txt")
    file = open(publish_txt)
    log = file.read()
    file.close()

    match = re.search("Thread 0: 'Ticks_S \d+', 'Ticks_E \d+', 'Ticks (\d+)', 'Active (\d+)', 'Idle (\d+)' and 'Speed (\d+)'", log)

    if match:
      ticks, active, idle, speed = match.group (1, 2, 3, 4)

      results = {'Timer Ticks'   : ticks,
                 'Active Cycles' : active,
                 'Idle Cycles'   : idle,
                 'Speed'         : speed,
                }

      return self.testsuiteSubmit(self.tests()[0], True, results)
    else:
      return self.error("Could not find CoreMark results")
