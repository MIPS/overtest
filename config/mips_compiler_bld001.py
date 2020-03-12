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
Module for mips-compiler-bld001 config
"""
import config.centos5

class Config(config.centos5.Config):
  """
  Class for mips-compiler-bld001 config
  """
  fqdn = "mips-compiler-bld001"
  localdir = "/scratch/overtest/root/"
  logdir = "/scratch/overtest/root/"
  shareddir = "/scratch/overtest/root/"
  python = "/mips/tools/sweng/freeware/python/2.7.13/Linux/bin/python"
  git = "/usr/local/bin/git"
  cores = 48
  gitref = "/scratch/overtest/git"
  tmpdir = "/dev/shm"
