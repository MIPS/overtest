"""
Module for CentOS 4.5 config
"""
import config.linux

class Config(config.linux.Config):
  """
  CentOS 4.5 default config
  """
  ccs = "/user/rgi_data2/Verify/CentOS-4/CoreSWTools_1.0.0.1/root/ccs"
  python = "/user/rgi_data2/Verify/CentOS-4/Python_2.7.2/root/bin/python"
  git = "/user/rgi_data2/Verify/CentOS-4/Git_1.7.4/root/bin/git"
  perl = "/user/rgi_data2/Verify/CentOS-4/Perl_5.14.1/root/bin/perl"
  cmake = "/user/rgi_data2/Verify/CentOS-4/CMake_2.8.4/root/bin/cmake"
