import logging
import os
import pprint
import re
import subprocess
import tempfile
import yaml

from p4_autobuild import OvertestTestrun
from p4_autobuild.watch_handlers import HandlerException

logger = logging.getLogger(__name__)

def _load_yaml_template():
  filename = os.path.split(__file__)[0]
  filename = os.path.join(filename, 'llvm.yaml')
  with open(filename) as fh:
    return yaml.load(fh)

def _specialise_template(test_def, change):
  test_def['description'] += ' @%d' % change.changelist

  for configuration in test_def['configuration']:
    cfg = configuration.get('LLVM Inputs')
    if cfg is None:
      continue
    cfg['LLVM_P4_CHANGELIST'] = int(change.changelist)
  logger.debug(pprint.pformat(test_def))
  return test_def

def _submit_to_overtest(filename):
  cmd = ['python', 'overtest.py', '--edit', '--new', '--file', filename, '--user', 'xbuild.meta', '--go']
  workdir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
  child = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=workdir)
  stdout, stderr = child.communicate()
  match = re.search('New testrun created \[([0-9]+)\]', stdout)
  if match is None:
    logging.error(stdout)
    logging.error(stderr)
    raise HandlerException("Submission to overtest failed")
  return int(match.group(1))

def submit(db, watch, change):
  change = change.lock(db)
  if change.overtest_testrun_id is not None:
    db.rollback()
    logger.info('Race detected. Another instance has submitted this build. Skipping')
    return True

  test_def = _load_yaml_template()
  test_def = _specialise_template(test_def, change)

  temp_file = tempfile.NamedTemporaryFile()
  yaml.dump(test_def, temp_file)

  change.overtest_testrun_id = _submit_to_overtest(temp_file.name)

  OvertestTestrun(change.overtest_testrun_id, False, None, False).insert(db)
  change.update(db)
  db.commit()

  return True
