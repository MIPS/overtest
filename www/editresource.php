<?php
  ini_set('display_errors', '1');
  error_reporting(E_ALL);

include_once('includes.inc');

htmlHeader("Resource Information", "hostlog(0, 1);claimlog(1)");

?>
<script language="javascript">
  function hostlog(thread, page)
  {
    new Ajax.Updater('log', 'viewresourceajax.php',
                     { method: 'get',
                       parameters: {what: 'hostlog',
                                    resourceid: <?php echo $_REQUEST['resourceid'];?>,
                                    thread: thread,
                                    page: page}});

  }
  function claimlog(page)
  {
    new Ajax.Updater('claimlog', 'viewresourceajax.php',
                     { method: 'get',
                       parameters: {what: 'claimlog',
                                    resourceid: <?php echo $_REQUEST['resourceid'];?>,
                                    page: page}});

  }
  function updateConcurrency(concurrency)
  {
    new Ajax.Updater('ErrorMessage', 'viewresourceajax.php',
                     { method: 'get',
                       parameters: {what: 'updateconcurrency',
                                    concurrency: concurrency,
                                    resourceid: <?php echo $_REQUEST['resourceid'];?>}});
  }
  function updateAttribute(attributeid, theid)
  {
    new Ajax.Updater('ErrorMessage', 'editresourceajax.php',
		    { method: 'get',
                      parameters: {what: 'updateattribute',
				   attributeid: attributeid,
                                   value: $F($(theid)).toString(),
                                   resourceid: <?php echo $_REQUEST['resourceid'];?>}});
  }

</script>
<?php

function showAttributes()
{
  global $ovtDB;
  echo "<h2>Attributes</h2>\n";
  $sql = "SELECT DISTINCT ovt_attribute.attributeid, ovt_attribute.attributename,\n".
         "       ovt_attribute.lookup, ovt_resourceattribute.value\n".
         "FROM ovt_attribute INNER JOIN ovt_resource USING (resourcetypeid)\n".
	 "     LEFT OUTER JOIN ovt_resourceattribute \n".
	 "     ON (ovt_attribute.attributeid=ovt_resourceattribute.attributeid\n".
	 "         AND ovt_resourceattribute.resourceid=ovt_resource.resourceid\n".
	 "         AND ovt_resourceattribute.value IS NOT NULL)\n".
         "WHERE ovt_resource.resourceid='".$_REQUEST['resourceid']."'\n".
         "ORDER BY ovt_attribute.attributename";

  $result = pg_query($ovtDB, $sql);

  if (pg_num_rows($result) == 0)
  {
    echo "This resource has no attributes!<br />";
  }
  else
  {
    echo "<form>\n";
    echo "<table>\n".
         "<tr><th>Attribute</th><th>Value</th></tr>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<tr><td>";
      echo htmlentities(pg_fetch_result($result, $i, "attributename"));
      echo "</td><td>";

      if (pg_fetch_result($result, $i, "lookup") == "f")
      {
        echo "<input name=\"att".pg_fetch_result($result, $i, "attributeid")."\" ".
	     "value=\"".pg_fetch_result($result, $i, "value")."\" onchange=\"updateAttribute(".pg_fetch_result($result, $i, "attributeid").", this);\">\n";
      }
      else
      {
	$sql = "SELECT ovt_attributevalue.attributevalueid, ovt_attributevalue.value,\n".
	       "       ovt_resourceattribute.resourceattributeid\n".
	       "FROM ovt_attributevalue LEFT OUTER JOIN ovt_resourceattribute\n".
	       "     ON (ovt_attributevalue.attributevalueid=ovt_resourceattribute.attributevalueid\n".
	       "         AND ovt_resourceattribute.resourceid='".$_REQUEST['resourceid']."')\n".
	       "WHERE ovt_attributevalue.attributeid='".pg_fetch_result($result, $i, "attributeid")."'\n".
	       "ORDER BY ovt_attributevalue.value\n";

	$innerresult = pg_query($ovtDB, $sql);

	echo "<select id=\"att".pg_fetch_result($result, $i, "attributeid")."\" name=\"att".pg_fetch_result($result, $i, "attributeid")."\" multiple=\"multiple\" size=\"5\" onchange=\"updateAttribute(".pg_fetch_result($result, $i, "attributeid").", this);\">\n";
	for ($j = 0 ; $j < pg_num_rows($innerresult); $j++)
	{
	  echo "<option value=\"".pg_fetch_result($innerresult, $j, "attributevalueid")."\"";
	  if (!pg_field_is_null($innerresult, $j, "resourceattributeid"))
	  {
	    echo " selected";
	  }
	  echo ">".pg_fetch_result($innerresult, $j, "value")."</option>\n";
	}
	echo "</select>\n";

      }
      echo "</td></tr>\n";
    }
    echo "</table>\n";
    echo "</form>\n";
  }
}

$sql = "SELECT ovt_resourcetype.resourcetypename\n".
       "FROM ovt_resourcetype INNER JOIN ovt_resource USING (resourcetypeid)\n".
       "WHERE ovt_resource.resourceid='".$_REQUEST['resourceid']."'";

$result = pg_query($ovtDB, $sql);

$resourcetype = pg_fetch_result($result, 0, "resourcetypename");
$ishost = ($resourcetype == "Execution Host");

$sql = "SELECT ovt_resource.resourcename, ovt_resourcestatus.status, concurrency\n".
       "FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid)\n".
       "WHERE ovt_resource.resourceid='".$_REQUEST['resourceid']."'";
$result = pg_query($ovtDB, $sql);

echo "<h1>".pg_fetch_result($result, 0, "resourcename"). " ".$resourcetype." information</h1>\n";


if ($ishost)
{
  $status = pg_fetch_result($result, 0, "status");
  echo "<div style=\"float:right\">\n";
  echo "Status: <b>".$status."</b><br />\n";

  if ($status == "OK")
  {
    echo "<form onSubmit=\"return false;\">\n".
         "Threads: <input type=\"text\" size=2 name=\"concurrency\" value=\"".pg_fetch_result($result, 0, "concurrency")."\" onblur=\"updateConcurrency(this.value);\">\n".
         "</form>\n";
    echo "<a href=\"viewresourceajax.php?what=restart&amp;resourceid=".$_REQUEST['resourceid']."\">Restart</a>\n";
    echo "<a href=\"viewresourceajax.php?what=disable&amp;resourceid=".$_REQUEST['resourceid']."\">Disable</a>\n";
    echo "<br />\n";
  }
  elseif ($status == "RESTART")
  {
    echo "Restart request being processed<br />\n";
  }
  elseif ($status == "DISABLE")
  {
    echo "Disable request being processed<br />\n";
  }
  elseif ($status == "DISABLED")
  {
    echo "Host is disabled: \n";
    echo "<a href=\"viewresourceajax.php?what=enable&amp;resourceid=".$_REQUEST['resourceid']."\">Enable</a><br />\n";
  }
  elseif ($status == "UPDATING")
  {
    echo "Host is updating for restart<br />\n";
  }
  elseif ($status == "OFFLINE")
  {
    echo "Host is offline<br />\n";
  }
  echo "<br />\n";
  /*
   * Find all the tra's linked to this host that have not completed
   */
  $sql = "SELECT ovt_testrun.testrunid, ovt_testrun.description, \n".
         "       ovt_action.actionname, ovt_testrunaction.archived\n".
         "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "     INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "     INNER JOIN ovt_testrunactionresource USING (testrunactionid)\n".
         "     INNER JOIN ovt_testrun USING (testrunid)\n".
         "WHERE ((ovt_testrunaction.starteddate IS NOT NULL\n".
         "        AND ovt_testrunaction.completeddate IS NULL)\n".
         "       OR NOT ovt_testrunaction.archived)\n".
         "AND ovt_testrunactionresource.resourceid='".$_REQUEST['resourceid']."'";

  $result = pg_query($ovtDB, $sql);

  echo "<h2>Current Tasks</h2>\n";
  if (pg_num_rows($result) == 0)
  {
    echo "There are no tasks currently<br /> executing on this host<br />\n";
  }
  else
  {
    echo "<table>\n".
         "<tr><th>ID</th><th>Testrun</th><th>Task</th></tr>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      $deco = "none";
      if (!pg_field_is_null($result, $i, "archived"))
      {
        $deco = "line-through";
      }
      echo "<tr><td><a href=\"viewtestrun.php?testrunid=".pg_fetch_result($result, $i, "testrunid")."\">".
           pg_fetch_result($result, $i, "testrunid")."</a></td>\n".
           "<td>".htmlentities(pg_fetch_result($result, $i, "description"))."</td>\n".
           "<td><span style=\"text-decoration:".$deco."\">".htmlentities(pg_fetch_result($result, $i, "actionname"))."</span></td></tr>\n";
    }
    echo "</table>\n";
  }

  echo "</div>\n";

  showAttributes();

  echo "<div id=\"log\"></div>\n";

}
else
{

  echo "<div style=\"float:right\">\n";
  echo "Status: <b>".pg_fetch_result($result, 0, "status")."</b><br /><br />\n";

  /*
   * Find all the tasks using this resource (should be one max currently)
   * Also list (in correct priority ordering) all tasks waiting)
   * Also state if there is an outstanding or held claim
   */
  echo "<h2>Current usage</h2>\n";
  $sql = "SELECT ovt_user.username, ovt_userclaim.reason, ovt_userclaimresource.held\n".
         "FROM ovt_userclaim INNER JOIN ovt_user USING (userid)\n".
         "     INNER JOIN ovt_userclaimresource USING (userclaimid)\n".
         "WHERE ovt_userclaimresource.resourceid='".$_REQUEST['resourceid']."'\n".
         "AND NOT dead\n".
         "ORDER BY ovt_userclaim.requestdate, ovt_userclaim.userclaimid";
  $result = pg_query($ovtDB, $sql);

  echo "<table>\n";
  if (pg_num_rows($result) == 0)
  {
    echo "<tr><td colspan=3>There are no user claims<br />\n".
         "currently using or waiting for<br />\n".
         "this resource</td></tr>\n";
  }
  else
  {
    echo "<tr><th>User</th><th colspan=2>Reason</th></tr>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      $start = "";
      $end = "";
      if (pg_fetch_result($result, $i, "held") == "t")
      {
        $start = "<b>";
        $end = "</b>";
      }
      echo "<tr><td>". pg_fetch_result($result, $i, "username")."</td>\n".
           "<td>$start".htmlentities(pg_fetch_result($result, $i, "reason"))."$end</td>\n".
           "</tr>\n";
    }

  }
 
  $sql = "SELECT ovt_testrun.testrunid, ovt_testrun.description, ovt_action.actionname, ovt_testrunactionresource.held\n".
         "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "     INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "     INNER JOIN ovt_testrun USING (testrunid)\n".
         "     INNER JOIN ovt_testrunactionresource USING (testrunactionid)\n".
         "WHERE ovt_testrunactionresource.resourceid='".$_REQUEST['resourceid']."'\n".
         "AND NOT ovt_testrunactionresource.dead\n".
         "ORDER BY ovt_testrun.priority, ovt_testrunactionresource.testrunactionresourceid";

  $result = pg_query($ovtDB, $sql);

  if (pg_num_rows($result) == 0)
  {
    echo "<tr><td colspan=3>There are no tasks currently <br />\n".
         "using or waiting for this <br />\n".
         "resource</td></tr>\n";
  }
  else
  {
    echo "<tr><th>ID</th><th>Testrun</th><th>Task</th></tr>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      $start = "";
      $end = "";
      if (pg_fetch_result($result, $i, "held") == "t")
      {
        $start = "<b>";
        $end = "</b>";
      }
      echo "<tr><td><a href=\"viewtestrun.php?testrunid=".pg_fetch_result($result, $i, "testrunid")."\">".
           pg_fetch_result($result, $i, "testrunid")."</a></td>\n".
           "<td>$start".htmlentities(pg_fetch_result($result, $i, "description"))."$end</td>\n".
           "<td>$start".htmlentities(pg_fetch_result($result, $i, "actionname"))."$end</td></tr>\n";
    }
  }

  echo "</table>\n";
  echo "</div>\n";
  echo "<h2>Linked resources</h2>\n";
  $sql = "SELECT ovt_resource.resourcename, ovt_resource.resourceid\n".
         "FROM ovt_resource\n".
         "WHERE ovt_resource.resourceid!='".$_REQUEST['resourceid']."'\n".
         "AND ovt_resource.linkedresourcegroupid=(SELECT linkedresourcegroupid\n".
         "                                        FROM ovt_resource\n".
         "                                        WHERE ovt_resource.resourceid='".$_REQUEST['resourceid']."')\n".
         "ORDER BY ovt_resource.resourcename";
  $result = pg_query($ovtDB, $sql);
  if (pg_num_rows($result) == 0)
  {
    echo "There are no linked resources<br />\n";
  }
  else
  {
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<a href=\"viewresource.php?resourceid=".
           pg_fetch_result($result, $i, "resourceid").
           "\">".pg_fetch_result($result, $i, "resourcename")."</a><br />\n";
    }
  }
  echo "<br />";
  showAttributes();

}
echo "<div id=\"claimlog\"></div>\n";

htmlFooter()
?>
