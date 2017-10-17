FPGA resources can be programmed remotely by using the client and server
provided here.

The server 'fpga_reprog_server2.py' runs on a windows machine with a xilinx USB
progrmmaing module attached and the xilinx ISE installed. It can be configured
to support an lx80 or lx160 based TCF with single or dual lx330s on the 
daughterboard. See script for further details.

The client 'program_fpga2.py' runs on a linux machine and is given the hostname
of the server along with one or more bitstreams to load. The mainboard (-m), 
first FPGA (-a) and the second FPGA (-b).
