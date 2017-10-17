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
