# -*- encoding: utf-8 -*-
##
'GreenTrunk module--only requires the Connector and Connection'

from postgresql.interface.proboscis.tracenull import \
	GreenTrunk_Connector as connector, \
	GreenTrunk_Connection as connection

def connect(**kw):
	return connector(**kw)()
