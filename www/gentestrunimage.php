<?php
  include_once('includes.inc');
  include_once('dot.inc');
  header("Content-type: image/png");
  echo draw_testrun($_REQUEST['testrunid']);


?>
