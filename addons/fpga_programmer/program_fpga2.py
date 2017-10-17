import socket
import sys
import getopt

PORT = 4321
DEBUG = 1

class ProgramFPGA:
  def __init__(self, server):
    self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    self.sock.connect((server,PORT))
    self.debug_print('Connected')

  def __del__(self):
    self.sock.send('EXIT\n')

  def debug_print(self, str):
    if DEBUG:
      print str
  
  def dutclock(self, clockfreq):
    """
    Program the FPGA on 'server' with 'bitfile'
    """
    self.debug_print('Sending DUTCLOCK cmd')
    self.sock.send('DUTCLOCK '+str(clockfreq) +'\n')
    reply = str(self.sock.recv(3))
    if reply.startswith('OK'):
      reply = str(self.sock.recv(70))
      return True, reply
    return False, ""

  def mainboard(self, bitfile):
    """
    Program the FPGA on 'server' with 'bitfile'
    """
    f = open(bitfile,'rb') 
    data = f.read()
    size = len(data)
    self.debug_print('Sending MAINBOARD BITFILE cmd')
    self.sock.send('MAINBOARD BITFILE '+str(size) +'\n')
    reply = str(self.sock.recv(20))
    if reply.startswith('OK send me the data'):
      self.debug_print('Sending data')
      self.sock.send(data)
    else:
      self.debug_print('ERROR: no reply from MAINBOARD BITFILE command')
      return False
    self.debug_print('Sending Complete')
    reply = str(self.sock.recv(3))
    return reply.startswith('OK')

  def daughterboarda(self, bitfile):
    """
    Program the FPGA on 'server' with 'bitfile'
    """
    f = open(bitfile,'rb') 
    data = f.read()
    size = len(data)
    self.debug_print('Sending DAUGHTERBOARD_A BITFILE cmd')
    self.sock.send('DAUGHTERBOARD_A BITFILE '+str(size) +'\n')
    reply = str(self.sock.recv(20))
    if reply.startswith('OK send me the data'):
      self.debug_print('Sending data')
      self.sock.send(data)
    else:
      self.debug_print('ERROR: no reply from DAUGHTERBOARD_A BITFILE command')
      return False
    self.debug_print('Sending Complete')
    reply = str(self.sock.recv(3))
    return reply.startswith('OK')

  def daughterboardb(self, bitfile):
    """
    Program the FPGA on 'server' with 'bitfile'
    """
    f = open(bitfile,'rb') 
    data = f.read()
    size = len(data)
    self.debug_print('Sending DAUGHTERBOARD_B BITFILE cmd')
    self.sock.send('DAUGHTERBOARD_B BITFILE '+str(size) +'\n')
    reply = str(self.sock.recv(20))
    if reply.startswith('OK send me the data'):
      self.debug_print('Sending data')
      self.sock.send(data)
    else:
      self.debug_print('ERROR: no reply from DAUGHTERBOARD_B BITFILE command')
      return False
    self.debug_print('Sending Complete')
    reply = str(self.sock.recv(3))
    return reply.startswith('OK')

  def program(self):
    self.debug_print('Issuing PROGRAM cmd')
    self.sock.send('PROGRAM\n')
    reply = str(self.sock.recv(19))
    if reply.startswith('Programming Passed'):
      self.debug_print('Programming Passed')
      return True
    else:
      self.debug_print('Programing Failed')
      self.sock.send('LOG\n')
      self.sock.settimeout(5)
      while 1:
        try:
          log = self.sock.recv(64)
          if(log):
            print(log)
          else:
            break
        except socket.timeout:
          break
      return False

def usage():
  print "-h <server>"
  print "-m <mainboard>"
  print "-a <daughterboarda>"
  print "-b <daughterboardb>"
  print "--dut-clock <frequency>"

if __name__ == '__main__' :
  try:
    opts, args = getopt.getopt(sys.argv[1:], "h:m:a:b:", ["dut-clock="])
  except getopt.GetoptError, e:
    print e
    usage()
    sys.exit(1)

  if len(opts) == 0:
    usage()
    sys.exit(1)

  host = None
  mainboard = None
  daughterboarda = None
  daughterboardb = None
  dutclock = None

  for o,a in opts:
    if o == "-h":
      host = a
    elif o == "-m":
      mainboard = a
    elif o == "-a":
      daughterboarda = a
    elif o == "-b":
      daughterboardb = a
    elif o == "--dut-clock":
      dutclock = a
 
  if host == None:
    print "ERROR: A host must be specified"
    sys.exit(1)

  programmer = ProgramFPGA(host)

  # Program the clock first as this may wipe the mainboard
  if dutclock != None:
    (success, message) = programmer.dutclock(dutclock)
    if success:
      print "Clock set: %s" % message
    else:
      del programmer
      sys.stderr.write("ERROR: Failed to set dutclock\n")
      sys.exit(2)

  if mainboard != None:
    if not programmer.mainboard(mainboard):
      del programmer
      sys.stderr.write("ERROR: Failed to send mainboard\n")
      sys.exit(2)

  if daughterboarda != None:
    if not programmer.daughterboarda(daughterboarda):
      del programmer
      sys.stderr.write("ERROR: Failed to send daughterboarda\n")
      sys.exit(2)

  if daughterboardb != None:
    if not programmer.daughterboardb(daughterboardb):
      del programmer
      sys.stderr.write("ERROR: Failed to send daughterboardb\n")
      sys.exit(2)

  if programmer.program():
    print "Programmed"
  else:
    del programmer
    sys.stderr.write("ERROR: Failed to program FPGA\n")
    sys.exit(2)

  del programmer
  sys.exit(0)
