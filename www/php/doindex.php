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
  ini_set('display_errors', '1');
    error_reporting(E_ALL);

include_once('includes.inc');
include_once('testrun_list.inc');

if (!isset($_REQUEST['what']))
{
  header("location: ../index.php");
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
else if ($_REQUEST['what'] == "createtestrungroup")
{
  pg_query($ovtDB, "BEGIN TRANSACTION");

  $sql = "SELECT *\n".
         "FROM ovt_create_testrungroup('".$_REQUEST['groupname']."','".$_SESSION['auth_userid']."','Default');";
  $result = pg_query($ovtDB, $sql);
  $testrunid = pg_fetch_result($result, 0, "newtestrunid");

  pg_query($ovtDB, "COMMIT");
 
  header("location: ../edittestrun.php?testrunid=".$testrunid);
  exit(0);

}
else if ($_REQUEST['what'] == "newtestrun")
{
  /* Create a new testrun in the specified group called 'Default <n>' */
  $sql = "SELECT ovt_create_testrun('Default', '".$_SESSION['auth_userid']."',".
         "                          '".$_REQUEST['testrungroupid']."')";
  $result = pg_query($ovtDB, $sql);
  $testrunid = pg_fetch_result($result, 0, 0);

  header("location: ../edittestrun.php?testrunid=".$testrunid);
  exit(0);
}
else if ($_REQUEST['what'] == "copytestrun")
{
  /* Takes a testrunid and duplicates all the referenced versioned actions,
     non-automatic configuration settings, and resource requirements */
  pg_query($ovtDB, "BEGIN TRANSACTION");

  $sql = "SELECT testrungroupid\n".
         "FROM ovt_testrun\n".
         "WHERE testrunid='".$_REQUEST['testrunid']."'";
  $result = pg_query($ovtDB, $sql);

  $sql = "SELECT ovt_duplicate_testrun('".$_REQUEST['testrunid']."', NULL, '".$_SESSION['auth_userid']."',".
         "                             '".pg_fetch_result($result, 0, "testrungroupid")."')";
  $result = pg_query($ovtDB, $sql);
  $testrunid = pg_fetch_result($result, 0, 0);

  pg_query($ovtDB, "COMMIT");
  header("location: ../edittestrun.php?testrunid=".$testrunid);
  exit(0);
}
else if ($_REQUEST['what'] == "copytestrungroup")
{
  /* Takes a testrungroup and duplicates all testruns into a new testrungroup */
  pg_query($ovtDB, "BEGIN TRANSACTION");

  $sql = "SELECT ovt_duplicate_testrungroup('".$_REQUEST['testrungroupid']."',NULL,'".$_SESSION['auth_userid']."')";
  $result = pg_query($ovtDB, $sql);

  $testrungroupid = pg_fetch_result($result, 0, 0);

  pg_query($ovtDB, "COMMIT");
  header("location: ../edittestrun.php?testrungroupid=".$testrungroupid);
}
else if ($_REQUEST['what'] == "go" ||
         $_REQUEST['what'] == "pause" ||
         $_REQUEST['what'] == "abort" ||
         $_REQUEST['what'] == "delete" ||
         $_REQUEST['what'] == "archive")
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
  header("location: ../index.php");
  exit(0);
}
else if ($_REQUEST['what'] == "testrunsearch")
{
  testrunlist($_REQUEST);
  exit(0);
}
?>
