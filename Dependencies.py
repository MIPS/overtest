from OvertestExceptions import *
from utils.TerminalUtilities import *

class Dependencies:
  def __init__(self, _ovtDB):
    self.ovtDB = _ovtDB
    self.interactive = False 

  def setInteractive(self, _interactive):
    self.interactive = _interactive

  def myprint(self, string, newline = True):
    if self.interactive:
      if newline:
        print string
      else:
        print string,

  def input(self, prompt):
    if self.interactive:
      return input(prompt)
    else:
      return None

  # Find and resolve all dependencies for the specified versionedaction
  def resolveDependencies(self, versionedactioniddict, autoadd = True):
    failure = False
    failnotice = ""
    oneperset = []
    changecount = 1
    changed = True
    depsmulti = self.ovtDB.getDependenciesMulti(versionedactioniddict)
    while changed:
      changed = False
      self.myprint("Resolving Dependencies (iteration "+str(changecount)+"):")
      changecount += 1
      for versionedactionid in versionedactioniddict.keys():
        deps = depsmulti[versionedactionid]
        if deps == None:
          self.myprint("No dependencies")
          continue
        myset = set()
        for group in deps:
          # groupdefault is the default producer when no producer has been specified and there
          # are multiple alternatives. There must be at most one default, though there may not
          # be one at all
          groupdefault = None
          if group != "":
            self.myprint("### " + group + " ###")
          else:
            self.myprint("### Other ###")
          actioncount = 0
          found = False;
          i = 0
          options = {}
          myset = set()
          for action in deps[group]:
            actioncount += 1
            # For named groups all actions must be examined. But the unnamed group has each 
            # action considered in its own right.
            if group == "":
              groupdefault = None
              found = False;
              i = 0
              options = {}
            # Auto select a dependency if it is the only version of an action in the empty group
            # or if it is the only version of the only action in a named group
            if autoadd and \
               (len(deps[group]) == 1 or group == "") and \
               len(deps[group][action]) == 1 and \
               not deps[group][action][0]['versionedactionid'] in versionedactioniddict:
              changed = True
              tempvaid=deps[group][action][0]['versionedactionid']
              depsmulti[tempvaid] = self.ovtDB.getDependencies(tempvaid)
              versionedactioniddict[tempvaid] = {}
            # Print out all the versions of this action (stating if it is selected)
            for details in deps[group][action]:
              # If this is a default dependency record the fact in case no producers are found
              # If there is already a default then error
              if details['defaultdep']:
                if groupdefault == None:
                  groupdefault = details['versionedactionid']
                else:
                  failnotice += "Error. Multiple defaults found: %s %s\n" % (groupdefault, details['versionedactionid'])
                  failure = True
              # specify that this action is part of a one only set and check if it is already included in the testset
              myset.add(details['versionedactionid'])
              options[i] = details['versionedactionid']
              self.myprint(str(i) + ") " + action + " : " + details['versionname'],False)
              if details['versionedactionid'] in versionedactioniddict:
                found = True
                versionedactioniddict[versionedactionid][details['versionedactionid']] = versionedactioniddict[details['versionedactionid']]
                self.myprint(" **selected** ")
              else:
                self.myprint("")
              i += 1
            # Print the input iff the group is empty or this is the last action of a named group
            # and a valid dependency has not yet been found
            while (group == "" or actioncount == len(deps[group])) and not found:
              if self.interactive:
                choice = self.input("Select a version:")
                if choice == None:
                  return None
                try:
                  versionedactioniddep = options[int(choice)]
                  if not versionedactioniddep in versionedactioniddict:
                    changed = True
                    depsmulti[versionedactioniddep] = self.ovtDB.getDependencies(versionedactioniddep)
                    versionedactioniddict[versionedactioniddep] = {}
                  found = True
                except:
                  self.myprint("Bad selection")
              else:
                # If the groupdefault logic has not found an error and there is a default
                if autoadd and not failure and groupdefault != None:
                  # Use the default
                  if not groupdefault in versionedactioniddict:
                    changed = True
                    depsmulti[groupdefault] = self.ovtDB.getDependencies(groupdefault)
                    versionedactioniddict[groupdefault] = {}
                else:
                  failnotice += "Error. One of the following must be specified:\n"
                  for my_id in options:
                    failnotice += str(self.ovtDB.getVersionedActionName(options[my_id])) + " "
                  failnotice += "\n"
                  failure = True
                found = True
             
            oneperset.append(myset)

            if group == "":
              myset = set()
          self.myprint("---")
    # verify that there is only one used vaid used per set
    keyset = set(versionedactioniddict.keys())
    for myset in oneperset:
      if len(myset) == 1:
        continue
      union = myset & keyset
      if len(union) > 1:
        failnotice += "Critical configuration error. Multiple solutions to a dependency group found, only one of the following allowed:\n"
        for vaid in union:
          failnotice += str(self.ovtDB.getVersionedActionName(vaid)) + " "
        failnotice += "\n"
        failure = True

    if failure:
      raise ImpossibleDependencyException(failnotice)
    return versionedactioniddict

  # Prints the entire testset including versions in a tree
  def printTestset(self, versionedactioniddict, results = {}, ids = False):
    # Firstly search the dictionary for all keys that are not referenced by any value dictionary
    toplevelvaids = []
    allrefs = []
    for vaid in versionedactioniddict:
      allrefs.extend(versionedactioniddict[vaid].keys())
    toplevelvaids = set(versionedactioniddict) - set(allrefs)
    # iterate over the top level versionactionids and print the dependencies
    for vaid in toplevelvaids:
      self.printSubTestset(versionedactioniddict, vaid, results=results, ids=ids)

  def printSubTestset(self, versionedactioniddict, vaid, indent = 0, results={}, ids = False):
    endextra = ""
    midextra = ""
    if vaid in results:
      endextra = ":"
      if results[vaid]['result'] == None:
        endextra += "NOT RUN"
      elif results[vaid]['result']:
        endextra += "PASS"
      else:
        endextra += "FAIL"
    if ids:
      midextra = magenta(str(vaid).ljust(7))
    print " "*indent + midextra+self.ovtDB.getFullVersionName(vaid)+endextra
    for vaid in versionedactioniddict[vaid]:
      self.printSubTestset(versionedactioniddict, vaid, indent+2, results=results, ids=ids)
