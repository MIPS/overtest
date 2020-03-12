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
  include_once('includes.inc');
  // Check that this testrun can be modified
  
  $sql = "SELECT count(ovt_testrun.testrunid) AS editcount, ovt_testrungroup.testrungroupname\n".
         "FROM ovt_testrun LEFT OUTER JOIN ovt_testrungroup USING (testrungroupid)\n".
         "     INNER JOIN ovt_runstatus USING (runstatusid)\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE ovt_testrun.testrunid='".$_REQUEST['testrunid']."'\n";
    $title = "Modify Testrun";
    $jsfield = "testrunid";
  }
  else
  {
    $sql .="WHERE ovt_testrun.testrungroupid='".$_REQUEST['testrungroupid']."'\n";
    $title = "Modify Testruns In Group";
    $jsfield = "testrungroupid";
  }
  $sql .="AND ovt_runstatus.iseditable\n".
         "GROUP BY ovt_testrungroup.testrungroupname";

  $result = pg_query($ovtDB, $sql);

  htmlHeader($title, "getCategories();getInitialConfig();", "http://k3/imgwiki/cgi-bin/imgwiki.pl?OverTestWebInterface/TestInstantiation");
  $iseditable = false;
  if (pg_num_rows($result) == 0 || pg_fetch_result($result, 0, "editcount") == 0)
  {
    if (isset($_REQUEST['testrunid']))
    {
      echo "<h1>Unable to edit testrun</h1>\n";
      echo "This testrun is no longer editable<br />\n";
    }
    else
    {
      echo "<h1>Unable to edit testrun group</h1>\n";
      echo "There are no editable testruns in this group<br />\n";
    }
  }
  else
  {
    $iseditable = true;
    echo "<h1>Modify testrun(s) in '".htmlentities(pg_fetch_result($result, 0, "testrungroupname"))."'</h1>\n";
  }
?>
<script type="text/javascript" src="tooltip.js"></script>
<script language="JavaScript">
var <?php echo $jsfield;?>=<?php echo isset($_REQUEST[$jsfield])?$_REQUEST[$jsfield]:0; ?>;

var configchanged = false;
var detailshavechanged = false;

var waitcount=0;

function updateCategories(value)
{
  getCategories();
}

function updateActions(value)
{
  getActions($F('category'));
}

function updateVersions(value)
{
  getVersions($F('action'));
}

function getCategories()
{
  wait();
  $('categories').update("<b>Loading...</b>");
  new Ajax.Updater('categories', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'categories',
                                  showall: $F("showallcategories") ? 1 : 0 },
                     onComplete: function(transport) { endwait(); } });
  $('actions').update("");
  $('versions').update("");
}
function getInitialConfig()
{
  wait();
  wait();
  new Ajax.Updater('testrun', 'edittestrunajax.php', 
                   { method: 'get',
                     parameters: {what: 'testrun',
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>}, 
                     onComplete: function(transport) { endwait(); } });
  new Ajax.Updater('resourcerequirements', 'edittestrunajax.php', 
                   { method: 'get',
                     parameters: {what: 'resourcerequirements',
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>}, 
                     onComplete: function(transport) { endwait(); } });
 
  getResourceTypes();
  refreshConfig();
}

function getResourceTypes()
{
  wait();
  $('attributes').update("<b>Attributes</b>");
  $('attributevalues').update("<b>Attribute Values</b>");
  new Ajax.Updater('resourcetypes', 'edittestrunajax.php', 
                   { method: 'get',
                     parameters: {what: 'resourcetypes',
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>}, 
                     onComplete: function(transport) { endwait(); } });


}

function configsettingchanged()
{
  configchanged = true;
}
function detailschanged()
{
  detailshavechanged = true;
}

function wait()
{
  Form.disable($("testrunform"));
  $("main").setStyle({cursor:"wait"});
  waitcount++;
}
function endwait()
{
  waitcount--;
  if (waitcount == 0)
  {
    Form.enable($("testrunform"));
    $("main").setStyle({cursor:"auto"});
  }
}

function getActions(actioncategoryid)
{
  wait();
  $('actions').update("<b>Loading...</b>");
  $('versions').update("");
  new Ajax.Updater('actions', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'actions',
                                  actioncategoryid:actioncategoryid,
                                  showall: $F("showallactions") ? 1 : 0 },
                     onComplete: function(transport) { endwait(); } });
}

function getVersions(actionid)
{
  var showallversions = $F("showallversions") ? 1 : 0;
  if (actionid.substr(0, 4) == 'more')
  {
    offset = actionid.substr(4);
    wait();
    $('actions').update("<b>Loading...</b>");
    $('versions').update("<b>Versions</b>");
    new Ajax.Updater('actions', 'edittestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'actions',
                                    offset: offset,
                                    actioncategoryid:$F('category'),
                                    showall: showallversions },
                       onComplete: function(transport) { endwait(); } });

  }
  else
  {
    wait();
    $('versions').update("<b>Loading...</b>");
    new Ajax.Updater('versions', 'edittestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'versions',
                                    actionid:actionid,
                                    showall: showallversions },
                       onComplete: function(transport) { endwait(); } });
  }
}

function getDependencies(versionedactionid)
{
  wait();
  $('dependencies').update("<b>Loading...</b>");
  new Ajax.Updater('dependencies', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'dependencies', 
                                  versionedactionid:versionedactionid},
                     onComplete: function(transport) { endwait(); } });

}

function getConfigOptions(configoptiongroupid, versionedactionid)
{
  wait();
  $('setting').update("<b>Setting</b>");
  $('configoptions').update("<b>Loading...</b>");
  new Ajax.Updater('configoptions', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'configoptions', 
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>,
                                  configoptiongroupid:configoptiongroupid},
                     onComplete: function(transport) { endwait(); } });


}

function getConfigSetting(configoptionid, versionedactionid)
{
  wait();
  $('setting').update("<b>Loading...</b>");
  configchanged = false;
  new Ajax.Updater('setting', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'setting', 
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>,
                                  configoptionid:configoptionid},
                     onComplete: function(transport) { endwait(); } });


}
function checkandsavedetails(type, value)
{
  if (detailshavechanged)
  {
    wait();
    new Ajax.Updater('ErrorMessage', 'edittestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'save'+type,
                                    <?php echo $jsfield;?>:<?php echo $jsfield;?>,
                                    value:value},
                       onComplete: function(transport) { endwait(); } });
    detailshavechanged = false;
  }
}

function checkandsaveconfig(value, configoptionid)
{
  if (configchanged)
  {
    wait();
    new Ajax.Updater('ErrorMessage', 'edittestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'saveconfig',
                                    <?php echo $jsfield;?>:<?php echo $jsfield;?>,
                                    value:value,
                                    configoptionid:configoptionid},
                       onComplete: function(transport) { endwait(); } });
    configchanged = false;
  }
}


function getAttributes(resourcetypeid)
{
  $('attributevalues').update("");
  $('attributes').update("<b>Loading...</b>");
  wait();
  new Ajax.Updater('attributes', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'attributes', 
                                  resourcetypeid:resourcetypeid},
                     onComplete: function(transport) { endwait(); } });
}

function getAttributeValues(attributeid)
{
  $('attributevalues').update("<b>Loading...</b>");
  wait();
  new Ajax.Updater('attributevalues', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'attributevalues', 
                                  attributeid:attributeid},
                     onComplete: function(transport) { endwait(); } });
}


function addVersionedAction(versionedactionid)
{
  wait();
  $('ErrorMessage').update("");
  refreshConfig(true);
  new Ajax.Updater('testrun', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'testrun', 
                                  versionedactionid:versionedactionid, 
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>},
                     onSuccess: function(transport) { getResourceTypes(); refreshConfig(false); }, 
                     onComplete: function(transport) { endwait(); } });
}

function refreshConfig(firstpart)
{
  if (firstpart)
  {
    $('configgroups').update("<b>Loading...</b>");
    $('configoptions').update("<b>Configuration Options</b>");
    $('setting').update("<b>Setting</b>");
  }
  else
  {
    wait();
    new Ajax.Updater('configgroups', 'edittestrunajax.php',
                     { method: 'get',
                       parameters: {what: 'configgroups', 
                                    <?php echo $jsfield;?>:<?php echo $jsfield;?>},
                       onComplete: function(transport) { endwait(); } });
  }
}

function addAttributeValue(attributevalueid)
{
  wait();
  $('ErrorMessage').update("");
  new Ajax.Updater('resourcerequirements', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'resourcerequirements', 
                                  attributevalueid:attributevalueid, 
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>},
                     onComplete: function(transport) { endwait(); } });

}

function removeVersionedAction(versionedactionid)
{
  wait();
  $('ErrorMessage').update("");
  $('dependencies').update("<b>Dependencies</b>");
  refreshConfig(true);
  new Ajax.Updater('testrun', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'testrun',
                                  versionedactionid:versionedactionid,
                                  remove:"1",
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>},
                     onSuccess: function(transport) { getResourceTypes(); refreshConfig(); }, 
                     onComplete: function(transport) { endwait(); } });
}
function removeAttributeValue(attributevalueid)
{
  wait();
  $('ErrorMessage').update("");
  new Ajax.Updater('resourcerequirements', 'edittestrunajax.php',
                   { method: 'get',
                     parameters: {what: 'resourcerequirements', 
                                  remove:"1",
                                  attributevalueid:attributevalueid, 
                                  <?php echo $jsfield;?>:<?php echo $jsfield;?>},
                     onComplete: function(transport) { endwait(); } });

}

<?php
echo "</script>\n";

if ($iseditable)
{
  echo "<form id=\"testrunform\">\n";
  echo "<h2>Step 1 - Testrun details</h2>\n";
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"testruninfo\">\n";

  $sql = "SELECT count(testrunid), priority\n".
         "FROM ovt_testrun\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE testrungroupid='".$_REQUEST['testrungroupid']."'\n";
  }
  $sql .="GROUP BY priority";
  
  $result = pg_query($ovtDB, $sql);
  $priority = "<various>";
  if (pg_num_rows($result) == 1)
  {
    $priority = pg_fetch_result($result, 0, "priority");
  }

  $sql = "SELECT count(testrunid), concurrency\n".
         "FROM ovt_testrun\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE testrungroupid='".$_REQUEST['testrungroupid']."'\n";
  }
  $sql .="GROUP BY concurrency";
  
  $result = pg_query($ovtDB, $sql);
  $concurrency = "<various>";
  if (pg_num_rows($result) == 1)
  {
    $concurrency = pg_fetch_result($result, 0, "concurrency");
  }

  $sql = "SELECT count(testrunid), to_char(startafter,'YYYY/MM/DD HH24:MI') AS startafter\n".
         "FROM ovt_testrun\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE testrungroupid='".$_REQUEST['testrungroupid']."'\n";
  }
  $sql .="GROUP BY startafter";
  
  $result = pg_query($ovtDB, $sql);
  $startafter = "<various>";
  if (pg_num_rows($result) == 1)
  {
    $startafter = pg_fetch_result($result, 0, "startafter");
  }

  $sql = "SELECT count(testrunid), autoarchive\n".
         "FROM ovt_testrun\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE testrungroupid='".$_REQUEST['testrungroupid']."'\n";
  }
  $sql .="GROUP BY autoarchive";
  
  $result = pg_query($ovtDB, $sql);
  $autoarchive = "";
  if (pg_num_rows($result) == 1)
  {
    $autoarchive = pg_fetch_result($result, 0, "autoarchive");
  }

  $sql = "SELECT count(testrunid), usegridengine\n".
         "FROM ovt_testrun\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql .="WHERE testrunid='".$_REQUEST['testrunid']."'\n";
  }
  else
  {
    $sql .="WHERE testrungroupid='".$_REQUEST['testrungroupid']."'\n";
  }
  $sql .="GROUP BY usegridengine";
  
  $result = pg_query($ovtDB, $sql);
  $usegridengine = "";
  if (pg_num_rows($result) == 1)
  {
    $usegridengine = pg_fetch_result($result, 0, "usegridengine");
  }
 
  echo "<table border=0>\n".
       "<tr>\n";
  if (isset($_REQUEST['testrunid']))
  {
    echo "<th>Enter a description</th>\n";
  }
  echo "<th>Priority</th>\n".
       "<th>Concurrency</th>\n".
       "<th>Start date/time</th>\n".
       "<th>Auto Archive</th>\n".
       "<th>Use GridEngine</th>\n".
       "</tr>\n";
  echo "<tr>\n";
  if (isset($_REQUEST['testrunid']))
  {
    $sql = "SELECT description\n".
           "FROM ovt_testrun\n".
           "WHERE testrunid='".$_REQUEST['testrunid']."'";
    $result = pg_query($ovtDB, $sql);
    echo "<td><textarea class=\"textarea\" id=\"description\" name=\"description\" rows=1 cols=30 onkeydown=\"detailschanged();\" onblur=\"checkandsavedetails('description', this.value);\">\n".
         htmlentities(pg_fetch_result($result, 0, "description")).
         "</textarea></td>\n";
  }
  echo "<td align=\"center\">\n".
       "<input type=\"text\" class=\"textbox\" id=\"priority\" name=\"priority\" size=4 value=\"".$priority."\" onkeydown=\"detailschanged();\" onblur=\"checkandsavedetails('priority', this.value);\">\n".
       "</td>\n".
       "<td align=\"center\">\n".
       "<input type=\"text\" class=\"textbox\" id=\"concurrency\" name=\"concurrency\" size=4 value=\"".$concurrency."\" onkeydown=\"detailschanged();\" onblur=\"checkandsavedetails('concurrency', this.value);\">\n".
       "</td>\n".
       "<td align=\"center\">\n".
       "<input type=\"text\" class=\"textbox\" id=\"startafter\" name=\"startafter\" size=20 value=\"".$startafter."\" onkeydown=\"detailschanged();\" onblur=\"checkandsavedetails('start', this.value);\">\n".
       "</td>\n".
       "<td align=\"center\">\n".
       "<select id=\"autoarchive\" name=\"autoarchive\" onchange=\"detailschanged();checkandsavedetails('autoarchive', this.value);\">\n".
       "<option value=\"t\"";
  if ($autoarchive == "t")
  {
    echo " selected";
  }
  echo ">Yes</option>\n".
       "<option value=\"f\"";
  if ($autoarchive == "f")
  {
    echo " selected";
  }
  echo ">No</option>\n";
  if ($autoarchive == "")
  {
    echo "<option value=\"\" selected>Various</option>\n";
  }
  echo "</select>\n".
       "</td>\n".
       "<td align=\"center\">\n".
       "<select id=\"usegridengine\" name=\"usegridengine\" onchange=\"detailschanged();checkandsavedetails('usegridengine', this.value);\">\n".
       "<option value=\"t\"";
  if ($usegridengine == "t")
  {
    echo " selected";
  }
  echo ">Yes</option>\n".
       "<option value=\"f\"";
  if ($usegridengine == "f")
  {
    echo " selected";
  }
  echo ">No</option>\n";
  if ($usegridengine == "")
  {
    echo "<option value=\"\" selected>Various</option>\n";
  }
  echo "</select>\n".
       "</td>\n".

       "</tr>\n".
       "</table>\n";
  echo "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  
  
  echo "<p style=\"clear:both\"></p>\n";
  echo "<h2>Step 2 - Add the tests</h2>\n";
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\">\n".
       "<b>Categories</b><br />\n".
       "<input type=\"checkbox\" name=\"showallcategories\" id=\"showallcategories\" onclick=\"updateCategories();\"> Show hidden items<br />\n".
       "<div style=\"padding:5px\" id=\"categories\">\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\">\n".
       "<b>Actions</b><br />\n".
       "<input type=\"checkbox\" name=\"showallactions\" id=\"showallactions\" onclick=\"updateActions();\"> Show hidden items<br />\n".
       "<div id=\"actions\">\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\">\n".
       "<b>Versions</b><br />\n".
       "<input type=\"checkbox\" name=\"showallversions\" id=\"showallversions\" onclick=\"updateVersions();\"> Show hidden items<br />\n".
       "<div id=\"versions\">\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  echo "<p style=\"clear:both\"></p>\n";
  echo "<div style=\"margin: 0 10px 10px 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"testrun\">\n".
       "<b>Actions in testrun</b></br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  echo "<div style=\"margin: 0 10px 10px 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"dependencies\">\n".
       "<b>Dependencies</b><br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  
  echo "<p style=\"clear:both\"></p>\n";
  echo "<h2>Step 3 - Specify the configuration</h2>\n";
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"configgroups\">\n".
       "<b>Configuration Groups</b><br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"configoptions\">\n".
       "<b>Configuration Options</b><br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"setting\">\n".
       "<b>Setting</b><br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  echo "<p style=\"clear:both\"></p>\n";
  echo "<h2>Step 4 - Specify the resource requirements</h2>\n";
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"resourcetypes\">\n".
       "<b>Resource types</b><br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"attributes\">\n".
       "<b>Attributes</b><br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  echo "<div style=\"margin: 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"attributevalues\">\n".
       "<b>Attribute values</b><br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  
  echo "<p style=\"clear:both\"></p>\n";
  echo "<div style=\"margin: 0 10px 10px 10px; float:left\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:5px\" id=\"resourcerequirements\">\n".
       "<b>Resource requirements</b><br />\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n";
  
  
  echo "</form>\n";
  
  echo "<p style=\"clear:both\"></p>\n";
  if (isset($_REQUEST['testrunid']))
  {
    echo "<a href=\"gentestrunimage.php?type=png&testrunid=".$_REQUEST['testrunid']."\" target=\"_blank\">View dependency graph</a><br />\n";
    echo "<a href=\"php/doindex.php?what=go&amp;testrunid=".$_REQUEST['testrunid']."\">Start testrun</a>\n";
  }
  else
  {
    echo "<a href=\"php/doindex.php?what=go&amp;testrungroupid=".$_REQUEST['testrungroupid']."\">Start ALL testruns</a>\n";
  }
  echo "<a href=\"index.php\">Save for later</a>\n";
}
htmlFooter();
?>
