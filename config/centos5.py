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
Module for CentOS 5 config
"""
import config.centos45

class Config(config.centos45.Config):
  """
  CentOS 5 default config
  """
  python = "/mips/tools/sweng/freeware/python/2.7.13/Linux/bin/python"
  cmake = "/mips/tools/sweng/freeware/cmake/2.8.12.2/bin/cmake"
  git = "/usr/bin/git"
