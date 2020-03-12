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
"""
Module for processing history and sending notifications to users
"""

import sys
from OvertestExceptions import formatExceptionInfo, ResultSubmissionException
from LogManager import LogManager
from TestManager import Testrun
from utils import Growl, Email
from socket import gaierror

# ------------------------------------------------------------------------------
# class NotificationDaemon
# ------------------------------------------------------------------------------

class NotificationDaemon:
  """
  Sends notifications to users using e-mail or growl
  """

  MAIL_HOST = "HHCAA01.hh.imgtec.org"
  MAIL_PORT = 25
  MAIL_POSTMASTER = "matthew.fortune@imgtec.com"
  MAIL_FROM_ADDR = "overtest@imgtec.com"

  def __init__(self, ovtDB):
    self.ovtDB = ovtDB
    self.log = LogManager("notification_daemon", True)
    self.ovtDB.registerLog(self.log)

  def run(self):
    """
    Main function
    """
    mailer = Email.Mailer(NotificationDaemon.MAIL_HOST,
                          NotificationDaemon.MAIL_PORT,
                          NotificationDaemon.MAIL_POSTMASTER)

    # get history and notifyTypes
    history = self.ovtDB.getHistory()
    notifyTypeCache = self.ovtDB.getNotifyTypes() # to have id->name mapping

    historyComplete = []

    for historyEntry in history:
      self.handleHistoryEntry(historyEntry, notifyTypeCache, mailer)
      historyComplete.append(historyEntry['historyid'])

    # cleanup
    self.ovtDB.setHistorySent(historyComplete)    
    del mailer

  def handleHistoryEntry(self, historyEntry, notifyTypeCache, mailer):
    """
    Gets related addresses, creates and sends reports.
    """
    # 1) Get addresses
    growlAddresses = self.ovtDB.getGrowlsToBeNotified(historyEntry['historyid'])
    emailAddresses = self.ovtDB.getEmailsToBeNotified(historyEntry['historyid'])

    if (len(growlAddresses) == 0) and (len(emailAddresses) == 0):
      return

    # 2) Create relevant object for report generation
    report = self.createReportObject(historyEntry, notifyTypeCache)

    # 3) Generate and send reports!
    self.sendGrowls(growlAddresses, notifyTypeCache, historyEntry, report)
    self.sendEmails(emailAddresses, report, mailer)

  def createReportObject(self, historyEntry, notifyTypeCache):
    """
    Return appropriate object for historyEntry
    """
    relatedEntities = self.ovtDB.getHistoryRelatedEntites(historyEntry['historyid'])
    notifyTypeName = notifyTypeCache[historyEntry['notifytypeid']]['notifytypename']

    if notifyTypeName in ("Testrun Status Change",
                          "Testrun Status Change Verbose",
                          "Testsuite Completed"):
      return HistoryEntry(self.ovtDB, historyEntry,
                               notifyTypeCache, relatedEntities)
    elif notifyTypeName == "Testrun Group Completed":
      testrungroupid = relatedEntities['testrungroupid']
      return TestgroupComplete(self.ovtDB, testrungroupid)
    else:
      raise NotImplementedError("Not implemented notifyTypeName = %s" % notifyTypeName)

  def sendGrowls(self, growlAddresses, notifyTypeCache, historyEntry, report):
    """
    Creates and sends growl notifications to all addresses
    """
    if len(growlAddresses) > 0:
      for growlAddr in growlAddresses:
        notifyTypeName = notifyTypeCache[historyEntry['notifytypeid']]['notifytypename']
        try:
          grl = Growl.GrowlNotifier(applicationName      = "Overtest",
                                    notifications        = [notifyTypeName],
                                    defaultNotifications = [0],
                                    hostname             = growlAddr['growlhost'],
                                    password             = growlAddr['growlpassword'])
          grl.register()
          grl.notify(notifyTypeName, report.genGrowlTitle(), report.genGrowl())
        except gaierror:
          pass

  def sendEmails(self, emailAddresses, report, mailer):
    """
    Creates and sends emails containing reports to all addresses
    """
    if len(emailAddresses) > 0:
      for emailAddr in emailAddresses:
        mailer.sendHtmlEmail(NotificationDaemon.MAIL_FROM_ADDR,
                             emailAddr['email'],
                             report.genGrowlTitle(),
                             report.genEmail(),
                             "This is an HTML email. No text version available")
    
# ------------------------------------------------------------------------------
# class GenerateReportInterface
# ------------------------------------------------------------------------------

class GenerateReportInterface:
  def genEmail(self):
    """ 
    Return generated email 
    """
    raise NotImplementedError("GenerateReportInterface::genEmail")

  def genGrowlTitle(self):
    """ 
    Return generated growl title 
    """
    raise NotImplementedError("GenerateReportInterface::genGrowlTitle")

  def genGrowl(self):
    """ 
    Return generated growl 
    """
    raise NotImplementedError("GenerateReportInterface::genGrowl")

# ------------------------------------------------------------------------------
# class TestgroupComplete(GenerateReportInterface)
# ------------------------------------------------------------------------------

class TestgroupComplete(GenerateReportInterface):
  """
  Generates report for notifytypename = TestgroupComplete
  """

  def __init__(self, ovtDB, testrungroupid):
    """
    Body of report is created in __init__.
    """
    self.ovtDB = ovtDB
    # Below members are used to generate email or growl
    self.testrungroupId = testrungroupid
    self.testrungroupName = self.ovtDB.getTestrungroupDescription(testrungroupid)
    self.testruns = self.ovtDB.getTestrunsFromTestgroup(testrungroupid)
    self.errorReport = ""
    self.reportHtml = "none"

    # Collect results
    actionObjList = self.getActionsWithResults()
    if len(actionObjList) > 0: # Store all summary results in self.resultsList
      summaryList = []
      for action in actionObjList.values(): # Format each summary
        summaryList.append(action.formatMultiResults())

      # Combine summaries from all testsuites together into one report
      self.reportHtml = ""
      for summary in summaryList:
        self.reportHtml += summary
        self.reportHtml += "\n<hr>\n\n" # separator

    # report is ready!

  def getActionsWithResults(self):
    """
    Construct all action objects and populate each with all result sets
    """
    # Below dictionaries keep intermediate data (not formatted results)
    actionObjList = {} # values = action object

    for testrunid in self.testruns: # testruns from testrungroup
      testsuites = self.ovtDB.getTestsuitesInTestrun(testrunid)

      for testsuiteid in testsuites: # testsuites from testrun
        actionid = testsuites[testsuiteid]

        versionedactionid = self.ovtDB.getVersionedActionid(testrunid, actionid)

        # Fetch results related to particular action
        actionObject = self.getActionObject(actionid, testrunid, versionedactionid)

        if actionObject is None:
          continue

        actionResults = self.fetchActionResults(actionObject)

        if actionResults is None:
          continue
        
        # If this is a first encountered action then put it in the list
        if not actionid in actionObjList:
          actionObjList[actionid] = actionObject

        actionObjList[actionid].addMultiResults(testrunid, actionResults)
    
    return actionObjList

  def getActionObject(self, actionid, testrunid, versionedactionid):
    """
    Returns A<actionid> object
    """
    task = None
    testrun = Testrun(self.ovtDB, testrunid=testrunid, logDB=self.ovtDB.log)
    try:
      exec("from action.A%d import *" % actionid)
      exec("task = A%d((testrun, versionedactionid, None, actionid))" % (actionid))
      exec("del(sys.modules['action.A%d'])" % actionid)
    except ImportError:
      self.errorReport += "Failed to import action (A%d)\n%s\n" \
          % (actionid, formatExceptionInfo())
      task = None
    except SyntaxError:
      self.errorReport += "Failed to import action (A%d) because of syntax error\n%s\n" \
          % (actionid, formatExceptionInfo())
      task = None
    except Exception:
      self.errorReport += "Unknown exception when importing action (A%d)\n%s\n" \
          % (actionid, formatExceptionInfo())
      task = None

    return task

  def fetchActionResults(self, actionObject):
    """
    Fetches results from an action without formatting.
    Also uses extendActionResults() function to add some fields.
    """
    
    actionResults = None
    try:
      actionResults = actionObject.actionQuery()

      if actionResults is not None:
        self.extendActionResults(actionResults, actionObject)
    except ResultSubmissionException, e:
      self.errorReport += "Failed to extract results for action (A%d)\n%s\n" \
                          % (actionObject.actionid, formatExceptionInfo())
    return actionResults

  def extendActionResults(self, actionResults, actionObject):
    """
    This function adds "heading" field to results so formatted tables are
    understandable for human. 
    
    Currently it adds core name as heading for Verify CSIM so user
    will be able to distinguish table columns with results in the report.

    TODO: this functionality should be in specialised version of actionQuery
    """

    if actionObject.name == "Verify CSIM":
      actionResults["heading"] = actionObject.config.getVariable("Target Board")

  def genEmail(self):
    email = "<html>\n"+\
            "<head>\n"+\
            ("<title> %s </title>\n" % self.testrungroupName) +\
            "</head>\n"+\
            "<body>\n"
    email += self.reportHtml
    email += "</body>\n"+\
             "</html>"
    return email

  def genGrowlTitle(self):
    title = "Testrun Group Complete"
    return title

  def genGrowl(self):
    text  = "Testgroup name: %s\n" % self.testrungroupName
    text += "Testgroup id: %d" % self.testrungroupId
    return text

# ------------------------------------------------------------------------------
# class HistoryEntry(GenerateReportInterface)
# ------------------------------------------------------------------------------

class HistoryEntry(GenerateReportInterface):
  """
  Stores information about a history entry and can generate various reports
  for it
  """
  def __init__(self, ovtDB, entry, notifytypecache, relatedEntities):
    """
    Initialise a history entity
    """
    self.entry = entry
    self.notifytypeid = entry['notifytypeid']
    self.ovtDB = ovtDB
    self.notifytypecache = notifytypecache
    self.relatedEntities = relatedEntities
    self.growltitle = None
    self.growl = None
    self.email = None

  def format(self, text):
    """
    Format the reports filling out the special identifiers as below
    %from%        Fetches the old value as text
    %to%          Fetches the new value as text
    %updateid%    Fetches the most closely associated entityid
    %date%        Fetches the date of the history entry
    %<fieldid>%   Fetched the entityid
    %[<fieldid>]% Fetches the textual representation of the entityid
    $testsuite%   Fetches results for the associated testsuiteid
    """
    text = text.replace("%date%", self.entry['eventdate'])
    text = text.replace("%from%", self.entry['fromvalue'])
    text = text.replace("%to%", self.entry['tovalue'])
    text = text.replace("%updateid%", str(self.entry['updateid']))
    for field in self.relatedEntities:
      entityid = self.relatedEntities[field]
      text = text.replace("%%%s%%" % field, str(entityid))
      description = self.ovtDB.getNotifyEntityDescription(field, entityid)
      text = text.replace("%%[%s]%%" % field, description)
    if "%testsuite%" in text:
      results = self.results()
      text = text.replace("%testsuite%", results)
    return text

  def results(self):
    """
    Fetch the testsuite results as processed text
    """
    task = None
    actionid = \
      self.ovtDB.getActionForTestsuite(self.relatedEntities['testsuiteid'])
    if actionid == None:
      return "Unknown actionid %d" % actionid

    testrun = Testrun(self.ovtDB, testrunid=self.relatedEntities['testrunid'],
                      logDB=self.ovtDB.log)
    try:
      exec("from action.A%d import *" % actionid)
      exec("task = A%d((testrun, None, None, actionid)) # %s" % (actionid, str(testrun)))
      exec("del(sys.modules['action.A%d'])" % actionid)
    except ImportError:
      return "Failed to import action (A%d)\n%s" \
             % (actionid, formatExceptionInfo())
    except SyntaxError:
      return "Failed to import action (A%d) because of syntax error\n%s" \
             % (actionid, formatExceptionInfo())
    except Exception:
      return "Unknown exception when importing action (A%d)\n%s" \
             % (actionid, formatExceptionInfo())

    try:
      formattedResult = task.formatResults()
    except ResultSubmissionException, e:
      formattedResult = "Testsuite formatting error:\n%s" % str(e)
    return formattedResult

  def genGrowlTitle(self):
    """
    Generate the growl title
    """
    if self.growltitle == None:
      cache = self.notifytypecache[self.notifytypeid]
      self.growltitle = self.format(cache['growltitletemplate'])
    return self.growltitle

  def genGrowl(self):
    """
    Generate the growl report
    """
    if self.growl == None:
      cache = self.notifytypecache[self.notifytypeid]
      self.growl = self.format(cache['growltemplate'])
    return self.growl

  def genEmail(self):
    """
    Generate the email report
    """
    if self.email == None:
      cache = self.notifytypecache[self.notifytypeid]
      self.email = "<html>\n" +\
                   "<head>\n" +\
                   ("<title>%s</title>\n" % (self.format(cache['growltitletemplate']))) +\
                   "</head>\n" +\
                   "<body>\n"
      self.email += self.format(cache['emailtemplate'])
      self.email += "</body>\n" +\
                    "</html>"
    return self.email
