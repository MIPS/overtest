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
from Interactive import Interactive
from utils.TerminalUtilities import *

class ResourceControl(Interactive):

  def __init__(self, _ovtDB):
    Interactive.__init__(self, _ovtDB)
    self.config['attributes']['addextra'] = self.addAttributeExtra

  def run(self, args):
    if len(args) >= 3:
      if args[0] == "-e" and args[1] == "-t":
        resourcetypeid = self.ovtDB.getResourceTypeByName(args[2])
        if resourcetypeid != None:
          exec("from resources.R%d import R%d"%(resourcetypeid,resourcetypeid))
          exec("res = R%d(self.ovtDB)" % (resourcetypeid))
          args.pop(0)
          args.pop(0)
          args.pop(0)
          return res.interactiveUpdate(args)
      elif args[0] == "-q" and args[1] == "-t":
        resourcetypeid = self.ovtDB.getResourceTypeByName(args[2])
        if resourcetypeid != None:
          exec("from resources.R%d import R%d"%(resourcetypeid,resourcetypeid))
          exec("res = R%d(self.ovtDB)" % (resourcetypeid))
          args.pop(0)
          args.pop(0)
          args.pop(0)
          return res.query(args)

    exit = False
    try:
      while not exit:
        print " Resource Configuration Console ".center(80, "-")
        print "Options:"
        print magenta("1")+") View resource types"
        print magenta("2")+") Add resource type"
        print magenta("3")+") Edit resource type"
        print magenta("0")+") Exit"
        choice = self.selectItem("Option", range(0,4))
        if choice == 0:
          exit = True
        elif choice == 1:
          self.config['resourcetypes']['showids'] = ["Resource Type"]
          self.viewItems('resourcetypes')
        elif choice == 2:
          self.addItem('resourcetypes')
        elif choice == 3:
          self.editResourceType()
    except (EOFError, KeyboardInterrupt):
      print ""
    return 0

  def editResource(self, resourcetypeid):
    self.config['resources']['showids'] = ["Resource"]
    self.config['resources']['resourcetypeid'] = resourcetypeid
    resources = self.viewItems('resources', True)
    del self.config['resources']['resourcetypeid'] 
    resourceid = self.selectItem("Resource", resources[0])
    if resourceid == 0:
      print "No selection"
      return
    exit = False

    try:
      while not exit:
        statuschange = None
        maxoption = 7
        print " Edit Resource ".center(80, "-")
        print "\nEditing Resource:"
        self.config['resources']['showids'] = ["Resource Attribute"]
        self.printItem('resources', resources[0][resourceid])
        print "\n"+magenta("1")+") Change name"
        print magenta("2")+") Change concurrency"
        print magenta("3")+") Change hostname"
        print magenta("4")+") Modify resource links"
        print magenta("5")+") Specify attribute value"
        print magenta("6")+") Clear attribute value"
        status = self.ovtDB.getResourceStatus(resourceid)
        if status == "OK":
          print magenta("7")+") Disable resource"
          statuschange = "disable"
          maxoption = 8
        elif status == "DISABLED":
          print magenta("7")+") Enable resource"
          statuschange = "enable"
          maxoption = 8
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0,maxoption))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            newname = raw_input("New name: ")
            if newname != "":
              self.ovtDB.simple.setResourceName(resourceid, newname)
          elif choice == 2:
            newconcurrency = int(raw_input("New concurrency: "))
            self.ovtDB.simple.setResourceConcurrency(resourceid, newconcurrency)
          elif choice == 3:
            newhostname = raw_input("New hostname: ")
            if newhostname == "":
              newhostname = None
            self.ovtDB.simple.setResourceHostname(resourceid, newhostname)
          elif choice == 4:
            self.modifyResourceLinks(resources[0][resourceid])
          elif choice == 5:
            self.specifyAttribute(resourcetypeid, resourceid)
          elif choice == 6:
            resourceattributeid = int(raw_input("Attribute value to clear: "))
            self.ovtDB.clearResourceAttribute(resourceid, resourceattributeid)
          elif choice == 7:
            if statuschange == "enable":
              self.ovtDB.setResourceStatus(resourceid, "OK")
            elif statuschange == "disable":
              self.ovtDB.setResourceStatus(resourceid, "DISABLED")
  
          resources = self.ovtDB.getResources(self.config['resources'], resourceid)
        except (ValueError):
          print "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""

  def specifyAttribute(self, resourcetypeid, resourceid):
    print " Specify Attribute ".center(80, "-")
    self.config['resourcetypes']['showids'] = ["Attribute"]
    self.config['resourcetypes']['resourcetypeid'] = resourcetypeid
    resourcetypes = self.viewItems('resourcetypes')
    del self.config['resourcetypes']['resourcetypeid']
    attributeids = {}
    for resourcetypeid in resourcetypes[0]:
      for attributeid in resourcetypes[0][resourcetypeid]['related'][0]:
        attributeids[attributeid] = resourcetypeid
    choice = self.selectItem("Attribute", attributeids)
    if choice == 0:
      return
    attributes = self.ovtDB.getAttributes({"resourcetypeid":attributeids[choice]})
    if "related" in attributes[0][choice]:
      self.config['attributes']['showids'] = ["Attribute Value"]
      self.printItem('attributes', attributes[0][choice])
      valueid = self.selectItem("Value", attributes[0][choice]['related'][0])
      if valueid == 0:
        return
      self.ovtDB.specifyAttribute(resourceid, choice, valueid)
    else:
      try:
        value = raw_input("Attribute Value: ")
        if value == "":
          return
        self.ovtDB.specifyAttribute(resourceid, choice, value)
      except (ValueError):
        print "Invalid value"
 
  def modifyResourceLinks(self, resource):
    print " Modify Resource Links ".center(80, "-")
    exit = False
    try:
      while not exit:
        print "Modify resource links for: " +resource['data']
        resourcelinks = self.ovtDB.getResourceLinks(resource['id'])
        linkresourceids = []
        if len(resourcelinks) == 0:
          print "There are no linked resources"
        else:
          for res in resourcelinks:
            print str(res['resourceid']).ljust(6, " ") + res['resourcename']
            linkresourceids.append(res['resourceid'])
        print "\n"+magenta("1")+") Add link"
        print magenta("2")+") Remove link"
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0,3))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            self.config['resources']['showids'] = ["Resource"]
            resources = self.viewItems('resources', True)
            choice = self.selectItem("Resource to add", resources[0])
            if choice == 0:
              print "No selection"
              continue
            else:
              self.ovtDB.addResourceLink(resource['id'], choice)
          elif choice == 2:
            choice = self.selectItem("Resource to remove", linkresourceids)
            if choice == 0:
              print "No selection"
              continue
            else:
              self.ovtDB.removeResourceLink(resource['id'], choice)
  
        except (ValueError):
          print "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""
 
  def editResourceType(self):
    self.config['resourcetypes']['showids'] = ["Resource Type"]
    resourcetypes = self.viewItems('resourcetypes', True)
    resourcetypeid = self.selectItem("Resource Type", resourcetypes[0])
    if resourcetypeid == 0:
      print "No selection"
      return
    exit = False
    try:
      while not exit:
        print " Edit Resource Type ".center(80, "-")
        print "\nEditing Resource Type:"
        self.config['resourcetypes']['showids'] = ["Attribute"]
        self.printItem('resourcetypes', resourcetypes[0][resourcetypeid])
        print "\n"+magenta("1")+") Change name"
        print magenta("2")+") View Attributes"
        print magenta("3")+") Add Attribute"
        print magenta("4")+") Edit Attribute"
        print magenta("5")+") View resources"
        print magenta("6")+") Add resource"
        print magenta("7")+") Edit resource"
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0,8))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            newname = raw_input("New name: ")
            if newname != "":
              self.ovtDB.simple.setResourceTypeName(resourcetypeid, newname)
          elif choice == 2:
            self.config['attributes']['resourcetypeid'] = resourcetypeid
            self.config['attributes']['showids'] = "Attribute"
            self.viewItems('attributes')
          elif choice == 3:
            self.addItem('attributes', {'resourcetypeid':resourcetypeid})
          elif choice == 4:
            self.editAttribute(resourcetypeid)
          elif choice == 5:
            self.config['resources']['showids'] = ["Resource"]
            self.config['resources']['resourcetypeid'] = resourcetypeid
            self.viewItems('resources')
            del self.config['resources']['resourcetypeid']
          elif choice == 6:
            self.addItem('resources', {'resourcetypeid':resourcetypeid})
          elif choice == 7:
            self.editResource(resourcetypeid)
  
          resourcetypes = self.ovtDB.getResourceTypes(self.config['resourcetypes'])
        except (ValueError):
          print "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""

  def addAttributeExtra(self, values):
    lookup = raw_input("Is lookup? (y/n) ")
    islookup = False
    if self.checkForYes(lookup):
      islookup = True
    values['islookup'] = islookup
    return True
                          

  def editAttribute(self, resourcetypeid):
    self.config['attributes']['showids'] = ['Attribute']
    self.config['attributes']['resourcetypeid'] = resourcetypeid
    attributes = self.viewItems('attributes', True)
    del self.config['attributes']['resourcetypeid']
    attributeid = self.selectItem("Attribute", attributes[0])
    if attributeid == 0:
      print "No selection"
      return
    exit = False
    try:
      while not exit:
        print " Edit Attribute ".center(80, "-")
        print "\nEditing Attribute:"
        self.config['attributes']['showids'] = ['Attribute Value']
        self.printItem('attributes', attributes[0][attributeid])
        print "\n"+magenta("1")+") Change name"
        choicecount = 1 
        if "related" in attributes[0][attributeid]:
          print magenta("2")+") Add value"
          choicecount = 2
        print magenta("0")+") Exit"
        try:
          choice = self.selectItem("Option", range(0, choicecount+1))
  
          if choice == 0:
            exit = True
          elif choice == 1:
            newname = raw_input("New name: ")
            if newname != "":
              self.ovtDB.simple.setAttributeName(attributeid, newname)
          elif choice == 2:
            self.addAttributeValue(attributeid)

          if choice != 0:
            self.config['attributes']['resourcetypeid'] = resourcetypeid
            attributes = self.ovtDB.getAttributes(self.config['attributes'])
            del self.config['attributes']['resourcetypeid']
        except (ValueError):
          print "Invalid selection"
          continue
    except (EOFError, KeyboardInterrupt):
      print ""
 
  def addAttributeValue(self, attributeid):
    print " Add value ".center(80, "-")
    value = raw_input("Value: ")
    if value != "":
      neednotrequest = raw_input("Should a resource with this value be allocated without requesting this value? ([yes], no) ")
      mustrequest = (neednotrequest == "no")

      self.ovtDB.addAttributeValue(attributeid, value, mustrequest)
    else:
      print "No name supplied"


