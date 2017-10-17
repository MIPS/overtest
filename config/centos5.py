"""
Module for CentOS 5 config
"""
import config.centos45

class Config(config.centos45.Config):
  """
  CentOS 5 default config
  """
  python = "/user/rgi_data2/Verify/CentOS-5/Python_2.7.2/root/bin/python"
  cmake = "/user/rgi_data2/Verify/CentOS-5/CMake_3.1.3_x64/bin/cmake"
  git = "/user/rgi_data2/Verify/CentOS-6/Git_2.14.2_x64/root/bin/git"
