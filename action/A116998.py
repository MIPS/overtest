import os
from Action import Action
from IMGAction import IMGAction

# AXD Testsuite

class A116998(Action, IMGAction):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 116998
    self.name = "AXD Testsuite"

  # Execute the action.
  def run(self):
    firmware_dir=self.config.getVariable('AXD_FIRMWARE_OUTPUT')

    output_binaries=os.path.join(firmware_dir, "output", "binaries")
    test_dir=os.path.join(firmware_dir, "test")
    audiotools_dir=os.path.join(test_dir, "AFsp-v9r0", "bin")

    DA=self.getResource("Debug Adapter")
    DA_NAME=DA.getAttributeValue("DA Name")

##################################
    run_result = self.neoRunDAScript(os.path.join(test_dir, "test_mp3.py"),
                                        [DA_NAME,output_binaries,test_dir,audiotools_dir], 
                                        workdir=test_dir)
    output = self.fetchOutput()
    lines = output.splitlines()
    results = {'':'\n'}
    success = True
    test = 'No test title found!'
    for line in lines :
      if line.find('::') != -1 :
        if line.find('Test::') != -1 :
          test = line
        else :
          results[''] = results[''] + line + '\n'
      elif line.find('FAIL') != -1 :
        results[''] = results[''] + '  ' +  line + '\n'
        success = False
      elif line.find('PASS') != -1 :
        results[''] = results[''] + '  ' + line + '\n'
    self.testsuiteSubmit(test, success, results)
###################################
    run_result = self.neoRunDAScript(os.path.join(test_dir, "test_tone.py"),
                                        [DA_NAME,output_binaries,test_dir], 
                                        workdir=test_dir)
    output = self.fetchOutput()
    lines = output.splitlines()
    results = {'':'\n'}
    success = True
    test = 'No test title found!'
    for line in lines :
      if line.find('::') != -1 :
        if line.find('Test::') != -1 :
          test = line
        else :
          results[''] = results[''] + line + '\n'
      elif line.find('FAIL') != -1 :
        results[''] = results[''] + line + '\n'
        success = False
      elif line.find('PASS') != -1 :
        results[''] = results[''] + line + '\n'
    self.testsuiteSubmit(test, success, results)

###################################
    run_result = self.neoRunDAScript(os.path.join(test_dir, "test_sweep.py"),
                                        [DA_NAME,output_binaries,test_dir], 
                                        workdir=test_dir)
    output = self.fetchOutput()
    lines = output.splitlines()
    results = {'':'\n'}
    success = True
    test = 'No test title found!'
    for line in lines :
      if line.find('::') != -1 :
        if line.find('Test::') != -1 :
          test = line
        else :
          results[''] = results[''] + line + '\n'
      elif line.find('FAIL') != -1 :
        results[''] = results[''] + line + '\n'
        success = False
      elif line.find('PASS') != -1 :
        results[''] = results[''] + line + '\n'
    self.testsuiteSubmit(test, success, results)
###################################
    run_result = self.neoRunDAScript(os.path.join(test_dir, "test_sweep_2.py"),
                                        [DA_NAME,output_binaries,test_dir], 
                                        workdir=test_dir)
    output = self.fetchOutput()
    lines = output.splitlines()
    results = {'':'\n'}
    success = True
    test = 'No test title found!'
    for line in lines :
      if line.find('::') != -1 :
        if line.find('Test::') != -1 :
          test = line
        else :
          results[''] = results[''] + line + '\n'
      elif line.find('FAIL') != -1 :
        results[''] = results[''] + line + '\n'
        success = False
      elif line.find('PASS') != -1 :
        results[''] = results[''] + line + '\n'
    self.testsuiteSubmit(test, success, results)
###################################
      
    return True
