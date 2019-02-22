<?php

include_once('inc/includes.inc');
include_once('inc/xmlrpc.inc');
include_once('inc/jsonrpc.inc');
include_once('inc/json_extension_api.inc');
include_once('inc/search_testruns.inc');
ini_set('display_errors', '1'); 
error_reporting(E_ALL);

$colors = array('66cc66','ccccff','FFCCFF','cc33cc','ff3366','cccc99','ffcc33','00ffff','FF9999','ccffcc','cccc66','996666','ff9900','ff66cc','66ccff','0066ff','66ff33','cc6666','ffff66');
$colors = array('ffffff','ffffff','FFffFF','ffffff','ffffff','ffffff','ffffff','ffffff','FFffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff');
global $colors;

function ovt_get_action_name($actionid)
{
  global $ovtDB;
  $sql = "SELECT actionname\n".
         "FROM ovt_action\n".
         "WHERE actionid='".$actionid."'";
  $result = pg_query($ovtDB, $sql);
  return pg_fetch_result($result, 0, 0);
}
function ovt_get_configoption_name($configoptionid)
{
  global $ovtDB;
  $sql = "SELECT configoptionname\n".
         "FROM ovt_configoption\n".
         "WHERE configoptionid='".$configoptionid."'";
  $result = pg_query($ovtDB, $sql);
  return pg_fetch_result($result, 0, 0);
}
function ovt_get_attribute_name($attributeid)
{
  global $ovtDB;
  $sql = "SELECT attributename\n".
         "FROM ovt_attribute\n".
         "WHERE attributeid='".$attributeid."'";
  $result = pg_query($ovtDB, $sql);
  return pg_fetch_result($result, 0, 0);
}

function showResultCell($tr, $mergecount, $mergedata, $resultsvary, $allresults, $resultstate, $options, $filterstate)
{
  global $colors;

  if (!$resultsvary)
  {
    if ($resultstate === NULL)
    {
      $mergedata = "";
    }
    else if (!$options['showextendedgroups'] && $resultstate)
    {
      $mergedata = "PASS";
      if (!$allresults) $mergedata .= "*";
    }
    else if (!$options['showextendedgroups'])
    {
      $mergedata = "FAIL";
      if (!$allresults) $mergedata .= "*";
    }
  }
  $color = $colors[$tr%2];
  if ($filterstate)
  {
    $color = "FF0000";
  }
  $options['output']['begin_cell']("overallresult", $color, $mergecount);
  echo $mergedata;
  $options['output']['end_cell']();
}

include_once('html_output.inc');
include_once('tab_output.inc');

/* Output the testrun headings and return the set of column sizes */
function output_group_headings($group_json, $testrunids, $options)
{
  $grouplists = array();
  $finalgrouplist = array();
  $lastgrouplist = array(count($testrunids));

  if (count($group_json) == 0)
  {
    $group_json[] = array('Recursive Equivalence');
  }

  /* Now do the grouped column headers */
  if (count($group_json) != 0)
  {
    for ($i = 0 ; $i < count($group_json) ; $i++)
    {
      if (is_array($group_json[$i]))
      {
        $options['output']['begin_row']();
        $options['output']['begin_cell']("resultgroups");
        switch ($group_json[$i][0])
        {
        case 'Action':
          $field = "va".pg_escape_string($group_json[$i][1]);
          $title = ovt_get_action_name($group_json[$i][1]);
          break;
        case 'Config Setting':
          $field = "cs".pg_escape_string($group_json[$i][1]);
          $title = ovt_get_configoption_name($group_json[$i][1]);
          break;
        case 'Resource Attribute':
          $field = "ra".pg_escape_string($group_json[$i][1]);
          $title = ovt_get_attribute_name($group_json[$i][1]);
          break;
        case 'Testrun Group':
          $field = "groupname";
          $title = "Testrun Group";
          break;
        case 'User':
          $field = "username";
          $title = "Owner";
          break;
        case 'Simple Equivalence':
          $field = "seid";
          $title = "Simple Equivalence";
          break;
        case 'Recursive Equivalence':
          $field = "reid";
          $title = "Total Equivalence";
          break;
        case 'Producer Equivalence':
          $field = "sreid";
          $title = "Producer Equivalence";
          break;
        }
        $options['output']['escape']($title);
        $options['output']['end_cell']();
        $lastvalue = NULL;
        $valuecount = 0;
        $finalgrouplist = array();
        $lastgrouplistindex = 0;
        for ($tr = 0 ; $tr < count($testrunids) ; $tr++)
        {
          $valuecount++;
          if ($lastvalue != $testrunids[$tr][$field] || $tr == count($testrunids)-1)
          {
            
            if ($tr != 0 || $tr+1 == count($testrunids))
            {
              if ($tr+1 != count($testrunids) || $lastvalue != $testrunids[$tr][$field])
              {
                $valuecount--;
              }
              $totalcolspan = $valuecount;
              while ($valuecount > $lastgrouplist[$lastgrouplistindex])
              {
                $valuecount -= $lastgrouplist[$lastgrouplistindex];
                $finalgrouplist[] = $lastgrouplist[$lastgrouplistindex];

                $options['output']['begin_header_cell']("overallresult", "", $lastgrouplist[$lastgrouplistindex]);
                $options['output']['escape']($lastvalue);
                $options['output']['end_header_cell']();

                $lastgrouplist[$lastgrouplistindex] = 0;
                if ($lastgrouplistindex < (count($lastgrouplist)-1))
                {
                  $lastgrouplistindex++;
                }
              }
              
              $lastgrouplist[$lastgrouplistindex] -= $valuecount;
              if ($lastgrouplist[$lastgrouplistindex] == 0)
              {
                if ($lastgrouplistindex < (count($lastgrouplist)-1))
                {
                  $lastgrouplistindex++;
                }
              }

              if ($valuecount!=0)
              {
                $finalgrouplist[] = $valuecount;
                $options['output']['begin_header_cell']("overallresult", "", $valuecount);
                $options['output']['escape']($lastvalue);
                $options['output']['end_header_cell']();
              }
              $valuecount = 1;
              if ($tr+1 == count($testrunids) && $lastvalue != $testrunids[$tr][$field])
              {
                // The last column is different to the previous so output its value
                // separately
                $finalgrouplist[] = 1;
                $options['output']['begin_header_cell']("overallresult", "", $valuecount);
                $options['output']['escape']($testrunids[$tr][$field]);
                $options['output']['end_header_cell']();
              }
            }
            $lastvalue = $testrunids[$tr][$field];
          }
        }

        $grouplists[$i] = $finalgrouplist;
        $lastgrouplist = $finalgrouplist;
        $options['output']['end_row']();
      }
    }
  }

  return $grouplists;
}

/* output the testrun numbers and field names for extended results */
function output_table_footer($finalgrouplist, $testrunids, $testsuiteid, $allfields, $options, $groupsect)
{
  $options['output']['begin_row']();
  $options['output']['begin_header_cell']("testrunnumber");
  $options['output']['escape']("Testrun number");
  $options['output']['end_header_cell']();
  $mergecount = 0;
  $mergegroup = 0;
  $mergedata = "";
  $gr = 0;
  $grcount = 0;
  for ($tr = 0; $tr < count($testrunids) ; $tr++, $grcount--)
  {
    if ($mergedata != "")
    {
      $mergedata .= ", ";
    }
    $mergedata .= $testrunids[$tr]['testrunid'];
    $mergecount++;

    if (count($finalgrouplist) == 0 || $mergecount == $finalgrouplist[$mergegroup])
    {
      $options['output']['begin_header_cell']("testrunnumber", "", $mergecount);
      $tok = strtok($mergedata, ',');
      if ($tr !== 0 && $grcount != 0)
      {
	    $last = $testrunids[$tr-1]['testrunid'];
            $options['output']['begin_hyperlink']("http://overtest.mipstec.com/viewresults.php?testsuiteid=".$testsuiteid."&group_terms=[[\"Testrun%20Group\"]]&search_terms=[[\"Testrun\",\"".$last."\"],\"or\",[\"Testrun\",\"".$tok."\"]]");
	    $options['output']['escape']("<=");
	    $options['output']['end_hyperlink']();
	    $options['output']['escape'](" ");
      }

      $options['output']['begin_hyperlink']("http://overtest.mipstec.com/viewtestrun.php?testrunid=".$tok);
      $options['output']['escape']($tok);
      $options['output']['end_hyperlink']();
      for ($tok = strtok(',') ; $tok !== false; $tok = strtok(','))
      {
	    $options['output']['escape'](", ");
            $options['output']['begin_hyperlink']("http://overtest.mipstec.com/viewtestrun.php?testrunid=".$tok);
	    $options['output']['escape']($tok);
            $options['output']['end_hyperlink']();
      }
      $options['output']['end_header_cell']();
      $mergegroup++;
      $mergecount = 0;
      $mergedata = "";
    }

    if ($grcount == 0 && $gr < count($groupsect))
    {
        $grcount = $groupsect[$gr];
	$gr++;
    }
  }
  $options['output']['end_row']();
}

/*
 * The result filter abstracts the logic to test whether a result should be
 * included or excluded from a filter based on the criteria. It will return
 * NULL if this comparison should not affect the previous decision about
 * inclusion/exclusion
 */
function resultFilter($resultStability, $resultsInclude, $passmatch, $value)
{
  /* When ignorant of stability the only filter is to include passes or fails */

  if ($resultStability == "any" &&
      $resultsInclude == ($value?'pass':'fail'))
  {
    return true;
  }

  /* When looking for different results (missing results matter), the first
   * iteration has the passmatch set to a special value. This is ignored but
   * on further iterations a NULL value is a mismatch. */

  if ($resultStability == "different"
      && $passmatch !== "firstresult" && $passmatch !== $value)
  {
    return true;
  }

  /* When looking for unstable results (missing results are assumed to be
   * favourable) any NULL value found should be ignored until a result is
   * found. */

  if (($resultStability == "unstable")
      && ($passmatch !== NULL && $passmatch != $value))
  {
    return true;
  }

  /* Stable results are an exclusion filter. All results are assumed stable
   * until a difference is found. (missing results are assumed to be favourable)
   * When filtering for all pass or all fail then any mismatch results in
   * excluding the row. Otherwise any change from the first value results in
   * excluding the row. */

  if (($resultStability == "stable")
      && (($resultsInclude != "any"
           && ($value?'pass':'fail') != $resultsInclude)
          || ($passmatch !== NULL && $passmatch != $value)))
  {
    return false;
  }
  return NULL;
}
function updateResults(&$result, $testrunid, $resulttestrunid, $value)
{
  if ($resulttestrunid != $testrunid)
  {
    $result["reg".$testrunid][$resulttestrunid] = $value;
  }
  else
  {
    $result[$testrunid] = $value;
  }
}
global $timings;
$timings = array();

function showResultTable($testrunids, $group_json, $testsuiteid, $resultStability, $resultsInclude, $options)
{
  global $ovtDB;
  global $colors;
  global $timings;

  $testrunidset = "(";
  $reids = array();
  $limitedresults = false;
  $limit = 0;
  for ($i = 0 ; $i < count($testrunids) ; $i++)
  {
    if (array_key_exists('testrunid', $testrunids[$i]))
    {
      if (!in_array($testrunids[$i]['reid'], $reids))
      {
        $reids[] = $testrunids[$i]['reid'];
      }
      if ($i != 0)
      {
        $testrunidset .= ", ";
      }
      $testrunidset .= "'".$testrunids[$i]['testrunid']."'";
    }
    else
    {
      /* This is the marker to say more testruns are available but were not
       * selected due to exceeding the limit */
      $limitedresults = true;
      $limit = $testrunids[$i]['limit'];
      array_pop($testrunids);
    }
  }
  $testrunidset .= ")";

  if ($limitedresults)
  {
    $options['output']['escape']("Testrun search returned too many results ($limit). Please refine your search.");
    $options['output']['newline']();
  }

  $options['output']['begin_table']();
  $timings['headings']['start'] = microtime(true);

  $grouplists = output_group_headings($group_json, $testrunids, $options);
  $finalgrouplist = $grouplists[count($grouplists) - 1];

  $timings['headings']['end'] = microtime(true);
  $timings['headings']['extra'] = "";

  $resarray = array();

  $sql  = "SELECT DISTINCT \n";

  $sql .= "     ovt_resultstring.resultfieldid AS srfi, ovt_resultstring.resultstring,\n".
          "     ovt_resultinteger.resultfieldid AS irfi, ovt_resultinteger.resultinteger,\n".
          "     ovt_resultfloat.resultfieldid AS frfi, ovt_resultfloat.resultfloat,\n".
          "     ovt_resultboolean.resultfieldid AS brfi, ovt_resultboolean.resultboolean,\n";
  
  $sql .= "       tra.passed,\n".
          "       tra.testrunactionid,\n".
          "       tra.testrunid AS resulttestrunid,\n".
          "       tra.testrunid,\n".
          "       to_char(tra.completeddate - tra.starteddate, 'HH24:MI:SS') AS duration,\n".
          "       tra.recursiveequivalenceid\n".
          "FROM ovt_testrunaction AS tra INNER JOIN ovt_versionedaction AS v USING (versionedactionid)\n".
          "     INNER JOIN ovt_action AS a USING (actionid)\n";

  $sql .= "     LEFT OUTER JOIN ovt_resultstring ON (ovt_resultstring.testrunactionid=tra.testrunactionid)\n".
          "     LEFT OUTER JOIN ovt_resultboolean ON (ovt_resultboolean.testrunactionid=tra.testrunactionid)\n".
          "     LEFT OUTER JOIN ovt_resultinteger ON (ovt_resultinteger.testrunactionid=tra.testrunactionid)\n".
          "     LEFT OUTER JOIN ovt_resultfloat ON (ovt_resultfloat.testrunactionid=tra.testrunactionid)\n";

  $sql .= "WHERE a.testsuiteid='".$testsuiteid."'\n".
          "AND tra.testrunid IN ".$testrunidset."\n";

  $timings['resultsql']['start'] = microtime(true);
  $resultvalues = pg_query($ovtDB, $sql);
  $timings['resultsql']['end'] = microtime(true);
  $timings['resultsql']['extra'] = $sql;
  $allfieldids = array();

  /* Populate the internal data structure for test results */
  $timings['resultarray']['start'] = microtime(true);
  for ($j = 0 ; $j < pg_num_rows($resultvalues) ; $j++)
  {
    $fetcharray = pg_fetch_array($resultvalues, $j);
    $testrunid = $fetcharray['testrunid'];
    $resarray["duration"][$testrunid] = $fetcharray['duration'];
    if ($fetcharray['srfi'] != NULL && $fetcharray['resultstring'] != NULL)
    {
      $rfi = $fetcharray['srfi'];
      if (!in_array($rfi, $allfieldids))
      {
        $allfieldids[] = $rfi;
      }
      $resarray[$rfi][$testrunid] = $fetcharray['resultstring'];
    }
    if ($fetcharray['irfi'] != NULL && $fetcharray['resultinteger'] != NULL)
    {
      $rfi = $fetcharray['irfi'];
      if (!in_array($rfi, $allfieldids))
      {
        $allfieldids[] = $rfi;
      }
      $resarray[$rfi][$testrunid] = (integer)$fetcharray['resultinteger'];
    }
    if ($fetcharray['frfi'] != NULL && $fetcharray['resultfloat'] != NULL)
    {
      $rfi = $fetcharray['frfi'];
      if (!in_array($rfi, $allfieldids))
      {
        $allfieldids[] = $rfi;
      }
      $resarray[$rfi][$testrunid] = (float)$fetcharray['resultfloat'];
    }
    if ($fetcharray['brfi'] != NULL && $fetcharray['resultboolean'] != NULL)
    {
      $rfi = $fetcharray['brfi'];
      if (!in_array($rfi, $allfieldids))
      {
        $allfieldids[] = $rfi;
      }
      $resarray[$rfi][$testrunid] = ($fetcharray['resultboolean'] == "t");
    }
  }

  $timings['resultarray']['end'] = microtime(true);
  $timings['resultarray']['extra'] = pg_num_rows($resultvalues);

  /* Get the field names and ordering */
  $timings['fieldssql']['start'] = microtime(true);

  $allfieldids = implode(",", $allfieldids);
  if ($allfieldids == "")
  {
    $allfieldids = "null";
  }
  $sql = "SELECT resultfieldid, resultfieldname, resulttypename\n".
         "FROM ovt_resultfield INNER JOIN ovt_resulttype USING (resulttypeid)\n".
         "WHERE resultfieldid IN (".$allfieldids.")\n".
         "ORDER BY ordering\n";
  $allfields = pg_query($ovtDB, $sql);

  $timings['fieldssql']['end'] = microtime(true);
  $timings['fieldssql']['extra'] = $sql;

  $timings['tableoutput']['start'] = microtime(true);
  $timings['groups']['start'] = 0;
  $timings['groups']['end'] = 0;
  $timings['groups']['extra'] = "";
  /* Set up the stability group.
   * This is used to restrict stability checks to groups in a certain category */
  if (is_numeric($options['stabilitylevel']))
  {
    $stabilitygroup = $grouplists[(int)$options['stabilitylevel']];
  }
  else
  {
    /* All levels equates to a group of all the testruns */
    $stabilitygroup = array(count($testrunids));
  }
  for ($i = 0 ; $i < count($stabilitygroup) ; $i++)
  {
    $stabilitygroup[$i] = array('count' => $stabilitygroup[$i], 'filtered' => false);
  }
  
  for ($i = 0 ; $i < pg_num_rows($allfields) + 1 ; $i++)
  {
    $grouptime = microtime(true);
    if ($i == pg_num_rows($allfields))
    {
      $rfi = "duration";
      $rowname = "Duration";
    }
    else
    {
      $rfi = pg_fetch_result($allfields, $i, "resultfieldid");
      $rowname = pg_fetch_result($allfields, $i, "resultfieldname");
    }
    $actionarray = $resarray[$rfi];

    /* testrun indices for cells to highlight */
    $stabilityhighlights = array();

    /* Plan whether or not to display the test.
     * Only proceed if some filtering is required. Showing any results with any pass or fail
     * status does not require filtering. */

    if ($resultsInclude != "any" || (count($testrunids) > 1 && $resultStability != "any"))
    {
      /* Track the stability level */
      $currentstabilitygroup = 0;
      $traccumulate = 0;

      /* Intially show all results when showing stability (until one does not match)
       *          show no results when showing any kind of instability (until all do match) */
      $show = ($resultStability == "stable");
      $groupshow = ($resultStability == "stable");

      /* Matching is done by tracking the last pass status.
       * Showing different results ignores missing results, so the initial value must be special */
      $passmatch = ($resultStability == "different")?"firstresult":NULL;

      /* Process each testrun (column) in turn */
      for ($tr = 0 ; $tr < count($testrunids) ; $tr++)
      {
        $testrunid = $testrunids[$tr]['testrunid'];
        $reid = $testrunids[$tr]['reid'];

        /* Determine if there are any pass/fail results for this testrun */
        if (array_key_exists($testrunid, $actionarray))
        {
          /* Hideous structure dereference! */
          $value = $actionarray[$testrunid];
          $showtemp = resultFilter($resultStability, $resultsInclude, $passmatch, $value);

          /* resultFilter will only return a boolean if it asserts inclusion or exclusion of a result */
          if ($showtemp !== NULL)
          {
            $show = $showtemp;
            $groupshow = $showtemp;
          }

          /* Track the last pass / fail state. It will always be 'true' or 'false' */
          $passmatch = $value;
        }
        else if ($resultStability == "different")
        {
          /* When the first result is missing, the last passmatch value can be set to NULL.
           * This allows subsequent iterations to compare NULL to pass/fail and see a difference.
           * If a result is found on the first iteration and the string 'firstresult' is found,
           * then the first result is not different. This mechanism makes passmatch a 4 state
           * variable instead of 3 to cope with a non-null value on the first iteration */
          if ($passmatch === "firstresult")
          {
            $passmatch = NULL;
          }

          /* Different results take in to account missing results */
          if ($passmatch !== NULL)
          {
            $show = true;
            $groupshow = true;
          }
        }

        /* Reset the show and passmatch state if we cross a group boundary based on the stability level */
        $traccumulate++;
        if ($traccumulate == $stabilitygroup[$currentstabilitygroup]['count'] || $tr == count($testrunids)-1)
        {
          /* Filtering only happens when stability is applied in a group not top level.
             This has the effect of disabling cell colouring when no level is specified */
          $stabilitygroup[$currentstabilitygroup]['filtered'] = is_numeric($options['stabilitylevel']) && $groupshow;

          $currentstabilitygroup++;
          $traccumulate = 0;
          $passmatch = ($resultStability == "different")?"firstresult":NULL;
          $groupshow = ($resultStability == "stable");
        }
      }
      if (!$show)
      {
        continue;
      }
    }
    $timings['groups']['end'] += microtime(true) - $grouptime;

    /* Display the test */
    $options['output']['begin_row']();
    $options['output']['begin_cell']("testname");
    $options['output']['escape']($rowname);
    $options['output']['end_cell']();

    $mergecount = 0;
    $mergegroup = 0;
    $mergedata = "";
    $allresults = true;
    $resultsvary = false;
    $resultstate = NULL;
    $extended = array();
    $extendedVersion = 0;
    $comparereid = NULL;
    $comparetestrunid = NULL;

    $currentstabilitygroup = 0;
    $traccumulate = 0;

    for ($tr = 0 ; $tr < count($testrunids) ; $tr++)
    {
      $mergecount++;

      /* extract the current testrunid and reid to make code more readable */
      $testrunid = $testrunids[$tr]['testrunid'];
      $reid = $testrunids[$tr]['reid'];

      /* use the first set of results as the basis for deltas. This needs to be configurable eventually */
      if ($comparereid === NULL)
      {
        $comparereid = $reid;
        $comparetestrunid = $testrunid;
      }

      if (!array_key_exists($testrunid, $actionarray))
      {
        $allresults = false;
	if ($mergedata != "")
	  $mergedata .= " | ";
        $mergedata .= "_";
      }
      else
      {
        $tempresultstate = $actionarray[$testrunid];
	if ($tempresultstate != "" && $mergedata != "")
	  $mergedata .= " | ";
        $mergedata .= $tempresultstate;
        if ($resultstate !== NULL && $tempresultstate != $resultstate)
        {
          $resultsvary = true;
        }
          $resultsvary = true;
        $resultstate = $tempresultstate;
      }
      if (count($finalgrouplist) == 0 || $mergecount == $finalgrouplist[$mergegroup])
      {
        showResultCell($tr, $mergecount, $mergedata, $resultsvary, $allresults, $resultstate, $options,
                       $stabilitygroup[$currentstabilitygroup]['filtered']);
        $mergegroup++;
        $mergecount = 0;
        $mergedata = "";
        $allresults = true;
        $resultsvary = false;
        $resultstate = NULL;
      }

      $traccumulate++;
      if ($traccumulate == $stabilitygroup[$currentstabilitygroup]['count'])
      {
        $currentstabilitygroup++;
        $traccumulate = 0;
      }
 
    }
  
    $options['output']['end_row']();

  }
  $timings['tableoutput']['end'] = microtime(true);
  $timings['tableoutput']['extra'] = "";

  $groupsect = array();
  $groupsect = $grouplists[count($grouplists)-2];
  output_table_footer($finalgrouplist, $testrunids, $testsuiteid, $allfields, $options, $groupsect);

  $options['output']['end_table']();

}

if (!isset($_REQUEST['what']))
{
  echo "BAD REQUEST";
  exit (0);
}
elseif ($_REQUEST['what'] == "show_group_combo")
{
  $json = json_decode(stripslashes($_REQUEST['groupstring']));
  echo "<option value=\"all\"";
  if ($_REQUEST['stabilitylevel'] == "all")
  {
    echo " selected";
  }
  echo ">Top Level</option>\n";
  if (is_array($json))
  {
    for ($i = 0 ; $i < count($json) ; $i++)
    {
      echo "<option value=\"$i\"";
      if ($_REQUEST['stabilitylevel'] == (string)$i)
      {
        echo " selected";
      }
      echo ">";
      if (!is_array($json[$i]))
      {
        echo "ERROR: Unknown element in JSON group string";
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
          echo pg_fetch_result ($result, 0, "actionname");
          break;
        case 'Config Setting':
          $sql = "SELECT ovt_configoption.configoptionname, ovt_configoption.islookup\n".
                 "FROM ovt_configoption\n".
                 "WHERE ovt_configoption.configoptionid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          echo pg_fetch_result ($result, 0, "configoptionname");
          break;
        case 'Resource Attribute':
          $sql = "SELECT ovt_resourcetype.resourcetypename, ovt_attribute.attributename\n".
                 "FROM ovt_attribute INNER JOIN ovt_resourcetype USING (resourcetypeid)\n".
                 "WHERE ovt_attribute.attributeid='".pg_escape_string($json[$i][1])."'";
          $result = pg_query($ovtDB, $sql);
          $group = pg_fetch_result($result, 0, "resourcetypename");
          echo $group." - ".pg_fetch_result($result, 0, "attributename");
          break;
        case 'User':
          echo "Owner";
          break;
        case 'Testrun Group':
        case 'Simple Equivalence':
        case 'Recursive Equivalence':
        case 'Producer Equivalence':
          echo $json[$i][0];
          break;
        }
      }
      echo "</option>\n";
    } 
  }
  else
  {
    echo "<option value=\"0\">ERROR: Invalid JSON group string</option>\n";
  }
}
elseif ($_REQUEST['what'] == "resulttable")
{
  $search_json = json_decode(stripslashes($_REQUEST['searchstring']));
  $group_json = json_decode(stripslashes($_REQUEST['groupstring']));
  
  if (!is_array($search_json))
  {
    echo "No testruns selected (Filter error)";
  }
  else
  {
    if (!is_array($group_json))
    {
      echo "No testruns selected (Group error)";
    }
    else
    {
      $timings['search']['start'] = microtime(true);
      $testrun_list = search_testruns($search_json, $group_json);
      $timings['search']['end'] = microtime(true);
      $timings['search']['extra'] = "";

      if ($testrun_list === NULL || count($testrun_list) == 0)
      {
        echo "No testruns found";
      }
      else
      {
        $_REQUEST['showextended'] = false;
        $_REQUEST['showextendedgroups'] = false;
        $_REQUEST['showversions'] = false;
        $_REQUEST['enableinference'] = false;
        $_REQUEST['resultstability'] = "unstable";
        $_REQUEST['resultsinclude'] = "any";
        $_REQUEST['stabilitylevel'] = "all";
        $_REQUEST['showdeltas'] = false;
        $_REQUEST['uniquetests'] = false;
        if (isset($_REQUEST['show']))
        {
          $showstrings = explode(",", $_REQUEST['show']);
          foreach ($showstrings as $showstring)
          {
            if (substr($showstring, 0, 3) == "lev")
            {
              $_REQUEST['stabilitylevel'] = substr($showstring, 3);
              continue;
            }

            switch ($showstring)
            {
            case "unstable":
            case "stable":
            case "any":
            case "different":
              $_REQUEST['resultstability'] = $showstring;
              break;
            case "pass":
            case "fail":
              $_REQUEST['resultsinclude'] = $showstring;
              break;
            case "extended":
              $_REQUEST['showextended'] = true;
              break;
            case "extendedgroups":
              $_REQUEST['showextendedgroups'] = true;
              break;
            case "versions":
              $_REQUEST['showversions'] = true;
              break;
            case "inference":
              $_REQUEST['enableinference'] = true;
              break;
            case "deltas":
              $_REQUEST['showdeltas'] = true;
              break;
            }
          }
        }

        if ($_REQUEST['output'] == "tab")
        {
          header('Content-type: text/plain');
          header('Content-Disposition: attachment; filename="ovt_results.txt"');
          
          $_REQUEST['output'] = $tab_output;
        }
        else
        {
          $_REQUEST['output'] = $html_output;
        }
        $timings['resulttable']['start'] = microtime(true);
        showResultTable($testrun_list, $group_json, $_REQUEST['testsuiteid'], $_REQUEST['resultstability'], $_REQUEST['resultsinclude'], $_REQUEST);
        $timings['resulttable']['end'] = microtime(true);
        $timings['resulttable']['extra'] = "";
      }
    }
  }

/* 
  $keys = array_keys($timings);
  for ($i = 0 ; $i < count($timings) ; $i++)
  {
    echo $keys[$i] . " <b>" .($timings[$keys[$i]]['end'] - $timings[$keys[$i]]['start'])."</b> - ".$timings[$keys[$i]]['extra']."<br />\n";
  }
 */
}
elseif ($_REQUEST['what'] == "testruninfo")
{
  $sql = "SELECT ovt_user.fname || ' ' || ovt_user.sname AS name,\n".
         "       ovt_testrun.description,\n".
         "       to_char(ovt_testrun.createddate, 'YYYY/MM/DD HH24:MI') AS createddate,\n".
         "       to_char(ovt_testrun.testdate, 'YYYY/MM/DD HH24:MI') AS testdate,\n".
         "       to_char(ovt_testrun.completeddate, 'YYYY/MM/DD HH24:MI') AS completeddate,\n".
         "       ovt_testrungroup.testrungroupname\n".
         "FROM ovt_testrun INNER JOIN ovt_testrungroup USING (testrungroupid)\n".
         "     INNER JOIN ovt_user ON (ovt_testrun.userid = ovt_user.userid)\n".
         "WHERE ovt_testrun.testrunid='".$_REQUEST['testrunid']."'";

  $result = pg_query($ovtDB, $sql);

  echo "Title: <b>".pg_fetch_result($result, 0, "description")."</b><br />\n".
       "Group: <b>".pg_fetch_result($result, 0, "testrungroupname")."</b><br />\n".
       "Owner: <b>".pg_fetch_result($result, 0, "name")."</b><br />\n".
       "Created: <b>".pg_fetch_result($result, 0, "createddate")."</b><br />\n".
       "Start: <b>".pg_fetch_result($result, 0, "testdate")."</b><br />\n".
       "End: <b>".pg_fetch_result($result, 0, "completeddate")."</b><br />\n";
}
?>
