<?php
  include_once('includes.inc');
  $_SESSION['auth_userid'] = $_REQUEST['userid'];
  header("location: ../index.php");
  exit(0);
?>
