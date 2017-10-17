import pprint
import sys
import os
import getopt
import types
from OvertestExceptions import *
from LazyTransaction import *
try:
  import yaml
except ImportError:
  supports_yaml = False
else:
  supports_yaml = True


class ActionImporter:
  ovtDB = None

  def __init__(self, _ovtDB):
    self.ovtDB = _ovtDB
    self.verbose_analyse = False
    self.verbose_execute = False

  def verboseAnalyse(self, str):
    if self.verbose_analyse:
      print str

  def verboseExecute(self, str):
    if self.verbose_execute:
      print str

  def usage(self, exitcode, error = None):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Usage:"
    print "  --file=<filename>"
    print "  --debug=<debug-opts>"
    print "          a - analysis"
    print "          e - execution"
    sys.exit (exitcode)

  def importData(self, args):
    try:
      opts, args = getopt.getopt (args, "f:", ["file=", "debug="])
    except getopt.GetoptError, e:
      self.usage (2, str(e))

    file = None

    for (o, a) in opts:
      if o in ("-f", "--file"):
        file = a
      if o == "--debug":
        if 'a' in a:
          self.verbose_analyse = True
        if 'e' in a:
          self.verbose_execute = True

    if supports_yaml:

      if file == None:
        self.usage (2, "No file specified")

      yaml_in = yaml.load (open (file, "r"))

      yaml_in = self.annotateYAML(yaml_in)

      success = False
      try:
        while not success:
          try:
            self.ovtDB.setAutoCommit(False)
  
            # Read the YAML and DB and generate a work list
            work = self.createActionCategories (yaml_in, yaml_in)
  
            transaction = LazyTransaction (self.ovtDB, verbose_execute=self.verbose_execute)
            transaction.execute (work)
  
            self.ovtDB.FORCECOMMIT()
          except DatabaseRetryException, e:
            pass
          except Exception, e:
            # Cancel the transaction and re-raise
            self.ovtDB.FORCEROLLBACK()
            raise
          else:
            success = True
            self.ovtDB.setAutoCommit (True)
      except (InconsistentValueException, CannotCreateException, MissingVersionException), e:
        print e
        sys.exit(3)
    else:
      self.error ("--file requires YAML support but this was not available")
      sys.exit (4)

  def annotateYAML(self, yaml):
    """ Scatter placeholders throughout the tree """
    if isinstance(yaml, dict):
      yaml['_placeholder'] = Placeholder()
      for key, val in yaml.items():
        self.annotateYAML(val)
    elif isinstance(yaml, list):
      for val in yaml:
        self.annotateYAML(val)
    return yaml

  def obtainAllLocks(self, locks):
    self.ovtDB.LOCKACTIONS ([lock.id for lock in locks])

  def releaseAllLocks(self, locks):
    self.ovtDB.UNLOCKACTIONS ([lock.id for lock in locks])

  def createActionCategories(self, yaml, root_yaml):
    work = []
    for cat_name, cat in yaml.items():
      if cat_name == '_placeholder':
        continue
      cat_id = self.ovtDB.simple.getActionCategoryByName (cat_name)
      if cat_id != None:
        self.verboseAnalyse ("%s (%s)"%(cat_name, cat_id))
        work.extend (self.createActions (cat_id, cat, root_yaml))
      else:
        raise CannotCreateException ("Action Category - '%s'" % cat_name)

    return work

  def createActions(self, in_cat_id, yaml, root_yaml):
    work = []
    for act_name, act in yaml.items():
      if act_name == '_placeholder':
        continue
      act_name=str(act_name)
      act_id = self.ovtDB.simple.getActionByName (in_cat_id, act_name)
      if act_id != None:
        self.verboseAnalyse (" %s (%s)"%(act_name, act_id))
        work.append (ActionLocker(act_id))
        work.extend (self.createVersionedActions (act_id, act, root_yaml))
      else:
        raise CannotCreateException ("Action - '%s'" % act_name)
    return work

  def createVersionedActions(self, of_act_id, yaml, root_yaml):
    work = []
    for ver_name, ver in yaml.items():
      if ver_name == '_placeholder':
        continue
      ver_name=str(ver_name)
      ver_id = self.ovtDB.simple.getVersionedActionByName (of_act_id, ver_name)
      if ver_id != None:
        self.verboseAnalyse ("  %s (%s)"%(ver_name,ver_id))
        new_cfgopt_links, new_producers, \
          new_consumers, new_resource_links, lifecyclestate = self.createVersionedActionAttribs (ver_id, ver, root_yaml)
        work.extend (new_cfgopt_links)
        work.extend (new_producers)
        work.extend (new_consumers)
        work.extend (new_resource_links)
        if lifecyclestate != None:
          self.ovtDB.simple.setVersionedActionLifeCycleState (ver_id, lifecyclestate)
        ver['_placeholder'].id = ver_id
      else:
        self.verboseAnalyse ("  %s (new)"%ver_name)
        new_cfgopt_links, new_producers, \
          new_consumers, new_resource_links, lifecyclestate = self.createVersionedActionAttribs (ver['_placeholder'], ver, root_yaml)
        newversionedaction = LazyVersionedAction (ver['_placeholder'],
                                                  ver_name, of_act_id, new_cfgopt_links,
                                                  new_producers, new_consumers, new_resource_links, lifecyclestate)
        work.append(newversionedaction)
    return work

  def createVersionedActionAttribs(self, ver_id, yaml, root_yaml):
    self.verboseAnalyse ("   config ")
    cfgopt_links = self.createLinkToConfigOptions (ver_id, yaml['config'])
    self.verboseAnalyse ("   consumers ")
    consumers = self.createConsumerDependencies (ver_id, yaml['consumers'], root_yaml)
    self.verboseAnalyse ("   producers ")
    producers = self.createProducerDependencies (ver_id, yaml['producers'], root_yaml)
    self.verboseAnalyse ("   resources ")
    resource_links = []
    resource_links.extend (self.createLinkToResourceTypes (ver_id, yaml['resources']['require']))
    self.verboseAnalyse ("   status ")
    if 'status' in yaml:
      lifecyclestate = self.ovtDB.simple.getLifeCycleStateByName (yaml['status'])
      if not lifecyclestate:
        raise CannotCreateException ("Life cycle state - '%s'" % yaml['status'])
    else:
      lifecyclestate = None

    if lifecyclestate:
      self.verboseAnalyse ("    %s (%d)"%(yaml['status'],lifecyclestate))
    return cfgopt_links, producers, consumers, resource_links, lifecyclestate

  def createLinkToConfigOptions(self, from_ver_id, yaml):
    newlinks = []
    for cfggrp_name, cfggrp in yaml.items():
      if cfggrp_name == '_placeholder':
        continue
      cfggrp_name = str(cfggrp_name)
      cfggrp_id = self.ovtDB.simple.getConfigOptionGroupByName (cfggrp_name)
      assert cfggrp_id != None
      self.verboseAnalyse ("    %s (exists)"%cfggrp_name)
      for cfgopt_name, cfglookup in cfggrp.items():
        if cfgopt_name == '_placeholder':
          continue
        cfgopt_name = str(cfgopt_name)
        cfgopt_id = self.ovtDB.simple.getConfigOptionByName (cfggrp_id, cfgopt_name)
        if cfgopt_id != None:
          newlinks.extend (self.createLinkToConfigOption (from_ver_id, cfgopt_name, cfgopt_id))
          if type(cfglookup) == types.ListType:
            for cfgoptlookup_name in cfglookup:
              cfgoptlookup_name = str(cfgoptlookup_name)
              cfgoptlookup_id = self.ovtDB.simple.getConfigOptionLookupByName (cfgopt_id, cfgoptlookup_name)
              if cfgoptlookup_id != None:
                newlinks.extend (self.createLinkToConfigOptionLookup (from_ver_id, cfgoptlookup_name, cfgoptlookup_id))
              else:
                raise CannotCreateException ("Config Option Lookup - '%s':'%s'" % (cfgopt_name, cfgoptlookup_name))
        else:
          raise CannotCreateException ("Config Option - '%s'" % cfgopt_name)
    return newlinks

  def createLinkToConfigOption(self, from_ver_id, to_opt_name, to_opt_id):
    if not isinstance(from_ver_id, Placeholder):
      link_id = self.ovtDB.simple.getLinkVersionedActionToConfigOption (from_ver_id, to_opt_id)
    else:
      link_id = None

    if link_id != None:
      self.verboseAnalyse ("     %s (%d)"%(to_opt_name,link_id))
      return []
    else:
      self.verboseAnalyse ("     %s (new link)"%to_opt_name)
      newlink = LazyConfigOptionLink (from_ver_id,
                                      to_opt_id)
      return [newlink]

  def createLinkToConfigOptionLookup(self, from_ver_id, to_optlookup_name, to_optlookup_id):
    if not isinstance(from_ver_id, Placeholder):
      link_id = self.ovtDB.simple.getLinkVersionedActionToConfigOptionLookup (from_ver_id, to_optlookup_id)
    else:
      link_id = None

    if link_id != None:
      self.verboseAnalyse ("       %s (%d)"%(to_optlookup_name,link_id))
      return []
    else:
      self.verboseAnalyse ("       %s (new link)"%to_optlookup_name)
      newlink = LazyConfigOptionLookupLink (from_ver_id,
                                            to_optlookup_id)
      return [newlink]

  def createConsumerDependencies(self, producer_id, yaml, root_yaml):
    newdeps = []
    for depgrp_name, depdepgrp in yaml.items():
      if depgrp_name == '_placeholder':
        continue
      depgrp_name = str(depgrp_name)
      depgrp_id = self.ovtDB.simple.getDependencyGroupByName (depgrp_name)
      for depactgrp_name, depactgrp in depdepgrp.items():
        if depactgrp_name == '_placeholder':
          continue
        depactgrp_name = str(depactgrp_name)
        depactgrp_id = self.ovtDB.simple.getActionCategoryByName (depactgrp_name)
        for depact_name, depact in depactgrp.items():
          if depact_name == '_placeholder':
            continue
          depact_name = str(depact_name)
          depact_id = self.ovtDB.simple.getActionByName (depactgrp_id, depact_name)
          for depver_name, depver in depact.items():
            if depver_name == '_placeholder':
              continue
            depver_name = str(depver_name)
            self.verboseAnalyse ("     %s %s"%(depact_name, depver_name))
            depver_id = self.ovtDB.simple.getVersionedActionByName (depact_id, depver_name)
            if depver_id == None:
              # The intention here is to use the placeholder associated with the full
              # description of the new version. There is another placeholder in the 
              # consumer area of the description but that is irrelevant as it represents
              # the dependency rather than the versioned action itself
              if not depactgrp_name in root_yaml \
                 or not depact_name in root_yaml[depactgrp_name] \
                 or not depver_name in root_yaml[depactgrp_name][depact_name]:
                   raise MissingVersionException("No details found for new version %s:%s:%s" % (depactgrp_name,depact_name,depver_name))
              depver_id = root_yaml[depactgrp_name][depact_name][depver_name]['_placeholder']
            newdeps.extend (self.createConsumerDependency (producer_id, depver_id, depgrp_id, depver))
    return newdeps

  def createProducerDependencies(self, consumer_id, yaml, root_yaml):
    newdeps = []
    for depgrp_name, depdepgrp in yaml.items():
      if depgrp_name == '_placeholder':
        continue
      depgrp_name = str(depgrp_name)
      depgrp_id = self.ovtDB.simple.getDependencyGroupByName (depgrp_name)
      for depactgrp_name, depactgrp in depdepgrp.items():
        if depactgrp_name == '_placeholder':
          continue
        depactgrp_name = str(depactgrp_name)
        depactgrp_id = self.ovtDB.simple.getActionCategoryByName (depactgrp_name)
        for depact_name, depact in depactgrp.items():
          if depact_name == '_placeholder':
            continue
          depact_name = str(depact_name)
          depact_id = self.ovtDB.simple.getActionByName (depactgrp_id, depact_name)
          for depver_name, depver in depact.items():
            if depver_name == '_placeholder':
              continue
            depver_name = str(depver_name)
            self.verboseAnalyse ("     %s %s"%(depact_name, depver_name))
            depver_id = self.ovtDB.simple.getVersionedActionByName (depact_id, depver_name)
            if depver_id == None:
              # The intention here is to use the placeholder associated with the full
              # description of the new version. There is another placeholder in the 
              # producer area of the description but that is irrelevant as it represents
              # the dependency rather than the versioned action itself
              if not depactgrp_name in root_yaml \
                 or not depact_name in root_yaml[depactgrp_name] \
                 or not depver_name in root_yaml[depactgrp_name][depact_name]:
                   raise MissingVersionException("No details found for new version %s:%s:%s" % (depactgrp_name,depact_name,depver_name))
              depver_id = root_yaml[depactgrp_name][depact_name][depver_name]['_placeholder']
            newdeps.extend (self.createProducerDependency (consumer_id, depver_id, depgrp_id, depver))
    return newdeps

  def createConsumerDependency(self, producer_id, consumer_id, depgrp_id, yaml):
    if not (isinstance(producer_id, Placeholder) or isinstance(consumer_id, Placeholder)):
      dep_id = self.ovtDB.simple.getLinkConsumerDependency (producer_id, consumer_id)
    else:
      dep_id = None
    newdeps = self.createDependency (dep_id, producer_id, consumer_id, depgrp_id, yaml)
    return newdeps

  def createProducerDependency(self, consumer_id, producer_id, depgrp_id, yaml):
    if not (isinstance(producer_id, Placeholder) or isinstance(consumer_id, Placeholder)):
      dep_id = self.ovtDB.simple.getLinkProducerDependency (consumer_id, producer_id)
    else:
      dep_id = None
    # NOTE the swapped from/to
    newdeps = self.createDependency (dep_id, producer_id, consumer_id, depgrp_id, yaml)
    return newdeps

  def createDependency(self, dep_id, producer_id, consumer_id, depgrp_id, yaml):
    if dep_id != None:
      db_depattrs = self.ovtDB.simple.getDependencyAttributesById (dep_id)
      assert db_depattrs != None
      db_depattrs = dict(db_depattrs)
      assert 'hostmatch'   in db_depattrs
      assert 'versiononly' in db_depattrs
      assert 'defaultdep'  in db_depattrs
      assert 'dependencygroupid'  in db_depattrs
      if yaml['host match'] != db_depattrs['hostmatch']:
        raise InconsistentValueException ('host match')
      if yaml['version only'] != db_depattrs['versiononly']:
        raise InconsistentValueException ('version only')
      if 'default dep' in yaml:
        if yaml['default dep'] != db_depattrs['defaultdep']:
          raise InconsistentValueException ('default dep')
      if depgrp_id != db_depattrs['dependencygroupid']:
        raise InconsistentValueException ('dependency group')
      self.verboseAnalyse ("      exists %d"%(dep_id))
      return []
    else:
      self.verboseAnalyse ("      new %s"%yaml)
      newdep = LazyDependency(producer_id,
                              consumer_id,
                              depgroup=depgrp_id,
                              hostmatch=yaml['host match']     if 'host match'   in yaml else None,
                              versiononly=yaml['version only'] if 'version only' in yaml else None,
                              defaultdep=yaml['default dep']   if 'default dep'  in yaml else None,
                              )
      return [newdep]

  def createLinkToResourceTypes(self, ver_id, yaml):
    work = []
    for restype_name, restype in yaml.items():
      if restype_name == '_placeholder':
        continue
      restype_name = str(restype_name)
      restype_id = self.ovtDB.simple.getResourceTypeByName (restype_name)
      if restype_id != None:
        self.verboseAnalyse ("  %s (%s)"%(restype_name, restype_id))
        work.extend (self.createLinkToAttributes (ver_id, restype_id, restype))
      else:
        raise CannotCreateException ("resource type - '%s'" % restype_name)
    return work

  def createLinkToAttributes(self, ver_id, type, yaml):
    work = []
    for attr_name, attr in yaml.items():
      if attr_name == '_placeholder':
        continue
      attr_name = str(attr_name)
      attr_id = self.ovtDB.simple.getAttributeByName (type, attr_name)
      if attr_id != None:
        self.verboseAnalyse ("   %s (%s)"%(attr_name, attr_id))
        work.extend (self.createLinkToAttributeValue (ver_id, attr_id, attr))
      else:
        raise CannotCreateException ("attribute - '%s'" % attr_name)
    return work

  def createLinkToAttributeValue(self, ver_id, attr_id, yaml):
    work = []
    for attrval_name in yaml:
      if attrval_name == '_placeholder':
        continue
      attrval_name = str(attrval_name)
      attrval_id = self.ovtDB.simple.getAttributeValueByName (attr_id, attrval_name)
      if attrval_id != None:
        self.verboseAnalyse ("    %s (%s)"%(attrval_name, attrval_id))
        if not isinstance (ver_id, Placeholder):
          lnkattrval_id = self.ovtDB.simple.getLinkVersionedActionToAttributeValue (ver_id, attrval_id)
        else:
          lnkattrval_id = None

        if lnkattrval_id != None:
          self.verboseAnalyse ("     Linked")
        else:
          self.verboseAnalyse ("     Not linked")
          work.append (LazyAttributeValueLink (ver_id, attrval_id))
      else:
        raise CannotCreateException ("link to attribute value - '%s'" % attrval_name)
    return work

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s"%error
