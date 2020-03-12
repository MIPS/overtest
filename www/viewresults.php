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

include_once('inc/includes.inc');
include_once('inc/search_testruns.inc');

$startup = "";
if (isset($_REQUEST['testrunactionid']))
{
  $sql = "SELECT ovt_testrunaction.testrunid, ovt_action.testsuiteid,\n".
         "       ovt_action.actionid, ovt_action.actionname\n".
         "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid)\n".
         "     INNER JOIN ovt_action USING (actionid)\n".
         "     INNER JOIN ovt_testrun USING (testrunid)\n".
         "     INNER JOIn ovt_user USING (userid)\n".
         "WHERE testrunactionid='".$_REQUEST['testrunactionid']."'";
  $result = pg_query($ovtDB, $sql);
  $testsuiteid = pg_fetch_result($result, 0, "testsuiteid");
  $testrunid = pg_fetch_result($result, 0, "testrunid");

  $startup = "searchfield='Testrun';search3='".$testrunid."';addSearchTerm(true);";

}
else
{
  $testsuiteid = $_REQUEST['testsuiteid'];
}

if (isset($_REQUEST['search_terms']))
{
  $startup = "initTerms();";
}

htmlHeader("Analyze results", $startup." initOptions();", "http://k3/imgwiki/cgi-bin/imgwiki.pl?OverTestWebInterface/ResultsAnalysis");

$showextended = false;
$showextendedgroups = false;
$showversions = false;
$enableinference = false;
$resultstability = "unstable";
$resultsinclude = "any";
$stabilitylevel = "all";
$showdeltas = false;
if (isset($_REQUEST['show']))
{
  $showstrings = explode(",", $_REQUEST['show']);
  foreach ($showstrings as $showstring)
  {
    if (substr($showstring, 0, 3) == "lev")
    {
      $stabilitylevel = substr($showstring, 3);
      continue;
    }
    switch ($showstring)
    {
    case "unstable":
    case "stable":
    case "any":
    case "different":
      $resultstability = $showstring;
      break;
    case "pass":
    case "fail":
      $resultsinclude = $showstring;
      break;
    case "extended":
      $showextended = true;
      break;
    case "extendedgroups":
      $showextendedgroups = true;
      break;
    case "versions":
      $showversions = true;
      break;
    case "inference":
      $enableinference = true;
      break;
    case "deltas":
      $showdeltas = true;
      break;
    }
  }
}

?>
<script type="text/javascript" src="tooltip.js"></script>
<script type="text/javascript" src="scripts/searchscript.js"></script>
<script language="JavaScript">

var waitcount=0;
var resultStability = '<?php echo $resultstability; ?>';
var resultsInclude = '<?php echo $resultsinclude; ?>';
var stabilityLevel = '<?php echo $stabilitylevel; ?>';
var showExtended = <?php echo ($showextended)?'true':'false'; ?>;
var showExtendedGroups = <?php echo ($showextendedgroups)?'true':'false'; ?>;
var showVersions = <?php echo ($showversions)?'true':'false'; ?>;
var showDeltas = <?php echo ($showdeltas)?'true':'false'; ?>;
var enableInference = <?php echo ($enableinference)?'true':'false'; ?>;
var testsuiteid = <?php echo $testsuiteid; ?>;

<?php
if (isset($_REQUEST['search_terms']) || isset($_REQUEST['group_terms']))
{
?>

  function initTerms()
  {
<?php
  if (isset($_REQUEST['search_terms']))
  {
    echo "    myFilterTerms='". $_REQUEST['search_terms']. "'.evalJSON();";
    if (isset($_REQUEST['group_terms']))
    {
      echo "    updateFilterTerms(false);";
    }
    else
    {
      echo "    updateFilterTerms(true);";
    }
  }
  if (isset($_REQUEST['group_terms']))
  {
    echo "    myGroupTerms='". $_REQUEST['group_terms']. "'.evalJSON();";
    echo "    updateGroupTerms(true);";
  }

?>
  }
<?php
}
?>

function initOptions()
{
  if ($F($("showunstable")) != null || $F($("showdifferent")) != null)
  {
    /* Unstable results cannot be restricted to pass/fail */
    $("showincludingfail").setValue(false);
    $("showincludingfail").disable();
    $("showincludingpass").setValue(false);
    $("showincludingpass").disable();
    $("showincludingany").setValue(true);
  }
  if ($F($("showany")) != null)
  {
    $("showstabilitylevel").disable();
  }
}

function getShowString()
{
  showstring=resultStability;
  if (stabilityLevel != 'all') showstring += ',lev'+stabilityLevel;
  if (resultsInclude != 'any') showstring += ','+resultsInclude;
  if (showExtended) showstring += ',extended';
  if (showExtendedGroups) showstring += ',extendedgroups';
  if (showVersions) showstring += ',versions';
  if (enableInference) showstring += ',inference';
  if (showDeltas) showstring += ',deltas';

  return showstring;
}
function checkBracketsCallback()
{
  showstring = getShowString();

  $('perma_link').writeAttribute("href",'viewresults.php?testsuiteid='+testsuiteid+'&search_terms='+Object.toJSON(myFilterTerms)+'&group_terms='+Object.toJSON(myGroupTerms)+'&show='+showstring);
}

function getResults()
{
  wait();
  setSearching();
  $('tab_link').show();

  showstring = getShowString();

  $('tab_link').writeAttribute("href",'viewresultsajax.php?what=resulttable&output=tab&searchstring='+Object.toJSON(myFilterTerms)+'&groupstring='+Object.toJSON(myGroupTerms)+'&show='+showstring+'&testsuiteid='+testsuiteid);

  new Ajax.Updater('resultdiv', 'viewresultsajax.php',
                   { method: 'post',
                     parameters: {what: 'resulttable',
                                  output: 'html',
                                  searchstring: Object.toJSON(myFilterTerms),
                                  groupstring: Object.toJSON(myGroupTerms),
                                  show: showstring,
                                  testsuiteid: testsuiteid},
                     onComplete: function(transport) { 
                              $('search_results_button_text').setStyle({backgroundColor: 'transparent',
                                                                        textDecoration: 'underline', 
                                                                        fontWeight:'normal'});
                              $('search_results_button_text').update('UPDATE');
                              endwait(); } });
}

function wait()
{
  $("main").setStyle({cursor:"wait"});
  waitcount++;
}
function endwait()
{
  waitcount--;
  if (waitcount == 0)
  {
    $("main").setStyle({cursor:"auto"});
  }
}

function loadTestrunInfoTooltip(testrunid)
{
  ShowTip('Loading ...');
  wait();
  new Ajax.Updater('ttip', 'viewresultsajax.php',
                   { method: 'post',
                     parameters: {what: 'testruninfo',
                                  testrunid: testrunid},
                     onComplete: function(transport) { endwait(); } });

}
function toggleShowDeltas(checked)
{
  showDeltas = checked;
  setSearchDirty();
  if (checkBrackets())
  {
    getResults();
  }
}
function toggleShowVersions(checked)
{
  showVersions = checked;
  setSearchDirty();
  if (checkBrackets())
  {
    getResults();
  }
}
function toggleEnableInference(checked)
{
  enableInference = checked;
  setSearchDirty();
  if (checkBrackets())
  {
    getResults();
  }
}

function toggleShowExtendedGroups(checked)
{
  showExtendedGroups = checked;
  setSearchDirty();
  if (checkBrackets())
  {
    getResults();
  }
}
function toggleShowExtended(checked)
{
  showExtended = checked;
  setSearchDirty();

  if (checkBrackets())
  {
    getResults();
  }
}
function updateShowFilter(which)
{
  stabilityLevel = $F($("showstabilitylevel"));
  resultStability = $F($("showany"));
  if (resultStability == null)
  {
    resultStability = $F($("showstable"));
    $("showstabilitylevel").enable();
  }
  else
  {
    $("showstabilitylevel").disable();
  }
  if (resultStability == null)
  {
    $("showincludingfail").setValue(false);
    $("showincludingpass").setValue(false);
    $("showincludingpass").disable();
    $("showincludingfail").disable();
    $("showincludingany").setValue(true);
    resultStability = $F($("showunstable"));
    if (resultStability == null)
    {
      resultStability = $F($("showdifferent"));
    }
  }
  else
  {
    $("showincludingpass").enable();
    $("showincludingfail").enable();
  }

  resultsInclude = 'any';
  if ($F($("showincludingpass")) == 'pass')
  {
    resultsInclude = 'pass';
  }
  if ($F($("showincludingfail")) == 'fail')
  {
    resultsInclude = 'fail';
  }
  setSearchDirty();

  if (checkBrackets())
  {
    getResults();
  }
}

function searchClick()
{
  if (waitcount == 0)
  {
    search();
  }
  else
  {
    alert("Search in progress");
  }
}

function search()
{
  setSearching();
  getResults();
}
function setSearching()
{
  $('search_results_button_text').setStyle({backgroundColor: 'orange',
                                            textDecoration: 'blink', 
                                            fontWeight:'bold'});
  $('search_results_button_text').update('UPDATING');

}
function setSearchDirty()
{
  $('tab_link').hide();
  $('search_results_button_text').setStyle({backgroundColor: 'red',
                                       textDecoration: 'blink', 
                                       fontWeight:'bold'});
}
</script>
<?php

$sql = "SELECT testsuitename\n".
       "FROM ovt_testsuite\n".
       "WHERE testsuiteid='".$testsuiteid."'";
$result = pg_query($ovtDB, $sql);
echo "<h1>Analyze ".pg_fetch_result($result, 0, "testsuitename")." testsuite results</h1>\n";

echo "<fieldset>\n".
     "<legend>Results search</legend>\n";

search_options($ovtDB, $testsuiteid);

echo "<fieldset style=\"width:600px\">\n";
echo "<legend>Options</legend>\n";
echo "<form style=\"margin:0, padding:0\" method=\"post\" action=\"#\">\n";
echo "<table>\n".
     "<tr style=\"vertical-align:top\"><td>\n";
echo "<input type=\"radio\" id=\"showany\" name=\"resultstability\" value=\"any\" onclick=\"updateShowFilter(null);\"";
if ($resultstability == "any")
{
  echo " checked";
}
echo "> Any results<br />\n";
echo "<input type=\"radio\" id=\"showunstable\" name=\"resultstability\" value=\"unstable\" onclick=\"updateShowFilter(null);\"";
if ($resultstability == "unstable")
{
  echo " checked";
}
echo "> Unstable results<br />\n";
echo "<input type=\"radio\" id=\"showdifferent\" name=\"resultstability\" value=\"different\" onclick=\"updateShowFilter(null);\"";
if ($resultstability == "different")
{
  echo " checked";
}
echo "> Different results<br />\n";
echo "<input type=\"radio\" id=\"showstable\" name=\"resultstability\" value=\"stable\" onclick=\"updateShowFilter(null);\"";
if ($resultstability == "stable")
{
  echo " checked";
}
echo "> Stable results<br />\n";
echo "Apply in group:<br />\n";
echo "<select id=\"showstabilitylevel\" name=\"stabilitylevel\" onchange=\"updateShowFilter(null);\">\n".
     "<option value=\"all\">Top Level</option>\n";
echo "</select>\n";

echo "</td><td>\n";
echo "<input type=\"radio\" id=\"showincludingpass\" name=\"resultsinclude\" value=\"pass\" onclick=\"updateShowFilter(this.value);\"";
if ($resultsinclude == "pass")
{
  echo " checked";
}
echo "> Including passes<br />\n";
echo "<input type=\"radio\" id=\"showincludingfail\" name=\"resultsinclude\" value=\"fail\" onclick=\"updateShowFilter(this.value);\"";
if ($resultsinclude == "fail")
{
  echo " checked";
}
echo "> Including failures<br />\n";
echo "<input type=\"radio\" id=\"showincludingany\" name=\"resultsinclude\" value=\"any\" onclick=\"updateShowFilter(this.value);\"";
if ($resultsinclude != "fail" && $resultsinclude != "pass")
{
  echo " checked";
}
echo "> Including any<br />\n";

echo "</td><td>\n";
echo "<input type=\"checkbox\" name=\"showextended\" onclick=\"toggleShowExtended(this.checked);\"";
if ($showextended)
{
  echo " checked";
}
echo "> Show extended results<br />\n";
echo "<input type=\"checkbox\" name=\"showextendedgroups\" onclick=\"toggleShowExtendedGroups(this.checked);\"";
if ($showextendedgroups)
{
  echo " checked";
}
echo "> Show extended result groups<br />\n";
echo "<input type=\"checkbox\" name=\"showdeltas\" onclick=\"toggleShowDeltas(this.checked);\"";
if ($showdeltas)
{
  echo " checked";
}
echo "> Show deltas<br />\n";
echo "<input type=\"checkbox\" name=\"showversions\" onclick=\"toggleShowVersions(this.checked);\"";
if ($showversions)
{
  echo " checked";
}
echo "> Show versions<br />\n";
echo "<input type=\"checkbox\" name=\"enableinference\" onclick=\"toggleEnableInference(this.checked);\"";
if ($enableinference)
{
  echo " checked";
}
echo "> Enable inference<br />\n";


echo "</td></tr>\n".
     "</table>";
echo "</form>\n";
search_buttons();
echo "</fieldset>\n";
echo "</fieldset>\n";

echo "<h2>Results</h2><br />\n";
echo "<div id=\"resultdiv\">\n".
     "Please select at least one filter.".
     "</div><br />\n";

htmlFooter();
?>
