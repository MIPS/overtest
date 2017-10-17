source pcilib.tcl
initpci
set fp [open $argv w]

puts $fp "source pcilib.tcl"
puts $fp "initpci"
puts $fp "PCI_WriteCfg32 0x4  [PCI_ReadCfg32 0x4]"
puts $fp "PCI_WriteCfg32 0xc  [PCI_ReadCfg32 0xc]"
puts $fp "PCI_WriteCfg32 0x10 [PCI_ReadCfg32 0x10]"
puts $fp "PCI_WriteCfg32 0x14 [PCI_ReadCfg32 0x14]"
puts $fp "PCI_WriteCfg32 0x18 [PCI_ReadCfg32 0x18]"

