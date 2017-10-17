import os
from Action import Action
import shlex
import tarfile
from Config import CONFIG
import csv
import sets

# ResultsEEMBC

class A113832(Action):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 113832
    self.name = "ResultsEEMBC"
    
  # Execute the action.
  def run(self):

    return True
