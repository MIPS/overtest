"""
The config for Overtest. 
"""
import socket
import ConfigFactory

CONFIG = ConfigFactory.configFactory(socket.gethostname())
