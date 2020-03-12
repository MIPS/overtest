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
session_start();
include_once('connect_overtestdb_webuser.inc');
header("Cache-Control: no-cache, must-revalidate"); // HTTP/1.1
header("Expires: Sat, 26 Jul 1997 05:00:00 GMT"); // Date in the past

function getTestrunCount()
{
  global $ovtDB;
  $testruncount = 1;
  if (!isset($_REQUEST['testrunid']))
  {
    $sql = "SELECT count(testrunid) AS testruncount\n".
           "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)\n".
           "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'\n".
           "AND ovt_runstatus.iseditable";
    $result = pg_query($ovtDB, $sql);

    $testruncount = pg_fetch_result($result, 0, "testruncount");
  }
  return $testruncount;
}

if (!isset($_REQUEST['what']))
{
  echo "BAD REQUEST";
}
else if ($_REQUEST['what'] == "categories")
{
  echo   "<select style=\"width:100%\" id=\"category\" name=\"category\" size=10 onmouseover=\"ShowTip('Click to view actions');\" onmouseout=\"HideTip();\"  onchange=\"getActions(this.value);\">\n";
  $sql = "SELECT *\n".
         "FROM ovt_actioncategory INNER JOIN ovt_lifecyclestate USING (lifecyclestateid)\n".
         "WHERE visible\n".
         "AND valid\n";
  if (!isset($_REQUEST['showall']) || $_REQUEST['showall'] != 1)
  {
    $sql .= "AND visiblebydefault\n";
  }
  $sql .="ORDER BY actioncategoryname";
  $result = pg_query($ovtDB, $sql);
  if (pg_num_rows($result) == 0)
  {
    echo "<option>[NO CATEGORIES]</option>\n";
  }
  else
  {
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "actioncategoryid")."\">".pg_fetch_result($result, $i, "actioncategoryname")."</option>\n";
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "actions")
{
  if (!isset($_REQUEST['offset']))
  {
    $_REQUEST['offset'] = 0;
  }
  $offset = (int)$_REQUEST['offset'];

  $sql = "SELECT *\n".
         "FROM ovt_action INNER JOIN ovt_lifecyclestate USING (lifecyclestateid)\n".
         "WHERE actioncategoryid='".$_REQUEST['actioncategoryid']."'\n".
         "AND visible\n".
         "AND valid\n";
  if (!isset($_REQUEST['showall']) || $_REQUEST['showall'] != 1)
  {
    $sql .= "AND visiblebydefault\n";
  }
  $sql .= "ORDER BY actionname\n".
         "OFFSET ".$offset." LIMIT 101";

  echo   "<select style=\"width:100%\" name=\"action\" id=\"action\" size=10 onmouseover=\"ShowTip('Click to view versions');\" onmouseout=\"HideTip();\" onchange=\"getVersions(this.value);\">\n";
  $result = pg_query($ovtDB, $sql);
  if (pg_num_rows($result) == 0)
  {
    echo "<option>[NO ACTIONS]</option>\n";
  }
  else
  {
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      if ($i == 100)
      {
        echo "<option value=\"more".($offset+100)."\">More Actions...</option>\n";
      }
      else
      {
        echo "<option value=\"".pg_fetch_result($result, $i, "actionid")."\">".pg_fetch_result($result, $i, "actionname")."</option>\n";
      }
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "versions")
{
  $sql = "SELECT *\n".
         "FROM ovt_versionedaction INNER JOIN ovt_lifecyclestate USING (lifecyclestateid)\n".
         "WHERE actionid='".$_REQUEST['actionid']."'\n".
         "AND visible\n".
         "AND valid\n";
  if (!isset($_REQUEST['showall']) || $_REQUEST['showall'] != 1)
  {
    $sql .= "AND visiblebydefault\n";
  }
  $sql .= "ORDER BY versionname";

  echo   "<select style=\"width:100%\" name=\"versionedaction\" size=10 onmouseover=\"ShowTip('Double click to add to testrun');\" onmouseout=\"HideTip();\" ondblclick=\"addVersionedAction(this.value);\">\n";
  $result = pg_query($ovtDB, $sql);
  if (pg_num_rows($result) == 0)
  {
    echo "<option>[NO VERSIONS]</option>\n";
  }
  else
  {
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "versionedactionid")."\" class=\"addtotestrun\">".pg_fetch_result($result, $i, "versionname")."</option>\n";
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "testrun")
{
  if (isset($_REQUEST['versionedactionid']))
  {
    $edittype='testrun';
    $editmode='add';
    
    if (isset($_REQUEST['remove']) && $_REQUEST['remove'] == 1)
    {
      $editmode = 'remove';
    }
    if (isset($_REQUEST['testrunid']))
    {
      $keyid=$_REQUEST['testrunid'];
    }
    else
    {
      $keyid=$_REQUEST['testrungroupid'];
      $edittype = 'group';
    }

    $sql = "SELECT ovt_modify_tasks('".$edittype."', '".$editmode."', '".$keyid."', '".$_REQUEST['versionedactionid']."')";
    pg_query($ovtDB, $sql);
  }

  $testruncount = getTestrunCount();

  $sql = "SELECT ovt_action.actionname, ovt_versionedaction.versionname, ovt_versionedaction.versionedactionid, count(ovt_versionedaction.versionedactionid) AS testruncount\n".
         "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "     INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "     INNER JOIN ovt_testrun USING (testrunid)\n".
         "     INNER JOIN ovt_runstatus USING (runstatusid)\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE ovt_testrunaction.testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE ovt_testrun.testrungroupid='".$_REQUEST['testrungroupid']."'\n".
           "AND ovt_runstatus.iseditable\n";
  }
  $sql .="GROUP BY ovt_versionedaction.versionedactionid, ovt_versionedaction.versionname, ovt_action.actionname\n".
         "ORDER BY ovt_action.actionname, ovt_versionedaction.versionname";
  $result = pg_query($ovtDB, $sql);
  echo "<b>Actions in testrun</b><br />\n";
  echo "<select style=\"width:100%\" name=\"testrun\" size=10";
  if (pg_num_rows($result) == 0)
  {
    echo ">\n";
    echo "<option>[EMPTY]</option>\n";
  }
  else
  {
    echo " onmouseover=\"ShowTip('Click to show dependencies.<br />Double click to remove from testrun');\" onmouseout=\"HideTip();\" onchange=\"getDependencies(this.value)\" ondblclick=\"removeVersionedAction(this.value);\">\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      $optionstyle="";
      if (pg_fetch_result($result, $i, "testruncount") < $testruncount)
      {
        $optionstyle=" style=\"background-color:#ffccff\"";
      }
      echo "<option value=\"".pg_fetch_result($result, $i, "versionedactionid")."\" class=\"removefromtestrun\" $optionstyle>".pg_fetch_result($result, $i, "actionname").":".pg_fetch_result($result, $i, "versionname")."</option>\n";
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "dependencies")
{
  $sql = "SELECT ovt_action.actionname, ovt_versionedaction.versionedactionid, ovt_versionedaction.versionname\n".
         "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "     INNER JOIN ovt_dependency ON (ovt_versionedaction.versionedactionid=ovt_dependency.versionedactiondep)\n".
         "WHERE ovt_dependency.versionedactionid='".$_REQUEST['versionedactionid']."'\n".
         "ORDER BY ovt_action.actionname, ovt_versionedaction.versionname";
  $result = pg_query($ovtDB, $sql);

  $sql = "SELECT ovt_action.actionname || ':' || ovt_versionedaction.versionname\n".
         "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "WHERE versionedactionid='".$_REQUEST['versionedactionid']."'";
  $name = pg_fetch_result(pg_query($ovtDB, $sql), 0, 0);
  echo "<b>Producers for ".$name."</b><br />\n";
  echo   "<select style=\"width:100%\" name=\"dependency\" size=10";
  if (pg_num_rows($result) == 0)
  {
    echo ">\n";
    echo "<option>[NO PRODUCERS]</option>\n";
  }
  else
  {
    echo " onmouseover=\"ShowTip('Double click to add to testrun');\" onmouseout=\"HideTip();\" ondblclick=\"addVersionedAction(this.value);\">\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "versionedactionid")."\" class=\"addtotestrun\">".pg_fetch_result($result, $i, "actionname").":".pg_fetch_result($result, $i, "versionname")."</option>\n";
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "resourcetypes")
{
  $sql = "SELECT DISTINCT * FROM\n".
         "((SELECT DISTINCT ovt_resourcetype.resourcetypeid, ovt_resourcetype.resourcetypename\n".
         "  FROM ovt_resourcetype INNER JOIN ovt_attribute USING (resourcetypeid)\n".
         "       INNER JOIN ovt_attributevalue USING (attributeid)\n".
         "       INNER JOIN ovt_versionedactionattributevalue USING (attributevalueid)\n".
         "       INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "       INNER JOIN ovt_testrun USING (testrunid)\n".
         "       INNER JOIN ovt_runstatus USING (runstatusid)\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="  WHERE ovt_testrunaction.testrunid='".$_REQUEST['testrunid']."')\n";
  }
  else
  {
    $sql .="  WHERE ovt_testrun.testrungroupid='".$_REQUEST['testrungroupid']."'\n".
           "  AND ovt_runstatus.iseditable)\n";
  }
  $sql .=" UNION\n".
         " (SELECT resourcetypeid, resourcetypename\n".
         "  FROM ovt_resourcetype\n".
         "  WHERE resourcetypename='Execution Host')) AS one\n".
         "ORDER BY resourcetypename";
  $result = pg_query($ovtDB, $sql);
  echo "<b>Resource Types</b><br />\n";
  echo   "<select style=\"width:100%\" name=\"resourcetype\" size=10";
  if (pg_num_rows($result) == 0)
  {
    echo ">\n";
    echo "<option>[NO GROUPS]</option>\n";
  }
  else
  {
    echo " onmouseover=\"ShowTip('Click to view attributes');\" onmouseout=\"HideTip();\" onchange=\"getAttributes(this.value);\">\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "resourcetypeid")."\">".pg_fetch_result($result, $i, "resourcetypename")."</option>\n";
    }
  }
  echo "</select>\n";

}
else if ($_REQUEST['what'] == "attributes")
{

  $sql = "SELECT attributeid, attributename\n".
         "FROM ovt_attribute\n".
         "WHERE resourcetypeid='".$_REQUEST['resourcetypeid']."'\n".
         "AND lookup\n".
         "ORDER BY attributename";
  $result = pg_query($ovtDB, $sql);
  echo "<b>Select an attribute</b><br />\n";
  echo   "<select style=\"width:100%\" name=\"attribute\" size=10 onmouseover=\"ShowTip('Click to view values');\" onmouseout=\"HideTip();\" onchange=\"getAttributeValues(this.value);\">\n";
  if (pg_num_rows($result) == 0)
  {
    echo "<option>[NO ATTRIBUTES]</option>\n";
  }
  else
  {
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "attributeid")."\">".pg_fetch_result($result, $i, "attributename")."</option>\n";
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "attributevalues")
{

  $sql = "SELECT attributevalueid, value\n".
         "FROM ovt_attributevalue\n".
         "WHERE attributeid='".$_REQUEST['attributeid']."'\n".
         "ORDER BY value";
  $result = pg_query($ovtDB, $sql);
  echo "<b>Select a value</b><br />\n";
  echo   "<select style=\"width:100%\" name=\"attributevalueid\" size=10 onmouseover=\"ShowTip('Double click to add to testrun');\" onmouseout=\"HideTip();\" ondblclick=\"addAttributeValue(this.value);\">\n";
  if (pg_num_rows($result) == 0)
  {
    echo "<option>[NO VALUES]</option>\n";
  }
  else
  {
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "attributevalueid")."\" class=\"addtotestrun\">".pg_fetch_result($result, $i, "value")."</option>\n";
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "resourcerequirements")
{
  if (isset($_REQUEST['attributevalueid']))
  {
    $edittype = "testrun";
    $editmode = "add";
    if (isset($_REQUEST['remove']) && $_REQUEST['remove'] = "1")
    {
      $editmode = "remove";
    }
    if (isset($_REQUEST['testrunid']))
    {
      $keyid = $_REQUEST['testrunid'];
    }
    else
    {
      $keyid = $_REQUEST['testrungroupid'];
      $edittype = "group";
    }
    $sql = "SELECT ovt_modify_requirements('".$edittype."', '".$editmode."', '".$keyid."', '".$_REQUEST['attributevalueid']."')";
    pg_query($ovtDB, $sql);
  }
  $testruncount = getTestrunCount();

  $sql = "SELECT ovt_resourcetype.resourcetypename,\n".
         "       ovt_attribute.attributename,\n".
         "       ovt_attributevalue.attributevalueid,\n".
         "       ovt_attributevalue.value,\n".
         "       count(ovt_attributevalue.attributevalueid) AS testruncount\n".
         "FROM ovt_testrunattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid)\n".
         "     INNER JOIN ovt_attribute USING (attributeid)\n".
         "     INNER JOIN ovt_resourcetype USING (resourcetypeid)\n".
         "     INNER JOIN ovt_testrun USING (testrunid)\n".
         "     INNER JOIN ovt_runstatus USING (runstatusid)\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE ovt_testrunattributevalue.testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE ovt_testrun.testrungroupid='".$_REQUEST['testrungroupid']."'\n".
           "AND ovt_runstatus.iseditable\n";
  }
  $sql .="GROUP BY ovt_attributevalue.attributevalueid, ovt_attribute.attributename, ovt_attributevalue.value, ovt_resourcetype.resourcetypename\n".
         "ORDER BY ovt_resourcetype.resourcetypename, ovt_attribute.attributename, ovt_attributevalue.value";

  $result = pg_query($ovtDB, $sql);
  echo "<b>Resource requirements</b><br />\n";
  echo   "<select style=\"width:100%\" name=\"requirementid\" size=10 onmouseover=\"ShowTip('Double click to remove from testrun');\" onmouseout=\"HideTip();\" ondblclick=\"removeAttributeValue(this.value);\">\n";
  if (pg_num_rows($result) == 0)
  {
    echo "<option>[NO VALUES]</option>\n";
  }
  else
  {
    $currentgroup = "";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      if ($currentgroup != pg_fetch_result($result, $i, "resourcetypename"))
      {
        if ($currentgroup != "")
        {
          echo "</optgroup>\n";
        }
        $currentgroup = pg_fetch_result($result, $i, "resourcetypename");
        echo "<optgroup label=\"".$currentgroup."\">\n";
      }
      $optionstyle="";
      if (pg_fetch_result($result, $i, "testruncount") < $testruncount)
      {
        $optionstyle=" style=\"background-color:#ffccff\"";
      }
      echo "<option value=\"".pg_fetch_result($result, $i, "attributevalueid")."\" class=\"removefromtestrun\" $optionstyle>".pg_fetch_result($result, $i, "attributename")."=".pg_fetch_result($result, $i, "value")."</option>\n";
    }
    echo "</optgroup>\n";
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "configgroups")
{
  $sql = "SELECT DISTINCT ovt_configoptiongroup.configoptiongroupid, ovt_configoptiongroup.configoptiongroupname\n".
         "FROM ovt_configoptiongroup INNER JOIN ovt_configoption USING (configoptiongroupid)\n".
         "     INNER JOIN ovt_versionedactionconfigoption USING (configoptionid)\n".
         "     INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "     INNER JOIN ovt_testrun USING (testrunid)\n".
         "     INNER JOIN ovt_runstatus USING (runstatusid)\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE ovt_testrunaction.testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE ovt_testrun.testrungroupid='".$_REQUEST['testrungroupid']."'\n".
           "AND ovt_runstatus.iseditable\n";
  }
  $sql .="AND NOT ovt_configoptiongroup.automatic\n".
         "ORDER BY ovt_configoptiongroup.configoptiongroupname";

  $result = pg_query($ovtDB, $sql);

  echo "<b>Configuration Group</b><br />\n";
  echo "<select style=\"width:100%\" name=\"configgroupid\" size=10";
  if (pg_num_rows($result) == 0)
  {
    echo ">\n";
    echo "<option>[NO GROUPS]</option>\n";
  }
  else
  {
    echo " onmouseover=\"ShowTip('Click to view options');\" onmouseout=\"HideTip();\" onchange=\"getConfigOptions(this.value);\">\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "configoptiongroupid")."\">".pg_fetch_result($result, $i, "configoptiongroupname")."</option>\n";
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "configoptions")
{
  $sql = "SELECT DISTINCT ovt_configoption.configoptionid, ovt_configoption.configoptionname\n".
         "FROM ovt_configoption INNER JOIN ovt_versionedactionconfigoption USING (configoptionid)\n".
         "     INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "     INNER JOIN ovt_testrun USING (testrunid)\n".
         "     INNER JOIN ovt_runstatus USING (runstatusid)\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE ovt_testrunaction.testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE ovt_testrun.testrungroupid='".$_REQUEST['testrungroupid']."'\n".
           "AND ovt_runstatus.iseditable\n";
  }
  $sql .="AND ovt_configoption.configoptiongroupid='".$_REQUEST['configoptiongroupid']."'\n".
         "ORDER BY ovt_configoption.configoptionname";

  $result = pg_query($ovtDB, $sql);

  echo "<b>Configuration Options</b><br />\n";
  echo   "<select style=\"width:100%\" name=\"configoptionid\" size=10 onmouseover=\"ShowTip('Click to view setting');\" onmouseout=\"HideTip();\" onchange=\"getConfigSetting(this.value);\">\n";
  if (pg_num_rows($result) == 0)
  {
    echo "<option>[NO OPTIONS]</option>\n";
  }
  else
  {
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "configoptionid")."\">".pg_fetch_result($result, $i, "configoptionname")."</option>\n";
    }
  }
  echo "</select>\n";
}
else if ($_REQUEST['what'] == "setting")
{
  $sql = "SELECT ovt_configoption.defaultvalue, ovt_configoptiontype.configoptiontypename,\n".
         "       ovt_configoption.islookup, ovt_configsetting.configoptionlookupid,\n".
         "       ovt_configsetting.configvalue, count(ovt_configsetting.configvalue) AS testruncount,\n".
         "       count(ovt_configsetting.configoptionlookupid) AS testruncountlookup\n".
         "FROM ovt_configoption INNER JOIN ovt_configoptiontype USING (configoptiontypeid)\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="     LEFT OUTER JOIN ovt_configsetting ON (ovt_configsetting.configoptionid=ovt_configoption.configoptionid\n".
           "                                           AND ovt_configsetting.testrunid='".$_REQUEST['testrunid']."')\n";
  }
  else
  {
    $sql .="     LEFT OUTER JOIN (ovt_configsetting INNER JOIN ovt_testrun ON (ovt_testrun.testrunid=ovt_configsetting.testrunid\n".
           "                                                                   AND ovt_testrun.testrungroupid='".$_REQUEST['testrungroupid']."')\n".
           "                      INNER JOIN ovt_runstatus ON (ovt_testrun.runstatusid=ovt_runstatus.runstatusid\n".
           "                                                   AND ovt_runstatus.iseditable))\n".
           "     USING (configoptionid)\n";
  }
  $sql .="WHERE ovt_configoption.configoptionid='".$_REQUEST['configoptionid']."'\n".
         "GROUP BY ovt_configsetting.configvalue, ovt_configsetting.configoptionlookupid, ovt_configoption.islookup, ovt_configoptiontype.configoptiontypename, ovt_configoption.defaultvalue";

  $result = pg_query($ovtDB, $sql);

  if (isset($_REQUEST['testrunid']))
  {
    $testruncount = 1;
  }
  else
  {
    $sql = "SELECT count(DISTINCT testrunid) AS testruncount\n".
           "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)\n".
           "     INNER JOIN ovt_testrunaction USING (testrunid)\n".
           "     INNER JOIN ovt_versionedactionconfigoption USING (versionedactionid)\n".
           "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'\n".
           "AND ovt_runstatus.iseditable\n".
           "AND ovt_versionedactionconfigoption.configoptionid='".$_REQUEST['configoptionid']."'";
    $countresult = pg_query($ovtDB, $sql);
    $testruncount = pg_fetch_result($countresult, 0, "testruncount");
  }

  echo "<b>Setting</b><br />\n";
  if (pg_fetch_result($result, 0, "islookup") == 't')
  {
    $multiple = false;
    $sql = "SELECT lookupname, configoptionlookupid\n".
           "FROM ovt_configoptionlookup\n".
           "WHERE defaultlookup\n".
           "AND configoptionid='".$_REQUEST['configoptionid']."'";
    $defaultresult = pg_query($ovtDB, $sql);
    if (pg_num_rows($result) != 1 || 
        (pg_fetch_result($result, 0, "testruncountlookup") != 0 && pg_fetch_result($result, 0, "testruncountlookup")!= $testruncount))
    {

      $multiple = true;
      echo "<i>&lt;Various&gt;</i><br />\n";
      $totalnondefault = 0;
      $defaultvalue = pg_fetch_result($defaultresult, 0, "lookupname");

      for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
      {
        $count = pg_fetch_result($result, $i, "testruncountlookup");
        $sql = "SELECT lookupname\n".
               "FROM ovt_configoptionlookup\n".
               "WHERE configoptionlookupid='".pg_fetch_result($result, $i, "configoptionlookupid")."'";
        $valueresult = pg_query($ovtDB, $sql);
        $value = pg_fetch_result($valueresult, 0, "lookupname");

        if ($value == $defaultvalue)
        {
          continue;
        }
        $totalnondefault += $count;
        echo "(".$count.") ";
        if (strlen($value) == 0)
        {
          $value = "<i>[empty]</i>";
        }
        else
        {
          $value = htmlentities($value);
        }
        echo $value."<br />\n";
      }
      if ($testruncount - $totalnondefault != 0)
      {
        echo "(".($testruncount - $totalnondefault).") ";
        $value = $defaultvalue;
        if (strlen($value) == 0)
        {
          $value = "<i>[empty]</i>";
        }
        else
        {
          $value = htmlentities($value);
        }
        echo $value."<br />\n";
      }
      echo "<br />\n";
    }

    /* Invert the inclusive selection of lookup options and then subtract those
       (non linked) config option lookups from the full set. Leaving only those
       that are common to all linked versioned actions. Always show the default
       option even if it is not linked */
    $sql = "SELECT *\n".
           "FROM \n".
           "((SELECT ovt_configoptionlookup.configoptionlookupid, lookupname, defaultlookup\n".
           " FROM ovt_configoptionlookup\n".
           " WHERE configoptionid='".$_REQUEST['configoptionid']."')\n".
           "EXCEPT\n".
           "(SELECT ovt_configoptionlookup.configoptionlookupid, lookupname, defaultlookup\n".
           " FROM ovt_configoptionlookup INNER JOIN ovt_configoption USING (configoptionid)\n".
           "      INNER JOIN ovt_versionedactionconfigoption USING (configoptionid)\n".
           "      INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
           "      INNER JOIN ovt_testrun USING (testrunid)\n".
           "      INNER JOIN ovt_runstatus USING (runstatusid)\n".
           "      LEFT OUTER JOIN ovt_versionedactionconfigoptionlookup ON (ovt_versionedactionconfigoption.versionedactionid=ovt_versionedactionconfigoptionlookup.versionedactionid\n".
           "                                                                AND ovt_versionedactionconfigoptionlookup.configoptionlookupid=ovt_configoptionlookup.configoptionlookupid)\n".
           " WHERE ovt_versionedactionconfigoptionlookup.versionedactionconfigoptionlookupid IS NULL\n".
           " AND NOT ovt_configoptionlookup.defaultlookup\n".
           " AND ovt_versionedactionconfigoption.configoptionid='".$_REQUEST['configoptionid']."'\n";
    if (isset($_REQUEST['testrunid']))
    {
      $sql .= " AND ovt_testrun.testrunid='".$_REQUEST['testrunid']."'\n";
    }
    else
    {
      $sql .= " AND ovt_testrun.testrungroupid='".$_REQUEST['testrungroupid']."'\n";
    }
    $sql .=" AND ovt_runstatus.iseditable)) AS lookups\n".
           "ORDER BY lookupname";

    $lookup = pg_query($ovtDB, $sql);

    echo   "<select style=\"width:100%\" name=\"settingid\" onchange=\"configsettingchanged();checkandsaveconfig(this.value, ".$_REQUEST['configoptionid'].");\">\n";

    /* Pretend there is a valid existing option (i.e. lack of a selected option is valid) */
    $foundexisting = true;

    /* Check the existing option if present */
    if (!pg_field_is_null($result, 0, "configoptionlookupid"))
    {
      $foundexisting = false;
      /* Check if the selected lookup option is in the list.
         If it is missing then display and select a blank row */
      for ($i = 0 ; $i < pg_num_rows($lookup) ; $i++)
      {
        if (pg_fetch_result($lookup, $i, "configoptionlookupid") == pg_fetch_result($result, 0, "configoptionlookupid"))
        {
          $foundexisting = true;
        }
      }
    }

    /* Multiple testruns or illegal options lead to a blank selection in the combo box
       with the default lookup as the value */
    if ($multiple || !$foundexisting)
    {
      echo "<option value=\"".pg_fetch_result($defaultresult, 0, "configoptionlookupid")."\">".
           "</option>\n";
    }
    for ($i = 0 ; $i < pg_num_rows($lookup) ; $i++)
    {
      $coli = pg_fetch_result($lookup, $i, "configoptionlookupid");
      echo "<option value=\"".$coli."\"";
      if (!$multiple && !pg_field_is_null($result, 0, "configoptionlookupid"))
      {
        if ($coli == pg_fetch_result($result, 0, "configoptionlookupid"))
        {
          echo " selected";
        }
      }
      else if (!$multiple && pg_fetch_result($lookup, $i, "defaultlookup") == 't')
      {
        echo " selected";
      }
      echo ">".pg_fetch_result($lookup, $i, "lookupname")."</option>\n";
    }
    echo "</select>\n";
  }
  else
  {
    if (pg_num_rows($result) != 1 || 
        (pg_fetch_result($result, 0, "testruncount") !=0 && pg_fetch_result($result, 0, "testruncount")!= $testruncount))
    {

      echo "<i>&lt;Various&gt;</i><br />\n";
      $totalnondefault = 0;
      $defaultvalue = pg_fetch_result($result, 0, "defaultvalue");
      for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
      {
        $count = pg_fetch_result($result, $i, "testruncount");
        $value = pg_fetch_result($result, $i, "configvalue");

        if ($value == $defaultvalue)
        {
          continue;
        }

        $totalnondefault += $count;
        echo "(".$count.") ";
        if (strlen($value) == 0)
        {
          $value = "<i>[empty]</i>";
        }
        else
        {
          $value = htmlentities($value);
        }
        echo $value."<br />\n";
      }
      if ($testruncount - $totalnondefault != 0)
      {
        echo "(".($testruncount - $totalnondefault).") ";
        $value = $defaultvalue;
        if (strlen($value) == 0)
        {
          $value = "<i>[empty]</i>";
        }
        else
        {
          $value = htmlentities($value);
        }
        echo $value."<br />\n";
      }
      echo "<br />\n";
      $default = "";
      $realdefault = pg_fetch_result($result, 0, "defaultvalue");
    }
    else
    {
      $default = pg_fetch_result($result, 0, "defaultvalue");
      if (!pg_field_is_null($result, 0, "configvalue"))
      {
        $default = pg_fetch_result($result, 0, "configvalue");
      }
    }
    $type = pg_fetch_result($result, 0, "configoptiontypename");
    switch ($type)
    {
    case "string":
      {
        echo "<input class=\"textbox\" type=\"text\" name=\"stringvalue\" value=\"".$default."\" oninput=\"configsettingchanged();\" onblur=\"checkandsaveconfig(this.value, ".$_REQUEST['configoptionid'].");\">";
      }
      break;
    case "integer":
      {
        echo "<input class=\"textbox\" type=\"text\" name=\"integervalue\" value=\"".$default."\" oninput=\"configsettingchanged();\" onblur=\"checkandsaveconfig(this.value, ".$_REQUEST['configoptionid'].");\">";
      }
      break;
    case "boolean":
      {
        echo "<select style=\"width:100%\" name=\"booleanvalue\" onchange=\"configsettingchanged();checkandsaveconfig(this.value, ".$_REQUEST['configoptionid'].");\">\n";
        if ($default == "")
        {
          echo "<option value=\"".$realdefault."\" selected></option>\n";
        }
        echo "<option value=\"true\"";
        if ($default == "true")
        {
          echo " selected";
        }
        echo ">True</option>\n".
             "<option value=\"false\"";
        if ($default == "false")
        {
          echo " selected";
        }
        echo ">False</option>\n".
             "</select>\n";
      }
      break;
    }
  }
}
else if ($_REQUEST['what'] == "saveconfig")
{
  $sql = "SELECT ovt_configoptiontype.configoptiontypename,\n".
         "       ovt_configoption.islookup\n".
         "FROM ovt_configoption INNER JOIN ovt_configoptiontype USING (configoptiontypeid)\n".
         "WHERE ovt_configoption.configoptionid='".$_REQUEST['configoptionid']."'";
  $result = pg_query($ovtDB, $sql);

  if (pg_fetch_result($result, 0, "islookup") == "t")
  {
    $sql = "SELECT ovt_configoptionlookup.lookupname\n".
           "FROM ovt_configoptionlookup\n".
           "WHERE ovt_configoptionlookup.configoptionlookupid='".$_REQUEST['value']."'";
    $result = pg_query($ovtDB, $sql);
    $_REQUEST['value'] = pg_fetch_result($result, 0, "lookupname");
  }
  else
  {
    switch (pg_fetch_result($result, 0, "configoptiontypename"))
    {
    case "string":
      // Nothing
      break;
    case "integer":
      $_REQUEST['value'] = trim($_REQUEST['value']);
      $intvalue = (int)$_REQUEST['value'];
      if ((string)$intvalue != $_REQUEST['value'])
      {
        echo "Invalid setting. Must be an integer";
        exit(0);
      }
      break;
    case "boolean":
      $_REQUEST['value'] = trim($_REQUEST['value']);
      if ($_REQUEST['value']!="true" && $_REQUEST['value']!="false")
      {
        echo "Invalid setting. Must be a boolean (True, False)";
        exit(0);
      }
      break;
    default:
      echo "Unknown config option type";
      exit(0);
      break;
    }
  }
  $edittype = "testrun";

  if (isset($_REQUEST['testrunid']))
  {
    $keyid = $_REQUEST['testrunid'];
  }
  else
  {
    $edittype = "group";
    $keyid = $_REQUEST['testrungroupid'];
  }
  $sql = "SELECT ovt_modify_config('".$edittype."', '".$keyid."', '".$_REQUEST['configoptionid']. "', '".$_REQUEST['value']."')";
  $result = pg_query($ovtDB, $sql);
  if ($result === false)
  {
    echo pg_last_error($ovtDB);
  }
  else
  {
    if (pg_fetch_result($result, 0, 0) == 'f')
    {
      echo "Unable to alter config";
    }
  }
}
else if ($_REQUEST['what'] == "savedescription")
{
  if (strlen($_REQUEST['value']) == 0)
  {
    echo " Missing description ";
  }
  else
  {
    $sql = "SELECT testrunid\n".
           "FROM ovt_testrun\n".
           "WHERE description='".$_REQUEST['value']."'\n".
           "AND testrunid != '".$_REQUEST['testrunid']."'\n".
           "AND testrungroupid=(SELECT testrungroupid\n".
           "                    FROM ovt_testrun\n".
           "                    WHERE testrunid='".$_REQUEST['testrunid']."')";
    $dupresult = pg_query($ovtDB, $sql);

    if (pg_num_rows($dupresult) == 0)
    {
      $sql = "UPDATE ovt_testrun\n".
             "SET description='".$_REQUEST['value']."'\n".
             "WHERE testrunid='".$_REQUEST['testrunid']."'";
      pg_query($ovtDB, $sql);
    }
    else
    {
      echo " Duplicate description in testrun group ";
    }
  }
}
else if ($_REQUEST['what'] == "savepriority")
{
  if ((string)(int)$_REQUEST['value'] != $_REQUEST['value'])
  {
    echo " Priority must be a number ";
  }
  else
  {
    $sql = "UPDATE ovt_testrun\n".
           "SET priority='".$_REQUEST['value']."'\n";
    if (isset($_REQUEST['testrunid']))
    {
      $sql .= "WHERE testrunid='".$_REQUEST['testrunid']."'";
    }
    else
    {
      $sql .= "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'";
    }
    pg_query($ovtDB, $sql);
  }
}
else if ($_REQUEST['what'] == "saveconcurrency")
{
  if ((string)(int)$_REQUEST['value'] != $_REQUEST['value'])
  {
    echo " Concurrency must be a number ";
  }
  else
  {
    $sql = "UPDATE ovt_testrun\n".
           "SET concurrency='".$_REQUEST['value']."'\n";
    if (isset($_REQUEST['testrunid']))
    {
      $sql .= "WHERE testrunid='".$_REQUEST['testrunid']."'";
    }
    else
    {
      $sql .= "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'";
    }
    pg_query($ovtDB, $sql);
  }

}
else if ($_REQUEST['what'] == "savestart")
{
  if (strlen($_REQUEST['value']) == 0)
  {
    echo " Please specify a start date";
  }
  else
  {
    $sql = "UPDATE ovt_testrun\n".
           "SET startafter='".$_REQUEST['value']."'\n";
    if (isset($_REQUEST['testrunid']))
    {
      $sql .= "WHERE testrunid='".$_REQUEST['testrunid']."'";
    }
    else
    {
      $sql .= "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'";
    }
    $result = @pg_query($ovtDB, $sql);
    if ($result === false)
    {
      echo "Bad start date format";
    }
  }
}
else if ($_REQUEST['what'] == "saveautoarchive")
{
  if (strlen($_REQUEST['value']) == 0)
  {
    echo " Please specify an archiving mode";
  }
  else
  {
    $sql = "UPDATE ovt_testrun\n".
           "SET autoarchive='".$_REQUEST['value']."'\n";
    if (isset($_REQUEST['testrunid']))
    {
      $sql .= "WHERE testrunid='".$_REQUEST['testrunid']."'";
    }
    else
    {
      $sql .= "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'";
    }
    $result = @pg_query($ovtDB, $sql);
    if ($result === false)
    {
      echo "Bad archive mode";
    }
  }
}
else if ($_REQUEST['what'] == "saveusegridengine")
{
  if (strlen($_REQUEST['value']) == 0)
  {
    echo " Please specify whether to use grid engine";
  }
  else
  {
    $sql = "UPDATE ovt_testrun\n".
           "SET usegridengine='".$_REQUEST['value']."'\n";
    if (isset($_REQUEST['testrunid']))
    {
      $sql .= "WHERE testrunid='".$_REQUEST['testrunid']."'";
    }
    else
    {
      $sql .= "WHERE testrungroupid='".$_REQUEST['testrungroupid']."'";
    }
    $result = @pg_query($ovtDB, $sql);
    if ($result === false)
    {
      echo "Bad archive mode";
    }
  }
}
?>
