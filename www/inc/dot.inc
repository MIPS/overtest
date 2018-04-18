<?php
  include_once('includes.inc');

function draw_testrun($testrunid, $type = "png")
{
  global $ovtDB;

  $sql = "SELECT ovt_resourcetype.resourcetypeid, ovt_resourcetype.resourcetypename,\n".
         "       ovt_attribute.attributeid, ovt_attribute.attributename,\n".
         "       ovt_attributevalue.attributevalueid, ovt_attributevalue.value\n".
         "FROM ovt_resourcetype INNER JOIN ovt_attribute USING (resourcetypeid)\n".
         "     INNER JOIN ovt_attributevalue USING (attributeid)\n".
         "     INNER JOIN ovt_testrunattributevalue USING (attributevalueid)\n".
         "WHERE ovt_testrunattributevalue.testrunid='".$_REQUEST['testrunid']."'\n".
         "ORDER BY ovt_resourcetype.resourcetypename, ovt_attribute.attributename, ovt_attributevalue.value";

  $resourcerequests = pg_query($ovtDB, $sql);

  $sql = "SELECT ovt_action.actionname, ovt_versionedaction.versionname,\n".
         "       (ovt_testrunaction.starteddate IS NOT NULL) AS running,\n".
         "       ovt_testrunaction.passed, ovt_testrunaction.versionedactionid,\n".
         "       ovt_testrunaction.testrunactionid\n".
         "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "     INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "WHERE ovt_testrunaction.testrunid='".$_REQUEST['testrunid']."'";
  
  $result = pg_query($ovtDB, $sql);
  
  $gv = "digraph testrun {dpi=100;size=\"12,200\";\n";
  for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
  {
    $hostoptions = "label=\"".pg_fetch_result($result, $i, "actionname")."\"";
    $hostoptions .= ", URL=\"javascript:viewresult(".pg_fetch_result($result, $i, "testrunactionid").");\"";
    if (!pg_field_is_null($result, $i, "passed"))
    {
      if (pg_fetch_result($result, $i, "passed") == 't')
      {
        $hostoptions .= ", color=green";
      }
      else
      {
        $hostoptions .= ", color=red, peripheries=2";
      }
    }
    else if (pg_fetch_result($result, $i, "running") == 't')
    {
      $hostoptions .= ", shape=doubleoctagon";
    }
    $gv .= pg_fetch_result($result, $i, "versionedactionid")." [".$hostoptions."];\n";
  }

  $sql = "SELECT t1.successful, t1.description, t1.testrunid\n".
         "FROM ovt_testrun AS t1 INNER JOIN ovt_testrun AS t2 ON (t1.testrunid=t2.deptestrunid)\n".
	 "WHERE t2.testrunid='".$_REQUEST['testrunid']."'";
  $result = pg_query($ovtDB, $sql);

  if (pg_num_rows($result) > 0)
  {
    $hostoptions = "shape=box, label=\"".pg_fetch_result($result, 0, "description")."\"";
    $hostoptions .= ", URL=\"viewtestrun.php?testrunid=".pg_fetch_result($result, 0, "testrunid")."\"";
    // There is a producer testrun
    if (!pg_field_is_null($result, 0, "successful"))
    {
      if (pg_fetch_result($result, 0, "successful") == "t")
      {
        $hostoptions .= ", color=green";
      }
      else
      {
        $hostoptions .= ", color=red";
      }
    }
    $gv .= "subgraph cluster_1 {\n";
    $gv .= "label=\"Depends on testrun\";\n";
    $gv .= "deptestrun [".$hostoptions."];\n";
    $gv .= "}\n";
  }

  $sql = "SELECT ovt_dependency.versionedactionid, ovt_dependency.versionedactiondep\n".
         "FROM ovt_dependency INNER JOIN ovt_testrunaction AS tr1 ON (tr1.versionedactionid=ovt_dependency.versionedactionid\n".
         "                                                            AND tr1.testrunid='".$_REQUEST['testrunid']."')\n".
         "     INNER JOIN ovt_versionedaction AS va1 ON (tr1.versionedactionid=va1.versionedactionid)\n".
         "     INNER JOIN ovt_action AS a1 ON (va1.actionid=a1.actionid)\n".
         "     INNER JOIN ovt_testrunaction AS tr2 ON (tr2.versionedactionid=ovt_dependency.versionedactiondep\n".
         "                                             AND tr2.testrunid='".$_REQUEST['testrunid']."')\n".
         "     INNER JOIN ovt_versionedaction AS va2 ON (tr2.versionedactionid=va2.versionedactionid)\n".
         "     INNER JOIN ovt_action AS a2 ON (va2.actionid=a2.actionid)\n";
  
  $result = pg_query($ovtDB, $sql);

  for ($i = 0 ;$i < pg_num_rows($result) ; $i++)
  {
    $gv .= pg_fetch_result($result, $i, "versionedactionid") . " -> ".pg_fetch_result($result, $i, "versionedactiondep")." [arrowtail=normal, arrowhead=none];\n";
  }

  if (pg_num_rows($resourcerequests) != 0)
  {
    $typeid = "";
    $attributeid = "";
    $resources = array();
    $valuecount = 0;
    for ($i = 0; $i < pg_num_rows($resourcerequests) ; $i++)
    {
      if ($typeid != pg_fetch_result($resourcerequests, $i, "resourcetypename"))
      {
        $typeid = pg_fetch_result($resourcerequests, $i, "resourcetypename");
        $resources[$typeid] = array();
        $attributeid = "";
      }
      if ($attributeid != pg_fetch_result($resourcerequests, $i, "attributename"))
      {
        $attributeid = pg_fetch_result($resourcerequests, $i, "attributename");
        $resources[$typeid][$attributeid] = array();
      }
      $resources[$typeid][$attributeid][] = pg_fetch_result($resourcerequests, $i, "value");;
      $valuecount++;
    }
    $rescount = 0;
    foreach ($resources as $resourcetype => $attributenamearray)
    {
      $gv .= "res".$rescount . " [ shape=none, margin=0, fontsize=8, label=<<TABLE BORDER=\"0\" CELLBORDER=\"1\" CELLSPACING=\"0\" CELLPADDING=\"4\"><TR><TD COLSPAN=\"$valuecount\">". $resourcetype."</TD></TR>\n";
      $gv .= "<TR>";
      $finalrow="<TR>";
      foreach ($attributenamearray as $attributename => $valuearray)
      {
        $gv .= "<TD COLSPAN=\"".count($valuearray)."\">$attributename</TD>";
        for ($i = 0 ; $i < count($valuearray) ; $i++)
        {
          $finalrow.="<TD>".$valuearray[$i]."</TD>";
        }
      }
      $gv .= "</TR>\n";
      $gv.=$finalrow."</TR>\n";
      $gv .= "</TABLE>>];\n";
      $rescount++;
    }
  }

  $gv .= "}\n";

  $descriptorspec = array(
   0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
   1 => array("pipe", "w")  // stdout is a pipe that the child will write to
  );
  $cwd = '/tmp';

  if ($type != "png" && $type != "cmapx")
  {
    $type = "png";
  }

  $process = proc_open("dot -T".$type." ", $descriptorspec, $pipes, $cwd);

  $contents = "";
  if (is_resource($process))
  {
    // $pipes now looks like this:
    // 0 => writeable handle connected to child stdin
    // 1 => readable handle connected to child stdout

    fwrite($pipes[0], $gv);
    fclose($pipes[0]);

    $contents = stream_get_contents($pipes[1]);
    fclose($pipes[1]);

    // It is important that you close any pipes before calling
    // proc_close in order to avoid a deadlock
    $return_value = proc_close($process);

  }
  if ($type == "cmapx")
  {
    $contents = str_replace("<map id=\"testrun\" name=\"testrun\">", "", $contents);
    $contents = str_replace("</map>", "", $contents);
  }
  return $contents;
}

function draw_graph()
{

  $descriptorspec = array(
   0 => array("pipe", "r"),  // stdin is a pipe that the child will read from
   1 => array("pipe", "w")  // stdout is a pipe that the child will write to
  );
  $cwd = '/tmp';
  $env['MPLCONFIGDIR'] = "/tmp";
  $process = proc_open("/home/overtest/python25/bin/python /home/mfortune/test.py", $descriptorspec, $pipes, $cwd, $env);
  $contents = "";
  if (is_resource($process))
  {
    // $pipes now looks like this:
    // 0 => writeable handle connected to child stdin
    // 1 => readable handle connected to child stdout

    fclose($pipes[0]);

    $contents = stream_get_contents($pipes[1]);
    fclose($pipes[1]);

    // It is important that you close any pipes before calling
    // proc_close in order to avoid a deadlock
    $return_value = proc_close($process);

  }
  return $contents;

}

?>
