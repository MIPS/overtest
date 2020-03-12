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

htmlHeader("Welcome to overtest", "testrunsearch()", "http://k3/imgwiki/cgi-bin/imgwiki.pl?OvertestWebInterface");

include_once('testrun_control.inc');
?>

<script type="text/javascript">
function showHide(groupid)
{
  tbody = $('testrungroup'+groupid).select('tbody');
  showhide = $('testrungroup'+groupid).select('img[name="showhide"]');
  if (tbody[0].visible())
  {
    showhide[0].writeAttribute('src', 'images/toggle_expand.png');
    showhide[0].writeAttribute('alt', 'Expand');
  }
  else
  {
    showhide[0].writeAttribute('src', 'images/toggle.png');
    showhide[0].writeAttribute('alt', 'Collapse');
  }
  tbody[0].toggle();
}

function toggleSelectGroup(groupid)
{
  $('testrungroup'+groupid).select('input[type="checkbox"]').invoke('setValue', $('groupselect'+groupid).checked);
  if ($('groupselect'+groupid).checked)
  {
    $('groupcontrols'+groupid).show();
    $('groupblank'+groupid).hide();
  }
  else
  {
    $('groupcontrols'+groupid).hide();
    $('groupblank'+groupid).show();
  }
}

function getCheckedTestruns(groupid)
{
  trboxes = $('testrungroup'+groupid).select('input[type="checkbox"][name^="select"]');
  trchecked = trboxes.findAll(function(o)
                              {
                                return o.checked;
                              });
  ids = trchecked.map(function(o)
                      {
                        return o.getAttribute('name').substr(6);
                      });
  return ids;
}

function toggleSelect(testrunid, groupid)
{
  if (getCheckedTestruns(groupid).size())
  {
    $('groupcontrols'+groupid).show();
    $('groupblank'+groupid).hide();
  }
  else
  {
    $('groupcontrols'+groupid).hide();
    $('groupblank'+groupid).show();
  }
}

function editGroupName(tgid)
{
  $('group'+tgid).update('');
  $('editbox'+tgid).show();
  $('editbox'+tgid).focus();
}
function showGroupName(tgid)
{
  new Ajax.Updater('group'+tgid, 'php/doindex.php',
                   { method: 'get',
                     parameters: {what: 'updategroupname',
                                  testrungroupid:tgid,
                                  testrungroupname:$('editbox'+tgid).getValue()} });

  $('editbox'+tgid).hide();
}
function update_row_callback(testrunid, info, owner)
{
  if (info['editable'] && owner)
  {
    $$('#row'+testrunid+' td[onClick]').invoke('writeAttribute', 'onClick',
                                               'showtestrundetail(\'edittestrun.php\', '+testrunid+');');
    $$('#row'+testrunid+' td[onClick]').invoke('writeAttribute', 'title',
                                               'Click to edit testrun');
  }
  else if (!info['editable'])
  {
    $$('#row'+testrunid+' td[onClick]').invoke('writeAttribute', 'onClick',
                                               'showtestrundetail(\'viewtestrun.php\', '+testrunid+');');
    $$('#row'+testrunid+' td[onClick]').invoke('writeAttribute', 'title',
                                               'Click to view testrun');
  }
}
var ctrl = false;

document.observe('keydown',function(k)
  {
    if (k.keyCode == 17)
    {
       ctrl = true;
    }
  })

document.observe('keyup',function(k)
  {
    if (k.keyCode == 17)
    {
       ctrl = false;
    }
  })

function showtestrundetail(page, testrunid)
{
  if (ctrl)
  {
    window.open(page+'?testrunid='+testrunid, 'tr'+testrunid);
  }
  else
  {
    location.href=page+'?testrunid='+testrunid;
  }
}
function testrunsearch(page)
{
  var form = $('testrunsearchform');
  $('testrunlist').update("<center><b>Searching...</b></center>");
  new Ajax.Updater('testrunlist', 'php/doindex.php',
                   { method: 'get',
                     parameters: {what: 'testrunsearch',
                                  userid: $F(form['userid']),
                                  showarchived: $F(form['showarchived']),
                                  ordering: $F(form['ordering']),
                                  showexternal: $F(form['showexternal']),
                                  testrunsperpage: $F(form['testrunsperpage']),
                                  page: page,
                                  testrungroupname: $F(form['testrungroupname'])
                                  } });


  return false;
}

</script>
<?php

echo "<h1>Test-run listing</h1>\n";

echo "<fieldset>\n".
     "<legend>Search testruns</legend>\n";
$sql = "SELECT *\n".
       "FROM ovt_user\n".
       "ORDER BY sname, fname";
$userresult = pg_query($ovtDB, $sql);

echo "<form id=\"testrunsearchform\" method=\"post\" onsubmit=\"return testrunsearch(1);\" action=\"#\">\n";
echo "<div>\n";
echo "<table>\n".
     "<tr><td>Select User:</td><td><select name=\"userid\">\n";
echo "<option value=\"ALL_USERS\"";
if (!isset($_REQUEST['userid']) && !isset($_SESSION['auth_userid']))
{
  echo " selected";
}
echo ">&lt;&lt;All Users&gt;&gt;</option>\n";
for ($i = 0 ; $i < pg_num_rows($userresult) ; $i++)
{
  echo "<option value=\"".pg_fetch_result($userresult, $i, "userid")."\"";
  if (isset($_REQUEST['userid']) && $_REQUEST['userid'] == pg_fetch_result($userresult, $i, "userid"))
  {
    echo " selected";
  }
  else if (!isset($_REQUEST['userid']) && isset($_SESSION['auth_userid']) && $_SESSION['auth_userid'] == pg_fetch_result($userresult, $i, "userid"))
  {
    $_REQUEST['userid'] = $_SESSION['auth_userid'];
    echo " selected";
  }
  echo ">".
       htmlentities(pg_fetch_result($userresult, $i, "sname")).", ".
       htmlentities(pg_fetch_result($userresult, $i, "fname"))."</option>\n";

}
echo "</select></td>\n";
echo "<td>Order:</td><td><select name=\"ordering\">\n";
echo "<option value=\"normal\"";
if (!isset($_REQUEST['ordering']) || $_REQUEST['ordering'] == "normal")
{
  echo " selected";
}
echo ">By Created Date</option>\n";
echo "<option value=\"end\"";
if (isset($_REQUEST['ordering']) && $_REQUEST['ordering'] == "end")
{
  echo " selected";
}
echo ">By End Date</option>\n";
echo "<option value=\"start\"";
if (isset($_REQUEST['ordering']) && $_REQUEST['ordering'] == "start")
{
  echo " selected";
}
echo ">By Start Date</option>\n";

echo "</select></td>\n";
echo "<td>Show archived?</td><td><input type=\"checkbox\" name=\"showarchived\"";
if (isset($_REQUEST['showarchived']) && $_REQUEST['showarchived'] == "on")
{
  echo " checked";
}
echo "></td><td rowspan=2>\n";
echo "<input type=\"submit\" name=\"submit\" value=\"Refine Search\"></td></tr>\n";

echo "<tr><td>Testrun group:</td><td><input class=\"textbox\" type=\"text\" name=\"testrungroupname\" value=\"";
if (isset($_REQUEST['testrungroupname']))
{
  echo htmlentities($_REQUEST['testrungroupname']);
}
echo "\"></td>";
echo "<td>Items per page:</td><td><select name=\"testrunsperpage\">";
foreach (array(10,25,50,100) as $numperpage)
{
  echo "<option value=\"".$numperpage."\"";
  if ((isset($_REQUEST['testrunsperpage']) && $_REQUEST['testrunsperpage'] == $numperpage)
      || (!isset($_REQUEST['testrunsperpage']) && $numperpage == 25))
  {
    echo " selected";
  }
  echo ">".$numperpage."</option>\n";
}
echo "</select></td>\n";
echo "<td>Show external?</td><td><input type=\"checkbox\" name=\"showexternal\"";
if (isset($_REQUEST['showexternal']) && $_REQUEST['showexternal'] == "on")
{
  echo " checked";
}
echo "></td></tr>\n".
     "</table>\n";

echo "</div>\n";
echo "</form>\n";
echo "</fieldset>";

echo "<form method=\"post\" onsubmit=\"return false;\" action=\"#\">\n";
echo "<div id=\"testrunlist\">\n";
echo "</div>\n";
echo "</form>\n";
echo "<br />\n";
echo "<fieldset>\n";
echo "<legend>Create new testrun group</legend>\n";
if (!isset($_SESSION['auth_userid']))
{
  echo "Please <a href=\"login.php\">log in</a> to create new testruns";
}
else
{
  echo "<form action=\"php/doindex.php\" method=\"post\">\n".
       "<div>\n".
       "Testrun Group Name: <input type=\"text\" class=\"textbox\" name=\"groupname\">\n".
       "<input type=\"submit\" class=\"formbutton\" name=\"\" value=\"Create\">\n".
       "<input type=\"hidden\" name=\"what\" value=\"createtestrungroup\">\n".
       "</div>\n".
       "</form>\n";
}
echo "</fieldset>";

popover();
htmlFooter();
?>
