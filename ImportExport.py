import sys
import os
import getopt
from OvertestExceptions import *
import importers
import exporters
import OvtDB

class ImportExport:
  ovtDB = None

  def __init__(self, _ovtDB):
    self.ovtDB = _ovtDB

  def usage(self, exitcode, error = None):
    """
    Display the usage
    """
    if error != None:
      self.error(error)
      print ""
    print "Usage:"
    print "  --schema=<schema>"
    print "  <options>"
    sys.exit (exitcode)

  def exporter(self, args):
    e = self.getSchemaClass (args, False)
    return e.exportData (args[1:])

  def importer(self, args):
    i = self.getSchemaClass (args, True)
    return i.importData (args[1:])

  def getSchemaClass(self, args, importing):
    """
    Parse the common options for import or export
    """
    if len(args) == 0:
      self.usage(2, "Schema not specified")

    try:
      opts, args = getopt.getopt (args[0:1], "s:", ["schema="])
    except getopt.GetoptError, e:
      self.usage (2, str(e))

    for (o, a) in opts:
      if o in ("-s", "--schema"):
        if a.lower() == "action":
          if importing:
            import importers.ActionImporter
            return importers.ActionImporter.ActionImporter(self.ovtDB)
          else:
            import exporters.ActionExporter
            return exporters.ActionExporter.ActionExporter(self.ovtDB)
        elif a.lower() == "hostconfig":
          if importing:
            self.error ("The hostconfig schema cannot be imported")
          else:
            import exporters.HostConfigExporter
            return exporters.HostConfigExporter.HostConfigExporter(self.ovtDB)
        elif a.lower() == "results":
          if importing:
            self.error ("The results schema cannot be imported")
          else:
            import exporters.ResultsExporter
            return exporters.ResultsExporter.ResultsExporter(self.ovtDB)
        elif a.lower() == "log":
          if importing:
            self.error ("The log schema cannot be imported")
          else:
            import exporters.LogExporter
            return exporters.LogExporter.LogExporter(self.ovtDB)
        elif a.lower() == "notify":
          if importing:
            self.error ("The notify schema cannot be imported")
          else:
            import exporters.NotifyExporter
            return exporters.NotifyExporter.NotifyExporter(self.ovtDB)
        elif a.lower() == "testrunid":
          if importing:
            self.error ("The testrunid schema cannot be imported")
          else:
            import exporters.TestrunIdExporter
            return exporters.TestrunIdExporter.TestrunIdExporter(self.ovtDB)
        elif a.lower() == "testrun":
          if importing:
            self.error ("The testrun schema cannot be imported")
          else:
            import exporters.TestrunExporter
            return exporters.TestrunExporter.TestrunExporter(self.ovtDB)
        elif a.lower() == "claim":
          if importing:
            self.error ("The claim schema cannot be imported")
          else:
            import exporters.ClaimExporter
            return exporters.ClaimExporter.ClaimExporter(self.ovtDB)
        else:
          self.usage(1, "Unknown schema")

    self.usage(2, "Schema not specified")

  def error(self, error):
    """
    Print an error message
    """
    print "ERROR: %s"%error

