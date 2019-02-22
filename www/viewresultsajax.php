<?php

include_once('inc/includes.inc');
include_once('inc/xmlrpc.inc');
include_once('inc/jsonrpc.inc');
include_once('inc/json_extension_api.inc');
include_once('inc/search_testruns.inc');
$colors = array('66cc66','ccccff','FFCCFF','cc33cc','ff3366','cccc99','ffcc33','00ffff','FF9999','ccffcc','cccc66','996666','ff9900','ff66cc','66ccff','0066ff','66ff33','cc6666','ffff66');
$colors = array('ffffff','ffffff','FFffFF','ffffff','ffffff','ffffff','ffffff','ffffff','FFffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff','ffffff');
global $colors;

ini_set('display_errors', '1');
error_reporting(E_ALL);

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
function output_table_footer($finalgrouplist, $testrunids, $allfields, $options)
{
  $options['output']['begin_row']();
  $options['output']['begin_header_cell']("testrunnumber");
  $options['output']['escape']("Testrun number");
  $options['output']['end_header_cell']();
  $mergecount = 0;
  $mergegroup = 0;
  $mergedata = "";
  for ($tr = 0 ; $tr < count($testrunids) ; $tr++)
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
  }
  for ($i = 0 ; $options['showextended'] && $i < pg_num_rows($allfields) ; $i++)
  {
    for ($tr = 0 ; $tr < count($testrunids) ; $tr++)
    {
      $options['output']['begin_header_cell']();
      $options['output']['escape'](pg_fetch_result($allfields, $i, "resultfieldname"));
      $options['output']['end_header_cell']();
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
function updateResults(&$result, $rfi, $reid, $testrunid, $resulttestrunid, $value)
{
  if (!array_key_exists($rfi, $result))
  {
    $result[$rfi] = array();
  }
  if (!array_key_exists($reid, $result[$rfi]))
  {
    $result[$rfi][$reid] = array();
  }
  if ($resulttestrunid != $testrunid)
  {
    $result[$rfi][$reid]["reg".$testrunid][$resulttestrunid] = $value;
  }
  else
  {
    $result[$rfi][$reid][$testrunid] = $value;
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

  $resultindexfield = "testid";
  if ($options['showversions'])
  {
    $resultindexfield = "versionedtestid";
  }

  $resarray = array();

  $sql  = "SELECT DISTINCT \n";

  if ($options['showextended'])
  {
    $sql .= "     ovt_testresultstring.resultfieldid AS srfi, ovt_testresultstring.testresultstring,\n".
            "     ovt_testresultinteger.resultfieldid AS irfi, ovt_testresultinteger.testresultinteger,\n".
            "     ovt_testresultfloat.resultfieldid AS frfi, ovt_testresultfloat.testresultfloat,\n".
            "     ovt_testresultboolean.resultfieldid AS brfi, ovt_testresultboolean.testresultboolean,\n";
  }
  
  if ($options['showversions'])
  {
    $sql .="      t2.testname || ':' || vt2.versionname AS name,\n";
  }
  else
  {
    $sql .= "     t2.testname AS name, \n";
  }

  $sql .= "       trtres.passed,\n".
          "       trtres.testruntestid,\n".
          "       trtres.testrunid AS resulttestrunid,\n".
          "       ovt_testrunaction.testrunid,\n".
          "       ovt_testrunaction.recursiveequivalenceid,\n".
          "       vt2.".$resultindexfield." AS resultindex\n".
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid)\n".
          "     INNER JOIN ovt_action USING (actionid)\n".
          "     INNER JOIN ovt_testrunaction AS trabuild USING (subrecursiveequivalenceid)\n".
          "     INNER JOIN ovt_testruntest AS trtvers ON (trabuild.testrunid=trtvers.testrunid)\n".
          "     INNER JOIN ovt_versionedtest AS vt2 ON (vt2.versionedtestid=trtvers.versionedtestid)\n".
          "     INNER JOIN ovt_test AS t2 ON (vt2.testid=t2.testid)\n".
          "     INNER JOIN ovt_testruntest AS trtres ON (vt2.versionedtestid=trtres.versionedtestid)\n".
          "     INNER JOIN ovt_testrunaction AS trasim ON (trtres.testrunid=trasim.testrunid\n".
          "                                                AND trasim.simpleequivalenceid=ovt_testrunaction.simpleequivalenceid)\n";

  if ($options['showextended'])
  {
    $sql .= "     LEFT OUTER JOIN ovt_testresultstring ON (ovt_testresultstring.testruntestid=trtres.testruntestid)\n".
            "     LEFT OUTER JOIN ovt_testresultboolean ON (ovt_testresultboolean.testruntestid=trtres.testruntestid)\n".
            "     LEFT OUTER JOIN ovt_testresultinteger ON (ovt_testresultinteger.testruntestid=trtres.testruntestid)\n".
            "     LEFT OUTER JOIN ovt_testresultfloat ON (ovt_testresultfloat.testruntestid=trtres.testruntestid)\n";
  }

  $sql .= "WHERE t2.testsuiteid='".$testsuiteid."'\n".
          "AND ovt_action.testsuiteid='".$testsuiteid."'\n".
          "AND ovt_testrunaction.testrunid IN ".$testrunidset."\n";

  if (!$options['enableinference'])
  {
    $sql .= "AND ovt_testrunaction.testrunid=trtres.testrunid\n";
    $sql .= "AND ovt_testrunaction.testrunid=trasim.testrunid\n";
    $sql .= "AND ovt_testrunaction.testrunid=trtvers.testrunid\n";
    $sql .= "AND ovt_testrunaction.testrunid=trabuild.testrunid";
  }

  $timings['resultsql']['start'] = microtime(true);
  $resultvalues = pg_query($ovtDB, $sql);
  $timings['resultsql']['end'] = microtime(true);
  $timings['resultsql']['extra'] = $sql;

  /* Store a list of fields associated with any test such that their names and
   * ordering can be extracted later. It is faster to fetch the fields using
   * their ids than re-run a query similar to the one below */
  $allfieldids = array();

  /* Store a list of test name(+version) to resultindex translations. It is
   * faster to fetch this information in one query than run multiple similar
   * queries. This results in more I/O to the database but less processing
   * time overall */
  $tests = array();

  /* Populate the internal data structure for test results */
  $timings['resultarray']['start'] = microtime(true);
  for ($j = 0 ; $j < pg_num_rows($resultvalues) ; $j++)
  {
    $fetcharray = pg_fetch_array($resultvalues, $j);
    $resultindex = $fetcharray['resultindex'];

    if (!array_key_exists($fetcharray['name'], $tests))
    {
      $tests[$fetcharray['name']] = $resultindex;
    }

    if (!array_key_exists($resultindex, $resarray))
    {
      $resarray[$resultindex] = array();
    }
    $testrunid = $fetcharray['testrunid'];
    $resulttestrunid = $fetcharray['resulttestrunid'];
    $reid = $fetcharray['recursiveequivalenceid'];
    if ($options['showextended'] && $fetcharray['srfi'] != NULL && $fetcharray['testresultstring'] != NULL)
    {
      $rfi = $fetcharray['srfi'];
      if (!in_array($rfi, $allfieldids))
      {
        $allfieldids[] = $rfi;
      }
      $value = $fetcharray['testresultstring'];
      updateResults($resarray[$resultindex], $rfi, $reid, $testrunid, $resulttestrunid, $value);
    }
    if ($options['showextended'] && $fetcharray['irfi'] != NULL && $fetcharray['testresultinteger'] != NULL)
    {
      $rfi = $fetcharray['irfi'];
      if (!in_array($rfi, $allfieldids))
      {
        $allfieldids[] = $rfi;
      }
      $value = (int)$fetcharray['testresultinteger'];
      updateResults($resarray[$resultindex], $rfi, $reid, $testrunid, $resulttestrunid, $value);
    }
    if ($options['showextended'] && $fetcharray['frfi'] != NULL && $fetcharray['testresultfloat'] != NULL)
    {
      $rfi = $fetcharray['frfi'];
      if (!in_array($rfi, $allfieldids))
      {
        $allfieldids[] = $rfi;
      }
      $value = (float)$fetcharray['testresultfloat'];
      updateResults($resarray[$resultindex], $rfi, $reid, $testrunid, $resulttestrunid, $value);
    }
    if ($options['showextended'] && $fetcharray['brfi'] != NULL && $fetcharray['testresultboolean'] != NULL)
    {
      $rfi = $fetcharray['brfi'];
      if (!in_array($rfi, $allfieldids))
      {
        $allfieldids[] = $rfi;
      }
      $value = ($fetcharray['testresultboolean'] == "t");
      updateResults($resarray[$resultindex], $rfi, $reid, $testrunid, $resulttestrunid, $value);
    }

    if ($resulttestrunid != $testrunid)
    {
      $resarray[$resultindex]["pass"][$reid]["reg".$testrunid][$resulttestrunid] = ($fetcharray['passed'] == "t");
    }
    else
    {
      $resarray[$resultindex]["pass"][$reid][$testrunid] = ($fetcharray['passed'] == "t");
    }
  }

  /* Sort the test names alphanumerically */
  ksort($tests);

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
  
  /* Iterate over the tests in order */
  $test_keys = array_keys($tests);
  foreach ($tests as $testname => $resultindex)
  {
    $grouptime = microtime(true);
    $actionarray = $resarray[$resultindex];

    /* Recalculate fields if tests are unique */
    if ($options['uniquetests'])
    {
      $allfieldids = array();
      foreach ($actionarray as $rfi => $value)
      {
        if (is_integer($rfi))
        {
          $allfieldids[] = $rfi;
        }
      }
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
    }

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
        if (array_key_exists($reid, $actionarray["pass"]))
        {
          /* First check to see if there is an actual result submitted for this testrun */
          if (array_key_exists($testrunid, $actionarray["pass"][$reid]))
          {
            /* Hideous structure dereference! */
            $value = $actionarray["pass"][$reid][$testrunid];
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
          /* Secondly check for an iterate through and inferred results taken from other testruns */
          if (array_key_exists("reg".$testrunid, $actionarray["pass"][$reid]))
          {
            /* Hideous structure dereference! The 'reg' stands for regression as in regression test */
            $valuedict = $actionarray["pass"][$reid]["reg".$testrunid];
            $keys = array_keys($valuedict);

            /* Look at each inferred result in turn. */
            for ($j = 0 ; $j < count($keys) ; $j++)
            {
              $value = $valuedict[$keys[$j]];

              /* Regression test results have the same standing as all others */
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
          }
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
    $options['output']['escape']($testname);
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

      if (!array_key_exists($reid, $actionarray["pass"]) ||
          (!array_key_exists($testrunid, $actionarray["pass"][$reid]) &&
           !array_key_exists("reg".$testrunid, $actionarray["pass"][$reid])))
      {
        $allresults = false;
        $mergedata .="_";
      }
      else
      {
        $currentExtended = array();
        for ($j = 0 ; $options['showextendedgroups'] && $j < pg_num_rows($allfields) ; $j++)
        {
          $rfi = pg_fetch_result($allfields, $j, "resultfieldid");
          if (array_key_exists($rfi, $actionarray) &&
              array_key_exists($reid, $actionarray[$rfi]) &&
              array_key_exists($testrunid, $actionarray[$rfi][$reid]))
          {
            /* WORK NEEDED: regression results for extended results */
            $currentExtended[$rfi] = $actionarray[$rfi][$reid][$testrunid];
          }
        }

        if (array_key_exists($testrunid, $actionarray["pass"][$reid]))
        {
          $tempresultstate = $actionarray["pass"][$reid][$testrunid];
          $mergedata .= ($tempresultstate?"P":"F");
          if ($resultstate !== NULL && $tempresultstate != $resultstate)
          {
            $resultsvary = true;
          }
          $resultstate = $tempresultstate;
        }

        if (array_key_exists("reg".$testrunid, $actionarray["pass"][$reid]))
        {
          $regdata = $actionarray["pass"][$reid]["reg".$testrunid];
          $keys = array_keys($regdata);
          for ($k = 0 ; $k < count($regdata) ; $k++)
          {
            $tempresultstate = $regdata[$keys[$k]];
            $mergedata .= ($tempresultstate?"Q":"G");
            if ($resultstate !== NULL && $resultstate != $tempresultstate)
            {
              $resultsvary = true;
            }
            $resultstate = $tempresultstate;
          }
        }

        /* Try to find a testrun that had identical extended results */
        $foundExt = false;
        for ($exi = 0 ;$exi < count($extended) ; $exi++)
        {
          if (count(array_diff_assoc($extended[$exi], $currentExtended)) == 0 &&
              count(array_diff_assoc($currentExtended, $extended[$exi])) == 0)
          {
            $foundExt = true;
            break;
          }
        }
        if (!$foundExt)
        {
          $extendedVersion++;
          $extended[] = $currentExtended;
        }
        if ($options['showextendedgroups'])
        {
          $mergedata .= $options['output']['superscript']($exi);
        }
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
  
    for ($j = 0 ; $options['showextended'] && $j < pg_num_rows($allfields) ; $j++)
    {
      $comparereid = NULL;
      for ($tr = 0 ; $tr < count($testrunids) ; $tr++)
      {
        $testrunid = $testrunids[$tr]['testrunid'];
        $reid = $testrunids[$tr]['reid'];

        $class="userresult";
        if ($j == pg_num_rows($allfields)-1 && $tr == count($testrunids)-1)
        {
          $class="lastuserresult";
        }
        $options['output']['begin_cell']($class, $colors[$tr%2], 1, "onmouseover=\"loadTestrunInfoTooltip('".$testrunid."');\" onmouseout=\"HideTip();\"");
        $rfi = pg_fetch_result($allfields, $j, "resultfieldid");
        if (array_key_exists($rfi, $actionarray) &&
            array_key_exists($reid, $actionarray[$rfi]) &&
            array_key_exists($testrunid, $actionarray[$rfi][$reid]))
        {

          /* use the first set of results as the basis for deltas. This needs to be configurable eventually */
          if ($comparereid === NULL)
          {
            $comparereid = $reid;
            $comparetestrunid = $testrunid;
          }
          if (pg_fetch_result($allfields, $j, "resulttypename") == "boolean")
          {
            if ($actionarray[$rfi][$reid][$testrunid])
            {
              $options['output']['pass']();
            }
            else
            {
              $options['output']['fail']();
            }
          }
          else
          {
            if ($options['showdeltas'] && (pg_fetch_result($allfields, $j, "resulttypename") == "integer"
                                           || pg_fetch_result($allfields, $j, "resulttypename") == "float")
                                       && array_key_exists($comparereid,$actionarray[$rfi]))
            {
              $options['output']['escape'](round(($actionarray[$rfi][$reid][$testrunid]
                                                  / $actionarray[$rfi][$comparereid][$comparetestrunid])
                                                  * 100, 2) . "%");
            }
            else
            {
              $options['output']['escape']($actionarray[$rfi][$reid][$testrunid]);
            }
          }
        }
        else
        {
          $options['output']['no_result']();
        }
        $options['output']['end_cell']();
      }
    }
  
    $options['output']['end_row']();

    if ($options['uniquetests'] && $testname != $test_keys[count($test_keys) - 1])
    {
      output_table_footer($finalgrouplist, $testrunids, $allfields, $options);
      $options['output']['end_table']();

      $options['output']['newline']();

      $options['output']['begin_table']();

      output_group_headings($group_json, $testrunids, $options);
    }
  }
  $timings['tableoutput']['end'] = microtime(true);
  $timings['tableoutput']['extra'] = "";

  output_table_footer($finalgrouplist, $testrunids, $allfields, $options);

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
