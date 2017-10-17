<?php
  include_once('includes.inc');
  include_once('dot.inc');

  htmlHeader("View Testrun", "startTimer();");
  include_once('testrun_control.inc');
  $testrunid = $_REQUEST['testrunid'];
?>
  <script language="javascript">
  var testrunid=<?php echo isset($testrunid)?$testrunid:0; ?>;
  
  var waitcount=0;

  var refreshcount = 0;

  function wait()
  {
  }

  function endwait()
  {
  }

  function refresh()
  {
    Element.writeAttribute('testrunimage',"src", "gentestrunimage.php?type=png&testrunid=<?php echo $testrunid;?>&c="+refreshcount.toString());
    wait();
    new Ajax.Updater('testrun', 'viewtestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'testrunmap',
                                    testrunid:testrunid },
                       onComplete: function(transport) { endwait(); } });



    wait();
    refreshcount++;
    new Ajax.Updater('statusinfo', 'viewtestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'statusinfo',
                                    testrunid:testrunid },
                       onComplete: function(transport) { endwait(); } });
  }

  function setEquivalenceName(field, type, testrunactionid)
  {
    wait();
    new Ajax.Updater('ErrorMessage', 'viewtestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'setequivalencename',
                                    testrunactionid:testrunactionid,
                                    type: type,
                                    value: field.value },
                       onComplete: function(transport) { endwait(); } });
  }

  function viewresult(testrunactionid)
  {
    viewresultauto(testrunactionid, false);
  }

  function viewresultauto(testrunactionid, showautomatic)
  {
    wait();
    if (showautomatic)
    {
      showautomatic = "1";
    }
    else
    {
      showautomatic = "0";
    }
    new Ajax.Updater('resultinfo', 'viewtestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'resultinfo',
                                    testrunid:testrunid,
                                    showautomatic:showautomatic,
                                    testrunactionid:testrunactionid},
                       onComplete: function(transport) { endwait(); } });

  }
  function startTimer()
  {
    refresh();
    setInterval ( "refresh()", 30000 );
  }
  
  </script>
<?php

  $sql = "SELECT ovt_testrungroup.testrungroupname, ovt_testrun.description AS testrunname,\n".
         "       ovt_runstatus.description AS runstatusdesc, ovt_testrun.userid, ovt_runstatus.*,\n".
	 "       ovt_testrun.autoarchive, ovt_testrun.usegridengine, ovt_testrun.gridjobid\n".
         "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)\n".
         "     LEFT OUTER JOIN ovt_testrungroup USING (testrungroupid)\n".
         "WHERE testrunid='".$testrunid."'";
  $result = pg_query($ovtDB, $sql);
  if (pg_num_rows($result) != 1)
  {
    echo "Testrun does not exist";
    exit(0);
  }
  $owner = isset($_SESSION['auth_userid']) && (pg_fetch_result($result, 0, "userid") == $_SESSION['auth_userid']);


  echo "<h1>View Testrun</h1>\n";
  echo "<h2>".htmlentities(pg_fetch_result($result, 0, "testrungroupname")) . " - " . htmlentities(pg_fetch_result($result, 0, "testrunname"))."</h2>\n";

  echo "<div style=\"width:120px; float: right; text-align:right\">\n";
  testrun_status($testrunid, $owner, pg_fetch_result($result, 0, "runstatusdesc"), "null");
  echo "</div>\n";
  echo "<div style=\"float: right\">\n";
  testrun_buttons($testrunid, $owner, pg_fetch_array($result, 0), 'null');
  echo "</div>\n";
  echo "<div id=\"statusinfo\">\n".
       "</div>\n";
  echo "<div id=\"staticinfo\">\n".
       "This testrun will ";
  if (pg_fetch_result($result, 0, "autoarchive") == 'f')
  {
    echo "not ";
  }
  echo "autoarchive";
  if (pg_fetch_result($result, 0, "usegridengine") == 't')
  {
    $jobid = pg_fetch_result($result, 0, "gridjobid");
    if ($jobid === null)
      echo " and will run in the grid engine";
    else
      echo " and is running as grid engine job $jobid";
  }
  echo "</div>\n";

  echo "<div id=\"testrunmap\" style=\"display:none\">\n".
       "<map id=\"testrun\" name=\"testrun\">\n".
       "</map>\n".
       "</div>\n";
  echo "<img id=\"testrunimage\" src=\"images/loading.png\" USEMAP=#testrun><br />\n";
  echo "<div id=\"resultinfo\">\n".
       "</div>\n";
  popover();
  htmlFooter();
?>
