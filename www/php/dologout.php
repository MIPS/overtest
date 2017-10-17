<?php
  include_once('includes.inc');

  session_destroy();

  header("location: ../index.php");
  exit(0);
?>
