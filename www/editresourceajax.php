<?php
include_once('includes.inc');

if (!isset($_REQUEST['what']))
{
  echo "BAD REQUEST";
}
elseif ($_REQUEST['what'] == "updateattribute")
{
echo $_REQUEST['value'];
echo $_REQUEST['attributeid'];
echo $_REQUEST['resourceid'];
echo "drdsfssfsd";
}

?>
