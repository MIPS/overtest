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
import os
from common.Supertest import A_supertest_generic

# Build mecc supertest (Slow Tests)

class A108963(A_supertest_generic):
  def get_config_mode(self):
    return 'compile'

  def get_config_configs(self):
    return []

  def get_config_testgrps(self):
    return ['Ydepth-opmix']

  def __init__(self, data):
    A_supertest_generic.__init__(self, data)
    self.actionid = 108963
    self.name = "Build mecc supertest (Slow Tests)"
