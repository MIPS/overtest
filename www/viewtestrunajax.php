<?php
include_once('includes.inc');
include_once('dot.inc');
$authenticated = isset($_SESSION['auth_userid']);

if (!isset($_REQUEST['what']))
{
  echo "BAD REQUEST";
}
else if ($_REQUEST['what'] == "setequivalencename")
{
  if ($_REQUEST['type'] != "simple"
       && $_REQUEST['type'] != "recursive"
       && $_REQUEST['type'] != "subrecursive")
  {
    echo "Invalid equivalence type specified: ".$_REQUEST['type'];
    exit(0);
  }
  $newvalue = $_REQUEST['value'];
  if (strlen($newvalue) == 0)
  {
    $newvalue = "NULL";
  }
  else
  {
    $newvalue = "'".$newvalue."'";
  }

  $sql = "UPDATE ovt_".$_REQUEST['type']."equivalence\n".
         "SET ".$_REQUEST['type']."equivalencename=".$newvalue."\n".
         "FROM ovt_testrunaction\n".
         "WHERE ovt_testrunaction.".$_REQUEST['type']."equivalenceid=ovt_".$_REQUEST['type']."equivalence.".$_REQUEST['type']."equivalenceid\n".
         "AND testrunactionid='".$_REQUEST['testrunactionid']."'";
  pg_query($ovtDB, $sql);
}
else if ($_REQUEST['what'] == "testrunmap")
{
  echo draw_testrun($_REQUEST['testrunid'], "cmapx");
}
else if ($_REQUEST['what'] == "statusinfo")
{
  echo "<div style=\"float: left\">\n";
  $sql = "SELECT DISTINCT ovt_attributevalue.value\n".
         "FROM ovt_attributevalue INNER JOIN ovt_resourceattribute USING (attributevalueid)\n".
         "     INNER JOIN ovt_attribute ON (ovt_attribute.attributeid = ovt_attributevalue.attributeid)\n".
         "     INNER JOIN ovt_resourcetype USING (resourcetypeid)\n".
         "     INNER JOIN ovt_testrunresource USING (resourceid)\n".
         "WHERE ovt_testrunresource.testrunid='".$_REQUEST['testrunid']."'\n".
         "AND ovt_attribute.attributename='Shared Filesystem'\n".
         "AND ovt_resourcetype.resourcetypename='Execution Host'";

  $result = pg_query($ovtDB, $sql);
  if (pg_num_rows($result) == 0)
  {
    echo "No Execution Hosts have been allocated to this testrun yet<br />\n";
  }
  else if (pg_num_rows($result) != 1)
  {
    echo "CONFIG ERROR: Hosts on different shared file systems are executing this testrun<br />\n";
  }
  else
  {
    echo "Executing in the ".pg_fetch_result($result, 0, 0)." filesystem<br />\n";
  }
  $sql = "SELECT DISTINCT ovt_resource.resourcename\n".
         "FROM ovt_testrunresource INNER JOIN ovt_resource USING (resourceid)\n".
         "     INNER JOIN ovt_resourcetype USING (resourcetypeid)\n".
         "WHERE ovt_testrunresource.testrunid='".$_REQUEST['testrunid']."'\n".
         "AND ovt_resourcetype.resourcetypename='Execution Host'\n".
         "ORDER BY ovt_resource.resourcename";
  $result = pg_query($ovtDB, $sql);
  if (pg_num_rows($result) != 0)
  {
    echo "Executing on";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      if ($i != 0)
      {
        if ($i == pg_num_rows($result)-1)
        {
          echo " and";
        }
        else
        {
          echo ",";
        }
      }
      echo " ".pg_fetch_result($result, $i, "resourcename");
    }
    echo "<br />\n";
  }
  echo "</div>\n".
       "<br clear=\"both\">\n";
}
else if ($_REQUEST['what'] == "resultinfo")
{
  $sql = "SELECT to_char(ovt_testrunaction.starteddate, 'HH24:MI DD Mon YYYY') AS starteddate,\n".
         "       to_char(ovt_testrunaction.completeddate,'HH24:MI DD Mon YYYY') AS completeddate,\n".
         "       ovt_testrunaction.passed, ovt_action.actionname, ovt_testrunaction.testrunid,\n".
         "       ovt_versionedaction.versionname, ovt_testrunaction.versionedactionid,\n".
         "       ovt_action.testsuiteid\n".
         "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid)\n".
         "     INNER JOIN ovt_action USING (actionid)\n".
         "WHERE ovt_testrunaction.testrunactionid='".$_REQUEST['testrunactionid']."'";
  $result = pg_query($ovtDB, $sql);

  if (pg_num_rows($result) == 0)
  {
    echo "Action not found\n";
  }
  else
  {
    $testrunid = pg_fetch_result($result, 0, "testrunid");
    $versionedactionid = pg_fetch_result($result, 0, "versionedactionid");
    $start = pg_fetch_result($result, 0, "starteddate");
    $end = "";
    $passed = "";
    if (pg_field_is_null($result, 0, "starteddate"))
    {
      $start = "Not started";
    }
    else
    {
      if (!pg_field_is_null($result, 0, "completeddate"))
      {
        $end = pg_fetch_result($result, 0, "completeddate");
      }
      else
      {
        $end = "Not finished";
      }
    }
    if (!pg_field_is_null($result, 0, "passed"))
    {
      if (pg_fetch_result($result, 0, "passed") == "t")
      {
        $passed = "Passed";
      }
      else
      {
        $passed = "Failed";
      }
    }

    echo "<h2>".pg_fetch_result($result, 0, "actionname")." [".pg_fetch_result($result, 0, "versionname")."]</h2>\n";
    echo "<div style=\"float:left; border:1px solid #0000DD; margin:5px;\">\n";
    echo "<form method=\"post\" action=\"#\">\n";
    echo "<table>\n";

    $sql = "SELECT configoptionname\n".
           "FROM ovt_view_testrunactionconfig\n".
           "WHERE testrunactionid='".$_REQUEST['testrunactionid']."'\n".
           "AND automatic\n".
           "LIMIT 1";
    $checkauto = pg_query($ovtDB, $sql);

    $sql = "SELECT configoptionname, value, automatic\n".
           "FROM ovt_view_testrunactionconfig\n".
           "WHERE testrunactionid='".$_REQUEST['testrunactionid']."'\n".
           "ORDER BY configoptionname";
    $config = pg_query($ovtDB, $sql);
    if (pg_num_rows($config) != 0)
    {
      for ($i = 0 ; $i < pg_num_rows($config) ; $i++)
      {
        $extraclass="";
        if (pg_fetch_result($config, $i, "automatic") == 't')
        {
          $extraclass=" style=\"display:none\" class=\"config_automatic\"";
        }
        echo "<tr".$extraclass."><th>".htmlentities(pg_fetch_result($config, $i, "configoptionname")).
             "</th><td>".htmlentities(pg_fetch_result($config, $i, "value"))."</td></tr>\n";
      }
    }

    $sql = "SELECT DISTINCT ovt_resource.resourcename, ovt_resource.resourceid, ovt_resourcetype.resourcetypename,\n".
           "                ovt_resourcetype.resourcetypeid, ovt_resourcestatus.status\n".
           "FROM ovt_resource INNER JOIN ovt_testrunactionresource USING (resourceid)\n".
           "     INNER JOIN ovt_resourcetype USING (resourcetypeid)\n".
           "     INNER JOIN ovt_resourcestatus USING (resourcestatusid)\n".
           "WHERE ovt_testrunactionresource.testrunactionid='".$_REQUEST['testrunactionid']."'\n".
           "ORDER BY ovt_resourcetype.resourcetypename";
    $resources = pg_query($ovtDB, $sql);
    $resourcelogs = array();
    $executionhostid = NULL;
    if (pg_num_rows($resources) != 0)
    {
      $resourceordering = array();
      for ($i = 0 ; $i < pg_num_rows($resources) ; $i++)
      {
        $resourcetypeid = pg_fetch_result($resources, $i, "resourcetypeid");

        /* Keep track of all the resources to display resource specific logsa.
           The logic here ensures that all resources are reported but the HISTORIC version of the
           resource takes precedence if it exists. This allows for the correct logs to be shown
           when resources fail to initialise (no historic resource will exist) but once
           successfully initialised the historic version is used to maintain consistency */

        if (array_key_exists($resourcetypeid, $resourcelogs))
        {
          if (pg_fetch_result($resources, $i, "status") == "HISTORIC")
          {
            $resourcelogs[$resourcetypeid]['name'] = pg_fetch_result($resources, $i, "resourcename");
            $resourcelogs[$resourcetypeid]['resourceid'] = pg_fetch_result($resources, $i, "resourceid");

            /* Store the HISTORIC execution host to find the correct host local work area when
               log files have not propagated */
            if (pg_fetch_result($resources, $i, "resourcetypename") == "Execution Host")
            {
              $executionhostid=pg_fetch_result($resources, $i, "resourceid");
            }
          }
        }
        else
        {
          $resourceordering[] = $resourcetypeid;
          /* Only one resource per resource type will ever exist so the resourcetypeid is a suitable key */
          $resourcelogs[$resourcetypeid] = array("name"=>pg_fetch_result($resources, $i, "resourcename"),
                                                 "typename"=>pg_fetch_result($resources, $i, "resourcetypename"),
                                                 "resourceid"=>pg_fetch_result($resources, $i, "resourceid"),
                                                 "logcount"=>0);

          /* Store the execution host to find the correct host local work area when
             log files have not propagated */
          if (pg_fetch_result($resources, $i, "resourcetypename") == "Execution Host")
          {
            $executionhostid=pg_fetch_result($resources, $i, "resourceid");
          }
        }
      }

      /* Display the resources in order */
      for ($i = 0 ; $i < count($resourceordering) ; $i++)
      {
        $info = $resourcelogs[$resourceordering[$i]];

        echo "<tr><th>".htmlentities($info['typename'])."</th><td>".
             "<a href=\"viewresource.php?resourceid=".$info['resourceid']."\">".
             htmlentities($info['name'])."</a></td></tr>\n";
      }

    }
    echo "<tr><th>Start Date</th><td>".$start."</td></tr>\n";
    if ($end != "")
    {
      echo "<tr><th>End Date</th><td>".$end."</td></tr>\n";
    }
    if ($passed != "")
    {
      echo "<tr><th>Status</th><td>".$passed."</td></tr>\n";
    }
    $tra = $_REQUEST['testrunactionid'];
    $istestsuite = !pg_field_is_null($result, 0, "testsuiteid");
    $sql = "SELECT rfl.resultfloat, ri.resultinteger, rs.resultstring, rb.resultboolean,\n".
           "       rf.resultfieldname, ovt_resulttype.resulttypename\n".
           "FROM ovt_resultfield AS rf INNER JOIN ovt_resulttype USING (resulttypeid)\n".
           "     LEFT OUTER JOIN ovt_resultfloat AS rfl ON (rf.resultfieldid=rfl.resultfieldid AND rfl.testrunactionid='".$_REQUEST['testrunactionid']."')\n".
           "     LEFT OUTER JOIN ovt_resultinteger AS ri ON (rf.resultfieldid=ri.resultfieldid AND ri.testrunactionid='".$_REQUEST['testrunactionid']."')\n".
           "     LEFT OUTER JOIN ovt_resultstring AS rs ON (rf.resultfieldid=rs.resultfieldid AND rs.testrunactionid='".$_REQUEST['testrunactionid']."')\n".
           "     LEFT OUTER JOIN ovt_resultboolean AS rb ON (rf.resultfieldid=rb.resultfieldid AND rb.testrunactionid='".$_REQUEST['testrunactionid']."')\n".
           "WHERE (rfl.resultfloat IS NOT NULL\n".
           "       OR ri.resultinteger IS NOT NULL\n".
           "       OR rs.resultstring IS NOT NULL\n".
           "       OR rb.resultboolean IS NOT NULL)";
    $result = pg_query($ovtDB, $sql);
    if (pg_num_rows($result) != 0)
    {
      echo "<tr><th>Results</th><td></td></tr>\n";
      for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
      {
        echo "<tr><td>".pg_fetch_result($result, $i, "resultfieldname")."</td><td>";
        switch (pg_fetch_result($result, $i, "resulttypename"))
        {
        case "integer":
          echo pg_fetch_result($result, $i, "resultinteger");
          break;
        case "float":
          echo pg_fetch_result($result, $i, "resultfloat");
          break;
        case "string":
          echo nl2br(htmlentities(pg_fetch_result($result, $i, "resultstring")));
          break;
        case "boolean":
          echo pg_fetch_result($result, $i, "resultboolean");
          break;
        default:
          echo "##UNKNOWN TYPE##";
          break;
        }
        echo "</td></tr>\n";
      }
    }

    $sql = "SELECT simpleequivalencename, recursiveequivalencename, subrecursiveequivalencename\n".
           "FROM ovt_testrunaction INNER JOIN ovt_simpleequivalence USING (simpleequivalenceid)\n".
           "     INNER JOIN ovt_recursiveequivalence USING (recursiveequivalenceid)\n".
           "     INNER JOIN ovt_subrecursiveequivalence USING (subrecursiveequivalenceid)\n".
           "WHERE testrunactionid=".$_REQUEST['testrunactionid'];
    $result = pg_query($ovtDB, $sql);
    if (pg_num_rows($result) != 1)
    {
      echo "<tr><td colspan=2>Error - equivalences missing</td></tr>\n";
    }
    else
    {
      echo "<tr style=\"display:none\" class=\"equivalences\"><th>Simple Equiv</th>".
           "<td>";
      if ($authenticated)
        echo "<input class=\"textbox\" type=\"textbox\" name=\"simpleequivalencename\" value=\"";
      echo htmlentities(pg_fetch_result($result, 0, "simpleequivalencename"));
      if ($authenticated)
        echo "\" onblur=\"setEquivalenceName(this, 'simple', ".$_REQUEST['testrunactionid'].")\">";
      echo "</td></tr>\n";
      echo "<tr style=\"display:none\" class=\"equivalences\"><th>Total Equiv</th>".
           "<td>";
      if ($authenticated)
        echo "<input class=\"textbox\" type=\"textbox\" name=\"recursiveequivalencename\" value=\"";
      echo htmlentities(pg_fetch_result($result, 0, "recursiveequivalencename"));
      if ($authenticated)
        echo "\" onblur=\"setEquivalenceName(this, 'recursive', ".$_REQUEST['testrunactionid'].")\">";
      echo "</td></tr>\n";
      echo "<tr style=\"display:none\" class=\"equivalences\"><th>Producer Equiv</th>".
           "<td>";
      if ($authenticated)
        echo "<input class=\"textbox\" type=\"textbox\" name=\"subrecursiveequivalencename\" value=\"";
      echo htmlentities(pg_fetch_result($result, 0, "subrecursiveequivalencename"));
      if ($authenticated)
        echo "\" onblur=\"setEquivalenceName(this, 'subrecursive', ".$_REQUEST['testrunactionid'].")\">";
      echo "</td></tr>\n";
    }
    if ($istestsuite)
    {
      echo "<tr><td></td><td><a href=\"viewresults.php?testrunactionid=".$tra."\">Analyze Testsuite</a></td></tr>\n";
    }

    $rootdir = "";
    if ($executionhostid !== NULL)
    {
      $sql = "SELECT ovt_resourceattribute.value, ovt_resource.hostname\n".
             "FROM ovt_resourceattribute INNER JOIN ovt_attribute USING (attributeid)\n".
             "     INNER JOIN ovt_resource USING (resourceid)\n".
             "WHERE ovt_resourceattribute.resourceid='".$executionhostid."'\n".
             "AND ovt_attribute.attributename='Overtest rootdir'";
      $result = pg_query($ovtDB, $sql);
      if (pg_num_rows($result) == 1)
      {
        $rootdir = pg_fetch_result($result, 0, "hostname").":".pg_fetch_result($result, 0, "value")."/";
      }
    }

    $dir = $overtestroot."/".$testrunid."/".$versionedactionid;
    if (is_dir($dir))
    {
      $logs = array();
      $actionlogs = array();
      if ($dh = opendir($dir))
      {
        while (($file = readdir($dh)) !== false)
        {
          if ($file == "." || $file == ".." || $file == "work")
            continue;
          if (strncmp($file, "log.", 4) == 0)
          {
            $actionlogs[] = substr($file, 4);
          }
          elseif (strncmp($file, "r", 1) == 0)
          {
            $keys = array_keys($resourcelogs);
            $file = substr($file, 1);
            for ($i = 0 ; $i < count($resourcelogs) ; $i++)
            {
              if (strncmp($keys[$i], $file, strlen($keys[$i])) == 0)
              {
                /* Found a log for a resource */
                $file = substr($file, strlen($keys[$i])+1);
                $resourcelogs[$keys[$i]]['logcount'] = ((int)$file)+1;
              }
            }
          }
          else
          {
            $filenumber = (int)$file;
            $file = substr($file, strpos($file, ".")+1);
            if (!isset($logs[$filenumber]))
              $logs[$filenumber] = array();
            $logs[$filenumber][] = $file;
          }
        }
        closedir($dh);
      }
      if (count($actionlogs) != 0)
      {
        echo "<tr><th>Application logs</th><td>";
        foreach ($actionlogs as $log)
        {
          echo "<a href=\"viewlog.php?testrunid=".$testrunid."&amp;versionedactionid=".$versionedactionid."&amp;log=".urlencode($log)."&amp;actionlog=1\">".$log."</a><br />\n";
        }
        echo "</td></tr>\n";
      }
    }
    else
    {
      echo "<tr><td></td><td>Results directory missing: ".$rootdir.$testrunid."/".$versionedactionid."</td></tr>\n";
    }

    if (pg_num_rows($checkauto) == 1)
    {
      echo "<tr><th colspan=2><a class=\"dom_link\" href=\"javascript:toggleVisible('tr','config_automatic');\">Toggle automatic config</a></th></tr>\n";
    }
    echo "<tr><th colspan=2><a class=\"dom_link\" href=\"javascript:toggleVisible('tr','equivalences');\">Toggle equivalences</a></th></tr>\n";

    echo "</table>\n".
         "</form>\n".
         "</div>\n";
    if (is_dir($dir))
    {
      echo "<div style=\"float:left; border:1px solid #0000DD; margin:5px;\">\n".
           "<table>\n";
      echo "<tr><th colspan=2>Task logs <a class=\"dom_link\" href=\"javascript:toggleVisible('span','tasklog_path');\">Toggle Paths</a></th></tr>\n";
      $lognames = array("stdin", "stdout", "stderr", "combined", "returncode");
      foreach ($lognames as $name)
      {
        echo "<tr><td>".$name."</td><td>";
        for ($i = 0 ; $i < count($logs) ; $i++)
        {
          $ext = "";
          if (!in_array($name, $logs[$i]))
          {
            $ext = ".gz";
          }
          echo "<a target=\"_blank\" href=\"viewlog.php?testrunid=".$testrunid."&amp;versionedactionid=".$versionedactionid."&amp;log=".$name.$ext."&amp;command=".$i."\">".$i."</a> ";
          echo "<span style=\"display:none\" class=\"tasklog_path\">$rootdir$testrunid/$versionedactionid/$i.$name$ext</span>";
        }
        echo "</td></tr>\n";
      }

      $keys = array_keys($resourcelogs);
      for ($i = 0 ; $i < count($resourcelogs) ; $i++)
      {
        if ($resourcelogs[$keys[$i]]['logcount'] != 0)
        {

         echo "</table>\n".
              "</div>\n".
              "<div style=\"float:left; border:1px solid #0000DD; margin:5px;\">\n".
              "<table>\n";
          echo "<tr><th colspan=2>".htmlentities($resourcelogs[$keys[$i]]['name']).
               " logs</th></tr>\n";
          foreach ($lognames as $name)
          {
            echo "<tr><td>".$name."</td><td>";
            for ($j = 0 ; $j < $resourcelogs[$keys[$i]]['logcount'] ; $j++)
            {
              echo "<a target=\"_blank\" href=\"viewlog.php?testrunid=".$testrunid."&amp;versionedactionid=".$versionedactionid."&amp;log=".$name."&amp;command=".$j."&amp;resourcetypeid=".$keys[$i]."\">".$j."</a> ";
            }
            echo "</td></tr>\n";
          }

        }
      }
      echo "</table>\n".
           "</div>\n";
    }

  }
}

?>
