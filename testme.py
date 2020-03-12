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
from imgedaflow import gridinterface
testrunid=1234
options = {'action'      : 'submit',
           '--cmd'       : "/bin/env > /user/mpf/me2",
           '--batch'     : True,
           '--queue'     : "build",
           '--mem'       : "4G",
           '--maxmem'    : "8G",
           '--stdouterr' : "/user/mpf/me",
	   '--wait_until_finish' : True,
	   '--export_env_var_list': 'PATH',
	   '--tail': True,
	   '--clean_output':True,
           '--resources' : 'hdd=ssd,os=rhel6',
           '--jobname'         : "pathtest"}
ga = gridinterface.GridAccess(**options)
return_code, job_id = ga.run()
print "Testrun [%d] started as job %s" % (testrunid, job_id)

