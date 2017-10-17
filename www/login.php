<?php
  include_once('includes.inc');

  htmlHeader("Login");

  $sql = "SELECT userid, sname || ', ' || fname AS name\n".
         "FROM ovt_user\n".
         "ORDER BY sname, fname";
  $result = pg_query($ovtDB, $sql);

  echo "<h1>Please log in</h1>\n";
  echo "<form method=\"post\" action=\"php/dologin.php\">\n".
       "<table style=\"margin:0 auto;\">\n".
       "<tr><th>Username</th><td><select name=\"userid\">";
  echo "<option value=\"\" selected></option>\n";
  for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
  {
    echo "<option value=\"".pg_fetch_result($result, $i, "userid")."\">".
                            pg_fetch_result($result, $i, "name")."</option>\n";
  }
  echo "</select></td></tr>\n".
       "<tr><td></td><td><input type=\"submit\" name=\"submit\", value=\"Login\"></td></tr>\n".
       "</table>\n".
       "</form>\n";
  htmlFooter();
?>
