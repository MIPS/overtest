<?php
include_once('testrun_control.inc');

function nav_list($num_of_testruns, $options, $result)
{
  $num_pages = ceil( $num_of_testruns / $options['testrunsperpage']);
  $start_num = max(1, min($options['page']-4, $num_pages-9 ));
  $fin_num = min($start_num+9, $num_pages);

  if ($options['page'] != $start_num)
  {
    echo "<a href=\"#\" onclick=\"javascript:testrunsearch(".(1).")\">&lt;&lt;</a> - ";
    echo "<a href=\"#\" onclick=\"javascript:testrunsearch(".($options['page']-1).")\">&lt;</a> - ";
  }

  for ($i = $start_num; $i <= $fin_num; $i++)
  {
    if ($i > $start_num)
    {
      echo " - ";
    }
    if (($i != $options['page']) && ($i <= $num_pages ))
    {
      echo "<a href=\"#\" onclick=\"javascript:testrunsearch(".($i).")\">".($i)."</a>";
    }
    if ($i == $options['page'])
    {
      echo ($i);
    }
  }

  if ($options['page'] != $num_pages)
  {
    echo " - <a href=\"#\" onclick=\"javascript:testrunsearch(".($options['page']+1).")\">&gt;</a>";
    echo " - <a href=\"#\" onclick=\"javascript:testrunsearch(".$num_pages.")\">&gt;&gt;</a>";
  }
  echo "</center>\n";
}

function testrunlist($options)
{
  global $ovtDB;
  $sql_select = "SELECT ovt_testrun.testrunid, to_char(ovt_testrun.createddate, 'YYYY/MM/DD HH24:MI') AS createddate,\n".
                "       to_char(ovt_testrun.completeddate, 'YYYY/MM/DD HH24:MI') AS completeddate,\n".
                "       to_char(ovt_testrun.startafter, 'YYYY/MM/DD HH24:MI') AS startafter,\n".
                "       ovt_testrun.description, ovt_user.username, ovt_user.userid, ovt_testrungroup.testrungroupname,\n".
                "       ovt_testrungroup.testrungroupid, ovt_runstatus.description AS rundesc, ovt_runstatus.*\n";
  $sql_select_count = "SELECT Count(ovt_testrun.testrunid) As run_count \n";
  $sql_from  =  "FROM ovt_testrun LEFT OUTER JOIN ovt_testrungroup USING (testrungroupid) \n".
                "     INNER JOIN ovt_user ON (ovt_user.userid=ovt_testrun.userid)\n".
                "     INNER JOIN ovt_runstatus USING (runstatusid)\n";
  $sql_where =  "WHERE true\n";
  
  if (!isset($options['showarchived']) || $options['showarchived'] != "on")
  {
    $sql_where .= "AND ovt_testrun.runstatusid != (SELECT runstatusid\n".
                  "                                FROM ovt_runstatus\n".
                  "                                WHERE status='ARCHIVED')\n";
  }
  if (!isset($options['showexternal']) || $options['showexternal'] != "on")
  {
    $sql_where .= "AND ovt_testrun.runstatusid != (SELECT runstatusid\n".
                  "                                FROM ovt_runstatus\n".
                  "                                WHERE status='EXTERNAL')\n";
  }
  if (isset($options['userid']) && $options['userid'] != "ALL_USERS")
  {
    $sql_where .= "AND ovt_testrun.userid='".$options['userid']."'\n";
  }
  
  if (isset($options['testrungroupname']) && $options['testrungroupname'] != "")
  {
    $sql_where .= "AND ovt_testrungroup.testrungroupname ILIKE '".$options['testrungroupname']."'\n";
  }
  $sql_orderby = "";
  if (isset($options['ordering']) && $options['ordering'] != "normal")
  {
    if ($options['ordering'] == "end")
    {
      $sql_orderby = "ORDER BY ovt_testrun.completeddate IS NOT NULL DESC, ovt_testrun.completeddate DESC,\n".
                     "         ovt_testrun.startafter DESC\n";
    }
    else if ($options['ordering'] == "start")
    {
      $sql_orderby = "ORDER BY ovt_testrungroup.testrungroupid IS NOT NULL DESC, ovt_testrungroup.createddate DESC,\n".
                     "         ovt_testrungroup.testrungroupid DESC, ovt_testrun.startafter DESC, ovt_testrun.description\n";
    }
  }
  else
  {
    $sql_orderby = "ORDER BY ovt_testrungroup.testrungroupid IS NOT NULL DESC, ovt_testrungroup.createddate DESC,\n".
                   "         ovt_testrungroup.testrungroupid DESC, ovt_testrun.createddate DESC, ovt_testrun.description\n";
  }
  /* paging logic */
  if (!isset($options['page']) || (int)$options['page'] < 1)
  {
    $options['page'] = 1;
  }
  
  if (!isset($options['testrunsperpage']) || (int)$options['testrunsperpage'] < 1)
  {
    $options['testrunsperpage'] = 1;
  }

  $offset = ($options['page']-1) * $options['testrunsperpage'];
  $limit = $options['testrunsperpage']+1;
  $startindex = 0;
  $endindex = $options['testrunsperpage'];
  if ($offset > 0)
  {
    $startindex = 1;
    $endindex += 1;
    $offset -= 1;
    $limit += 1;
  }

  $sql_offset = "OFFSET " . $offset . "\n";
  $sql_limit = "LIMIT " . $limit ."\n";

  /* Concatinate sql statements. 
     sql_testruns is to get all the test runs to populate the resulting pages 
     sql_count is to get the number of test runs */
  $sql_testruns = $sql_select . $sql_from . $sql_where . $sql_orderby . $sql_offset . $sql_limit;
  $sql_count = $sql_select_count . $sql_from . $sql_where . ";";

  $result = pg_query($ovtDB, $sql_testruns);
  $result_count = pg_query($ovtDB, $sql_count);

  $num_of_testruns = pg_fetch_result($result_count, 0, "run_count");

  /* There may be one result from the previous page but none for this page */
  if (pg_num_rows($result) <= $startindex)
  {
    echo "<br />Search returned no testruns<br />\n";
  }
  else
  {
    echo "<p align=center>";
    nav_list($num_of_testruns, $options, $result);
    echo "</p>";
    $group = "";
    $groupid = -1;
    for ($i = $startindex ; $i < min(pg_num_rows($result), $endindex) ; $i++)
    {
      if ($groupid != pg_fetch_result($result, $i, "testrungroupid"))
      {
        if ($i != $startindex)
        {
          echo "</tbody>\n";
          echo "</table>\n";
        }
        $groupid = pg_fetch_result($result, $i, "testrungroupid");
        echo "<table class=\"listTable\" style=\"table-layout: fixed;\" id=\"testrungroup".$groupid."\" cellspacing=0>\n";
        echo "<col width=\"100px\">\n".
             "<col width=\"100px\">\n".
             "<col width=\"130px\">\n".
             "<col width=\"*\">\n".
             "<col width=\"150px\">\n".
             "<col width=\"130px\">\n";
        echo "<thead>\n";
        $group = pg_fetch_result($result, $i, "testrungroupname");
  
        $userresult = null;
        if (!pg_field_is_null($result, $i, "testrungroupid"))
        {
          $sql = "SELECT userid\n".
                 "FROM ovt_testrungroup\n".
                 "WHERE testrungroupid='".pg_fetch_result($result, $i, "testrungroupid")."'";
          $userresult = pg_query($ovtDB, $sql);
        }
  
        $enableoptions = false;
        if (!pg_field_is_null($result, $i, "testrungroupid") && isset($_SESSION['auth_userid'])
            && pg_fetch_result($userresult, 0, "userid")==$_SESSION['auth_userid'])
        {
          $enableoptions = true;
        }
        $tdopts = "";
        $tropts = "";
        if ($enableoptions && $group != "")
        {
          $tdopts = "onMouseOver=\"style.cursor='pointer';\" onDblClick=\"location.href='edittestrun.php?testrungroupid=".
                    pg_fetch_result($result, $i, "testrungroupid")."';\" title=\"Double click to edit testrun group\"";
          $tropts = "onMouseOut=\"style.backgroundColor='white';style.cursor='default'\" onMouseOver=\"style.backgroundColor='#ADD6C7';\"";
        }
        $tgid = pg_fetch_result($result, $i, "testrungroupid");
        echo "<tr class=\"group\" $tropts><td colspan=4 $tdopts>\n";
        echo "<span class=\"clickable\" onClick=\"javascript:showHide(".$groupid.")\"><img name=\"showhide\" src=\"images/toggle.png\" alt=\"\"></span>\n";
        if ($enableoptions && $group != "")
        {
          echo "<input style=\"display:none;width:250px;\" type=\"text\" id=\"editbox".$tgid."\" name=\"groupedit".$tgid."\" class=\"textbox\" ".
                      "value=\"".htmlentities($group)."\" onblur=\"showGroupName(".$tgid.");\">\n";
        }
        echo "<span id=\"group".$tgid."\" ";
        if ($enableoptions && $group != "")
        {
          echo "title=\"Click to edit group name\" ";
          echo "onmouseover=\"$('group".$tgid."').setStyle({'color':'red'});\" onmouseout=\"$('group".$tgid."').setStyle({'color':'black'});\" ";
          echo "onclick=\"editGroupName('".$tgid."');\"";
        }
        echo "><b>";
        if ($group != "")
        {
          echo htmlentities($group);
        }
        else
        {
          echo "NO GROUP";
        }
        echo "</b></span>\n";
        echo "<span style=\"float:right\">\n";
        if (!pg_field_is_null($result, $i, "testrungroupid") && isset($_SESSION['auth_userid']))
        {
          echo "<a href=\"php/doindex.php?testrungroupid=".
               pg_fetch_result($result, $i, "testrungroupid").
               "&amp;what=copytestrungroup\"><img src=\"images/copygroup.gif\" width=\"20px\" height=\"20px\" alt=\"Copy Testrun Group\"></a>\n";
        }
        else
        {
          echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">\n";
        }
        if ($enableoptions)
        {
          echo "<a href=\"php/doindex.php?testrungroupid=".
               pg_fetch_result($result, $i, "testrungroupid").
               "&amp;what=newtestrun\"><img src=\"images/new.gif\" width=\"20px\" height=\"20px\" alt=\"New Testrun\"></a>\n";
        }
        else
        {
          echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">\n";
        }
        echo "</span>\n";
        echo "</td>\n";
        echo "<td colspan=2>\n";
  
        echo "<span style=\"display:none\" id=\"groupcontrols".$groupid."\">\n";
        echo "<a href=\"javascript:runCommand('group',".$groupid.",'go', update_row_callback);\"><img src=\"images/go.gif\" alt=\"Go\"></a>\n";
        echo "<a href=\"javascript:runCommand('group',".$groupid.",'pause', update_row_callback);\"><img src=\"images/pause.gif\" alt=\"Pause\"></a>\n";
        echo "<a href=\"javascript:runCommand('group',".$groupid.",'abort', update_row_callback);\"><img src=\"images/abort.gif\" alt=\"Abort\"></a>\n";
        echo "<a href=\"javascript:archiveTestrunPrompt('group',".$groupid.", '".addslashes(htmlentities($group))."');\"><img src=\"images/archive.gif\" alt=\"Archive\"></a>\n";
        echo "<a href=\"javascript:deleteTestrunPrompt('group',".$groupid.",'".addslashes(htmlentities($group))."');\"><img src=\"images/delete.gif\" alt=\"Delete\"></a>\n";
        echo "</span>\n";
  
        echo "<span id=\"groupblank".$groupid."\">\n";
        echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">\n";
        echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">\n";
        echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">\n";
        echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">\n";
        echo "<img src=\"images/blank.gif\" width=\"20px\" height=\"20px\" alt=\"\">\n";
        echo "</span>\n";
        if ($enableoptions)
        {
          echo "<input type=\"checkbox\" id=\"groupselect".$groupid."\" class=\"checkbox\" name=\"groupselect".$groupid."\" onclick=\"toggleSelectGroup(".$groupid.")\">\n";
        }
        echo "</td></tr>\n";
  
        echo "</thead>\n";
        echo "<tbody>\n";
        echo "<tr>\n".
             "<th>Testrun</th>\n".
             "<th>User</th>\n";
        if (isset($options['ordering']) && $options['ordering'] == "end")
        {
          echo "<th>Date Completed</th>\n";
        }
        else if (isset($options['ordering']) && $options['ordering'] == "start")
        {
          echo "<th>Date started</th>\n";
        }
        else
        {
          echo "<th>Date Created</th>\n";
        }
        echo "<th>Description</th>\n".
             "<th>Options</th>\n".
             "<th>Status</th>\n".
             "</tr>\n";
      }
      /* Now handle extremes to show next and last page entries */
      if ($i != 0 && $i == $startindex)
      {
        /* This entry is before the current page but check if the entry is in
           the same testrun group so that the user knows if there are more entries */
        if (pg_fetch_result($result, 0, "testrungroupid") == pg_fetch_result($result, $i, "testrungroupid"))
        {
          echo "<tr><td colspan=6>Group contains more testruns on previous page</td></tr>\n";
        }
      }
      $enableoptions = false;
      if (!pg_field_is_null($result, $i, "testrungroupid") && isset($_SESSION['auth_userid'])
          && pg_fetch_result($result, $i, "userid")==$_SESSION['auth_userid'])
      {
        $enableoptions = true;
      }
  
      $status = pg_fetch_result($result, $i, "rundesc");
      $tdopts = "";
      $tropts = "";
      $testrunid = pg_fetch_result($result, $i, "testrunid");
      if ($enableoptions && pg_fetch_result($result, $i, "iseditable") == "t")
      {
        $tdopts = "onMouseOver=\"style.cursor='pointer';\" onClick=\"showtestrundetail('edittestrun.php',".$testrunid.");\" title=\"Click to edit testrun\"";
      }
      elseif (pg_fetch_result($result, $i, "iseditable") != "t")
      {
        $tdopts = "onMouseOver=\"style.cursor='pointer';\" onClick=\"showtestrundetail('viewtestrun.php',".$testrunid.");\" title=\"Click to view testrun\"";
      }
      if ($tdopts != "")
      {
        $tropts = "onMouseOut=\"style.backgroundColor='white';style.cursor='default'\" onMouseOver=\"style.backgroundColor='#E1E8EE';\"";
      }
      echo "<tr id=\"row".$testrunid."\" $tropts>\n";
      echo "<td ".$tdopts."><a name='anchor_$testrunid'></a>$testrunid</td>\n";
      echo "<td ".$tdopts.">".pg_fetch_result($result, $i, "username")."</td>\n";
  
      if (isset($options['ordering']) && $options['ordering'] == "end")
      {
        echo "<td ".$tdopts.">".pg_fetch_result($result, $i, "completeddate")."</td>\n";
      }
      else if (isset($options['ordering']) && $options['ordering'] == "start")
      {
        echo "<td ".$tdopts.">".pg_fetch_result($result, $i, "startafter")."</td>\n";
      }
      else
      {
        echo "<td ".$tdopts.">".pg_fetch_result($result, $i, "createddate")."</td>\n";
      }
      echo "<td id=\"description".$testrunid."\" ".$tdopts.">".pg_fetch_result($result, $i, "description")."</td>\n";
      echo "<td>";
      if (isset($_SESSION['auth_userid']))
      {
        echo "<a href=\"php/doindex.php?testrunid=".$testrunid."&amp;what=copytestrun\"><img src=\"images/copy.gif\" alt=\"Copy Testrun\"></a>\n";
      }
      testrun_buttons($testrunid, $enableoptions, pg_fetch_array($result, $i), "update_row_callback");
  
      if ($enableoptions)
      {
        echo "<input type=\"checkbox\" class=\"checkbox\" name=\"select".$testrunid."\" onclick=\"toggleSelect(".$testrunid.", ".$groupid.")\">\n";
      }
      echo "</td>\n";
      echo "<td>";
      testrun_status($testrunid, $enableoptions, $status, "update_row_callback");
      echo "</td>\n";
      echo "</tr>\n";

      if ($i == $endindex-1 && $endindex != pg_num_rows($result))
      {
        /* This entry is after the current page but check if the entry is in
           the same testrun group so that the user knows if there are more entries */
        if (pg_fetch_result($result, $i, "testrungroupid") == pg_fetch_result($result, $endindex, "testrungroupid"))
        {
          echo "<tr><td colspan=6>Group contains more testruns on next page</td></tr>\n";
        }
      }


    }
    echo "</tbody>\n";
    echo "</table>\n";
    echo "<center>";
 
    nav_list($num_of_testruns, $options, $result);
    echo "</center>\n";
  }

}
?>
