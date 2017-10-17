# PLL Freq Set Using scb_i2c Interface
# Daniel Aldridge
# 19/09/2006

source [file join [file dirname [info script]] scb.tcl]
# source [file join [file dirname [info script]] pll_configs_Atlas.tcl]

# Global Variables

set ::DataErrors 0
set ::PLL_Addr 0x6A
set ::D_config(0,0) 0x10
set ::D_config(0,1) 0x11
set ::D_config(0,2) 0x12
set ::D_config(0,3) 0x13
set ::D_config(1,0) 0x28
set ::D_config(1,1) 0x29
set ::D_config(1,2) 0x2A
set ::D_config(1,3) 0x2B
set ::D_config(2,0) 0x40
set ::D_config(2,1) 0x41
set ::D_config(2,2) 0x42
set ::D_config(2,3) 0x43
set ::N_config_lower(0,0) 0x14
set ::N_config_lower(0,1) 0x15
set ::N_config_lower(0,2) 0x16
set ::N_config_lower(0,3) 0x17
set ::N_config_lower(1,0) 0x2C
set ::N_config_lower(1,1) 0x2D
set ::N_config_lower(1,2) 0x2E
set ::N_config_lower(1,3) 0x2F
set ::N_config_lower(2,0) 0x44
set ::N_config_lower(2,1) 0x45
set ::N_config_lower(2,2) 0x46
set ::N_config_lower(2,3) 0x47
set ::N_config_upper(0,0) 0x18
set ::N_config_upper(0,1) 0x19
set ::N_config_upper(0,2) 0x1A
set ::N_config_upper(0,3) 0x1B
set ::N_config_upper(1,0) 0x30
set ::N_config_upper(1,1) 0x31
set ::N_config_upper(1,2) 0x32
set ::N_config_upper(1,3) 0x33
set ::N_config_upper(2,0) 0x48
set ::N_config_upper(2,1) 0x49
set ::N_config_upper(2,2) 0x4A
set ::N_config_upper(2,3) 0x4B

set ::RZ_config(0,0) 0x08
set ::RZ_config(0,1) 0x09
set ::RZ_config(0,2) 0x0A
set ::RZ_config(0,3) 0x0B
set ::CPCZ_config(0,0) 0x0C
set ::CPCZ_config(0,1) 0x0D
set ::CPCZ_config(0,2) 0x0E
set ::CPCZ_config(0,3) 0x0F

set ::RZ_config(1,0) 0x20
set ::RZ_config(1,1) 0x21
set ::RZ_config(1,2) 0x22
set ::RZ_config(1,3) 0x23
set ::CPCZ_config(1,0) 0x24
set ::CPCZ_config(1,1) 0x25
set ::CPCZ_config(1,2) 0x26
set ::CPCZ_config(1,3) 0x27

set ::RZ_config(2,0) 0x38
set ::RZ_config(2,1) 0x39
set ::RZ_config(2,2) 0x3A
set ::RZ_config(2,3) 0x3B
set ::CPCZ_config(2,0) 0x3C
set ::CPCZ_config(2,1) 0x3D
set ::CPCZ_config(2,2) 0x3E
set ::CPCZ_config(2,3) 0x3F
set ::SRCBlock1 0x34
set ::SRCBlock2 0x35
set ::OutConf(2) 0x4D
set ::OutConf(3) 0x51
set ::OutConf(4) 0x55
set ::OutConf(5) 0x59
set ::OutConf(6) 0x5D
set ::Divby1  0x11
set ::Divby2  0x22
set ::Divby3  0x33
set ::pll_reg_def_addr {}
set ::pll_reg_def_val {}
lappend   ::pll_reg_def_addr   0x05
lappend   ::pll_reg_def_addr   0x06
lappend   ::pll_reg_def_addr   0x1d
lappend   ::pll_reg_def_addr   0x34
lappend   ::pll_reg_def_addr   0x35
lappend   ::pll_reg_def_addr   0x4d
lappend   ::pll_reg_def_addr   0x51
lappend   ::pll_reg_def_addr   0x54
lappend   ::pll_reg_def_addr   0x55
lappend   ::pll_reg_def_addr   0x58
lappend   ::pll_reg_def_addr   0x59
lappend   ::pll_reg_def_addr   0x5c
lappend   ::pll_reg_def_addr   0x5d
lappend   ::pll_reg_def_val   0xFF
lappend   ::pll_reg_def_val   0x30
lappend   ::pll_reg_def_val   0x40
lappend   ::pll_reg_def_val   0x46
lappend   ::pll_reg_def_val   0x55
lappend   ::pll_reg_def_val   0xBB
lappend   ::pll_reg_def_val   0xBB
lappend   ::pll_reg_def_val   0x0C
lappend   ::pll_reg_def_val   0xBB
lappend   ::pll_reg_def_val   0x0C
lappend   ::pll_reg_def_val   0xBB
lappend   ::pll_reg_def_val   0x03
lappend   ::pll_reg_def_val   0xBB


#######################################################
# Function Name	:	NumtoHex
# Inputs 	:       string with decimal number
# Returns	:       string with hex number
# Description	:	Convert Number value into hex value
######################################################
proc NumtoHex {Data} {
   if {$Data == 0} {
      return 0x00
   } else {
      return [format "%#04x" $Data]
   }
}

######################################################
# Function Name	:	SetPllDefs
# Inputs 	:
# Returns	:       Nothing
# Description	:	Sets the PLL's register bank to its
#                       default value
######################################################
proc SetPLLDefs {PLL {KeepTrying 1}} {
   set errors 0
   SelectBus $PLL
   for {set i 111} {$i > 3} {incr i -1} {
      set HasVal [lsearch $::pll_reg_def_addr [NumtoHex $i]]
      if {$HasVal != -1} {
         set ToWrite  [lindex $::pll_reg_def_val $HasVal]
         } else {
         set ToWrite 0x00
      }
      ProgWrite [NumtoHex $i] $ToWrite 1
      if { [ProgRead [NumtoHex $i] 1  0] != $ToWrite} {
         if {$KeepTrying} {
            incr i 1
         }
         incr errors 1
         puts "Address [NumtoHex $i] did not restore to default data was $::Global_Data(0) not $ToWrite"
      }
   }
   if {$errors > 0} {
      puts "\n PLL $PLL Not saved error in writing"
   } else {
      after 500 # allow write to be saved in registers before save
      ProgSave $PLL
      puts "\n PLL $PLL set to default"
   }
}

#######################################################
# Function Name	:
# Inputs 	:
# Description   :
######################################################
proc TurnOutsOff {} {
   for {set i 2 } {$i <= 6 } {incr i} {
      ProgWrite $::OutConf($i) 0x00 1
      ProgWrite [expr $::OutConf($i) + 1]  0x00 1
      ProgWrite [expr $::OutConf($i) + 2]  0x00 1
   }
}

#######################################################
# Function Name	:	ProgWrite
# Inputs 	:	DataAddr Data
# Description	:	Implerments the ProgWrite routine as exampled in the
#			5v9885 data sheet
######################################################
proc ProgWrite {DataAddr Data {Check 0} } {
   set DataToSend(0) 0x00
   set DataToSend(1) $DataAddr
   set DataToSend(2) $Data
   ;#puts "Writing to $DataAddr"
   WriteManyBytes $::PLL_Addr DataToSend
   if {$Check} {
      if {[ProgRead $DataAddr 1 0] != $Data} {
         puts "Error Data Mismatch"
         if {$::debug} {puts "DEBUG::--- data was $::Global_Data(0) , second $::Global_Data(1), should be[NumtoHex $Data]"}
         set ::DataErrors [expr $::DataErrors + 1]
      }
   }
}

#######################################################
# Function Name	:	ProgRead
# Inputs 	:	DataAddr HowMany
# Returns	:	Fills Global_Data
# Description	:
######################################################
proc ProgRead {DataAddr {HowMany 1} {Display 1}} {
   global Global_Data
   set ::Global_Data(0) 0x00
   set ::Global_Data(1) 0x00
   set ToRead(0) 0x00
   set ToRead(1) $DataAddr ;
   set HowMany [expr $HowMany +1];# to compensate for id of 0x10 read before data
   WriteManyBytes $::PLL_Addr ToRead
   ReadManyBytes $HowMany
   WriteManyBytes $::PLL_Addr ToRead
   ReadManyBytes $HowMany
   for {set q 0} {$q < 1} {incr q} {
      if {$Display} { puts "Data in position $q is $::Global_Data($q)" }
   }
   return $::Global_Data(0)
}

#######################################################
# Function Name	:	LoadPLL
# Inputs 	:       PLL number filename and display
# Returns	:
# Description	:
######################################################
proc LoadPLL {PLL filename {Display 0}} {
   SelectBus $PLL
   if {($filename != "") & [file exists $filename.pll]} {
      set res [open "$filename.pll" "r"]
      puts "\n File Opened"

      for {set i 111} {$i > 3} {incr i -1} {
         set data [gets $res]
         if {$data != ""} {ProgWrite [NumtoHex $i] $data 1}
         if {$Display} {puts "\n Address :- [NumtoHex $i] Value :- $data"}
      }
   } else {
      puts "\n Unable to Find File"
      set ::DataErrors [expr $::DataErrors + 1]
   }
}

#######################################################
# Function Name	:	ReadBackPLL
# Inputs 	:       PLL number
# Returns	:       PLL's register values
# Description	:	 Reads All PLL's Register vaules and stores in array
######################################################
proc ReadBackPLL {PLL filename {Display 0}} {
   if {$filename != ""} {
      set res [open "$filename.pll" "w"]
   }
   SelectBus $PLL
   for {set i 111} {$i > 3} {incr i -1} {
      ProgRead [NumtoHex $i] 1 0
      set ::PLLReadData([NumtoHex $i]) [NumtoHex $::Global_Data(0)]
						if {$filename != ""} {
         puts $res "$::PLLReadData([NumtoHex $i])"
      }
      if {$Display} {
         puts "Address :- [NumtoHex $i] Value :- $::PLLReadData([NumtoHex $i])"
      }
   }
   if {$filename != ""} {
      close $res
   }
}

#######################################################
# Function Name	:	ProgSave
# Inputs 	:
# Returns	:
# Description	:
######################################################
proc ProgSave {PLL} {
   SelectBus $PLL
   set ToSave  0x01
   WriteAByte $::PLL_Addr $ToSave
   return ""
}

#######################################################
# Function Name	:	ProgStore
# Inputs 	:
# Returns	:
# Description	:
######################################################
proc ProgStore {PLL} {
   SelectBus $PLL
   set ToStore 0x02
   WriteAByte $::PLL_Addr $ToStore
   return ""
}

proc ClearPLLs {} {
   SetPLLDefs 1 0
   for {set i 0} {$i < 4} {incr i} {
      after 500
   }
   SetPLLDefs 0 0
      after 500
}

#######################################################
# Function Name	:	SetSwitchMatrix
# Inputs 	:
# Returns	:
# Description	:
######################################################
proc SetSwitchMatrix {Outputs} {
   upvar $Outputs Outs
   set SRC63 0x00
   set SRC21 0x00
   for {set i 0} {$i <= 3} {incr i} {
      set  SRC63 [expr [expr $SRC63 << 2] + [expr $Outs($i) + 0]]
   }
   set ToKeep 0x46
   for {set i 4} {$i <= 5} {incr i} {
      set SRC21 [expr [expr $SRC21 << 2] + [expr $Outs($i) + 0]]
   }
  set SRC21 [expr [expr $SRC21 << 4] || [expr $ToKeep & 0x0F]]
  ProgWrite $::SRCBlock1 [NumtoHex $SRC21]
  ProgWrite $::SRCBlock2 [NumtoHex $SRC63]
}

proc SetDconfig {Num Value} {
   for {set i 0} {$i < 4} {incr i} {
      ProgWrite $::D_config($Num,$i) $Value 1
   }
}

proc SetNconfigLower {Num Value} {
   for {set i 0} {$i < 4} {incr i} {
      ProgWrite $::N_config_lower($Num,$i) $Value 1
   }
}

proc SetNconfigUpper {Num Value} {
   for {set i 0} {$i < 4} {incr i} {
      ProgWrite $::N_config_upper($Num,$i) $Value 1
   }
}

proc SetRCC {InnerPLL Rz Cp Cz} {
   set Rz [expr $Rz & 0x0F]
   for {set i 0} {$i < 4} {incr i} {
      ProgWrite $::RZ_config($InnerPLL,$i) $Rz 1
   }
   set CpCz [expr [expr $Cp << 4] + $Cz]
   for {set i 0} {$i < 4} {incr i} {
      ProgWrite $::CPCZ_config($InnerPLL,$i) $CpCz 1
   }
}

proc CheckCRC {PLL} {
   ProgSave $PLL
   for {set i 0} {$i < 45} {incr i} {
      after 1 ;# Give PLL time to save and reload PROM data
   }
   ProgStore $PLL
   for {set i 0} {$i < 45} {incr i} {
      after 1;# Give PLL time to save and reload PROM data
   }
   ProgRead 0x81 1 0
   set CRC [expr 0x00000010 & $::Global_Data(0)]
   if {$CRC} {
      puts "\n CRC Error Data at PLL $PLL Not Saved"
   } else {
      puts "\n PLL $PLL Programed and Saved."
   }
}

proc InitReads {} {
  # ProgRead 0x05 1 0
  # ProgRead 0x04 1 0
  # ProgRead 0x05 1 0
  # ProgRead 0x04 1 0
}

proc FindCoeffs {output {input 27} {minmulti 720} {mininput 1} {maxerr .06}} {

   set ::posscoeffs {}
   set output [expr $output * 2]
   set input [expr double($input)]
   set maxmulti 1100
   set m 1
   if {$output == 0} {set output $input ; puts "0Hz changed to input freq"}
   set post [expr int($maxmulti / $output)]
   set startmulti [expr $post * $output]
   set tryinput $input
   while {$tryinput >= $mininput} {
      incr m
      set n 1.00
      set potmulti $startmulti
      while {$potmulti > $minmulti} {
         if { [expr abs([expr double($potmulti) / double($tryinput)] -[expr round($potmulti / double($tryinput))]) ] < $maxerr} {
            ;#puts "Pre-Divider = [expr $m -1], Multiplier = [expr round(double($potmulti) / $tryinput)], Post Divider = [expr $post - $n + 1], VCO = [expr double($potmulti)]"
            lappend ::posscoeffs [expr $m -1] [expr round(double($potmulti) / $tryinput)] [expr $post - $n + 1] [expr double($potmulti)]
            ;#return "[expr $m -1],[expr round(double($potmulti) / $tryinput)],[expr $post - $n + 1]"
            }
      set potmulti [expr ($post - $n) * $output]
      set n [expr $n + 1]
      }
      set tryinput [expr double($input / $m)]
   }
   if {[llength $::posscoeffs] == 0} { lappend ::posscoeffs 0 0 0 ; puts "Error No Values In Range"}
   return $::posscoeffs
}

proc SetCoeffs {PLL coeffstring} {
   if {$PLL == 2} {
      set D [string range $coeffstring 0 [expr [string first "," $coeffstring] - 1]]
      set coeffstring [string range $coeffstring [expr [string first "," $coeffstring] + 1] end]
      set M $coeffstring
      set Nlower [expr $M & 0xFF]
      set Nupper [expr ($M & 0xF00) >> 8]
      SetDconfig 2 $D
      SetNconfigLower 2 $Nlower
      SetNconfigUpper 2 $Nupper
      SetRCC 2 0xF 0xF 0xF
   } else {
      set D [string range $coeffstring 0 [expr [string first "," $coeffstring] - 1]]
      set coeffstring [string range $coeffstring [expr [string first "," $coeffstring] + 1] end]
      set M $coeffstring

      if {[expr $M % 2] == 0} {
									set M [expr $M / 2]
         set A 0x00
         set Nlower [expr $M & 0xFF]
         set Nupper [expr [expr ($M & 0xF00) >> 8] | [expr $A << 4]]
      } else {
         set M [expr ($M - 3) / 2]
         set A 0x02
         set Nlower [expr $M & 0xFF]
         set Nupper [expr [expr ($M & 0xF00) >> 8] | [expr $A << 4]]
      }
      if {$PLL == 1} {
         SetDconfig 1 $D
         SetNconfigLower 1 $Nlower
         SetNconfigUpper 1 $Nupper
         SetRCC 1 0xF 0xF 0xF
      }
      if {$PLL == 0} {
         SetDconfig 0 $D
         SetNconfigLower 0 $Nlower
         SetNconfigUpper 0 $Nupper
         SetRCC 0 0xF 0xF 0xF
      }
   }
}

#######################################################
# Function Name	:	SetDiv
######################################################
proc SetOutputDiv {Output Value} {
   set Value [expr int($Value)]
   set Output [expr int($Output)]
   if {$Value == 1} {
      ProgWrite $::OutConf($Output) $::Divby1 1
   } elseif {$Value == 2} {
     ProgWrite $::OutConf($Output) $::Divby2 1
   } else {
      set LowerVal [expr ($Value - 2) & 0x0000003]
      set UpperVal [expr ($Value -2) & 0xFC]
      ProgWrite $::OutConf($Output) [NumtoHex [expr [expr $LowerVal << 6] | [expr $LowerVal << 2] | $::Divby3]] 1
						ProgWrite [NumtoHex [expr $::OutConf($Output) + 1]] [NumtoHex [expr $UpperVal >> 2]] 1
      ProgWrite [NumtoHex [expr $::OutConf($Output) + 2]] [NumtoHex [expr $UpperVal >> 2]] 1

   }
}

proc SetPLLtoOut {PLL Output} {
   if {$PLL == 0} {set pllval 0x01}
   if {$PLL == 1} {set pllval 0x02}
   if {$PLL == 2} {set pllval 0x03}
   if {$Output < 3} {
      set ToKeep [ProgRead $::SRCBlock1 1 0]
      set ToWrite [expr [expr $pllval << [expr ($Output - 2 + 3) *2]] | [expr $ToKeep & [expr 0xFF ^ [expr 0x03 << [expr ($Output -2 + 3) *2 ]]]]]
						ProgWrite $::SRCBlock1 $ToWrite  1
    } else {
      set ToKeep [ProgRead $::SRCBlock2 1 0]
      set ToWrite [expr [expr $pllval << [expr ($Output - 3) * 2 ]] | [expr $ToKeep & [expr 0xFF ^ [expr 0x03 << [expr ($Output -3) * 2]]]]]
						ProgWrite $::SRCBlock2 $ToWrite 1
   }
}

proc SetFreq {PLL} {

   SelectBus $PLL

   puts "Out 2 Freq :-"
   set out2freq [gets stdin]
   puts "Out 3 Freq :-"
   set out3freq [gets stdin]
   puts "Out 4 Freq :-"
   set out4freq [gets stdin]
   puts "Out 5 Freq :-"
   set out5freq [gets stdin]
   puts "Out 6 Freq :-"
   set out6freq [gets stdin]

   set outposs(2) [FindCoeffs $out2freq]
   set outposs(3) [FindCoeffs $out3freq]
   set outposs(4) [FindCoeffs $out4freq]
   set outposs(5) [FindCoeffs $out5freq]
   set outposs(6) [FindCoeffs $out6freq]
   set posscols 4
   set outpossvcouni(2) {}
   set outpossvcouni(3) {}
   set outpossvcouni(4) {}
   set outpossvcouni(5) {}
   set outpossvcouni(6) {}
   set outposspostuni(2) {}
   set outpospostsuni(3) {}
   set outpospostsuni(4) {}
   set outpospostsuni(5) {}
   set outpospostsuni(6) {}
   set vcos {}
   set vcoouts() {}
   set outvco() 0
   set got {}
   set need {2 3 4 6}
   set allvcos {}
   set maxouts {}
   set maxoutsvco {}
   set neededvcos {}
   set vcooutsfinal() {}
   set PLL(0) "0,0,0"
   set PLL(1) "1,0,0"
   set PLL(2) "2,0,0"

   for {set k 2} {$k <= 6} {incr k} {
      for {set m 0} {$m < [llength $outposs($k)]} {incr m $posscols} {
         lappend outpossvco($k)    [lindex $outposs($k) [expr $m + 3]]
         lappend outposspost($k)   [lindex $outposs($k) [expr $m + 2]]
         lappend outpossmulti($k)  [lindex $outposs($k) [expr $m + 1]]
         lappend outposspre($k)    [lindex $outposs($k) [expr $m + 0]]
      }
   }

   for {set p 2} {$p <= 6 } {incr p} {
      for {set n 0} {$n < [llength $outpossvco($p)]} {incr n} {
         if {[lsearch $outpossvcouni($p) [lindex $outpossvco($p) $n]] == -1} {
            lappend outpossvcouni($p)    [lindex $outpossvco($p) $n]
            lappend outposspostuni($p)   [lindex $outposspost($p) $n]
            lappend outpossmultiuni($p)  [lindex $outpossmulti($p) $n]
            lappend outposspreuni($p)    [lindex $outposspre($p) $n]
         }
      }
   }

   for {set i 2} {$i <= 6} {incr i} {
      for {set j [expr $i + 1]} {$j <= 6} {incr j} {
         for {set k 0} { $k < [expr [llength $outpossvcouni($i)]]} {incr k} {
            for {set l 0} { $l < [expr [llength $outpossvcouni($j)]]} {incr l} {
               if {[lindex $outpossvcouni($i) $k] == [lindex $outpossvcouni($j) $l] & [lindex $outpossvcouni($i) $k] != 0} {
                  if {[lsearch $vcos [lindex $outpossvcouni($j) $l]] == -1} {
                     lappend vcos [lindex $outpossvcouni($j) $l]
                     set vcoouts([lindex $outpossvcouni($j) $l]) {}
                  }
                  if {[lsearch $vcoouts([lindex $outpossvcouni($j) $l]) $i] == -1} {
                     lappend vcoouts([lindex $outpossvcouni($j) $l]) $i
                  }
                  if {[lsearch $vcoouts([lindex $outpossvcouni($j) $l]) $j] == -1} {
                     lappend vcoouts([lindex $outpossvcouni($j) $l]) $j
                  }
               }
            }
         }
      }
   }

   for {set q 0} {$q < [llength $vcos]} {incr q} {
      lappend maxouts [llength $vcoouts([lindex $vcos $q])]
      lappend maxoutsvco [lindex $vcos $q]
   }

   for {set x 0} {$x < [llength $maxouts]} {incr x} {
      for {set y 0} {$y < [llength $vcoouts([lindex $maxoutsvco $x])]} {incr y} {
         if {[lsearch $got [lindex $vcoouts([lindex $maxoutsvco $x]) $y]] == -1} {
            puts "Setting outvco [lindex $vcoouts([lindex $maxoutsvco $x]) $y ] to be  [lindex $maxoutsvco $x]"
           	lappend vcooutsfinal([lindex $maxoutsvco $x]) [lindex $vcoouts([lindex $maxoutsvco $x]) $y ]
            set number [lindex $vcoouts([lindex $maxoutsvco $x]) $y ]
            set outpost($number) [lindex $outposspostuni($number) [lsearch $outpossvcouni($number) [lindex $maxoutsvco $x]]]
            if {[lsearch $neededvcos [lindex $maxoutsvco $x]] == -1} {lappend neededvcos [lindex $maxoutsvco $x]}
               set outvco([lindex $vcoouts([lindex $maxoutsvco $x]) $y ]) [lindex $maxoutsvco $x]
               lappend got [lindex $vcoouts([lindex $maxoutsvco $x]) $y ]
            if {[lsearch $need [lindex $vcoouts([lindex $maxoutsvco $x]) $y]] != -1} {
               set need [lreplace $need [lsearch $need [lindex $vcoouts([lindex $maxoutsvco $x]) $y ]] [lsearch $need [lindex $vcoouts([lindex $maxoutsvco $x]) $y ]] ""]
            }
        }
     }
   }

   for {set m 0} {$m < [llength $need]} {incr m} {
      if {[lindex $need $m] != {}} {
         puts "Setting outvco [lindex $need $m] to be  [lindex $outpossvcouni([lindex $need $m]) 0]"
         lappend neededvcos [lindex $outpossvcouni([lindex $need $m]) 0]
         lappend vcoouts([lindex $outpossvcouni([lindex $need $m]) 0]) [lindex $need $m]
         lappend outpossvcouni([lindex $need $m]) [lindex $outpossvcouni([lindex $need $m]) 0]
         lappend outpossmultiuni([lindex $need $m]) [lindex $outposs([lindex $need $m]) [expr [lsearch $outposs([lindex $need $m]) [lindex $outpossvcouni([lindex $need $m]) 0]] - 2]]
         lappend outpossprevcouni([lindex $need $m]) [lindex $outposs([lindex $need $m]) [expr [lsearch $outposs([lindex $need $m]) [lindex $outpossvcouni([lindex $need $m]) 0]] - 3]]
         set outpost([lindex $need $m]) [lindex $outposs([lindex $need $m]) [expr [lsearch $outposs([lindex $need $m]) [lindex $outpossvcouni([lindex $need $m]) 0]] - 1]]
									lappend vcooutsfinal([lindex $outpossvcouni([lindex $need $m]) 0]) [lindex $need $m]
      }
   }

   if {[llength $neededvcos] > 3} {
      puts "cannot generate enough vco's for current setup"
   } else {
      for {set r 0} {$r < [llength $neededvcos]} {incr r} {
         set PLL($r) "[lindex $outposspreuni([lindex $vcoouts([lindex $neededvcos $r]) 0]) [lsearch $outpossvcouni([lindex $vcooutsfinal([lindex $neededvcos $r]) 0]) [lindex $neededvcos $r]]],[lindex $outpossmultiuni([lindex $vcoouts([lindex $neededvcos $r]) 0]) [lsearch $outpossvcouni([lindex $vcoouts([lindex $neededvcos $r]) 0]) [lindex $neededvcos $r]]],"
									for {set z 0} {$z < [llength $vcooutsfinal([lindex $neededvcos $r])]} {incr z} {
            SetPLLtoOut $r [lindex $vcooutsfinal([lindex $neededvcos $r]) $z]
									}
       }
   }

   SetCoeffs 0 $PLL(0)
   SetCoeffs 1 $PLL(1)
   SetCoeffs 2 $PLL(2)

   SetOutputDiv 2 $outpost(2)
   SetOutputDiv 3 $outpost(3)
   SetOutputDiv 4 $outpost(4)
   SetOutputDiv 5 $outpost(5)
   SetOutputDiv 6 $outpost(6)
   ProgSave $PLL
   return "\n Complete"

}

proc WhatFreq {PLL InternalPLL Output {InputFreq 27}} {

   SelectBus $PLL
   set D      [ProgRead $::D_config($InternalPLL,0) 1 0]
   set NLower [ProgRead $::N_config_lower($InternalPLL,0) 1 0]
   set NUpper [ProgRead $::N_config_upper($InternalPLL,0) 1 0]
   set OutDivL [ProgRead $::OutConf($Output) 1 0]
   set OutDivH [ProgRead [expr $::OutConf($Output)+ 1] 1 0]

   if {$OutDivL == $::Divby1} {
       set Div 1
   } elseif {$OutDivL == $::Divby2} {
      set Div 2
   } else {
   set Low [expr ($OutDivL & 0x0C) >> 2]
   set Div [expr (($OutDivH & 0xF) << 2) + $Low + 2]
   }

   if {$InternalPLL == 2} {
      set M [expr double($NLower + (($NUpper & 0x0F) << 8))]
   } else {
      set A [expr ($NUpper & 0xF0) >> 4]
      if {$A == 0} {set A -1}
         set M [expr double(((2*$NLower) + (($NUpper & 0x0F) << 8)) + 1 + $A)]
   }



   set Freq [expr double((($InputFreq / $D) * $M) / $Div)]
   if {$Output > 1} {
      set ManDiv 2
   } else {
      set ManDiv 1
   }
   puts "Output Freqency is Approx [expr double($Freq / $ManDiv)]"
   return [expr double($Freq / $ManDiv) ]
}