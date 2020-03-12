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
import os
from Action import Action
from Config import CONFIG
from IMGAction import IMGAction
from common.KernelTest import KernelTest
# META Linux LTP

class A112263(Action, IMGAction, KernelTest):
  def __init__(self, data):
    Action.__init__(self, data)
    self.actionid = 112263
    self.name = "META Linux LTP"
    self.umask = 0

  # Execute the action.
  def run(self):
    """
    Use the KernelTest framework to grab a pre-built buildroot, kernel and test framework
    Tweak the filesystem so that it has the correct startup scripts
    Use the KernelTest framework to Rebuild the filesystem
    Build LTP
    Use the KernelTest framework to Put the bootable package together
    Use the KernelTest framework to Run the test
    Process the results
    """

    if not self.fetchLinuxBuildSystem():
      return False

    # Adjust the filesystem
    path = os.path.join(self.testbench_dir, "prepare_test.sh")

    ltp_override={}
    # Kernel options required by LTP tests
    ltp_override["CONFIG_ELF_CORE"] = "y"
    ltp_override["CONFIG_SYSVIPC"] = "y"
    ltp_override["CONFIG_SYSVIPC_SYSCTL"] = "y"
    ltp_override["CONFIG_SYSCTL_SYSCALL"] = "y"
    ltp_override["CONFIG_BSD_PROCESS_ACCT"] = "y"
    ltp_override["CONFIG_BSD_PROCESS_ACCT_V3"] = "y"
    # Networking options
    ltp_override["CONFIG_NET"] = "y"
    ltp_override["CONFIG_INET"] = "y"
    ltp_override["CONFIG_NLATTR"] = "y"
    ltp_override["CONFIG_POSIX_MQUEUE"] = "y"
    ltp_override["CONFIG_TASKSTATS"] = "n"
    ltp_override["CONFIG_AUDIT"] = "n"
    ltp_override["CONFIG_PACKET"] = "y"
    ltp_override["CONFIG_UNIX"] = "y"
    # The rest of network options are disabled by default
    for netopt in ('CONFIG_UNIX_DIAG', 'CONFIG_XFRM_USER', 'CONFIG_XFRM_SUB_POLICY',
                'CONFIG_XFRM_MIGRATE', 'CONFIG_XFRM_STATISTICS','CONFIG_NET_KEY',
                'CONFIG_NET_KEY', 'CONFIG_IP_MULTICAST', 'CONFIG_IP_PNP',
                'CONFIG_IP_ADVANCED_ROUTER', 'CONFIG_NET_IPIP','CONFIG_NET_IPGRE_DEMUX',
                'CONFIG_ARPD', 'CONFIG_SYN_COOKIES', 'CONFIG_INET_AH','CONFIG_INET_ESP',
                'CONFIG_INET_IPCOMP', 'CONFIG_INET_XFRM_MODE_TRANSPORT',
                'CONFIG_INET_XFRM_MODE_TUNNEL', 'CONFIG_INET_XFRM_MODE_BEET',
                'CONFIG_INET_LRO', 'CONFIG_INET_DIAG', 'CONFIG_TCP_CONG_ADVANCED',
                'CONFIG_TCP_MD5SIG', 'CONFIG_IPV6', 'CONFIG_NETWORK_SECMARK',
                'CONFIG_NETWORK_PHY_TIMESTAMPING', 'CONFIG_NETFILTER',
                'CONFIG_IP_DCCP', 'CONFIG_IP_SCTP', 'CONFIG_RDS', 'CONFIG_TIPC',
                'CONFIG_ATM', 'CONFIG_L2TP', 'CONFIG_BRIDGE', 'CONFIG_VLAN_8021Q',
                'CONFIG_DECNET', 'CONFIG_LLC2', 'CONFIG_IPX', 'CONFIG_ATALK', 
                'CONFIG_X25', 'CONFIG_LAPB', 'CONFIG_ECONET', 'CONFIG_WAN_ROUTER',
                'CONFIG_PHONET', 'CONFIG_IEEE802154', 'CONFIG_NET_SCHED',
                'CONFIG_DCB', 'CONFIG_BATMAN_ADV', 'CONFIG_OPENVSWITCH',
                'CONFIG_NET_PKTGEN', 'CONFIG_HAMRADIO', 'CONFIG_CAN', 'CONFIG_IRDA',
                'CONFIG_BT', 'CONFIG_AF_RXRPC', 'CONFIG_WIRELESS',
                'CONFIG_WIMAX', 'CONFIG_RFKILL', 'CONFIG_NET_9P', 'CONFIG_CAIF',
                'CONFIG_CEPH_LIB', 'CONFIG_NFC', 'CONFIG_CONNECTOR',
                'CONFIG_BLK_DEV_NBD', 'CONFIG_ATA_OVER_ETH', 'CONFIG_BLK_DEV_RBD',
                'CONFIG_NETDEVICES', 'CONFIG_ISDN', 'CONFIG_N_GSM','CONFIG_NETWORK_FILESYSTEMS'):
      ltp_override[netopt] = "n"
    
    target_board = self.getResource("Target Board")
    board_type = target_board.getAttributeValue("Board Type")    
    if board_type == "FPGA":
      ltp_fpga=True
      # No nfs on FPGAs. We need to store results locally and get them via DAFS
      ltp_override["CONFIG_IMGDAFS_FS"] = "y"
      if self.execute(workdir=self.buildroot_dir,
                    command=[path, "ltp", "local", "nfs", self.nfs_server]) != 0:
        self.error("Failed to adjust filesystem to boot to LTP")
    else:
      ltp_fpga=False
      if self.execute(workdir=self.buildroot_dir,
                    command=[path, "ltp", "nfs", self.nfs_server]) != 0:
        self.error("Failed to adjust filesystem to boot to LTP")
    
    if self.version == "ltp-20090831-metag-linux-p1":
      ltp_incvs=True
    else:
      ltp_incvs=False

    env = {}
    env['PATH'] = "%s:%s" % (self.compiler_path, os.environ['PATH'])

    # Choose the correct repository to use
    ltp_module = "ltp"
    if not ltp_incvs:
      if not self.version == "Latest":
        ltp_metag_ref = self.version
      else:
        ltp_metag_ref = "metag"
      ltp_git = "git://git.le.imgtec.org/"+ltp_module
    else:
      host = self.getResource("Execution Host")
      cvsroot = host.getAttributeValue("LEEDS CVSROOT")

    ltp_dir = os.path.join(self.getWorkPath(), ltp_module)
    
    if ltp_incvs:
      if not self.cvsCheckout(ltp_module, cvsroot, self.version):
	    self.error("Failed to check out LTP")
    else:
      if not self.gitExport(uri=ltp_git, tag=ltp_metag_ref):
        self.error("Failed to export LTP")

    # Old cvs build system
    if ltp_incvs:
      if self.execute(workdir=ltp_dir,
                    env=env,
                    command=["make", "CROSS_COMPILER=metag-linux-"]) != 0:
        self.error("Failed to build LTP")

      if self.execute(workdir=os.path.join(ltp_dir, "testcases"),
                    env=env,
                    command=["make", "CROSS_COMPILER=metag-linux-","CC=metag-linux-gcc", "install"]) != 0:
        self.error("Failed to build LTP testcases")

      if self.execute(workdir=os.path.join(ltp_dir, "tools"),
                    env=env,
                    command=["make", "CROSS_COMPILER=metag-linux-", "install"]) != 0:
        self.error("Failed to build LTP tools")
    else:
      # Autotools build system in new Git repository
      if ltp_fpga:
        ltp_prefix=self.buildroot_dir+"/output/target/testbench/ltp"
      else:
        ltp_prefix=self.getWorkPath()+"/ltp"
      if self.execute(workdir=ltp_dir,
                    env=env,
                    command=["./configure","--host=metag-linux","--prefix="+ltp_prefix]):
        self.error("Failed to configure LTP")
      if self.execute(workdir=ltp_dir,
                    env=env,
                    command=["make"]):
        self.execute("Failed to build LTP")
      if self.execute(workdir=ltp_dir,
                    env=env,
                    command=["make", "install"]):
        self.execute("Failed to install LTP")
      if self.execute(workdir=ltp_dir,
                    env=env,
                    command=["sh", "scripts/clean-target.sh"]):
        self.execute("Failed to remove unused testcases")
    
    ltp_config=[]
    if not ltp_incvs:
      # New LTP requires bash for getopts
      ltp_config.append("BR2_PACKAGE_BASH=y")

    if not self.rebuildFilesystem(extraconfig=ltp_config):
      return False

    if not self.buildKernel(config_override=ltp_override):
      return False

    if not self.prepareBootloader():
      return False

    if ltp_fpga:
      rawresult_log_file = os.path.join(self.getWorkPath(), "meta-bootloader", "ltpoutput.txt")
      result_log_file = os.path.join(self.getWorkPath(), "meta-bootloader", "ltprun.log")
    else:
      rawresult_log_file = os.path.join(self.getWorkPath(), "run", "ltpoutput.txt")
      result_log_file = os.path.join(self.getWorkPath(), "run", "ltprun.log")
    
    if self.executeKernelTest():
      self.processResults(result_log_file)

    self.registerLogFile(rawresult_log_file)
    self.registerLogFile(result_log_file)

    return True

  def processResults(self, result_file_name):
    """
    Extract the names and results of tests
    """

    summary = {}
    try:
      result_file = open(result_file_name)
    except IOError:
      return self.success({"Result Error":"No result file found"})

    lines = result_file.readlines()[5:-8]
    result_file.close()

    summary['Pass'] = 0
    summary['Fail'] = 0
    for l in lines:
      vals = ";".join(l.split()).split(";")
      passed = vals[1] == "PASS"
      self.testsuiteSubmit(vals[0], passed, {"Exit Code":int(vals[2])})
      if passed:
        summary['Pass'] += 1
      else:
        summary['Fail'] += 1

    self.success(summary)

    return True

