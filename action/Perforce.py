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

