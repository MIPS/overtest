<?php
include_once('includes.inc');

htmlHeader("View resources");

echo "<h1>View Resources</h1>\n";

/* Find all the resource types */

$sql = "SELECT *\n".
       "FROM ovt_resourcetype\n".
       "ORDER BY resourcetypename";
$result = pg_query($ovtDB,$sql);

if (pg_num_rows($result) == 0)
{
  echo "There are no resource types defined<br />\n";
}
else
{
  for ($i = 0 ; $i < pg_num_rows($result); $i++)
  {
    echo "<div style=\"float:left;padding:5px;\">\n";
    echo "<h2>".htmlentities(pg_fetch_result($result, $i, "resourcetypename"))."</h2>\n";
    $sql = "SELECT DISTINCT resourcename, resourceid\n".
           "FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid)\n".
           "WHERE ovt_resource.resourcetypeid='".pg_fetch_result($result, $i, "resourcetypeid")."'\n".
           "AND ovt_resourcestatus.status != 'HISTORIC'\n".
           "ORDER BY resourcename";
    $resources = pg_query($ovtDB, $sql);

    if (pg_num_rows($resources) == 0)
    {
      echo "There are no resources in this category";
    }
    else
    {
      for ($j = 0 ; $j < pg_num_rows($resources) ; $j++)
      {
        echo "<a href=\"viewresource.php?resourceid=".pg_fetch_result($resources, $j, "resourceid")."\">".htmlentities(pg_fetch_result($resources, $j, "resourcename"))."</a><br />\n";
      }
    }
    echo "</div>";
  }
}

htmlFooter();
?>
