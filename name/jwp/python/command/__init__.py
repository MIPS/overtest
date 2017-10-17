# $Id: __init__.py 495 2008-01-03 23:53:28Z jwp $
"""
Python command tools.

See runtime.execution for the "endpoint". 

Python command command and extended console:
	python -m name.jwp.python.command.runtime (== jwpython)
	jwpython -c 'print "foo"'
	jwpython --python-context='import sys' \
		-c 'for x in sys.stdin: sys.stdout.write(x)'
"""
