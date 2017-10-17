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

