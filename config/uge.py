"""
Module for UGE config
"""
import config.centos5
import os

class Config(config.centos5.Config):
  """
  HH UGE config
  """
  fqdn = "hhuge.hh.imgtec.org"
  localdir = "/scratch/%s.%s/" % (os.environ['JOB_ID'], 1 if not 'SGE_TASK_ID' in os.environ or os.environ['SGE_TASK_ID'] == "undefined" else os.environ['SGE_TASK_ID'])
  logdir = os.getcwd()
  shareddir = "/scratch/%s.%s/" % (os.environ['JOB_ID'], 1 if not 'SGE_TASK_ID' in os.environ or os.environ['SGE_TASK_ID'] == "undefined" else os.environ['SGE_TASK_ID'])
  python = "/vl/edatools/bin/python2.7"
  python_exe = "/vl/edatools/intern/python/2.7.5/centos5.8_x86_64/main/bin/python2.7"
  git = "/vl/edatools/intern/git/git-2.5.1/bin/git"
  cmake = "/vl/edatools/intern/cmake/3.1.3/bin/cmake"
