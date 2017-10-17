puts "Setting clock to ${argv}MHz"

source pcilib.tcl
initpci

set a [expr ( [PCI_Read32 0 0x1048] )]
puts "Read clock as ${a}MHz"

PCI_Write32 0 0x1048 ${argv}
PCI_Write32 0 0x1058 1

set a [expr ( [PCI_Read32 0 0x1048] )]
puts "Read clock as ${a}MHz"
