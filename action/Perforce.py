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
import logging
import multiprocessing

# FIXME: Remove when overtest can import imgtec.p4python
import sys
lib = '/user/rgi_data2/Verify/kl/CentOS-5/P4Python_1.0.0/root/lib/python2.7/site-packages'
if lib not in sys.path:
  sys.path.insert(1, lib)
# END FIXME

from imgtec.p4python import PerforceConnection as PerforceConnectionSuper, \
                            TemporaryClientDef as TemporaryClientDefSuper, \
                            TemporaryClient as TemporaryClientSuper

class PerforceConnection(PerforceConnectionSuper):
  def __init__(self, *args, **kwargs):
    super(PerforceConnection, self).__init__(*args, **kwargs)

  def get_logger(self):
    return logging.getLogger('action.perforce')

  def get_p4_logger(self):
    return logging.getLogger('action.perforce.p4')

