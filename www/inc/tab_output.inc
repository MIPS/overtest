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
$tab_output = array();
function tab_begin_table()
{
}
$tab_output['begin_table'] = 'tab_begin_table';
function tab_end_table()
{
}
$tab_output['end_table'] = 'tab_end_table';
function tab_begin_row()
{
}
$tab_output['begin_row'] = 'tab_begin_row';
function tab_end_row()
{
  echo "\r\n";
}
$tab_output['end_row'] = 'tab_end_row';
$savecolspan = 1;
global $savecolspan;
function tab_begin_cell($class, $colour="", $columns=1, $extra="")
{
  global $savecolspan;
  $savecolspan = $columns;
}
$tab_output['begin_cell'] = 'tab_begin_cell';
function tab_end_cell()
{
  global $savecolspan;
  for ($i = 0 ; $i < $savecolspan ; $i++)
  {
    echo "\t";
  }
}
$tab_output['end_cell'] = 'tab_end_cell';

function tab_begin_header_cell($class="", $colour="", $columns=1, $extra="")
{
  global $savecolspan;
  $savecolspan = $columns;
}
$tab_output['begin_header_cell'] = 'tab_begin_header_cell';
function tab_end_header_cell()
{
  global $savecolspan;
  for ($i = 0 ; $i < $savecolspan ; $i++)
  {
    echo "\t";
  }
}
$tab_output['end_header_cell'] = 'tab_end_header_cell';
function tab_superscript($text)
{
  return "|".$text."|";
}
$tab_output['superscript'] = 'tab_superscript';
function tab_no_result()
{
}
$tab_output['no_result'] = 'tab_no_result';
function tab_pass()
{
  echo "PASS";
}
$tab_output['pass'] = 'tab_pass';
function tab_fail()
{
  echo "FAIL";
}
$tab_output['fail'] = 'tab_fail';
function tab_escape($text)
{
  echo $text;
}
$tab_output['escape'] = 'tab_escape';
function tab_newline($text)
{
  echo "\n";
}
$tab_output['newline'] = 'tab_newline';

?>
