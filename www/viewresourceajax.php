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


function getResourceStatus($resourceid)
{
  global $ovtDB;
  $sql = "SELECT status\n".
         "FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid)\n".
         "WHERE ovt_resource.resourceid='".$resourceid."'";
  $result = pg_query($ovtDB, $sql);

  return pg_fetch_result($result, 0, "status");
}
function setResourceStatus($resourceid, $status)
{
  global $ovtDB;

  $sql = "UPDATE ovt_resource\n".
         "SET resourcestatusid=(SELECT resourcestatusid\n".
         "                      FROM ovt_resourcestatus\n".
         "                      WHERE status='".$status."')\n".
         "WHERE resourceid='".$resourceid."'";
  pg_query($ovtDB, $sql);
}

if (!isset($_REQUEST['what']))
{
  echo "BAD REQUEST";
}
elseif ($_REQUEST['what'] == "restart")
{
  $status = getResourceStatus($_REQUEST['resourceid']);

  if ($status == "OK")
  {
    setResourceStatus($_REQUEST['resourceid'], "RESTART");
  }
  header("Location: viewresource.php?resourceid=".$_REQUEST['resourceid']);
  exit(0);
}
elseif ($_REQUEST['what'] == "disable")
{
  $status = getResourceStatus($_REQUEST['resourceid']);

  if ($status == "OK")
  {
    setResourceStatus($_REQUEST['resourceid'], "DISABLE");
  }
  header("Location: viewresource.php?resourceid=".$_REQUEST['resourceid']);
  exit(0);
}
elseif ($_REQUEST['what'] == "enable")
{
  $status = getResourceStatus($_REQUEST['resourceid']);

  if ($status == "DISABLED")
  {
    setResourceStatus($_REQUEST['resourceid'], "OFFLINE");
  }
  header("Location: viewresource.php?resourceid=".$_REQUEST['resourceid']);
  exit(0);
}
elseif ($_REQUEST['what'] == "updateconcurrency")
{
  if ((string)(int)$_REQUEST['concurrency'] != $_REQUEST['concurrency'] || (int)$_REQUEST['concurrency'] < 0)
  {
    echo "Thread values must be non-negative numbers";
    exit(0);
  }
  $sql = "UPDATE ovt_resource\n".
         "SET concurrency='".$_REQUEST['concurrency']."'\n".
         "WHERE resourceid='".$_REQUEST['resourceid']."'";

  pg_query($ovtDB, $sql);
}
elseif ($_REQUEST['what'] == "claimlog")
{
  /* Get the history for this resource */

  $offset = ($_REQUEST['page']-1)*20;
  $sql = "SELECT testrunid, userclaimid, reason, to_char(start, 'YYYY/MM/DD HH24:MI') AS starttext, to_char(endtime, 'YYYY/MM/DD HH24:MI') AS endtext\n".
         "FROM \n".
         "((SELECT ovt_testrun.testrunid, NULL AS userclaimid, ovt_user.username || ' - ' || ovt_testrun.description || ' - ' || ovt_action.actionname AS reason,\n".
         "         ovt_testrunaction.starteddate AS start, ovt_testrunaction.completeddate AS endtime\n".
         "  FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "       INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "       INNER JOIN ovt_testrun USING (testrunid)\n".
         "       INNER JOIN ovt_user USING (userid)\n".
         "       INNER JOIN ovt_testrunactionresource USING (testrunactionid)\n".
         "  WHERE ovt_testrunactionresource.resourceid='".$_REQUEST['resourceid']."'\n".
         "  AND ovt_testrunaction.starteddate IS NOT NULL\n".
         "  AND ovt_testrunactionresource.dead)\n".
         " UNION\n".
         " (SELECT NULL AS testrunid, ovt_userclaim.userclaimid, ovt_user.username || ' - ' || ovt_userclaim.reason AS reason,\n".
         "         ovt_userclaim.grantdate AS start, ovt_userclaim.returndate AS endtime\n".
         "  FROM ovt_userclaim INNER JOIN ovt_user USING (userid)\n".
         "       INNER JOIN ovt_userclaimresource USING (userclaimid)\n".
         "  WHERE ovt_userclaimresource.resourceid='".$_REQUEST['resourceid']."'\n".
         "  AND dead\n".
         "  AND ovt_userclaim.grantdate IS NOT NULL)) AS claims\n".
         "ORDER BY start DESC\n".
         "OFFSET $offset LIMIT 21";
  $result = pg_query($ovtDB, $sql);

  echo "<h3>Claims log</h3>\n";
  if (pg_num_rows($result) == 0)
  {
    echo "This resource has never been claimed";
  }
  else
  {
    echo "<table>\n".
         "<tr><th>ID</th><th>Reason</th><th>Start claim</th><th>End claim</th></tr>\n";

    $count = pg_num_rows($result);
    $more = ($count == 21);
    $count = ($more?20:$count);
    for ($i = 0 ; $i < $count ; $i++)
    {
      echo "<tr><td>";
      if (!pg_field_is_null($result, $i, "testrunid"))
      {
        echo pg_fetch_result($result, $i, "testrunid");
      }
      else
      {
        echo pg_fetch_result($result, $i, "userclaimid");
      }
      echo "</td><td>";
      if (!pg_field_is_null($result, $i, "testrunid"))
      {
        echo "<a href=\"viewtestrun.php?testrunid=".pg_fetch_result($result, $i, "testrunid")."\">";
      }
      echo pg_fetch_result($result, $i, "reason");
      if (!pg_field_is_null($result, $i, "testrunid"))
      {
        echo "</a>";
      }
      echo "</td>\n".
           "<td>".pg_fetch_result($result, $i, "starttext")."</td>\n".
           "<td>".pg_fetch_result($result, $i, "endtext")."</td></tr>\n";
    }
    echo "<tr><td colspan=3>\n";
    if ($_REQUEST['page'] != 1)
    {
      echo "<div style=\"float:left;\"><span class=\"clickable\" onclick=\"claimlog(".
           ($_REQUEST['page']-1).");\">Previous</span></div>";
    }
    if ($more)
    {
      echo "<div style=\"float:right;\"><span class=\"clickable\" onclick=\"claimlog(".
           ($_REQUEST['page']+1).");\">Next</span></div>";
    }
    echo "</td></tr>\n";

    echo "</table>\n";
  }
}
elseif ($_REQUEST['what'] == "hostlog")
{

  $sql = "SELECT concurrency\n".
         "FROM ovt_resource\n".
         "WHERE resourceid='".$_REQUEST['resourceid']."'";
  $result = pg_query($ovtDB, $sql);
  $concurrency = pg_fetch_result($result, 0, 0);

  $offset = ($_REQUEST['page']-1)*20;
  $sql = "SELECT resourcelogid, message, to_char(entrydate, 'HH24:MI DD Mon YYYY') AS entrydate\n".
         "FROM ovt_resourcelog\n".
         "WHERE index='".$_REQUEST['thread']."'\n".
         "AND resourceid='".$_REQUEST['resourceid']."'\n".
         "ORDER BY ovt_resourcelog.entrydate DESC\n".
         "OFFSET $offset LIMIT 21";
  $result = pg_query($ovtDB, $sql);
  echo "<h3>Thread ".$_REQUEST['thread']." log</h3>\n";

  echo "View log from: \n";
  for ($i = 0 ; $i < $concurrency ; $i++)
  {
    echo "<span onclick=\"hostlog(".$i.", 1);\" class=\"clickable\">Thread ".$i."</span> \n";
  }
  echo "<br />\n";

  if (pg_num_rows($result) == 0)
  {
    echo "There are no logs available<br />\n";
  }
  else
  {
    echo "<table>\n".
         "<tr><th style=\"width:150px;\">Date</th><th>Message</th></tr>\n";
    $count = pg_num_rows($result);
    $more = ($count == 21);
    $count = ($more?20:$count);
    for ($i = 0 ; $i < $count ; $i++)
    {
      $message = htmlentities(pg_fetch_result($result, $i, "message"));
      $firstnl =  strpos($message, "\n");
      if ($firstnl === false)
      {
        $minimessage = $message;
        $moretext = "";
      }
      else
      {
        $moretext = "class=\"clickable;\" ";
        $minimessage = substr($message, 0, $firstnl);
      }
      $id = pg_fetch_result($result, $i, "resourcelogid");
      echo "<tr><td valign=\"top\">".pg_fetch_result($result, $i, "entrydate")."</td>\n".
           "<td><span ".$moretext."id=\"mm".$id."\" onclick=\"$('mm".$id."').hide();$('m".$id."').show();\">".nl2br($minimessage)."</span>\n".
           "<div style=\"display:none\"  onclick=\"$('m".$id."').hide();$('mm".$id."').show();\" id=\"m".$id."\">".nl2br($message)."</div></td></tr>\n";
    }
    echo "<tr><td colspan=2>\n";
    if ($_REQUEST['page'] != 1)
    {
      echo "<div style=\"float:left;\"><span class=\"clickable\" onclick=\"hostlog(".
           $_REQUEST['thread'].", ".($_REQUEST['page']-1).");\">Previous</span></div>";
    }
    if ($more)
    {
      echo "<div style=\"float:right;\"><span class=\"clickable\" onclick=\"hostlog(".
           $_REQUEST['thread'].", ".($_REQUEST['page']+1).");\">Next</span></div>";
    }
    echo "</td></tr>\n".
         "</table>\n";
  }
}

?>
