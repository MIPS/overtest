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
