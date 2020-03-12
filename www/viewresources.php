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
