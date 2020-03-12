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

htmlHeader("View testsuites");

echo "<h1>View Testsuites</h1>\n";

$sql = "SELECT *, (SELECT count(DISTINCT ovt_testrunaction.testrunid)\n".
       "           FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)\n".
       "           INNER JOIN ovt_testrunaction USING (versionedactionid)\n".
       "           WHERE ovt_testsuite.testsuiteid=ovt_action.testsuiteid) AS testruncount\n".
       "FROM ovt_testsuite INNER JOIN ovt_action USING (testsuiteid)\n".
       "     INNER JOIN ovt_lifecyclestate USING (lifecyclestateid)\n".
       "WHERE valid\n".
       "ORDER BY testsuitename";
$result = pg_query($ovtDB, $sql);

echo "<table>\n".
     "<tr><th>Testsuite</th><th>Test runs</th></tr>\n";
for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
{
  echo "<tr>";
  $count = pg_fetch_result($result, $i, "testruncount");
  if ($count > 0)
  {
    echo "<td><a href=\"viewresults.php?testsuiteid=".pg_fetch_result($result, $i, "testsuiteid")."\">".
              pg_fetch_result($result, $i, "testsuitename")."</a></td>";
  }
  else
  {
    echo "<td>".pg_fetch_result($result, $i, "testsuitename")."</td>";
  }
  echo "<td>".$count."</td>";
  echo "</tr>\n";
}
echo "</table>\n";

htmlFooter();
?>
