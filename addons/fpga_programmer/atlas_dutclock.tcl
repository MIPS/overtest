puts "Setting clock to ${argv}MHz"
set argc 0
source pcilib.tcl
initpci
source pll.tcl
set end 0
SetDUTCoreClk 60
after 1000 set end 1
vwait end
set end 0
SetDUTInterClk 60
after 1000 set end 1
vwait end
set end 0
SetAtlasCoreClk 100
after 1000 set end 1
vwait end
set end 0


set a [expr ( [WhatFreq 0 0 2] )]
set a [expr ( $a / 2 )]
puts "Read clock as ${a}MHz"

set a [expr ( ${argv} * 2 )]
SetDUTCoreClk $a
after 1000 set end 1
vwait end
set end 0

SetDUTInterClk $a

set a [expr ( [WhatFreq 0 0 2] )]
set a [expr ( $a / 2 )]
puts "Read clock as ${a}MHz"
