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
