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
$html_output = array();
function html_begin_table()
{
  echo "<table cellspacing=0 class=\"resultstable\">\n";
}
$html_output['begin_table'] = 'html_begin_table';
function html_end_table()
{
  echo "</table>\n";
}
$html_output['end_table'] = 'html_end_table';
function html_begin_row()
{
  echo "<tr>\n";
}
$html_output['begin_row'] = 'html_begin_row';
function html_end_row()
{
  echo "</tr>\n";
}
$html_output['end_row'] = 'html_end_row';
function html_begin_cell($class, $colour="", $columns=1, $extra="")
{
  echo "<td";
  if ($class != "")
  {
    echo " class=\"".$class."\"";
  }
  if ($colour != "")
  {
    echo " style=\"background-color:#".$colour."\"";
  }
  if ($columns != 1)
  {
    echo " colspan=".$columns;
  }
  if ($extra != "")
  {
    echo " ".$extra;
  }
  echo ">\n";
}
$html_output['begin_cell'] = 'html_begin_cell';
function html_end_cell()
{
  echo "</td>\n";
}
$html_output['end_cell'] = 'html_end_cell';
function html_begin_header_cell($class="", $colour="", $columns=1, $extra="")
{
  echo "<th";
  if ($class != "")
  {
    echo " class=\"".$class."\"";
  }
  if ($colour != "")
  {
    echo " style=\"background-color:#".$colour."\"";
  }
  if ($columns != 1)
  {
    echo " colspan=".$columns;
  }
  if ($extra != "")
  {
    echo " ".$extra;
  }
  echo ">\n";
}
$html_output['begin_header_cell'] = 'html_begin_header_cell';
function html_end_header_cell()
{
  echo "</th>\n";
}
$html_output['end_header_cell'] = 'html_end_header_cell';
function html_superscript($text)
{
  return "<span style=\"vertical-align:super; font-size:70%\">".$text."</span>";
}
$html_output['superscript'] = 'html_superscript';
function html_no_result()
{
  echo "<span class=\"na\"></span>";
}
$html_output['no_result'] = 'html_no_result';
function html_pass()
{
  echo "<span class=\"pass\">PASS</span>";
}
$html_output['pass'] = 'html_pass';
function html_fail()
{
  echo "<span class=\"fail\">FAIL</span>";
}
$html_output['fail'] = 'html_fail';
function html_escape($text)
{
  echo htmlentities($text);
}
$html_output['escape'] = 'html_escape';
function html_newline()
{
  echo "<br />\n";
}
$html_output['newline'] = 'html_newline';

?>
