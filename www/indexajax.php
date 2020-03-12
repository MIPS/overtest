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
include_once('inc/xmlrpc.inc');
include_once('inc/jsonrpc.inc');
include_once('inc/json_extension_api.inc');

if (!isset($_REQUEST['what']))
{
  echo "Unknown command";
  exit(0);
}
else if ($_REQUEST['what'] == "updategroupname")
{
  $sql = "SELECT ovt_testrungroup.testrungroupid\n".
         "FROM ovt_testrungroup\n".
         "WHERE testrungroupname='".$_REQUEST['testrungroupname']."'\n".
         "AND userid=(SELECT userid\n".
         "            FROM ovt_testrungroup\n".
         "            WHERE testrungroupid='".$_REQUEST['testrungroupid']."')";

  $result = pg_query($ovtDB, $sql);
  if ($_REQUEST['testrungroupname'] == "" || pg_num_rows($result) != 0)
  {
    $sql = "SELECT testrungroupname\n".
           "FROM ovt_testrungroup\n".
           "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'";
    $result = pg_query($ovtDB, $sql);
    echo "<b>".htmlentities(pg_fetch_result($result, 0, "testrungroupname"))."</b>";
    exit(0);
  }
  else
  {
    $sql = "UPDATE ovt_testrungroup\n".
           "SET testrungroupname='".$_REQUEST['testrungroupname']."'\n".
           "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'";
    pg_query($ovtDB, $sql);
    echo "<b>".htmlentities(stripslashes($_REQUEST['testrungroupname']))."</b>";
  }
}
else if ($_REQUEST['what'] == "updatetestrun")
{
  $testrunid = $_REQUEST['testrunid'];

  $sql = "SELECT ovt_runstatus.*, ovt_testrun.description AS trdescription\n".
         "FROM ovt_runstatus INNER JOIN ovt_testrun USING (runstatusid)\n".
         "WHERE testrunid='".$testrunid."'";
  $result = pg_query($ovtDB, $sql);
 
  $retval = array();

  $retval['gopause'] = "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">";
  $retval['abort'] = "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">";
  $retval['archive'] = "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">";
  $retval['delete'] = "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">\n";
  $retval['status'] = "<i>deleted</i>";
  $retval['description'] = "<i>deleted</i>";
  $retval['editable'] = false;

  if (pg_num_rows($result) == 1)
  { 
    if (pg_fetch_result($result, 0, "goenabled") == "t"
        || pg_fetch_result($result, 0, "checkenabled") == "t")
    {
      $retval['gopause'] = "<a href=\"javascript:runCommand('testrun',".$testrunid.",'go');\"><img src=\"images/go.gif\" alt=\"Go\"></a>";
    }
    else if (pg_fetch_result($result, 0, "pauseenabled") == "t")
    {
      $retval['gopause'] = "<a href=\"javascript:runCommand('testrun',".$testrunid.",'pause');\"><img src=\"images/pause.gif\" alt=\"Pause\"></a>";
    }

    if (pg_fetch_result($result, 0, "abortenabled") == "t")
    {
      $retval['abort'] =  "<a href=\"javascript:runCommand('testrun',".$testrunid.",'abort');\"><img src=\"images/abort.gif\" alt=\"Abort\"></a>";
    }

    if (pg_fetch_result($result, 0, "archiveenabled") == "t")
    {
      $retval['archive'] = "<a href=\"javascript:archiveTestrunPrompt('testrun',".$testrunid.",'".addslashes(htmlentities(pg_fetch_result($result, 0, "description")))."');\"><img src=\"images/archive.gif\" alt=\"Archive\"></a>";
    }

    if (pg_fetch_result($result, 0, "deleteenabled") == "t")
    {
      $retval['delete'] = "<a href=\"javascript:deleteTestrunPrompt('testrun',".$testrunid.",'".addslashes(htmlentities(pg_fetch_result($result, 0, "description")))."');\"><img id=\"deleteimg".$testrunid."\" src=\"images/delete.gif\" alt=\"Delete\"></a>";
    }

    if (pg_fetch_result($result, 0, "iseditable") == "t")
    {
      $retval['editable'] = true;
    }

    $retval['status'] = htmlentities(pg_fetch_result($result, 0, "description"));
    $retval['description'] = htmlentities(pg_fetch_result($result, 0, "trdescription"));
  }
  echo json_encode($retval);
}
else if ($_REQUEST['what'] == "go" ||
         $_REQUEST['what'] == "pause" ||
         $_REQUEST['what'] == "abort" ||
         $_REQUEST['what'] == "archive" ||
         $_REQUEST['what'] == "delete")
{
  pg_query($ovtDB, "BEGIN TRANSACTION");

  if (isset($_REQUEST['testrunid']))
  {
    $sql = "SELECT ovt_change_status('testrun', '".$_REQUEST['testrunid'] ."', '".$_REQUEST['what']."')";
  }
  else
  {
    $sql = "SELECT ovt_change_status('group', '".$_REQUEST['testrungroupid'] ."', '".$_REQUEST['what']."')";
  }
  pg_query($ovtDB, $sql);

  switch ($_REQUEST['what'])
  {
  case "delete":
    {
      if (isset($_REQUEST['testrunid']))
      {
        $sql = "SELECT ovt_runstatus.status\n".
               "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)\n".
               "WHERE ovt_testrun.testrunid='".$_REQUEST['testrunid']."'";
        $result = pg_query($ovtDB, $sql);
   
        if (pg_fetch_result($result, 0, "status") == "READYTODELETE")
        {
          $sql = "SELECT count(ovt_testrunresource.testrunresourceid) AS hostcount\n".
                 "FROM ovt_testrunresource\n".
                 "WHERE testrunid='".$_REQUEST['testrunid']."'";
          $res = pg_query($ovtDB, $sql);
  
          if (pg_fetch_result($res, 0, "hostcount") == 0)
          {
            $sql = "SELECT testrungroupid, count(testrunid) AS groupcount\n".
                   "FROM ovt_testrun\n".
                   "WHERE testrungroupid=(SELECT testrungroupid\n".
                   "                      FROM ovt_testrun\n".
                   "                      WHERE testrunid='".$_REQUEST['testrunid']."')\n".
                   "GROUP BY testrungroupid\n";
            $res = pg_query($ovtDB, $sql);
  
            $sql = "DELETE FROM ovt_testrun\n".
                   "WHERE testrunid='".$_REQUEST['testrunid']."'";
            pg_query($ovtDB, $sql);
  
            if (pg_fetch_result($res, 0, "groupcount") == 1)
            {
              $sql = "DELETE FROM ovt_testrungroup\n".
                     "WHERE testrungroupid='".pg_fetch_result($res, 0, "testrungroupid")."'";
              pg_query($ovtDB, $sql);
            }
  
          }
        }
      }
    }
  }
  pg_query($ovtDB, "COMMIT");
  exit(0);
}
?>
