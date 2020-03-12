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
