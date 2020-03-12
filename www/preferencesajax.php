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
include_once('inc/xmlrpc.inc');
include_once('inc/jsonrpc.inc');
include_once('inc/json_extension_api.inc');

if (!isset($_SESSION['auth_userid']))
{
  echo "Please log in\n";
  exit(0);
}

if (!isset($_REQUEST['what']))
{
  echo "BAD REQUEST";
  exit(0);
}
elseif ($_REQUEST['what'] == "entitysubscription")
{
  if ($_REQUEST['entityclass'] == "testruns")
  {
    $sql = "UPDATE ovt_subscription\n".
           "SET testruns=".$_REQUEST['setting']."\n".
           "WHERE userid='".$_SESSION['auth_userid']."'\n".
           "AND notifymethodid='".$_REQUEST['notifymethodid']."'";
    pg_query($ovtDB, $sql);
    $sql = "INSERT INTO ovt_subscription\n".
           "(userid, notifymethodid, testruns)\n".
           "(SELECT userid, notifymethodid, '".$_REQUEST['setting']."'::boolean\n".
           " FROM ((SELECT '".$_SESSION['auth_userid']."' AS userid, '".$_REQUEST['notifymethodid']."' AS notifymethodid)\n".
           "       EXCEPT\n".
           "       (SELECT userid, notifymethodid\n".
           "        FROM ovt_subscription\n".
           "        WHERE userid='".$_SESSION['auth_userid']."'\n".
           "        AND notifymethodid='".$_REQUEST['notifymethodid']."')) AS foo)";
    pg_query($ovtDB, $sql);
  }
}
else if ($_REQUEST['what'] == "updateprofile")
{
  $validfields = array("fname", "sname", "email", "growlhost", "growlpassword");
  if (!in_array($_REQUEST['field'], $validfields))
  {
    echo "Unrecognised field: ".$_REQUEST['field'];
    exit(0);
  }
  $sql = "UPDATE ovt_user\n".
         "SET ".$_REQUEST['field']."='".$_REQUEST['value']."'\n".
         "WHERE userid='".$_SESSION['auth_userid']."'";
  pg_query($ovtDB, $sql);
}
else if ($_REQUEST['what'] == "getsubscriptions")
{

  $sql = "SELECT ovt_notifymethod.notifymethodid, ovt_notifytype.notifytypeid,\n".
         "       ovt_subscription.subscriptionid,\n".
         "       (SELECT pkid\n".
         "        FROM ovt_subscriptionentity\n".
         "        WHERE ovt_subscriptionentity.subscriptionid=ovt_subscription.subscriptionid\n".
         "        LIMIT 1) AS pkid\n".
         "FROM (ovt_notifytype FULL OUTER JOIN ovt_notifymethod ON true)\n".
         "     LEFT OUTER JOIN ovt_subscription USING (notifytypeid, notifymethodid)\n".
         "WHERE ovt_subscription.subscriptionid IS NULL\n".
         "OR ovt_subscription.userid='".$_SESSION['auth_userid']."'";

  $result = pg_query($ovtDB, $sql);
  $subscriptions = array();
  for ($i = 0 ; $i < pg_num_rows($result) ; $i++)
  {
    $idstring = "nt".pg_fetch_result($result, $i, "notifytypeid")."nm".pg_fetch_result($result, $i, "notifymethodid");
    if (pg_field_is_null($result, $i, "subscriptionid"))
    {
      $subscriptions[$idstring] = "none";
    }
    else
    {
      $subscriptions[$idstring] = "all";
      if (!pg_field_is_null($result, $i, "pkid"))
      {
        $subscriptions[$idstring] = "some";
      }
    }
  }
  echo json_encode($subscriptions);
}

?>
