<?php
include_once('inc/includes.inc');
include_once('inc/xmlrpc.inc');
include_once('inc/jsonrpc.inc');
include_once('inc/json_extension_api.inc');

if (!isset($_REQUEST['what']))
{
    echo "BAD REQUEST";
      exit (0);
}
elseif ($_REQUEST['what'] == "show_group_string")
{
  $json = json_decode(stripslashes($_REQUEST['groupstring']));
  if (is_array($json))
  {
    if (count($json) != 0)
    {
      echo "Group testruns by:<br />\n";
    }
    for ($i = 0 ; $i < count($json) ; $i++)
    {
      echo "<span class=\"clickable\" id=\"groupterm${i}\" onclick=\"selectGroupTerm(${i});\">";
      if (!is_array($json[$i]))
      {
        echo "ERROR: Unknown element in JSON group string";
      }
      else
      {
        if ($i != 0)
        {
          echo "then ";
        }
        switch ($json[$i][0])
        {
        case 'Action':
          $sql = "SELECT ovt_action.actionname\n".
                 "FROM ovt_action\n".
                 "WHERE actionid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          echo "by version of '" . pg_fetch_result ($result, 0, "actionname")."'";
          break;
        case 'Config Setting':
          $sql = "SELECT ovt_configoption.configoptionname, ovt_configoption.islookup\n".
                 "FROM ovt_configoption\n".
                 "WHERE ovt_configoption.configoptionid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          echo "by value of '".pg_fetch_result ($result, 0, "configoptionname")."'";
          break;
        case 'Resource Attribute':
          $sql = "SELECT ovt_resourcetype.resourcetypename, ovt_attribute.attributename\n".
                 "FROM ovt_attribute INNER JOIN ovt_resourcetype USING (resourcetypeid)\n".
                 "WHERE ovt_attribute.attributeid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          $group = pg_fetch_result($result, 0, "resourcetypename");
          echo "by value of the '".$group."' attribute '".pg_fetch_result($result, 0, "attributename")."'";
          break;
        case 'Testrun Group':
          echo "by testrun group";
          break;
        case 'User':
          echo "by owner";
          break;
        case 'Simple Equivalence':
          echo "by simple equivalence";
          break;
        case 'Recursive Equivalence':
          echo "by recursive equivalence";
          break;
        case 'Producer Equivalence':
          echo "by producer equivalence";
          break;
        }
      }
      echo "</span><br />";
    } 
  }
  else
  {
    echo "ERROR: Invalid JSON group string";
  }

}
elseif ($_REQUEST['what'] == "show_filter_string")
{
  $json = json_decode(stripslashes($_REQUEST['filterstring']));
  if (is_array($json))
  {
    echo "Find testruns that:<br />\n";
    for ($i = 0 ; $i < count($json) ; $i++)
    {
      echo "<span class=\"clickable\" id=\"searchterm${i}\" onclick=\"selectFilterTerm(${i});\">";
      if (!is_array($json[$i]))
      {
        switch ($json[$i])
        {
        case 'and':
          echo " AND<br />\n";
          break;
        case 'or':
          echo " OR<br />\n";
          break;
        case 'not':
          echo "NOT ";
          break;
        case '(':
        case ')':
          echo $json[$i];
          break;
        default:
          echo $json[$i]."<br />\n";
          break;
        }
      }
      else
      {
        switch ($json[$i][0])
        {
        case 'Action':
          $sql = "SELECT ovt_action.actionname\n".
                 "FROM ovt_action\n".
                 "WHERE actionid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          echo "contain '" . pg_fetch_result ($result, 0, "actionname")."'";
          break;
        case 'Version of Action':
          $sql = "SELECT ovt_action.actionname, ovt_versionedaction.versionname\n".
                 "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
                 "WHERE versionedactionid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          echo "contain version '".pg_fetch_result ($result, 0, "versionname")."' of '" . pg_fetch_result ($result, 0, "actionname")."'";
          break;
        case 'Testsuite Config Setting':
        case 'Other Config Setting':
          $sql = "SELECT ovt_configoption.configoptionname, ovt_configoption.islookup\n".
                 "FROM ovt_configoption\n".
                 "WHERE ovt_configoption.configoptionid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          if (pg_fetch_result($result, 0, "islookup") == "t")
          {
            $sql = "SELECT ovt_configoptionlookup.lookupname\n".
                   "FROM ovt_configoptionlookup\n".
                   "WHERE configoptionlookupid='".pg_escape_string($json[$i][2])."'";
            $result2 = pg_query($ovtDB, $sql);
            $json[$i][2] = pg_fetch_result ($result2, 0, "lookupname");
          }
          echo "have '".pg_fetch_result ($result, 0, "configoptionname")."' set to '".$json[$i][2]."'";
          break;
        case 'Resource Attribute':
        case 'Requested Resource Attribute':
          $sql = "SELECT ovt_resourcetype.resourcetypename, ovt_attribute.attributename, ovt_attributevalue.value\n".
                 "FROM ovt_attributevalue INNER JOIN ovt_attribute USING (attributeid)\n".
                 "     INNER JOIN ovt_resourcetype USING (resourcetypeid)\n".
                 "WHERE ovt_attributevalue.attributevalueid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          $group = pg_fetch_result($result, 0, "resourcetypename");
          $value = pg_fetch_result($result, 0, "value");
          $extra1 = '';
          $extra2 = '';
          if (in_array(strtolower($group{0}), Array('a','e','i','o','u')))
          {
            $extra1 = 'n';
          }
          if (in_array(strtolower($value{0}), Array('a','e','i','o','u')))
          {
            $extra2 = 'n';
          }
          if ($json[$i][0] == 'Requested Resource Attribute')
          {
            echo "specifically ";
          }
          echo "use a${extra1} '".$group."' with a${extra2} '".$value."' '".pg_fetch_result($result, 0, "attributename")."'";
          break;
        case 'Started After':
          echo "started after '".$json[$i][1]."'";
          break;
        case 'Started Before':
          echo "started before '".$json[$i][1]."'";
          break;
        case 'Testrun Group':
          $sql = "SELECT ovt_testrungroup.testrungroupname\n".
                 "FROM ovt_testrungroup\n".
                 "WHERE ovt_testrungroup.testrungroupid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          echo "are in the '".pg_fetch_result($result, 0, "testrungroupname")."' group";
          break;
        case 'User':
          $sql = "SELECT ovt_user.fname || ' ' || ovt_user.sname AS name\n".
                 "FROM ovt_user\n".
                 "WHERE ovt_user.userid='".pg_escape_string($json[$i][1])."'"; 
          $result = pg_query($ovtDB, $sql);
          echo "are owned by '".pg_fetch_result($result, 0, "name")."'";
          break;
        case 'Testrun':
          $sql = "SELECT ovt_testrun.description\n".
                 "FROM ovt_testrun\n".
                 "WHERE testrunid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          echo "are the '".pg_fetch_result($result, 0, "description")."' testrun";
          break;
        }
      }
      echo "</span>";
    }
  }
  else
  {
    echo "ERROR: Invalid JSON filter string";
  }
}
elseif ($_REQUEST['what'] == "search1")
{
  switch ($_REQUEST['searchfield'])
  {
  case 'Action':
  case 'Version of Action':
    $sql = "SELECT *\n".
           "FROM ovt_actioncategory\n".
           "ORDER BY ovt_actioncategory.actioncategoryname\n";
    $result = pg_query($ovtDB, $sql);
    echo "<select name=\"search1select\" onchange=\"updateSearch2(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "actioncategoryid")."\">".
           pg_fetch_result($result, $i, "actioncategoryname")."</option>\n";
    }
    echo "</select>\n";
    break;
  case 'Testsuite Config Setting':
  case 'Other Config Setting':
    $sql = "SELECT DISTINCT ovt_configoptiongroup.configoptiongroupid,\n".
           "       ovt_configoptiongroup.configoptiongroupname\n".
           "FROM ovt_configoptiongroup";
    if ($_REQUEST['searchfield'] == 'Testsuite Config Setting')
    {
      /* Restrict the options to those applicable to the testsuite */
      $sql .=                        " INNER JOIN ovt_configoption USING (configoptiongroupid)\n".
           "     INNER JOIN ovt_versionedactionconfigoption USING (configoptionid)\n".
           "     INNER JOIN ovt_versionedaction USING (versionedactionid)\n".
           "     INNER JOIN ovt_action USING (actionid)\n".
           "WHERE ovt_action.testsuiteid='".$_REQUEST['testsuiteid']."'";
//           "AND NOT ovt_configoptiongroup.automatic";
    }
    else
    {
//      $sql .= "\n".
//           "WHERE NOT ovt_configoptiongroup.automatic";
    }
    $sql .="\n".
           "ORDER BY ovt_configoptiongroup.configoptiongroupname\n";
    $result = pg_query($ovtDB, $sql);

    /* Output the select box for config option groups */
    echo "<select name=\"search1select\" onchange=\"updateSearch2(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "configoptiongroupid")."\">".
           pg_fetch_result($result, $i, "configoptiongroupname")."</option>\n";
    }
    echo "</select>\n";
    break;
  case 'Resource Attribute':
  case 'Requested Resource Attribute':
    $sql = "SELECT *\n".
           "FROM ovt_resourcetype\n".
           "ORDER BY ovt_resourcetype.resourcetypename";
    $result = pg_query($ovtDB, $sql);

    /* Output the select box for resource types */
    echo "<select name=\"search1select\" onchange=\"updateSearch2(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "resourcetypeid")."\">".
           pg_fetch_result($result, $i, "resourcetypename")."</option>\n";
    }
    echo "</select>\n";
    break;
  case 'Started After':
  case 'Started Before':
    echo "<input type=\"text\" value=\"".strftime("%Y/%m/%d %H:%I")."\" name=\"datevalue\" onkeyup=\"updateSearch2(this.value);\">\n";
    break;
  case 'Testrun Group':
  case 'User':
  case 'Testrun':
    $sql = "SELECT userid, sname || ', ' || fname AS name\n".
           "FROM ovt_user\n".
           "ORDER BY sname, fname";
    $result = pg_query($ovtDB, $sql);

    /* Output the select box for users */
    echo "<select name=\"search1select\" onchange=\"updateSearch2(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "userid")."\">".
           pg_fetch_result($result, $i, "name")."</option>\n";
    }
    echo "</select>\n";
    break;
  }
}
elseif ($_REQUEST['what'] == "search2")
{
  switch ($_REQUEST['searchfield'])
  {
  case 'Action':
  case 'Version of Action':
    $sql = "SELECT ovt_action.actionid, ovt_action.actionname\n".
           "FROM ovt_action\n".
           "WHERE ovt_action.actioncategoryid='".$_REQUEST['search1value']."'\n".
           "ORDER BY ovt_action.actionname";

    $result = pg_query($ovtDB, $sql);

    /* Output the select box for actions */
    echo "<select name=\"search2select\" onchange=\"updateSearch3(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "actionid")."\">".
           pg_fetch_result($result, $i, "actionname")."</option>\n";
    }
    echo "</select>\n";
    break;
  case 'Testsuite Config Setting':
  case 'Other Config Setting':
    $sql = "SELECT DISTINCT ovt_configoption.configoptionid,\n".
           "       ovt_configoption.configoptionname\n".
           "FROM ovt_configoption";
    if ($_REQUEST['searchfield'] == 'Testsuite Config Setting')
    {
      /* Restrict the options to those applicable to the testsuite */
      $sql .=                    " INNER JOIN ovt_versionedactionconfigoption USING (configoptionid)\n".
           "     INNER JOIN ovt_versionedaction USING (versionedactionid)\n".
           "     INNER JOIN ovt_action USING (actionid)\n".
           "WHERE ovt_action.testsuiteid='".$_REQUEST['testsuiteid']."'".
           "AND ovt_configoption.configoptiongroupid='".$_REQUEST['search1value']."'";
    }
    else
    {
      $sql .= "\n".
           "WHERE ovt_configoption.configoptiongroupid='".$_REQUEST['search1value']."'";
    }
    $sql .="\n".
           "ORDER BY ovt_configoption.configoptionname\n";
    $result = pg_query($ovtDB, $sql);

    /* Output the select box for config options */
    echo "<select name=\"search2select\" onchange=\"updateSearch3(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "configoptionid")."\">".
           pg_fetch_result($result, $i, "configoptionname")."</option>\n";
    }
    echo "</select>\n";
    break;
  case 'Resource Attribute':
  case 'Requested Resource Attribute':
    $sql = "SELECT ovt_attribute.attributename, ovt_attribute.attributeid\n".
           "FROM ovt_attribute\n".
           "WHERE ovt_attribute.resourcetypeid='".$_REQUEST['search1value']."'\n".
           "AND ovt_attribute.lookup\n".
           "ORDER BY ovt_attribute.attributename";
    $result = pg_query($ovtDB, $sql);

    /* Output the select box for resource attributes */
    echo "<select name=\"search2select\" onchange=\"updateSearch3(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "attributeid")."\">".
           pg_fetch_result($result, $i, "attributename")."</option>\n";
    }
    echo "</select>\n";
    break;
  case 'Testrun Group':
  case 'Testrun':
    $sql = "SELECT ovt_testrungroup.testrungroupid, ovt_testrungroup.testrungroupname\n".
           "FROM ovt_testrungroup\n".
           "WHERE ovt_testrungroup.userid='".$_REQUEST['search1value']."'\n".
           "ORDER BY ovt_testrungroup.testrungroupname";
    $result = pg_query($ovtDB, $sql);

    /* Output the select box for testrungroups */
    echo "<select name=\"search2select\" onchange=\"updateSearch3(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "testrungroupid")."\">".
           pg_fetch_result($result, $i, "testrungroupname")."</option>\n";
    }
    echo "</select>\n";
    break;
  }
}
elseif ($_REQUEST['what'] == "search3")
{
  switch ($_REQUEST['searchfield'])
  {
  case 'Version of Action':
    $sql = "SELECT ovt_versionedaction.versionedactionid, ovt_versionedaction.versionname\n".
           "FROM ovt_versionedaction\n".
           "WHERE ovt_versionedaction.actionid='".$_REQUEST['search2value']."'\n".
           "ORDER BY ovt_versionedaction.versionname";

    $result = pg_query($ovtDB, $sql);

    /* Output the select box for versioned actions */
    echo "<select name=\"search3select\" onchange=\"updateSearch4(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "versionedactionid")."\">".
           pg_fetch_result($result, $i, "versionname")."</option>\n";
    }
    echo "</select>\n";
    break;
  case 'Testsuite Config Setting':
  case 'Other Config Setting':
    $sql = "SELECT islookup\n".
           "FROM ovt_configoption\n".
           "WHERE configoptionid='".$_REQUEST['search2value']."'";
    $result = pg_query($ovtDB, $sql);
    if (pg_fetch_result($result, 0, "islookup") == "t")
    {
      $sql = "SELECT ovt_configoptionlookup.configoptionlookupid, ovt_configoptionlookup.lookupname\n".
             "FROM ovt_configoptionlookup\n".
             "WHERE ovt_configoptionlookup.configoptionid='".$_REQUEST['search2value']."'\n".
             "ORDER BY ovt_configoptionlookup.lookupname";
      $result = pg_query($ovtDB, $sql);
  
      /* Output the select box for config values */
      echo "<select name=\"search3select\" onchange=\"updateSearch4(this.value);\">\n".
           "<option selected></option>\n";
      for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
      {
        echo "<option value=\"".pg_fetch_result($result, $i, "configoptionlookupid")."\">".
             pg_fetch_result($result, $i, "lookupname")."</option>\n";
      }
      echo "</select>\n";

    }
    else
    {
      echo "<input type=\"text\" name=\"search3text\" onkeyup=\"updateSearch4(this.value);\">\n";
    }
    break;
  case 'Resource Attribute':
  case 'Requested Resource Attribute':
    $sql = "SELECT ovt_attributevalue.attributevalueid, ovt_attributevalue.value\n".
           "FROM ovt_attributevalue\n".
           "WHERE ovt_attributevalue.attributeid='".$_REQUEST['search2value']."'\n".
           "ORDER BY ovt_attributevalue.value";
    $result = pg_query($ovtDB, $sql);

    /* Output the select box for attribute values */
    echo "<select name=\"search3select\" onchange=\"updateSearch4(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "attributevalueid")."\">".
           pg_fetch_result($result, $i, "value")."</option>\n";
    }
    echo "</select>\n";
    break;
  case 'Testrun':
    $sql = "SELECT ovt_testrun.description, ovt_testrun.testrunid\n".
           "FROM ovt_testrun\n".
           "WHERE ovt_testrun.testrungroupid='".$_REQUEST['search2value']."'\n".
           "ORDER BY description";
    $result = pg_query($ovtDB, $sql);

    /* Output the select box for testruns */
    echo "<select name=\"search3select\" onchange=\"updateSearch4(this.value);\">\n".
         "<option selected></option>\n";
    for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
    {
	$res = pg_fetch_result($result, $i, "description");
	if (strlen($res) > 100)
	{
	   $res = substr($res,0,100) . "...";
	}
      echo "<option value=\"".pg_fetch_result($result, $i, "testrunid")."\">".
           $res."</option>\n";
    }
    echo "</select>\n";
    break;
  }
}
elseif ($_REQUEST['what'] == "get_filter_list")
{
  $testsuiteid = $_REQUEST['testsuiteid'];

  if ($_REQUEST['searchfield'] == 'Other Config Setting')
  {
    $sql = "SELECT DISTINCT ovt_configsetting.configvalue, ovt_configoptionlookup.configoptionlookupid, ovt_configoptionlookup.lookupname\n".
           "FROM ovt_configsetting LEFT OUTER JOIN ovt_configoptionlookup USING (configoptionlookupid)\n".
           "WHERE ovt_configsetting.configoptionid='".$_REQUEST['search2']."'\n".
           "AND EXISTS (SELECT ovt_action.testsuiteid\n".
           "            FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
           "                 INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
           "            WHERE ovt_testrunaction.testrunid=ovt_configsetting.testrunid\n".
           "            AND ovt_action.testsuiteid='".$testsuiteid."')\n".
           "ORDER BY configvalue, lookupname";

    $result = pg_query($ovtDB, $sql);
    echo "<select id=\"filterlist\" size=5 name=\"filterlist\" onchange=\"selectFilter(this.value)\">\n";
    for ($i =0 ; $i < pg_num_rows($result) ; $i++)
    {
      if (!pg_field_is_null($result, $i, "configvalue"))
      {
        echo "<option value=\"".pg_fetch_result($result, $i, "configvalue")."\">".pg_fetch_result($result, $i, "configvalue")."</option>\n";
      }
      else
      {
        echo "<option value=\"".pg_fetch_result($result, $i, "configoptionlookupid")."\">".pg_fetch_result($result, $i, "lookupname")."</option>\n";
      }
    }
    echo "</select>";
  }
  else
  {
    switch ($_REQUEST['searchfield'])
    {
    case 'Requested Resource Attribute':
      $sql = "SELECT DISTINCT ovt_attributevalue.attributevalueid AS id, ovt_attributevalue.value AS name\n".
             "FROM ovt_attributevalue INNER JOIN ovt_testrunattributevalue USING (attributevalueid)\n".
             "WHERE ovt_attributevalue.attributeid='".$_REQUEST['search2']."'\n". 
             "AND EXISTS (SELECT ovt_action.testsuiteid\n".
             "            FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
             "                 INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
             "            WHERE ovt_testrunaction.testrunid=ovt_testrunattributevalue.testrunid\n".
             "            AND ovt_action.testsuiteid='".$testsuiteid."')\n".
             "ORDER BY name";
      break;
    case 'Version of Action':
      $sql = "SELECT DISTINCT ovt_versionedaction.versionedactionid AS id, ovt_versionedaction.versionname AS name\n".
             "FROM ovt_versionedaction INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
             "WHERE ovt_versionedaction.actionid='".$_REQUEST['search2']."'\n". 
             "AND EXISTS (SELECT ovt_action.testsuiteid\n".
             "            FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
             "                 INNER JOIN ovt_testrunaction AS subtestrunaction USING (versionedactionid)\n".
             "            WHERE subtestrunaction.testrunid=ovt_testrunaction.testrunid\n".
             "            AND ovt_action.testsuiteid='".$testsuiteid."')\n".
             "ORDER BY name";
      break;
    case 'Testrun Group':
      $sql = "SELECT DISTINCT ovt_testrungroup.testrungroupid AS id, ovt_testrungroup.testrungroupname AS name\n".
             "FROM ovt_testrungroup INNER JOIN ovt_testrun USING (testrungroupid)\n".
             "WHERE\n". 
             "EXISTS (SELECT ovt_action.testsuiteid\n".
             "        FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
             "             INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
             "        WHERE ovt_testrunaction.testrunid=ovt_testrun.testrunid\n".
             "        AND ovt_action.testsuiteid='".$testsuiteid."')\n".
             "ORDER BY name";
      break;
    case 'User':
      $sql = "SELECT DISTINCT ovt_user.userid AS id, ovt_user.fname || ' ' || ovt_user.sname AS name\n".
             "FROM ovt_user INNER JOIN ovt_testrun USING (userid)\n".
             "WHERE\n". 
             "EXISTS (SELECT ovt_action.testsuiteid\n".
             "        FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
             "             INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
             "        WHERE ovt_testrunaction.testrunid=ovt_testrun.testrunid\n".
             "        AND ovt_action.testsuiteid='".$testsuiteid."')\n".
             "ORDER BY name";
      break;
    case 'Simple Equivalence':
    case 'Recursive Equivalence':
    case 'Producer Equivalence':
      echo "Unable to filter currently";
      exit(0);
      break;
    }
    $result = pg_query($ovtDB, $sql);
    echo "<select id=\"filterlist\" size=5 name=\"filterlist\" onchange=\"selectFilter(this.value)\">\n";
    for ($i =0 ; $i < pg_num_rows($result) ; $i++)
    {
      echo "<option value=\"".pg_fetch_result($result, $i, "id")."\">".pg_fetch_result($result, $i, "name")."</option>\n";
    }
    echo "</select>";

  }
  echo "<br />\n".
       "<span id=\"add_filter_button_simple\" class=\"clickable\" style=\"display:none\" onclick=\"addSearchTerm(false);\">Add to filter</span>\n";
}
?>
