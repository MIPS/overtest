#  Copyright (C) 2012-2020 MIPS Tech LLC
#  Written by Matthew Fortune <matthew.fortune@imgtec.com> and
#  Daniel Sanders <daniel.sanders@imgtec.com>
#  This file is part of Overtest.
#
#  Overtest is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3, or (at your option)
#  any later version.
#
#  Overtest is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with overtest; see the file COPYING.  If not, write to the Free
#  Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
#  02110-1301, USA.
import sys
import os
import getopt
from utils.Utilities import versionCompare
from OvertestExceptions import *
try:
  import yaml
except ImportError:
  supports_yaml = False
else:
  supports_yaml = True

class UnableToUpdateException(Exception):
  def __init__(self, message):
    self.value = message

  def __str__(self):
    return "Unable to Update Error: "+self.value

class ActionExporter:
  ovtDB = None

  """
  This dictionary defines the possible diagnostics.
  Options are automatically defined and added to the usage message.
  Of course, you still need to write code to emit the diagnostic and obey the severity level
  """
  diagnostics = { 'missing-versions'   : 'Diagnose when a matched action contains no matching versions',
                  'missing-actions'    : 'Diagnose when a matched category contains no matching actions',
                  'missing-categories' : 'Diagnose when the filter contains no matching categories',
                }

  def __init__(self, _ovtDB):
    self.ovtDB = _ovtDB
    self.debug_enabled = False

  def usage(self, exitcode, error = None):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Usage:"
    print "  --category=<filter>  Define the category filter (default: '%')"
    print "  --action=<filter>    Define the action filter (default: '%')"
    print "  --version=<filter>   Define the version filter (default: '%')"
    print "  --update             Specify new versions to transform the exported data"
    print "  --import             Immediately import the transformed data, requires --update"
    print "  --file=<filename>    Dump the output to a file"
    for k,v in ActionExporter.diagnostics.items():
      print "  --W%s=<severity>\t%s (default: silent)"%(k, v)
    print ""
    print "<filter> may contain % characters which match any character sequence"
    print "<severity> may be 'silent' or 'error'"
    sys.exit (exitcode)

  def exportData(self, args):
    error_if = dict([(k, False) for k in ActionExporter.diagnostics.keys()])
    diagnostic_opts     = dict([ ("--W%s"%k, k) for k in error_if.keys() ])
    diagnostic_opts_def = [ "W%s="%k  for k in error_if.keys() ]

    try:
      opts, args = getopt.getopt (args, "c:a:v:f:ui", ["category=", "action=", "version=", "file=", "update", "import"] + diagnostic_opts_def)
    except getopt.GetoptError, e:
      self.usage (2, str(e))

    cur_category = None
    cur_action = None
    immediate_import = False
    filter = {}
    self.update = {}
    current = filter
    outfile = sys.stdout

    if not supports_yaml:
      self.error ("This requires YAML support but this was not available")
      sys.exit (4)

    for (o, a) in opts:
      if o in diagnostic_opts.keys():
        if a == "error":
          error_if[diagnostic_opts[o]] = True
        elif a == "silent":
          error_if[diagnostic_opts[o]] = False
        else:
          self.usage ("'%s' is not a known diagnostic type" % a)
      elif o in ("-c", "--category"):
        if not a in current:
          current[a] = {}
        cur_category = a
        cur_action = None
      elif o in ("-a", "--action"):
        if cur_category == None:
          current['%'] = {}
          cur_category = '%'

        if not a in current[cur_category]:
          current[cur_category][a] = []
        cur_action = a
      elif o in ("-v", "--version"):
        if cur_action == None:
          current[cur_category]['%'] = []
          cur_action = '%'

        if not a in current[cur_category][cur_action]:
          current[cur_category][cur_action].append (a)
      elif o in ("-i", "--import"):
        immediate_import = True
      elif o in ("-u", "--update"):
        current = self.update
        cur_category = None
        cur_action = None
      elif o in ("-f", "--file"):
        try:
          outfile = open(a, "w")
        except IOError, e:
          self.error ("Unable to open %s because %s" % (a, e))
          sys.exit(5)

    # Ensure import is only specified for updated exports
    if immediate_import and len(self.update) == 0:
      self.usage(2, "Import option requires at least one update")

    if immediate_import:
      self.usage(2, "Import not yet supported")

    # Fill in wildcards for incomplete definitions
    for category_filter in filter.values():
      if len(category_filter) == 0:
        category_filter['%'] = []
      for action_filter in category_filter.keys():
        if len(category_filter[action_filter]) == 0:
          category_filter[action_filter] = ['%']

    # Perform error checking on the update definition.
    # The only wildcard supported is in the category definition
    # Only one new version can be specified for any action
    for category in self.update:
      if len(self.update[category]) == 0:
        self.usage(2, "Update category '%s' specified without any actions" % category)
      for action in self.update[category]:
        if len(self.update[category][action]) == 0:
          self.usage(2, "Update action '%s:%s' specified without any versions" % (category, action))
        if "%" in action:
          self.usage(2, "Wildcard actions not permitted for update")
        if len(self.update[category][action]) != 1:
          self.usage(2, "Update action '%s:%s' specified with multiple versions" % (category, action))
        if "%" in self.update[category][action][0]:
          self.usage(2, "Wildcard versions not permitted for update")

        # Change the version list to a dictionary to record whether the update has happened or not
        # Updates are classed as changes to explicitly exported actions in this context.
        # They do not have to happen in this way but if they do, they can only happen once.
        # The second use for an update is to modify the dependencies of the exported actions
        self.update[category][action] = {'version':self.update[category][action][0], 'updated':False}

    # Must have something to dump
    if len(filter) == 0:
      self.usage(2, "At least one filter must be specified")

    # Store the output as a class member so that any function can inspect the current state
    self.yaml_out = {}

    # Take each category to dump in turn
    for category_filter, actions in filter.items():
      self.debug ("%s"%category_filter)

      # For error checking ensure that each filter finds at least one category
      found_any_cat_in_this_filter = False

      # Search permitting wildcards '%'
      cats = self.ovtDB.simple.getActionCategoryByWildcard (category_filter)

      # Process all the categories found and search for the actions in the filter
      if cats != None:
        for cat_name, cat_id in cats:
          # Strip the unicode for YAML purposes
          cat_name = str(cat_name)

          # Found a category
          found_any_cat_in_this_filter = True

          # Put the category in the YAML output
          if not cat_name in self.yaml_out:
            self.yaml_out[cat_name] = {}

          # Take each action to dump in turn
          for action_filter, versions in actions.items():
            self.debug ("%s/%s"%(cat_id, action_filter))

            # For error checking ensure that each filter finds at least one action
            found_any_act_in_this_cat = False

            # Search permitting wildcards '%'
            acts = self.ovtDB.simple.getActionByWildcard (cat_id, action_filter)

            # Process all the actions found and search for the versions in the filter
            if acts != None:
              for act_name, act_id in acts:
                # Strip the unicode for YAML purposes
                act_name = str(act_name)

                # Found an action
                found_any_act_in_this_cat = True

                # Put the action in the YAML output
                if not act_name in self.yaml_out[cat_name]:
                  self.yaml_out[cat_name][act_name] = {}

                # Take each version to dump in turn
                for version_filter in versions:
                  self.debug ("%s/%s/%s"%(cat_id, act_id, version_filter))

                  # For error checking ensure that each filter finds at least one version
                  found_any_ver_in_this_act = False

                  # Search permitting wildcards '%'
                  vers = self.ovtDB.simple.getVersionedActionByWildcard (act_id, version_filter)

                  # Process all the versions found
                  if vers != None:
                    for ver_name, ver_id in vers:
                      # Strip the unicode for YAML purposes
                      ver_name = str(ver_name)

                      # Found a version
                      found_any_ver_in_this_act = True

                      self.debug ("%s/%s/%s"%(cat_id, act_id, ver_id))

                      # Before exporting the version check if this action is set to be updated
                      # If it is then we must ensure that only one version of this action is
                      # being exported otherwise it may lead to unexpected behavior
                      update_version = None
                      if cat_name in self.update and act_name in self.update[cat_name]:
                        update_version = self.update[cat_name][act_name]
                      if update_version == None and "%" in self.update and act_name in self.update["%"]:
                        update_version = self.update["%"][act_name]

                      if update_version != None:
                        # The action is marked as update
                        # Check if it has already been updated
                        if update_version['updated']:
                          self.error ("Update of %s/%s failed due to multiple versions being exported" % (cat_name, act_name))
                          sys.exit(1)
                        # The action has now been updated
                        update_version['updated'] = True
                        # The version being exported is now the updated version
                        ver_name = update_version['version']
                        # No check is made to see if the version being updated/added already exists
                        # this should be safe as it will just mean that its description is updated
                        # with any extra information from the version that is being exported

                      # Put the version in the YAML output
                      yaml_out_ver_data = {}
                      self.yaml_out[cat_name][act_name][ver_name] = yaml_out_ver_data

                      # extract all info on the specified version
                      self.processVersion (ver_id, yaml_out_ver_data) 

                  # Perform optional error checking
                  if not found_any_ver_in_this_act and error_if['missing-versions']:
                    self.error ("No versions of %s/%s matched %s" % (cat_name, act_name, version_filter))
                    sys.exit(1)
            else:
              # No action implies no version
              if error_if['missing-versions']:
                self.error ("Cannot find versions in non-existant action %s/%s" % (cat_name, action_filter))
                sys.exit(1)

            if not found_any_act_in_this_cat and error_if['missing-actions']:
              self.error ("No actions in %s matched %s" % (cat_name, action_filter))
              sys.exit(1)

      else:
        # No cat implies no action or version
        if error_if['missing-actions']:
          self.error ("Cannot find actions in non-existant category %s" % (category_filter))
          sys.exit(1)
        elif error_if['missing-versions']:
          self.error ("Cannot find versions in non-existant category %s" % (category_filter))
          sys.exit(1)

      if not found_any_cat_in_this_filter and error_if['missing-categories']:
        self.error ("No actions in %s matched %s" % (cat_name, category_filter))
        sys.exit(1)

    for cat in self.yaml_out.keys():
      self.yaml_out[cat] = dict ( [(k, v) for k, v in self.yaml_out[cat].items() if len(v) > 0] )
    self.yaml_out = dict ( [(k, v) for k, v in self.yaml_out.items() if len(v) > 0] )

    yaml.dump (self.yaml_out, outfile, default_flow_style = False, explicit_start = True)
    if self.yaml_out:
      return 0
    else:
      return 1

  def processVersion(self, ver_id, yaml_out_ver_data):
    """
    Extract all the information about ver_id and dump it to yaml_out_ver_data
    """

    lifecyclestate        = self.ovtDB.simple.getVersionedActionLifeCycleState (ver_id)
    lifecyclestate        = self.ovtDB.simple.getLifeCycleStateNameById (lifecyclestate)
    pdepgrps, pdepgrp_ids = self.ovtDB.getVersionedActionDependencies(ver_id, "Producer")
    cdepgrps, cdepgrp_ids = self.ovtDB.getVersionedActionDependencies(ver_id, "Consumer")
    cfgs, cfg_ids         = self.ovtDB.getVersionedActionConfig(ver_id)
    ress, res_ids         = self.ovtDB.getResourceRequirements(ver_id)
  
    yaml_out_ver_data['producers'] = self.dependencyGroupToYAML (pdepgrp_ids, pdepgrps, self.update)
    yaml_out_ver_data['consumers'] = self.dependencyGroupToYAML (cdepgrp_ids, cdepgrps, self.update)
    yaml_out_ver_data['config']    = self.configGroupToYAML (cfg_ids, cfgs)
    yaml_out_ver_data['resources'] = { 'require' : self.resourcesGroupToYAML (res_ids, ress) }
    yaml_out_ver_data['status']    = str(lifecyclestate)

  def resourcesGroupToYAML(self, ids, data):
    r = {}
    for id in ids:
      assert data[id]['type'] == 'Resource Type'
      subdata, subids = data[id]['related']
      r[str(data[id]['data'])] = self.resourceToYAML (subids, subdata)
    return r

  def resourceToYAML(self, ids, data):
    r = {}
    for id in ids:
      assert data[id]['type'] == 'Attribute'
      subdata, subids = data[id]['related']
      r[str(data[id]['data'])] = self.attributeToYAML (subids, subdata)
    return r

  def attributeToYAML(self, ids, data):
    r = []
    for id in ids:
      assert data[id]['type'] == 'Attribute Value'
      r.append (str(data[id]['data']))
    return r

  def configGroupToYAML(self, ids, data):
    r = {}
    for id in ids:
      assert data[id]['type'] == 'Config Option Group'
      subdata, subids = data[id]['related']
      r[str(data[id]['data'])] = self.configToYAML (subids, subdata)
    return r

  def configToYAML(self, ids, data):
    r = {}
    for id in ids:
      assert data[id]['type'] == 'Config Option'
      if 'related' in data[id]:
        subdata, subids = data[id]['related']
        r[str(data[id]['data'])] = self.configLookupToYAML (subids, subdata)
      else:
        r[str(data[id]['data'])] = None
    return r

  def configLookupToYAML(self, ids, data):
    r = []
    for id in ids:
      assert data[id]['type'] == 'Config Option Lookup'
      r.append(str(data[id]['data']))
    return r

  def dependencyGroupToYAML(self, ids, data, update):
    r = {}
    for id in ids:
      assert data[id]['type'] == 'Dependency Group'
      subdata, subids = data[id]['related']
      r[str(data[id]['data'])] = self.dependenciesToYAML (subids, subdata, update)
    return r

  def dependenciesToYAML(self, ids, data, update):
    r = {}
    for id in ids:
      assert data[id]['type'] == 'Action Category'
      subdata, subids = data[id]['related']
      subupdate = {}
      if data[id]['data'] in update:
        subupdate = update[data[id]['data']]
      elif "%" in update:
        subupdate = update["%"]
      if data[id]['visible']:
        r[str(data[id]['data'])] = self.dependencyActionsToYAML (subids, subdata, subupdate, str(data[id]['data']))
    return r

  def dependencyActionsToYAML(self, ids, data, update, category):
    r = {}
    for id in ids:
      assert data[id]['type'] == 'Action'
      subdata, subids = data[id]['related']
      subupdate = None
      if data[id]['data'] in update:
        subupdate = update[data[id]['data']]
      if data[id]['visible']:
        r[str(data[id]['data'])] = self.dependencyVersionsToYAML (subids, subdata, subupdate, category, str(data[id]['data']), id)
    return r

  def dependencyVersionsToYAML(self, ids, data, update, category, action, actionid):
    """
    Convert versions to YAML but take in to account any pending updates
    Updates will result in the specified versions being included and no others, those
    that do not already exist will get attributes from the closest matching existing
    version
    """
    r = {}
    # Updates override existing versions, all versions must have an existing dependency to
    # copy attributes from so use a dictionary
    newversions = {}
    if update != None:
      newversions[str(update['version'])] = None

    for id in ids:
      assert data[id]['type'] == 'Dependency'
      if not data[id]['visible']:
        continue
      if update == None:
        newversions[str(data[id]['data'])] = id
      else:
        # The aim here is to find the closest version that is lower than the new one
        # This only searches the versions which were already linked via a dependency
        # not all available versions in the database. This feels correct as the existing
        # version is supposed to be a template so the linked components should also
        # be considered templates
        for version in newversions:
          try:
            if versionCompare(str(data[id]['data']).split("."),
                              version.split(".")) <= 0:
              if newversions[version] == None:
                newversions[version] = id
              elif versionCompare(str(data[newversions[version]]['data']).split("."),
                                  str(data[id]['data']).split(".")) < 0:
                newversions[version] = id
          except ValueError:
            # When confronted by a non-numeric version refuse to acknowledge it unless it
            # is a perfect match
            if version == str(data[id]['data']):
              newversions[version] = id

    for version in newversions:
      # Ensure that an existing version was found
      if newversions[version] == None:
        raise UnableToUpdateException("Can't find version close to %s"%version)

      # Copy the attributes
      r[version] = { 'host match'   : data[newversions[version]]['hostmatch'],
                     'version only' : data[newversions[version]]['versiononly']}

      # Any versions which were not found need to be dumped too
      if version != data[newversions[version]]['data']:
        # If the version is already in the database it need not be dumped as it
        # does not need creating. The dependency will be created by the referencing
        # versionedaction
        vers = self.ovtDB.simple.getVersionedActionByWildcard (actionid, version)
        if vers == None or len(vers) != 1:
          # Add to the new filter if it has not already been dumped
          if not category in self.yaml_out \
             or not action in self.yaml_out[category] \
             or not version in self.yaml_out[category][action]:
            # Create the category if it doesn't exist
            if not category in self.yaml_out:
              self.yaml_out[category] = {}
            # Create the action if it doesn't exist
            if not action in self.yaml_out[category]:
              self.yaml_out[category][action] = {}
  
            # Put the version in the YAML output
            yaml_out_ver_data = {}
            self.yaml_out[category][action][version] = yaml_out_ver_data
  
            vaid = data[newversions[version]]['versionedactionid']
            self.processVersion(vaid, yaml_out_ver_data) 

    return r

  def debug(self, debug):
    """
    Print an debug message
    """
    if self.debug_enabled:
      print "DEBUG: %s"%debug

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s"%error

