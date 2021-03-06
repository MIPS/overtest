<!-- Copyright (C) 2012-2020 MIPS Tech LLC
     Written by Matthew Fortune <matthew.fortune@imgtec.com> and
     Daniel Sanders <daniel.sanders@imgtec.com>
     This file is part of Overtest.
    
     Overtest is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 3, or (at your option)
     any later version.
    
     Overtest is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.
    
     You should have received a copy of the GNU General Public License
     along with overtest; see the file COPYING.  If not, write to the Free
     Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
     02110-1301, USA.  -->
<?php
  include_once('includes.inc');
  ini_set('display_errors', '1');
  error_reporting(E_ALL);

  $testrunid = (int)$_REQUEST['testrunid'];
  $versionedactionid = (int)$_REQUEST['versionedactionid'];
  $logname = basename($_REQUEST['log']);

  function download($filename, $shortname)
  {
    if (file_exists ($filename))
    {
      $mime = mime_content_type($filename);
      header("Content-type: ".$mime);
      header("Content-Disposition: attachment; filename=\"".$shortname."\"");
      readfile($filename);
    }
    else
    {
      header("HTTP/1.0 404 Not Found");
    }
  }

  $size = 0;
  if (isset($_REQUEST['actionlog']))
  {
    $filename = $overtestroot."/".$testrunid."/".$versionedactionid."/log.".$logname;
    $name = $logname;
  }
  else
  {
    $prefix = "";
    if (isset($_REQUEST['resourcetypeid']))
    {
      $prefix = "r".$_REQUEST['resourcetypeid'].".";
    }
    $command = (int)$_REQUEST['command'];
  
    $filename = $overtestroot."/".$testrunid."/".$versionedactionid."/".$prefix.$command.".".$logname;
    $size = filesize($filename);
    $name = $command.".".$logname;
  }

  if (isset($_REQUEST['actionlog']) || isset($_REQUEST['download']) || $size > 24288)
  {
    download($filename, $name);
  }
  else
  {
    htmlHeader("View Log File");
    if ($size == 0)
    {
      print "[EMPTY LOG FILE]<br />\n";
    }
    else
    {
      if (substr($filename, -strlen(".gz")) == ".gz")
      {
        $fh = gzopen($filename, "r");
        echo "<pre>\n";
        gzpassthru($fh);
        echo "</pre>\n";
        gzclose($fh);
      }
      else
      {
        $fh = fopen($filename, "r");
        echo "<pre>\n";
        echo fread($fh, $size);
        echo "</pre>\n";
        fclose($fh);
      }
    }

    htmlFooter();
  }

?>
