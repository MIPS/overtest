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

function testrun_buttons($testrunid, $owner, $state, $update_callback)
{
//    if ($state['successful'] == "t")
//      echo "<img src=\"images/tick.gif\" alt=\"Successful\">";
//    else if ($state['successful'] == "f")
//      echo "<img src=\"images/cross.png\" alt=\"Failed\">";
    echo "<span id=\"gopause".$testrunid."\">";
    if ($owner && ($state['goenabled'] == "t"
                   || $state['checkenabled'] == "t"))
    {
      echo "<a href=\"javascript:runCommand('testrun',".$testrunid.",'go', ".$update_callback.");\"><img src=\"images/go.gif\" alt=\"Go\"></a>";
    }
    else if ($owner && $state['pauseenabled'] == "t")
    {
      echo "<a href=\"javascript:runCommand('testrun',".$testrunid.",'pause', ".$update_callback.");\"><img src=\"images/pause.gif\" alt=\"Pause\"></a>";
    }
    else
    {
      echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">";
    }
    echo "</span>\n";
    echo "<span id=\"abort".$testrunid."\">";
    if ($owner && $state['abortenabled'] == "t")
    {
      echo "<a href=\"javascript:runCommand('testrun',".$testrunid.", 'abort', ".$update_callback.");\"><img src=\"images/abort.gif\" alt=\"Abort\"></a>";
    }
    else
    {
      echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">";
    }
    echo "</span>\n";
    echo "<span id=\"archive".$testrunid."\">";
    if ($owner && $state['archiveenabled'] == "t")
    {
      echo "<a href=\"javascript:archiveTestrunPrompt('testrun',".$testrunid.", '".addslashes(htmlentities($state['description']))."');\"><img src=\"images/archive.gif\" alt=\"Archive\"></a>";
    }
    else
    {
      echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">";
    }
    echo "</span>\n";
    echo "<span id=\"delete".$testrunid."\">";
    if ($owner && $state['deleteenabled'] == "t")
    {
      echo "<a href=\"javascript:deleteTestrunPrompt('testrun',".$testrunid.",'".addslashes(htmlentities($state['description']))."');\"><img src=\"images/delete.gif\" alt=\"Delete\"></a>";
    }
    else
    {
      echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">";
    }
    echo "</span>\n";
}
function testrun_status($testrunid, $owner, $status, $update_callback)
{
    echo "<span class=\"clickable\" id=\"status".$testrunid."\" onClick=\"javascript:refreshStatus(".$testrunid.",";
    if ($owner)
    {
      echo "true";
    }
    else
    {
      echo "false";
    }
    echo ", ".$update_callback.")\">".$status."</span>";
}

function popover()
{
  echo "<div id=\"popover\" style=\"position: fixed; display:none;left:0px; top:0px; width:100%;height:100%; text-alignment:center;z-index:1000;background-image:url('images/trans.png');\">\n".
       "<div style=\"margin:150px auto; width:300px\" class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div style=\"padding:20px;width:260px;height:200px;text-align:center\" class=\"boxBottomLeft\">\n".
       "<h2 id=\"popmessage\"></h2>\n".
       "<br>\n".
       "<a id=\"poplink\" href=\"\" accesskey='y'>Yes</a> <a href=\"javascript:endPopover();\" accesskey='n'>No</a>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div></div>\n";
}
?>
<script type="text/javascript">
function deleteTestrunPrompt(type, testrunid, description)
{
  $('popmessage').update("Confirm delete:<br />"+description);
  $('poplink').writeAttribute("href", "javascript:endPopover();runCommand('"+type+"',"+testrunid+",'delete');");
  $('popover').show();
}

function archiveTestrunPrompt(type, testrunid, description)
{
  $('popmessage').update("Confirm archive:<br />"+description);
  $('poplink').writeAttribute("href", "javascript:endPopover();runCommand('"+type+"',"+testrunid+",'archive');");
  $('popover').show();
}

function endPopover()
{
  $('popover').hide();
}

function updateButtons(testrunid, progress, owner, callback)
{
  if (progress)
  {
    updateimage='<img src="images/updating.gif" alt="updating">';
    $('status'+testrunid).update('<i>Updating...</i>');
    if (owner)
    {
      $('gopause'+testrunid).update(updateimage);
      $('abort'+testrunid).update(updateimage);
      $('archive'+testrunid).update(updateimage);
      $('delete'+testrunid).update(updateimage);
    }
  }
  else
  {
    new Ajax.Request('indexajax.php',
                     { method: 'post',
                       parameters: {what: 'updatetestrun',
                                    testrunid: testrunid},
                       onComplete: function(transport)
                                   {
                                     info = transport.responseText.evalJSON(true);
                                     if (owner)
                                     {
                                       $('gopause'+testrunid).update(info['gopause']);
                                       $('abort'+testrunid).update(info['abort']);
                                       $('archive'+testrunid).update(info['archive']);
                                       $('delete'+testrunid).update(info['delete']);
                                     }
                                     $('status'+testrunid).update(info['status']);
                                     $('description'+testrunid).update(info['description']);
                                     if (callback != null)
                                     {
                                       callback(testrunid, info, owner);
                                     }
                                  } });

  }
}

function refreshStatus(testrunid, owner, callback)
{
  updateButtons(testrunid, true, owner, callback);
  updateButtons(testrunid, false, owner, callback);
}

function runCommand(type,theid, command, callback)
{
  if (type=='testrun')
  {
    updateButtons(theid, true, true, callback);
    new Ajax.Request('indexajax.php',
                     { method: 'post',
                       parameters: {what: command,
                                    testrunid: theid},
                       onComplete: function(transport)
                                   {
                                     updateButtons(theid, false, true, callback);
                                   } });
  }
  else
  {
    ids = getCheckedTestruns(theid);
    ids.map(function(o)
            {
              runCommand('testrun', o, command, callback);
              return o;
            });

    $('groupselect'+theid).checked = false;
    toggleSelectGroup(theid);
  }
}

</script>

