import os
import errno

def pid_exists(pid):
  try:
    os.kill(pid, 0)
    return True
  except OSError, err:
    return err.errno == errno.EPERM

def versionCompare(a, b):
  """
  Compare two version numbers passed as arrays of numbers.
  Returns -1 for a < b, 0 for a == b, and 1 for a > b.
  Convert a dotted version number to a suitable list using version.split(".")
  """
  for adigit, bdigit in zip(a, b):
    try:
      if int(adigit) < int(bdigit):
        return -1
      if int(adigit) > int(bdigit):
        return 1
    except ValueError:
      if str(adigit) < str(bdigit):
        return -1
      if str(bdigit) < str(adigit):
        return 1

  if len(a) > len(b):
    return 1

  if len(a) < len(b):
    return -1

  return 0
