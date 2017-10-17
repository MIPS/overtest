<?php

function search_options($ovtDB, $testsuiteid)
{
  /* Using the testsuiteid find all relevant criteria to group by.
   * This is an iterative process starting from the testsuite in all testruns and
   * following dependency chains to the roots of the tree */
  $sql = "SELECT *\n".
         "FROM ";
  
  /* 1) Do the config options */
  $sql .= "((SELECT DISTINCT 3 AS type,ovt_configoptiongroup.configoptiongroupname || '::' || ovt_configoption.configoptionname AS criteria,\n".
         "                 'co'||CAST(ovt_configoption.configoptionid AS character varying) AS identifier\n".
         " FROM ovt_configoption INNER JOIN ovt_configsetting USING (configoptionid)\n".
         "      INNER JOIN ovt_configoptiongroup USING (configoptiongroupid)\n".
         " WHERE NOT ovt_configoptiongroup.automatic\n".
         " AND EXISTS (SELECT ovt_action.testsuiteid\n".
         "             FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "                  INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "             WHERE ovt_testrunaction.testrunid=ovt_configsetting.testrunid\n".
         "             AND ovt_action.testsuiteid='".$testsuiteid."')\n".
         " ORDER BY criteria)\n";
  /* 2) Do the resource attributes */
  $sql .="UNION\n";
  $sql .="(SELECT DISTINCT 2 AS type,ovt_resourcetype.resourcetypename || '::' || ovt_attribute.attributename AS criteria,\n".
         "                 'ra'||CAST(ovt_attribute.attributeid AS character varying) AS identifier\n".
         " FROM ovt_resourcetype INNER JOIN ovt_attribute USING (resourcetypeid)\n".
         "      INNER JOIN ovt_attributevalue USING (attributeid)\n".
         "      INNER JOIN ovt_testrunattributevalue USING (attributevalueid)\n".
         " WHERE\n".
         " EXISTS (SELECT ovt_action.testsuiteid\n".
         "         FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "              INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         "         WHERE ovt_testrunaction.testrunid=ovt_testrunattributevalue.testrunid\n".
         "         AND ovt_action.testsuiteid='".$testsuiteid."')\n".
         " AND EXISTS (SELECT ovt_attributevalue.attributeid\n".
         "             FROM ovt_versionedactionattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid)\n".
         "                  INNER JOIN ovt_attribute AS subattribute USING (attributeid)\n".
         "                  INNER JOIN ovt_versionedaction USING (versionedactionid)\n".
         "                  INNER JOIN ovt_action USING (actionid)\n".
         "             WHERE subattribute.resourcetypeid=ovt_attribute.resourcetypeid\n".
         "             AND ovt_action.testsuiteid='".$testsuiteid."')\n".
         " ORDER BY criteria)\n";
  /* 3) Do all actions from all testruns */
  $sql .="UNION\n";
  $sql .="(SELECT DISTINCT 1 AS type,ovt_actioncategory.actioncategoryname || '::' || ovt_action.actionname AS criteria,\n".
         "                 'ac'||CAST(ovt_action.actionid AS character varying) AS identifier\n".
         " FROM ovt_actioncategory INNER JOIN ovt_action USING (actioncategoryid)\n".
         "      INNER JOIN ovt_versionedaction USING (actionid)\n".
         "      INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
         " WHERE EXISTS (SELECT ovt_action.testsuiteid\n".
         "               FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
         "                    INNER JOIN ovt_testrunaction AS subtestrunaction USING (versionedactionid)\n".
         "               WHERE subtestrunaction.testrunid=ovt_testrunaction.testrunid\n".
         "               AND ovt_action.testsuiteid='".$testsuiteid."')\n".
         " ORDER BY criteria)) AS info\n".
         "ORDER BY type,criteria";
  $result = pg_query($ovtDB, $sql);
  
  echo "<form action=\"#\" style=\"margin:0; padding:0\">\n".
       "<span id=\"toggle_view\" class=\"clickable\" onclick=\"toggleView(false);\">Advanced view</span><br />\n";
  
  echo "<div id=\"simple_search\">\n".
       "<table>\n".
       "<tr><th>Grouping</th><th>Filter</th></tr>\n".
       "<tr style=\"vertical-align:top\"><td>\n";
  echo "<select name=\"groupinglist\" id=\"groupinglist\" onchange=\"selectGrouping(this.value)\">\n";
  for ($i = 0; $i < pg_num_rows($result); $i++)
  {
    echo "<option value=\"".pg_fetch_result($result, $i, "identifier")."\">".pg_fetch_result($result, $i, "criteria")."</option>\n";
  }
  echo "<option value=\"gr\">Testrun Group</option>\n";
  echo "<option value=\"us\">Owner</option>\n";
  echo "<option value=\"se\">Simple Equivalence</option>\n";
  echo "<option value=\"re\">Recursive Equivalence</option>\n";
  echo "<option value=\"pe\">Producer Equivalence</option>\n";
  echo "</select><br />".
       "<span id=\"add_group_button_simple\" class=\"clickable\" style=\"display:none\" onclick=\"addGroupTerm(true);\">Add grouping</span>\n";
  echo "</td><td id=\"filter_list\">\n";
  echo "</td></tr>\n".
       "</table>\n".
       "<br />\n".
       "</div>\n";
  echo "<div id=\"advanced_search\" style=\"display:none\">\n".
       "<table>\n".
       "<tr><th>Field</th><th id=\"search1header\"></th><th id=\"search2header\"></th><th id=\"search3header\"></th><th></th></tr>\n";
  echo "<tr>\n";
  
  echo "<td>\n".
       "<select id=\"searchfield\" name=\"searchfield\" onchange=\"updateSearch1(this.value);\">\n".
       "<option selected></option>\n".
       "<option value=\"Action\">Action</option>\n".
       "<option value=\"Version of Action\">Version of Action</option>\n".
       "<option value=\"Testsuite Config Setting\">Testsuite Config Setting</option>\n".
       "<option value=\"Other Config Setting\">Other Config Setting</option>\n".
       "<option value=\"Resource Attribute\">Resource Attribute</option>\n".
       "<option value=\"Requested Resource Attribute\">Requested Resource Attribute</option>\n".
       "<option value=\"Started After\">Started After</option>\n".
       "<option value=\"Started Before\">Started Before</option>\n".
       "<option value=\"Testrun Group\">Testrun Group</option>\n".
       "<option value=\"User\">User</option>\n".
       "<option value=\"Testrun\">Testrun</option>\n".
       "</select>\n".
       "</td>\n";
  
  echo "<td id=\"search1\"></td><td id=\"search2\"></td><td id=\"search3\"></td>\n".
       "<td>\n".
       "<span id=\"add_filter_button\" class=\"clickable\" style=\"display:none\" onclick=\"addSearchTerm(false);\">Add to filter</span>\n".
       "<span id=\"add_group_button\" class=\"clickable\"style=\"display:none\" onclick=\"addGroupTerm(true);\">Add grouping</span>\n".
       "</td>\n";
  
  echo "</tr>\n";
  echo "</table>\n".
       "</div>\n";
  echo "</form>\n";
  echo "<div id=\"filter_strings\"></div>\n";
  echo "<div id=\"group_strings\"></div>\n";
  echo "<br />\n";
} 

function search_buttons()
{
  echo "<table><tr>\n";
  echo "<td width=\"30px\" align=\"center\"><span class=\"clickable\" style=\"display:none\" id=\"add_left_bracket\" onclick=\"addSearchTermLeftBracket();\">+'(' </span></td>\n";
  echo "<td width=\"90px\" align=\"center\"><span class=\"clickable\" style=\"display:none\" id=\"move_up\" onclick=\"moveTermUp();\">Move Up </span></td>\n";
  echo "<td width=\"80px\" align=\"center\"><span class=\"clickable\" style=\"display:none\" id=\"remove_term\" onclick=\"removeTerm();\">Remove </span></td>\n";
  echo "<td width=\"90px\" align=\"center\"><span class=\"clickable\" style=\"display:none\" id=\"move_down\" onclick=\"moveTermDown();\">Move Down </span></td>\n";
  echo "<td width=\"30px\" align=\"center\"><span class=\"clickable\" style=\"display:none\" id=\"add_right_bracket\" onclick=\"addSearchTermRightBracket();\">+')' </span></td>\n";
  echo "<td width=\"40px\" align=\"center\"><span class=\"clickable\" style=\"display:none\" id=\"change_to_and\" onclick=\"toggleAndOr();\">AND </span>\n";
  echo "<span class=\"clickable\" style=\"display:none\" id=\"change_to_or\" onclick=\"toggleAndOr();\">OR </span>\n";
  echo "<span class=\"clickable\" style=\"display:none\" id=\"add_not\" onclick=\"addSearchTermNot();\">NOT </span></td>\n";
  echo "<td width=\"270px\" align=\"center\"><span style=\"display:none\" id=\"search_results_button\"><span id=\"search_results_button_text\" class=\"clickable\" onclick=\"searchClick();\">UPDATE</span> <a id=\"perma_link\" href=\"#\">perma-link</a></span> <a id=\"tab_link\" style=\"display:none\" href=\"#\">Download</a>\n";
  echo "<span style=\"display:none;color:red\" id=\"bracket_match_error\">Bracket mis-match</span>\n";
  echo "<span style=\"display:none;color:red\" id=\"filter_empty_error\">Filter is empty</span></td>\n";
  echo "</tr></table>\n";
}

/* Helper function to merge the current mergeable elements (this does not nest
 * only currently unmerged terms can be merged). All but the first of the
 * merged terms are chopped from the filter and the number of elements removed
 * is returned to the caller.
 * It is safe to call this function with one element in the mergearray. This
 * will change its value to an array of length one but have no other effects. */
function merge_elements(&$search_json, $firstorelementindex, $mergearray)
{
  $mergefield = 1;
  if ($search_json[$firstorelementindex][0] == 'Testsuite Config Setting'
      || $search_json[$firstorelementindex][0] == 'Other Config Setting')
  {
    $mergefield = 2;
  }

  $search_json[$firstorelementindex][$mergefield] = array($search_json[$firstorelementindex][$mergefield]);
  for ($j = 1 ; $j < count($mergearray) ; $j++)
  {
    $search_json[$firstorelementindex][$mergefield][] = $search_json[$mergearray[$j]][$mergefield];
  }

  if (count($mergearray) > 1)
  {
    /* Need to chop a bit out of the array
       This is all elements
       from firstorelementindex + 1 inclusive
       to $mergearray[count($mergearray)-1] inclusive */
    $removecount = $mergearray[count($mergearray)-1] - $firstorelementindex;
    array_splice($search_json, $firstorelementindex + 1, $removecount);
    return $removecount;
  }
  return 0;
}

/*
 * The theory with this function is to optimise search terms that are boolean OR'd
 * together and have compatible types. This changes multiple EXISTS clauses OR'd
 * together in to one EXISTS clause with an OR in the SELECT statment. The
 * performance gain is significant and directly proportional to number of terms.
 * No attempt is made to simplify bracketed terms to detect nested OR constructs.
 * It is assumed that the user will not do such pointless things! */
function merge_or_elements(&$search_json)
{
  $firstorelementindex = -1;
  $canstartor = true;
  $mergearray = array();
  for ($i = 0 ; $i < count($search_json) ; $i++)
  {
    if (!is_array($search_json[$i]))
    {
      switch ($search_json[$i])
      {
      case 'and':
        if ($firstorelementindex != -1)
        {
          /* Remove the last element from the mergearray as it is part of the and clause */
          array_pop($mergearray);
        }
      case 'not':
        if ($firstorelementindex != -1)
        {
          /* merge the mergearray */
          $i -= merge_elements($search_json, $firstorelementindex, $mergearray);
        }
        $canstartor = false;
        $firstorelementindex = -1;
        $mergearray = array();
        break;
      case 'or':
        break;
      case '(':
      case ')':
        if ($firstorelementindex != -1)
        {
          /* merge the mergearray */
          $i -= merge_elements($search_json, $firstorelementindex, $mergearray);
        }
        $firstorelementindex = -1;
        $mergearray = array();
        $canstartor = true;
        break;
      }
    }
    else
    {
      /* Not all terms can be optimised as AND binds more tightly than OR and
       * also brackets affect applicability of the optimisation */
      if ($canstartor)
      {
        if ($firstorelementindex == -1)
        {
          $firstorelementindex = $i;
        }
        switch ($search_json[$i][0])
        {
        /* WORK NEEDED: This does not merge lookup values from different options
         *              which is possible because the filter is based on the
         *              lookup value identifier and is ignorant of the option
         *              identifier */
        case 'Testsuite Config Setting':
        case 'Other Config Setting':
          if ($search_json[$firstorelementindex][0] != $search_json[$i][0]
              || $search_json[$firstorelementindex][1] != $search_json[$i][1])
          {
            /* merge the mergearray */
            $i -= merge_elements($search_json, $firstorelementindex, $mergearray);

            /* OR with different search term type. Clobber the list and start again*/
            $firstorelementindex = $i;
            $mergearray = array();
          }
          array_push($mergearray, $i);
          break;
        case 'Action':
        case 'Version of Action':
        case 'Resource Attribute':
        case 'Requested Resource Attribute':
        case 'Testrun Group':
        case 'User':
        case 'Testrun':
          if ($search_json[$firstorelementindex][0] != $search_json[$i][0])
          {
            /* merge the mergearray */
            $i -= merge_elements($search_json, $firstorelementindex, $mergearray);

            /* OR with different search term type. Clobber the list and start again*/
            $firstorelementindex = $i;
            $mergearray = array();
          }
          array_push($mergearray, $i);
          break;
        }
      }
      $canstartor = true;
    }
  }
  if ($firstorelementindex != -1)
  {
    /* merge the mergearray */
    merge_elements($search_json, $firstorelementindex, $mergearray);
  }
}

function get_test_string($term)
{
  $sql = "";
  if (is_array($term))
  {
    $sql = " IN (";
    for ($i = 0 ; $i < count($term) ; $i++)
    {
      if ($i != 0)
      {
        $sql .= ", ";
      }
      $sql .= "'".pg_escape_string($term[$i])."'";
    }
    $sql .= ")";
  }
  else
  {
    $sql = "='".pg_escape_string($term)."'";
  }
  return $sql;
}

function search_testruns($search_json, $group_json)
{
  global $ovtDB;
  global $timings;
  if (is_array($search_json) && is_array($group_json))
  {
    if (count($search_json) == 0)
    {
      return array();
    }
    $withsql = array();
    $sql = "SELECT DISTINCT ovt_testrun.testrunid, \n".
           "       ovt_testrunaction.simpleequivalenceid AS seid, \n".
           "       ovt_testrunaction.recursiveequivalenceid AS reid,\n".
           "       ovt_testrunaction.subrecursiveequivalenceid AS sreid\n";
    # Include all the fields that we want to order by
    for ($i = 0 ; $i < count($group_json) ; $i++)
    {
      if (is_array($group_json[$i]))
      {
        switch ($group_json[$i][0])
        {
        case 'Action':
          $sql .= ",(SELECT ovt_versionedaction.versionname\n".
                  "  FROM ovt_versionedaction INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
                  "  WHERE ovt_versionedaction.actionid='".pg_escape_string($group_json[$i][1])."'\n".
                  "  AND ovt_testrunaction.testrunid=ovt_testrun.testrunid) AS va".pg_escape_string($group_json[$i][1])."\n";
          break;
        case 'Config Setting':
          $sql2 = "SELECT ovt_configoption.islookup\n".
                  "FROM ovt_configoption\n".
                  "WHERE ovt_configoption.configoptionid='".pg_escape_string($group_json[$i][1])."'";
          $result = pg_query($ovtDB, $sql2);
          if (pg_fetch_result ($result, 0, "islookup") == "t")
          {
            $sql .= ", (SELECT ovt_configoptionlookup.lookupname\n".
                    "   FROM ovt_configoptionlookup INNER JOIN ovt_configsetting USING (configoptionlookupid)\n".
                    "   WHERE ovt_configoptionlookup.configoptionid='".pg_escape_string($group_json[$i][1])."'\n".
                    "   AND ovt_configsetting.testrunid=ovt_testrun.testrunid) AS cs".pg_escape_string($group_json[$i][1])."\n";
          }
          else
          {
            $sql .= ", (SELECT ovt_configsetting.configvalue\n".
                    "   FROM ovt_configsetting\n".
                    "   WHERE ovt_configsetting.configoptionid='".pg_escape_string($group_json[$i][1])."'\n".
                    "   AND ovt_configsetting.testrunid=ovt_testrun.testrunid) AS cs".pg_escape_string($group_json[$i][1])."\n";
          }
          break;
        case 'Resource Attribute':
          $sql .= ", (SELECT value\n".
                  "   FROM ((SELECT ovt_attributevalue.value, 1 AS ordering\n".
                  "    FROM ovt_testrunattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid)\n".
                  "         INNER JOIN ovt_attribute USING (attributeid)\n".
                  "         INNER JOIN ovt_attribute AS attribute2 ON (ovt_attribute.resourcetypeid=attribute2.resourcetypeid)\n".
                  "         INNER JOIN ovt_attributevalue AS attributevalue2 ON (attribute2.attributeid=attributevalue2.attributeid)\n".
                  "         INNER JOIN ovt_versionedactionattributevalue ON (attributevalue2.attributevalueid=ovt_versionedactionattributevalue.attributevalueid)\n".
                  "    WHERE ovt_testrunattributevalue.testrunid=ovt_testrun.testrunid\n".
                  "    AND ovt_versionedactionattributevalue.versionedactionid=ovt_testrunaction.versionedactionid\n".
                  "    AND ovt_attributevalue.attributeid='".pg_escape_string($group_json[$i][1])."')\n".
                  "   UNION\n".
                  "   (SELECT ovt_attributevalue.value, 2 AS ordering\n".
                  "    FROM ovt_attributevalue INNER JOIN ovt_versionedactionattributevalue USING (attributevalueid)\n".
                  "    WHERE ovt_attributevalue.attributeid='".pg_escape_string($group_json[$i][1])."'\n".
                  "    AND ovt_testrunaction.versionedactionid=ovt_versionedactionattributevalue.versionedactionid)\n".
                  "   UNION\n".
                  "   (SELECT ovt_attributevalue.value, 3 AS ordering\n".
                  "    FROM ovt_testrunactionresource\n".
                  "         INNER JOIN ovt_resourceattribute USING (resourceid)\n".
                  "         INNER JOIN ovt_resource ON (ovt_testrunactionresource.resourceid=ovt_resource.resourceid)\n".
                  "         INNER JOIN ovt_resourcestatus USING (resourcestatusid)\n".
                  "         INNER JOIN ovt_attributevalue USING (attributevalueid)\n".
                  "    WHERE ovt_testrunactionresource.testrunactionid=ovt_testrunaction.testrunactionid\n".
                  "    AND ovt_resourceattribute.attributeid='".pg_escape_string($group_json[$i][1])."'\n".
                  "    AND ovt_resourcestatus.status='HISTORIC')\n".
                  "  ) AS tmp\n".
                  "  ORDER BY ordering, value\n".
                  "  LIMIT 1) AS ra".pg_escape_string($group_json[$i][1])."\n";
          break;
        case 'Testrun Group':
          $sql .= ", (SELECT ovt_testrungroup.testrungroupname\n".
                  "   FROM ovt_testrungroup\n".
                  "   WHERE ovt_testrungroup.testrungroupid=ovt_testrun.testrungroupid) AS groupname\n";
          break;
        case 'User':
          $sql .= ", (SELECT ovt_user.fname || ' ' || ovt_user.sname\n".
                  "   FROM ovt_user\n".
                  "   WHERE ovt_user.userid=ovt_testrun.userid) AS username\n";
          break;
        }
      }
    }
    /* Ensure the testrun contains the correct testsuite */
    $sql .= "FROM ovt_testrun INNER JOIN ovt_testrunaction USING (testrunid)\n".
            "     INNER JOIN ovt_versionedaction USING (versionedactionid)\n".
            "     INNER JOIN ovt_action USING (actionid)\n".
            "WHERE ovt_action.testsuiteid='".$_REQUEST['testsuiteid']."'\n";
    $sql .= "AND (";

    /* Optimise the search string to merge OR constructs of the same search class */
    merge_or_elements($search_json);

    for ($i = 0 ; $i < count($search_json) ; $i++)
    {
      if (!is_array($search_json[$i]))
      {
        switch ($search_json[$i])
        {
        case 'and':
          $sql .= " AND \n";
          break;
        case 'or':
          $sql .= " OR \n";
          break;
        case 'not':
          $sql .= " NOT ";
          break;
        case '(':
        case ')':
          $sql .= " ".$search_json[$i]." \n";
          break;
        }
      }
      else
      {
        switch ($search_json[$i][0])
        {
        case 'Action':
          $sql .= "EXISTS (SELECT ovt_versionedaction.actionid\n".
                  "        FROM ovt_versionedaction INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
                  "        WHERE ovt_testrunaction.testrunid=ovt_testrun.testrunid\n".
                  "        AND ovt_versionedaction.actionid".get_test_string($search_json[$i][1]).")\n";
          break;
        case 'Version of Action':
          $sql .= "EXISTS (SELECT ovt_testrunaction.versionedactionid\n".
                  "        FROM ovt_testrunaction\n".
                  "        WHERE ovt_testrunaction.testrunid=ovt_testrun.testrunid\n".
                  "        AND ovt_testrunaction.versionedactionid".get_test_string($search_json[$i][1]).")\n";
          break;
        case 'Testsuite Config Setting':
        case 'Other Config Setting':
          $sql2 = "SELECT ovt_configoption.configoptionname, ovt_configoption.islookup\n".
                 "FROM ovt_configoption\n".
                 "WHERE ovt_configoption.configoptionid='".pg_escape_string($search_json[$i][1])."'";
          $result = pg_query($ovtDB, $sql2);
          if (pg_fetch_result($result, 0, "islookup") == "t")
          {
            $sql .= "EXISTS (SELECT ovt_configsetting.configoptionlookupid\n".
                    "        FROM ovt_configsetting\n".
                    "        WHERE ovt_configsetting.testrunid=ovt_testrun.testrunid\n".
                    "        AND ovt_configsetting.configoptionlookupid".get_test_string($search_json[$i][2]).")\n";
          }
          else
          {
            $sql .= "EXISTS (SELECT ovt_configsetting.configoptionlookupid\n".
                    "        FROM ovt_configsetting\n".
                    "        WHERE ovt_configsetting.testrunid=ovt_testrun.testrunid\n".
                    "        AND ovt_configsetting.configoptionid='".pg_escape_string($search_json[$i][1])."'\n".
                    "        AND ovt_configsetting.configvalue".get_test_string($search_json[$i][2]).")\n";
          }
          break;
        case 'Resource Attribute':
          $sql .= "EXISTS (SELECT ovt_resourceattribute.attributevalueid\n".
                  "        FROM ovt_testrunactionresource\n".
                  "             INNER JOIN ovt_resourceattribute USING (resourceid)\n".
                  "             INNER JOIN ovt_resource ON (ovt_testrunactionresource.resourceid=ovt_resource.resourceid)\n".
                  "             INNER JOIN ovt_resourcestatus USING (resourcestatusid)\n".
                  "        WHERE ovt_testrunactionresource.testrunactionid=ovt_testrunaction.testrunactionid\n".
                  "        AND ovt_resourcestatus.status='HISTORIC'\n".
                  "        AND ovt_resourceattribute.attributevalueid".get_test_string($search_json[$i][1]).")\n";
          break;
        case 'Requested Resource Attribute':
          /* Optimise these queries with a CTE */
          $withsql[] = "rra$i(resourcetypeid, attributevalueid) AS\n".
                       "  (SELECT resourcetypeid, attributevalueid\n".
                       "   FROM ovt_attribute INNER JOIN ovt_attributevalue USING (attributeid)\n".
                       "   WHERE attributevalueid".get_test_string($search_json[$i][1]).")";
          $sql .= "(EXISTS (SELECT 1\n".
                  "         FROM ovt_testrunattributevalue\n".
                  "              INNER JOIN rra$i USING (attributevalueid)\n".
                  "              INNER JOIN ovt_attribute USING (resourcetypeid)\n".
                  "              INNER JOIN ovt_attributevalue USING (attributeid)\n".
                  "              INNER JOIN ovt_versionedactionattributevalue ON \n".
                  "                          (ovt_attributevalue.attributevalueid=ovt_versionedactionattributevalue.attributevalueid\n".
                  "                           AND ovt_testrunaction.versionedactionid=ovt_versionedactionattributevalue.versionedactionid)\n".
                  "         WHERE ovt_testrunattributevalue.testrunid=ovt_testrun.testrunid\n".
                  "         AND ovt_testrunattributevalue.attributevalueid".get_test_string($search_json[$i][1]).")\n".
                  " OR\n".
                  " EXISTS (SELECT 1\n".
                  "         FROM ovt_versionedactionattributevalue\n".
                  "         WHERE ovt_versionedactionattributevalue.versionedactionid=ovt_testrunaction.versionedactionid\n".
                  "         AND attributevalueid".get_test_string($search_json[$i][1])."))\n";
          break;
        case 'Started After':
          $sql .= " ovt_testrun.testdate >= '".pg_escape_string($search_json[$i][1])."' ";
          break;
        case 'Started Before':
          $sql .= " ovt_testrun.startafter <= '".pg_escape_string($search_json[$i][1])."' ";
          break;
        case 'Testrun Group':
          $sql .= " ovt_testrun.testrungroupid".get_test_string($search_json[$i][1])." ";
          break;
        case 'User':
          $sql .= " ovt_testrun.userid".get_test_string($search_json[$i][1])." ";
          break;
        case 'Testrun':
          $sql .= " ovt_testrun.testrunid".get_test_string($search_json[$i][1])." ";
          break;
        }
      }
    }
    $sql .= ")\n";
    $sql .= "ORDER BY \n";
    if (count($group_json) != 0)
    {
      for ($i = 0 ; $i < count($group_json) ; $i++)
      {
        if ($i != 0)
        {
          $sql .= ", ";
        }
        if (is_array($group_json[$i]))
        {
          switch ($group_json[$i][0])
          {
          case 'Action':
            $sql .= "va".pg_escape_string($group_json[$i][1])."\n";
            break;
          case 'Config Setting':
            $sql .= "cs".pg_escape_string($group_json[$i][1])."\n";
            break;
          case 'Resource Attribute':
            $sql .= "ra".pg_escape_string($group_json[$i][1])."\n";
            break;
          case 'Testrun Group':
            $sql .= "groupname\n";
            break;
          case 'User':
            $sql .= "username\n";
            break;
          case 'Simple Equivalence':
            $sql .= "seid\n";
            break;
          case 'Recursive Equivalence':
            $sql .= "reid\n";
            break;
          case 'Producer Equivalence':
            $sql .= "sreid\n";
            break;
          }
        }
      }
      $sql .= ", ";
    }
    $sql .= "seid, sreid, reid\n";
    if (count($withsql) != 0)
    {
      $prefixsql = "WITH ";
      for ($i = 0 ; $i < count($withsql) ; $i++)
      {
        if ($i != 0)
        {
          $prefixsql .= ", ";
        }
        $prefixsql .= $withsql[$i];
      }
      $sql = $prefixsql . $sql;
    }
    $sql .= "LIMIT 251";

    $timings['testrunsql']['start'] = microtime(true);
    $result = pg_query($ovtDB, $sql);
    $timings['testrunsql']['end'] = microtime(true);
    $timings['testrunsql']['extra'] = $sql;

    $testrun_list = array();
    for ($i = 0 ; $i < min(pg_num_rows($result),250) ; $i++)
    {
      $testrun_list[] = pg_fetch_array($result, $i);
    }
    if (pg_num_rows($result) == 251)
    {
      $testrun_list[] = array("limit"=>250);
    }
    return $testrun_list;
  }
  return NULL;
}
?>
