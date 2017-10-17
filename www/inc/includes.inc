<?php
session_start();
header ("Expires: Tue, 10 Sep 2002 00:00:00 GMT"); // date in the past
header ("Last-Modified: " . gmdate ("D, d M Y H:i:s") . " GMT"); // changes always
header ("Cache-Control: no-cache, must-revalidate");  // HTTP/1.1
header ("Pragma: no-cache");

$overtestroot="/home/overtest/root/";

include_once('connect_overtestdb_webuser.inc');
include_once('htmlHeadFoot.inc');

?>
