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
from __future__ import with_statement
import sys
import os
import SocketServer
import array
import re
import subprocess

TCF_TYPE = 'lx330'
MAINBOARD = 'xc4vlx160'
# MAINBOARD = 'xc4vlx80'
# TCF_TYPE = 'lx760'
IS_DUAL = False
MEMRESET_SCRIPT=None
DUTCLOCK_SCRIPT="c:\\FPGAS\\atlas_dutclock.tcl"
PCICONFIG_SCRIPT="c:\\FPGAS\\pciconfig.tcl"
# The following script is written by pciconfig.tcl
PCICONFIGRESTORE_SCRIPT="c:/FPGAS/pciconfigrestore.tcl"
PCILIB_FOLDER="c:\\TCF\\tcf_scb"
ATLAS_PCISAFE="C:\\FPGAs\\Atlas_Lx160\\atlasgen_lx160_12\\atlas.bit"
CMD_FILE = 'xilinx.cmd'
RESULTS_FILE = '_impactbatch.log'
PORT = 4321
DEBUG = 1
BLOCK_SIZE = 4096

def debug_print(str):
    if DEBUG: print str

#server stuf:
class comms_handler(SocketServer.StreamRequestHandler):
    def setup(self):
       SocketServer.StreamRequestHandler.setup(self)
       self.MAINBOARD_BIT_FILE = None
       self.DAUGHTERBOARD_A_BIT_FILE = None
       self.DAUGHTERBOARD_B_BIT_FILE = None
        
    def handle(self):      
        debug_print('Connected')
        dont_exit = 1
        while(dont_exit):
            cmd  = self.rfile.readline()
            cmdstr = str(cmd)
            cmdstr = cmdstr.upper()
            if cmdstr.startswith('MAINBOARD BITFILE'):
                self.MAINBOARD_BIT_FILE = 'mainboard.bit'
                regex = re.compile(r"MAINBOARD BITFILE (\d+)")
                m = regex.search(cmdstr)
                size = int(m.group(1))
                debug_print('MAINBOARD BITFILE command recieved with size ' + str(size))
                self.wfile.write('OK send me the data\n')
                
                data = ""
                while(size):
                    if size > BLOCK_SIZE:
                        read_amount = BLOCK_SIZE
                    else:
                        read_amount = size
                    data+=self.rfile.read(read_amount)
                    size -= read_amount
                debug_print('Transfer Complete')   
                delete_existing_file(self.MAINBOARD_BIT_FILE)
                with open(self.MAINBOARD_BIT_FILE, 'ab') as f:
                        f.write(data)
                self.wfile.write('OK\n')
            elif cmdstr.startswith('DAUGHTERBOARD_A BITFILE'):
                self.DAUGHTERBOARD_A_BIT_FILE = 'daughterboard_a.bit'
                regex = re.compile(r"DAUGHTERBOARD_A BITFILE (\d+)")
                m = regex.search(cmdstr)
                size = int(m.group(1))
                debug_print('DAUGHTERBOARD_A BITFILE command recieved with size ' + str(size))
                self.wfile.write('OK send me the data\n')
                
                data = ""
                while(size):
                    if size > BLOCK_SIZE:
                        read_amount = BLOCK_SIZE
                    else:
                        read_amount = size
                    data+=self.rfile.read(read_amount)
                    size -= read_amount
                debug_print('Transfer Complete')   
                delete_existing_file(self.DAUGHTERBOARD_A_BIT_FILE)
                with open(self.DAUGHTERBOARD_A_BIT_FILE, 'ab') as f:
                        f.write(data)
                self.wfile.write('OK\n')
            elif cmdstr.startswith('DAUGHTERBOARD_B BITFILE'):
                self.DAUGHTERBOARD_B_BIT_FILE = 'daughterboard_b.bit'
                regex = re.compile(r"DAUGHTERBOARD_B BITFILE (\d+)")
                m = regex.search(cmdstr)
                size = int(m.group(1))
                debug_print('DAUGHTERBOARD_B BITFILE command recieved with size ' + str(size))
                self.wfile.write('OK send me the data\n')
                
                data = ""
                while(size):
                    if size > BLOCK_SIZE:
                        read_amount = BLOCK_SIZE
                    else:
                        read_amount = size
                    data+=self.rfile.read(read_amount)
                    size -= read_amount
                debug_print('Transfer Complete')   
                delete_existing_file(self.DAUGHTERBOARD_B_BIT_FILE)
                with open(self.DAUGHTERBOARD_B_BIT_FILE, 'ab') as f:
                        f.write(data)
                self.wfile.write('OK\n')
            elif cmdstr.startswith('PROGRAM'):
                if TCF_TYPE=="lx330":
                  create_xilinx_cmd_file_lx330(self.MAINBOARD_BIT_FILE, self.DAUGHTERBOARD_A_BIT_FILE, self.DAUGHTERBOARD_B_BIT_FILE)
                elif TCF_TYPE=="lx760":
                  create_xilinx_cmd_file_lx760(self.MAINBOARD_BIT_FILE, self.DAUGHTERBOARD_A_BIT_FILE, self.DAUGHTERBOARD_B_BIT_FILE)
                if not reprogram():
                    debug_print('Programming Failed')
                    self.wfile.write('Programming Failed\n')
                else:
                    debug_print('Programming Passed')
                    self.wfile.write('Programming Passed\n')
            elif cmdstr.startswith('DUTCLOCK'):
                regex = re.compile(r"DUTCLOCK (\d+)")
                m = regex.search(cmdstr)
                frequency = int(m.group(1))
                clock_success = False
                lastline = ""
                if TCF_TYPE=="lx330":
                  (clock_success, lastline) =set_dutclock_lx330(frequency)
                else:
                  clock_success=set_dutclock_lx760(frequency)
                if clock_success:
                    self.wfile.write('OK\n')
                    lastline = lastline.strip('\r\n')
                    self.wfile.write(lastline + (" "*(70-len(lastline))))
                else:
                    self.wfile.write('NO\n')
            elif cmdstr.startswith('LOG'):       
                with open(RESULTS_FILE) as f:
                    for line in f:
                        self.wfile.write(line  + '\r')   
            elif cmdstr.startswith('EXIT'):
                dont_exit = 0
            else:
                self.wfile.write('Unknown Command\n')

#xilinx stuf:
def delete_existing_file( filename ) :
    if os.path.exists( filename ):
        os.remove( filename )

def append_to_file( filename, data ) :
	try :
		f = open( filename, 'a' )
	except IOError :
		return	
	f.write( data )
	f.close( )

def create_xilinx_cmd_file_lx330(mainboard, daughterboard_a, daughterboard_b):
    xil_path = os.getenv('XILINX')
    delete_existing_file(CMD_FILE)
    mainboard_num = 0
    daughterboard_a_num = 0
    daughterboard_b_num = 0

    if not IS_DUAL and daughterboard_b != None:
      debug_print('Configuration error: single daughterboard with two bitstreams provided')

    append_to_file(CMD_FILE,'setMode -bscan\n')
    append_to_file(CMD_FILE,'setCable -p auto\n')
    device_num = 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\acecf\\data\\xccace.bsd\n' % (device_num, xil_path))
    device_num += 1
    if mainboard == None:
      append_to_file(CMD_FILE,'addDevice -p %d -file %s\\virtex4\\data\\%s.bsd\n' % (device_num, xil_path, MAINBOARD))
    else:
      append_to_file(CMD_FILE,'addDevice -p %d -file %s\n'  % (device_num, mainboard))
    mainboard_num = device_num
    device_num +=1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    if daughterboard_a == None:
      append_to_file(CMD_FILE,'addDevice -p %d -file %s\\virtex5\\data\\xc5vlx330.bsd\n' % (device_num, xil_path))
    else:
      append_to_file(CMD_FILE,'addDevice -p %d -file %s\n' % (device_num, daughterboard_a))
    daughterboard_a_num = device_num
    device_num += 1
    if IS_DUAL:
      if daughterboard_b == None:
        append_to_file(CMD_FILE,'addDevice -p %d -file %s\\virtex5\\data\\xc5vlx330.bsd\n' % (device_num, xil_path))
      else:
        append_to_file(CMD_FILE,'addDevice -p %d -file %s\n' % (device_num, daughterboard_b))
      daughterboard_b_num = device_num
      device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    
    if mainboard != None:
      append_to_file(CMD_FILE,'program -p %d\n' % (mainboard_num))
    if daughterboard_a != None:
      append_to_file(CMD_FILE,'program -p %d\n' % (daughterboard_a_num))
    if daughterboard_b != None:
      append_to_file(CMD_FILE,'program -p %d\n' % (daughterboard_b_num))
    append_to_file(CMD_FILE,'quit\n')

def create_xilinx_cmd_file_lx760(mainboard, daughterboard_a, daughterboard_b):
    xil_path = os.getenv('XILINX')
    delete_existing_file(CMD_FILE)
    mainboard_num = 0
    daughterboard_a_num = 0
    daughterboard_b_num = 0

    if not IS_DUAL and daughterboard_b != None:
      debug_print('Configuration error: single daughterboard with two bitstreams provided')

    append_to_file(CMD_FILE,'setMode -bscan\n')
    append_to_file(CMD_FILE,'setCable -p auto\n')
    device_num = 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\spartan3e\\data\\xc3s500e.bsd\n' % (device_num, xil_path))
    device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\xcfp\\data\\xcf32p.bsd\n' % (device_num, xil_path))
    device_num += 1
    append_to_file(CMD_FILE,'addDevice -p %d -file %s\\virtex5\\data\\xc5vlx30t.bsd\n' % (device_num, xil_path))
    device_num += 1
    if mainboard == None:
       append_to_file(CMD_FILE,'addDevice -p %d -file %s\\virtex5\\data\\xc5vlx110.bsd\n' % (device_num, xil_path))
    else:
       append_to_file(CMD_FILE,'addDevice -p %d -file %s\n' % (device_num, mainboard))
    mainboard_num = device_num   
    device_num += 1

    if daughterboard_a == None:
      append_to_file(CMD_FILE,'addDevice -p %d -file %s\\virtex5\\data\\xc5vlx760.bsd\n' % (device_num, xil_path))
    else:
      append_to_file(CMD_FILE,'addDevice -p %d -file %s\n' % (device_num, daughterboard_a))
    daughterboard_a_num = device_num
    device_num += 1
    if IS_DUAL:
      if daughterboard_b == None:
        append_to_file(CMD_FILE,'addDevice -p %d -file %s\\virtex5\\data\\xc5vlx760.bsd\n' % (device_num, xil_path))
      else:
        append_to_file(CMD_FILE,'addDevice -p %d -file %s\n' % (device_num, daughterboard_b))
      daughterboard_b_num = device_num
      device_num += 1
    
    if mainboard != None:
      append_to_file(CMD_FILE,'program -p %d\n' % (mainboard_num))
    if daughterboard_a != None:
      append_to_file(CMD_FILE,'program -p %d\n' % (daughterboard_a_num))
    if daughterboard_b != None:
      append_to_file(CMD_FILE,'program -p %d\n' % (daughterboard_b_num))
    append_to_file(CMD_FILE,'quit\n')

def reprogram():
    result = os.system('iMPACT -batch '+CMD_FILE)
    if result != 0:
        return False
    if MEMRESET_SCRIPT != None:
        result = subprocess.call(["tclsh", MEMRESET_SCRIPT], cwd=PCILIB_FOLDER, shell=True)
    return result==0

def load_pci_configuration():
    sts = subprocess.call(["tclsh", PCICONFIG_SCRIPT, PCICONFIGRESTORE_SCRIPT], cwd=PCILIB_FOLDER, shell=True)
    return sts==0

def restore_pci_configuration():
    create_xilinx_cmd_file_lx330(ATLAS_PCISAFE, None, None)
    if not reprogram():
        return False
    sts = subprocess.call(["tclsh", PCICONFIGRESTORE_SCRIPT], cwd=PCILIB_FOLDER, shell=True)
    return sts==0    

def set_dutclock_lx330(frequency):
    if not restore_pci_configuration():
        return False
    p = subprocess.Popen(["tclsh", DUTCLOCK_SCRIPT, str(frequency)], stdout=subprocess.PIPE, cwd=PCILIB_FOLDER, shell=True)
    stdout = p.communicate()[0]
    sts=p.returncode
    lastline = ""
    if sts==0:
        lastline = stdout.split("\n")[-2]
    print stdout
    return (sts==0, lastline)

def set_dutclock_lx760(frequency):
    sts = subprocess.call(["tclsh", DUTCLOCK_SCRIPT, str(frequency)], cwd=PCILIB_FOLDER, shell=True)
    return sts==0

if __name__ == '__main__' :
    if not TCF_TYPE in ("lx330", "lx760"):
      print "ERROR: bad config, neither lx330 or lx760 based board"
      sys.exit(1)
    server = SocketServer.TCPServer(('',PORT),comms_handler)
    if not load_pci_configuration():
        print "ERROR: unable to load PCI configuration"
        sys.exit(1)
    print "PCI config loaded"
    server.serve_forever()


