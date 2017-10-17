#!/usr/bin/env python
#*****************************************************************************
#
#               file : $RCSfile: Dnl.py,v $
#             author : $Author: rst $
#  date last revised : $Date: 2010/11/17 14:42:47 $
#    current version : $Revision: 1.2 $
#
#          copyright : 2010 by Imagination Technologies.
#                      All rights reserved.
#                      No part of this software, either material or conceptual
#                      may be copied or distributed, transmitted, transcribed,
#                      stored in a retrieval system or translated into any
#                      human or computer language in any form by any means,
#                      electronic, mechanical, manual or otherwise, or
#                      disclosed to third parties without the express written
#                      permission of:
#                        Imagination Technologies, Home Park Estate,
#                        Kings Langley, Hertfordshire, WD4 8LZ, U.K.
#
#        description : Meta MiniBench
#
#            defines :
#
#****************************************************************************

"""Decodes a .dnl file and downloads it to the target

  Usage : 

    %s input.dnl [DA identifier]
  
    Where target identifier is the DA identifier, e.g. DA-net 2
    
    Or from python, usage is : 
    
    from CSUtils import Dnl
    from CSUtils import DAtiny
    
    Dnl.WriteFile(DAtiny, "filename.dnl")

"""
import sys
import os

undefined = None

def DecodeLine(line) : 
    """Read the line as a dnl ccommand.  Returns (address, [data]).
    
    >>> DecodeLine('12345678/abcdef;')
    (305419896L, [11259375L])
    >>> DecodeLine('12345678:12345679/abcdef;')
    (305419896L, [11259375L, 11259375L])
    >>> DecodeLine('12345678:1234567A/abcdef;')
    (305419896L, [11259375L, 11259375L, 11259375L])
    """
    try : 
        address, data = line.split('/', 1)
    except ValueError, e : 
        print "Not a valid dnl file\n"
        sys.exit(2)
        
    if data[-1] == ';' :
        data = data[:-1]
        if long(data, 16) == 0 :
          return
        
    length = 1
    range = address.find(':')
    if range != -1 : 
        begin, end = address[:range], address[range+1:]
        begin      = long(begin, 16) 
        end        = long(end, 16)       
        if begin > end : 
            print("Warning : ignoring " + line + " because begin > end")
            return None
            
        length     = end - begin + 1
    else :
        begin = long(address, 16)       
        
        
    data = [long(data, 16)] * length
    return (begin, data)


def Decode(lines) : 
    """Reads the lines as a dnl sequence, returns a list of (address, [data]) pairs."""
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line]
    lines = [line for line in lines if line[0] != '#']
    Decoded = [DecodeLine(line) for line in lines]
    return [x for x in Decoded if x] # remove empties
    
    
def Optimise(sequence) : 
    """Collapse contiguous operations in (address, [data]) pairs.
    
    >>> Optimise([(0, [1])])
    [(0, [1])]
    >>> Optimise([(0, [1, 2]), (2, [3]), (4, [5, 6])])
    [(0, [1, 2, 3]), (4, [5, 6])]
    >>> Optimise([(0, [1, 2]), (2, [3, 4]), (4, [5, 6])])
    [(0, [1, 2, 3, 4, 5, 6])]
    """
    ret = []    
    current_address = -1
    current_data = []
    for address, data in sorted(sequence) : 
        if address == current_address + len(current_data) : 
            current_data.extend(data)
        else : 
            if current_data :
                ret.append((current_address, current_data))
            current_address = address
            current_data    = list(data)
            
    if current_data :
        ret.append((current_address, current_data))
    return ret


def DecodeAddress(line):
    """Read the line as a dnl command. Returns ([address], data).
     
     >>>DecodeAddress(12345678/abcdef;')
     (305419896L, [11259375L])
     >>>DecodeAddress('12345678:12345679/abcdef;')
     ([305419896L, 305419897L], 11259375L)
     >>>DecodeAddress('12345678:1234567A/abcdef;')
     ([305419896L, 305419897L, 305419898L], 11259375L)
     """
    try : 
        address, data = line.split('/', 1)
    except ValueError, e :
        print "Not a valid dnl file\n"
        sys.exit(2)

    if data[-1] == ';' :
        data = data[:-1]

    range = address.find(':')

    if range != -1 : 
        begin, end = address[:range], address[range+1:]
        begin      = long(begin, 16) 
        end        = long(end, 16)       
        if begin > end : 
            print("Warning : ignoring " + line + " because begin > end")
            return None
            
        addr = [begin]
        while begin < end :
          begin = begin + 1
          addr.append(begin)

    else :
        addr = [long(address, 16)]
        
    data = long(data, 16)
    
    return (addr, data)


def WriteSequence(da, seq, memsp, offset, wordrange, filebase) :
    """Writes a wordrange number of words from seq starting at filebase to the specified memsp:offset"""
    baseaddr = filebase
    offset_chk = offset/4
    print offset
    offset_chk = offset_chk * 4
    memaddr = memsp + offset_chk
    prevaddr = None
    prevvalues = None
    print "start"
    print memaddr
    for addr, values in seq :
        if (baseaddr - filebase)/4 < wordrange:
            if (addr*4) < baseaddr :
                prevaddr = addr
                prevvalues = values
                continue

            if (addr*4) > baseaddr and prevaddr != undefined :
                writeval = []
                for value in prevvalues :
                    if (baseaddr - filebase)/4 < wordrange:
                        if (prevaddr*4) == baseaddr :
                            writeval.append(value)
                            baseaddr = baseaddr + 4
                        prevaddr = prevaddr + 1
                    else:
                        break
            
                if writeval :
                    da.WriteMemoryBlock(memaddr, len(writeval), 4, writeval)
                    memaddr = memaddr + (4*len(writeval))

                while (baseaddr - filebase)/4 < wordrange and baseaddr < (addr*4) :
                    baseaddr = baseaddr + 4
                    memaddr = memaddr + 4

            if prevaddr == undefined :
                while (baseaddr - filebase)/4 < wordrange and baseaddr < (addr*4) :
                    baseaddr = baseaddr + 4
                    memaddr = memaddr + 4
            
            if (addr*4) == baseaddr :
                writeval = []
                for value in values :
                    if (baseaddr - filebase)/4 < wordrange:
                        if (addr*4) == baseaddr :
                            writeval.append(value)
                            baseaddr = baseaddr + 4
                        addr = addr + 1
                    else:
                        break
                        
                if writeval :
                    da.WriteMemoryBlock(memaddr, len(writeval), 4, writeval)
                    memaddr = memaddr + (4*len(writeval))
                
            prevaddr = None
            prevvalues = None
            
        else:
            break
        
def ReadBlockFromTarget(da, memsp, offset, wordrange, filebase, filename):
    """ 
    Read the block from the target and writes to the given file
    or
    Reads a block from the target and compares with the given file contents
    """
    
    baseaddr = filebase/4
    
    if baseaddr*4 != filebase :
        baseaddr = baseaddr + 1

    offset_chk = offset/4
    
    if offset_chk*4 != offset :
        offset_chk = (offset/4 + 1)

    memaddr = offset_chk * 4
    
    i = 0
    
    if not os.path.isfile(os.path.abspath(filename)) :
        
        fp = open(filename, 'w')
    
        fp.write('#\n')
        fp.write('# Register setup\n')
        fp.write('#\n\n')
    
        while i < wordrange :
            memstrt = memaddr
            basestrt = baseaddr
            data1 = da.MemRead(":%s:%x" %(memsp, memaddr))
            i = i + 1
            contigvalue = 1
        
            while i < wordrange and data1 == da.MemRead(":%s:%x" %(memsp, memaddr + 4)) :
                i = i + 1
                contigvalue = 0
                memaddr = memaddr + 4
                baseaddr = baseaddr + 1
        
            if contigvalue == 1 :
                writestr = "%x/%x;\n" %(basestrt, data1)
                fp.write(writestr)
            else :
                writestr = "%x:%x/%x;\n" %(basestrt, baseaddr, data1)
                fp.write(writestr)
            
            memaddr = memaddr + 4
            baseaddr = baseaddr + 1
        
        fp.close()
        
    else :
        fp = open(filename)
        lines = [line.strip() for line in fp]
        lines = [line for line in lines if line]
        lines = [line for line in lines if line[0] != '#']
        DecodedSeq = [DecodeAddress(line) for line in lines]
        setFlag = 0
    
        for address, data in sorted(DecodedSeq) :
            for addr in address :
                # check if the address matches with the given filebase
                if i < wordrange and addr == baseaddr :
                    memdata = da.MemRead(":%s:%x" %(memsp, memaddr))
                    # check if the data matches
                    if data !=  memdata :
                        setFlag = 1
                        print "\n Memory dump mismatch found \n"
                        print "Memory address : %s:%x \n" %(memsp, memaddr)
                        print "File base address : %x \n" %baseaddr
                        print "Memory address value : %x \n" %memdata
                        print "File data value : %x \n" %data                        

                    baseaddr = baseaddr + 1
                    memaddr = memaddr + 4
                    i = i + 1
                    
        if setFlag == 0:
            print "No mismatches found\n"
        
        fp.close()
        
    return            

def Write(da, sequence) : 
    """Writes the sequence to the target."""
    for address, data in sequence :
          da.WriteMemoryBlock(address * 4, len(data), 4, data)   
        
def WriteFile(da, filename) :
    """Read the .dnl file and write it to the target."""
    
    if da == 'CSim':
      import CSim
    elif da == 'FPGA':
      import FPGA
    elif da == 'DAtiny':
      from CSUtils import DAtiny
      
    Write(da, Optimise(Decode(open(filename))))
    
def WriteFileAtAddr(da, msp, os, wr, fb, filename) :
    """Read the .dnl file and write it to the target at the given location."""

    if da == 'CSim':
      import CSim
    elif da == 'FPGA':
      import FPGA
    elif da == 'DAtiny':
      from CSUtils import DAtiny

    optseq = Optimise(Decode(open(filename)))
    WriteSequence(da, optseq, msp, os, wr, fb)
    
def ReadtoFilefromAddr(da, msp, os, wr, fb, filename) :
    """
    Read the from the target from the given location and write it to a .dnl file
    or
    Check the contents of a .dnl file
    """
    
    if da == 'CSim':
      import CSim
    elif da == 'FPGA':
      import FPGA
    elif da == 'DAtiny':
      from CSUtils import DAtiny
      
    ReadBlockFromTarget(da, msp, os, wr, fb, filename)



#@Test.Function
#
#def ExtendedTest(test) : 
#    """Test that a real example is Decoded, Optimised, and actually written to the target correctly"""
#    dnl = """
#        20000000/1;
#        20000001/2;
#        20000002/3;
#        20000003/4;
#        20000004:20000005/5;
#        20000008/6;
#        20000010:20000017/7;
#    """.split("\n")
#    decoded = Decode(dnl)
#    test.assertEquals([(0x20000000, [1]), 
#                       (0x20000001, [2]), 
#                       (0x20000002, [3]), 
#                       (0x20000003, [4]), 
#                       (0x20000004, [5, 5]), 
#                       (0x20000008, [6]), 
#                       (0x20000010, [7, 7, 7, 7, 7, 7, 7, 7])], decoded)
#    optimised = Optimise(decoded)
#    test.assertEquals([(0x20000000, [1, 2, 3, 4, 5, 5]), 
#                       (0x20000008, [6]),
#                       (0x20000010, [7, 7, 7, 7, 7, 7, 7, 7])], optimised)
#                       
#    from CSUtils import DAtiny
#    
#    address = 0x20000000 * 4
#    count   = 0x20
#    length  = count * 4
#    DAtiny.UseTarget("DA-sim 4095")
#    DAtiny.FillMemory(address, length, 0)
#    test.assertEquals([0] * count, DAtiny.ReadMemoryBlock(address, count))
#    
#    Write(DAtiny, optimised)
#    
#    expected = [0x00000001, 0x00000002, 0x00000003, 0x00000004, 
#                0x00000005, 0x00000005, 0x00000000, 0x00000000,
#                0x00000006, 0x00000000, 0x00000000, 0x00000000, 
#                0x00000000, 0x00000000, 0x00000000, 0x00000000, 
#                0x00000007, 0x00000007, 0x00000007, 0x00000007, 
#                0x00000007, 0x00000007, 0x00000007, 0x00000007, 
#                0x00000000, 0x00000000, 0x00000000, 0x00000000, 
#                0x00000000, 0x00000000, 0x00000000, 0x00000000, 
#            ]
#    test.assertEquals(expected, DAtiny.ReadMemoryBlock(address, count))
#"""    
#
#"""
#def main(argv) :
#    from CSUtils import DAtiny
#    if len(argv) == 2 or len(argv) == 6: 
#        da = argv[0]
#        DAtiny.UseTarget(da)
#        DAtiny.Reset(0)
#    else:
#        raise InputError("Invalid arguments")
#        sys.exit(2)
#    if len(argv) == 2:
#        WriteFile(DAtiny, argv[1])
#    else:
#        WriteFileAtAddr(DAtiny, int(argv[1], 16), int(argv[2], 16), int(argv[3], 16), int(argv[4], 16), argv[5])
#"""
#    
#"""
#if __name__ == "__main__" : 
#    if len(sys.argv) == 1 : 
#        Test.main()
#        sys.exit(__doc__ % sys.argv[0])
#    main(sys.argv[1:])
#"""    
#
#"""
#if __name__ == "__main__" :
#
#  import FPGA
#  
#  FPGA.UseTarget(sys.argv[1])
#  
#  FPGA.ResetTarget(0)
#  
#  memsp = "REGMETA"
#  
#  addr = "04800010"
#  
#  import Dnl
#  
#  Dnl.ReadtoFilefromAddr(FPGA, memsp, int(addr, 16), 8, int(addr, 16), 'dump.dnl')
# 
#  print 'done done done'
#  
#  FPGA.stopTarget()
#"""


# End of Dnl.py
