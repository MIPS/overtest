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
Module for generic windows config
"""
import ConfigFactory

class Config(ConfigFactory.DefaultConfig):
  """
  Class for generic windows config
  """
  fqdn = None
  cvs = "/usr/bin/cvs"
  ccs = "/img/usr/metag/Verify/Windows/CoreSWTools_1.0.0.0/root/ccs"
  neo = "/cygdrive/k/rgi_data2/Verify/Components/metag/neo/neo"
  python = "/img/usr/metag/Verify/Windows/Python_2.7.2/root/bin/python"
  bitstreams = "/cygdrive/k/rgi_data2/Verify/BitStreams"
  searchPathSep = ':'
