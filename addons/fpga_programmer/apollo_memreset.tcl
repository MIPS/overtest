puts "Resetting memory interface"

source pcilib.tcl
initpci

set a [PCI_Read32 0 0x80]
puts "Read tcf_ctrl as ${a}"

PCI_Write32 0 0x80 0

set a [PCI_Read32 0 0x80]
puts "Read tcf_ctrl as ${a}"

PCI_Write32 0 0x80 0x2041F

set a [PCI_Read32 0 0x80]
puts "Read tcf_ctrl as ${a}"