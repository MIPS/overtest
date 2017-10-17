"""
Abstraction for executing commands on the host platform.
Currently only supports linux.
"""

import errno
import fcntl
import os
import select
import signal
import subprocess
import sys
import time
import types
import gzip

from Config import CONFIG
from OvertestExceptions import TestrunAbortedException, TimeoutException

class Execute:
  """
  Abstracts all the execution features required in the test system
  """

  def getWorkPath(self):
    """ Abstract method """
    assert(False)

  def error(self, string, exception=True):
    """ Abstract method """
    assert(False and string and exception)

  def getLogPath(self):
    """ Abstract method """
    assert(False)

  def updateEnvironment(self, env):
    """ Abstract method """
    assert(False and env)

  def getPrefix(self):
    """ Abstract method """
    assert(False)

  def __init__(self):
    self.versionedactionid = None
    self.testrun = None
    self.proccount = 0
    self.archiveMode = False
    self.name = ""
    self.umask = 007
    self.commandtags = {}

  def createDirectory(self, path):
    """
    Safely create a directory
    """
    try:
      os.makedirs(os.path.normpath(path))
    except OSError:
      pass

    # Fail if something went horribly wrong
    if not os.path.isdir(path):
      self.error("Cannot create overtest directory: %s" % path)
    return True

  def getResource(self, resourcetype):
    """
    Retrieve an allocated resource. This can be interrogated using the :py:class:`resource.Resource` class.

    :param resourcetype: The type of resource to retrieve.
    :type resourcetype: string
    :return: The allocated resource
    :rtype: Resource or None
    """
    return self.testrun.getResource(self.versionedactionid, resourcetype)

  def _my_preexec_fn(self):
    """
    Cleans up everything to give subprocesses a clean slate.
    """
    os.setpgrp()
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

  def execute(self, command, workdir=None, env=None, shell=False, spoofStdin='', timeout=None, tag=None, silent=True):
    """
    Executes a single command in the environment provided. Logs of stdout,
    stderr, interleaved output and exit code are created. The stdout can be 
    retrieved using :py:meth:`~.Action.fetchOutput` or 
    :py:meth:`~.Action.fetchOutputFile`.

    :param command: Name of the executable or script followed by the arguments
    :type command: list or tuple
    :param workdir: Directory where the command must be executed, defaults to 
                    the current working area
    :type workdir: path
    :param env: Additional environment variables for the command. Any existing 
                variable will be re-defined.
    :type env: dictionary
    :param shell: When set, invokes the command within a shell. Required for
                  scripts.
    :type shell: boolean
    :param spoofStdin: Input to provide to the command during execution
    :type spoofStdin: string
    :param timeout: The number of seconds before the command should be 
                    forcefully kllled. This is a hint and the exact timeout may
                    be longer
    :type timeout: integer
    :param tag: A name that can be used later to refer to this command
    :type tag: string
    :param silent: Ensure all output from the command is only sent to log files. 
                   Set to false for debugging
    :type silent: boolean
    :returns: exit code from command. Negative indicates killed by signal.
    :rtype: integer
    """
    # Get the standard working area from the testrun
    if workdir == None:
      workdir = self.getWorkPath()

    if env == None:
      env = {}

    if tag != None:
      self.commandtags[tag] = self.proccount

    # block others but allow group write
    oldumask = os.umask(self.umask)

    # Copy the existing environment
            # Commands can time out
    newenv = {}
    for var in os.environ:
      newenv[var] = os.environ[var]

    # There are cleanup actions that must take place in exception conditions
    try:
      proc = None
      stdout = None
      stdoutgz = None
      stdin = None
      stderr = None
      stderrgz = None
      combined = None
      combinedgz = None
      returncode = None
      stdoutread = None
      stdoutwrite = None
      stderrread = None
      stderrwrite = None

      # Override the environment
      for var in env:
        newenv[var] = str(env[var])

      # Allow environment adjustments
      self.updateEnvironment(newenv)

      # Commands should be lists of arguments
      if not type(command) == types.ListType:
        self.error("Command is not of list type: %s" % str(command))

      # Remember the old path
      try:
        oldcwd = os.getcwd()
      except OSError, ex:
        if ex.errno == 2:
          oldcwd = "/tmp"
        else:
          raise

      dirsuccess = self.createDirectory(workdir)
      if not dirsuccess:
        return False

      # Change to the new working directory
      os.chdir(workdir)

      # Open all log files
      prefix = self.getPrefix()

      args = (prefix, self.proccount)
      stderr_path = os.path.join(self.getLogPath(), "%s%u.stderr.gz"%args)
      stdout_path = os.path.join(self.getLogPath(), "%s%u.stdout.gz"%args)
      combined_path = os.path.join(self.getLogPath(), "%s%u.combined.gz"%args)
      returncode_path = os.path.join(self.getLogPath(), "%s%u.returncode"%args)
      stderr = open(stderr_path, "w")
      stderrgz = gzip.GzipFile("hidden", "w", 9, stderr)
      stdout = open(stdout_path, "w")
      stdoutgz = gzip.GzipFile("hidden", "w", 9, stdout)
      combined = open(combined_path, "w")
      combinedgz = gzip.GzipFile("hidden", "w", 9, combined)
      returncode = open(returncode_path, "w")

      # Keep a copy of the stdin stream that is sent to the process
      stdin_path = os.path.join(self.getLogPath(), "%s%u.stdin"%args)
      stdin = open(stdin_path, "w")
      stdin.write(spoofStdin)
      stdin.close()
      stdin = None

      # Create the process comms pipes
      (stdoutread, stdoutwrite) = os.pipe()
      (stderrread, stderrwrite) = os.pipe()
      # Set the readers to non-blocking so that large data blobs can be read without
      # fear of running out of input
      fcntl.fcntl(stdoutread, fcntl.F_SETFL, os.O_NONBLOCK)
      fcntl.fcntl(stderrread, fcntl.F_SETFL, os.O_NONBLOCK)

      # Popen has some exceptions that are interesting and should be handled here
      try:
        # Log the fact that the test is running
        self.logHelper("Executing: %s" % ' '.join(command))

        # Store the working directory, environment and command
        combinedgz.write("Workdir: %s\n" % (workdir))
        combinedgz.write("Environment:\n")
        if len(env) == 0:
          combinedgz.write("No environment overrides...\n")
        for key in env:
          combinedgz.write("%s=%s\n"%(key, env[key]))
        combinedgz.write("\n"+(" ".join(command))+"\n")

        # Start the command
        proc = subprocess.Popen(command, stdout=stdoutwrite, stderr=stderrwrite,
                                stdin=subprocess.PIPE, shell=shell, env=newenv,
                                preexec_fn=self._my_preexec_fn)

        # Write any stdin to the process
        try:
          proc.stdin.write (spoofStdin)
          proc.stdin.close ()
        except IOError:
          if not silent:
            sys.stderr.write("Failed to send spoofed stdin to process\n")
          combinedgz.write("Failed to send spoofed stdin to process\n")
      except ValueError:
        self.error("Invalid arguments")
      except OSError:
        self.error("Executable '%s' not found" % command[0])

      # Allow subclasses to do something when a process starts
      self.processStarted(proc)

      # Initialise a timer to sporadically check for an abort
      lastabortcheck = time.time()
      timeoutStart = lastabortcheck

      # Prefill iwtd to force at least one iteration (in case of immediate process exit)
      iwtd = [stdoutread, stderrread]

      # Loop until there was no output on the last read, or the process is still running
      while proc.poll() == None or len(iwtd) != 0:
        # Check for an abort every 30 seconds
        currenttime = time.time()
        if (not self.archiveMode) and currenttime - lastabortcheck > 30:
          if self.testrun.isAborted():
            raise TestrunAbortedException("%s run interrupted" % self.name)
          lastabortcheck = currenttime

        # Commands can time out
        if timeout != None and currenttime - timeoutStart > timeout:
          raise TimeoutException(currenttime - timeoutStart)

        # Check for any output but do not block
        (iwtd, _, _) = select.select([stdoutread, stderrread], [], [], 0.1)

        # Record any stderr first
        if stderrread in iwtd:
          tmp = os.read(stderrread, 1024)
          if not silent:
            sys.stderr.write(tmp)
          stderrgz.write(tmp)
          combinedgz.write(tmp)
        elif stdoutread in iwtd:
          tmp = os.read(stdoutread, 1024)
          if not silent:
            sys.stdout.write(tmp)
          stdoutgz.write(tmp)
          combinedgz.write(tmp)

      # Return to previous directory
      try:
        os.chdir(oldcwd)
      except OSError, ex:
        if ex.errno != 2:
          raise

      # Add a log message
      self.logHelper("Run Complete")

      # Save the return code in a file
      returncode.write("Return Code: %d" %proc.returncode)
    finally:
      # Move to next process
      self.proccount += 1

      # Close the exec pipes
      if stdoutread != None:
        os.close(stdoutread)
      if stdoutwrite != None:
        os.close(stdoutwrite)
      if stderrread != None:
        os.close(stderrread)
      if stderrwrite != None:
        os.close(stderrwrite)

      # Close stdout, stderr, combined
      if stdin != None:
        stdin.close()
      if stdoutgz != None:
        stdoutgz.close()
      if stdout != None:
        stdout.close()
      if stderrgz != None:
        stderrgz.close()
      if stderr != None:
        stderr.close()
      if combinedgz != None:
        combinedgz.close()
      if combined != None:
        combined.close()
      if returncode != None:
        returncode.close()

      # Restore the previous umask
      os.umask(oldumask)

      # Do this last in case it throws some unexpected exception. We really want the finally
      # code above to complete so that the log files are written out.
      if proc != None:
        try:
          os.killpg(proc.pid, signal.SIGTERM)
          time.sleep(2)
          while True:
            try:
              pid, status = os.waitpid(-proc.pid, os.WNOHANG)
            except OSError, ex:
              if ex.errno == errno.ECHILD:
                # no more children in this group.
                break
              raise
            if pid == 0:
              break

          os.killpg(proc.pid, signal.SIGKILL)
          while True:
            try:
              pid, status = os.waitpid(-proc.pid, 0)
            except OSError, ex:
              if ex.errno == errno.ECHILD:
                # no more children in this group.
                break
              raise
        except OSError, ex:
          if ex.errno != errno.ESRCH:
            print "CLEANUP ERROR: %s" % ex

    # Return the exit code. A negative number represents an inverted signal number
    return proc.returncode

  def fetchOutput(self, tag = None):
    """
    Fetches the output from one of the commands that has been executed.

    :param tag: The tag or number of the command to retrieve the output from.
                Commands are numbered from zero. The default is to fetch the last
                executed command's output
    :type tag: string, integer or none
    :return: All stdout from the specified command
    :rtype: string
    """
    filename = self.fetchOutputFile(tag)

    stdout = None
    try:
      try:
        stdout = gzip.open(filename)
        output = stdout.read()
      except IOError:
        self.error("Failed to read stdout for command: %s" % tag)
    finally:
      if stdout != None:
        stdout.close()
    return output

  def fetchOutputFile(self, tag = None):
    """
    Fetches the output filename from one of the commands that has been executed.

    :param tag: The tag or number of the command to retrieve the output from.
                Commands are numbered from zero. The default is to fetch the last
                executed command's output
    :type tag: string, integer or none
    :return: The filename where stdout is stored
    :rtype: path
    """
    if tag == None:
      procnum = self.proccount-1
    elif type(tag) == types.StringType:
      if not tag in self.commandtags:
        self.error("fetchOutputFile: request for output from non-existent command: %s" % tag)
      procnum = self.commandtags[tag]
    else:
      procnum = tag

    if procnum >= self.proccount:
      self.error("fetchOutputFile: request for output from non-existant process: %d" % procnum)

    prefix = self.getPrefix()

    return os.path.join(self.getLogPath(), "%s%u.stdout.gz" % (prefix,procnum))

