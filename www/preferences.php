<?php

include_once('includes.inc');

htmlHeader("User Preferences");

if (!isset($_SESSION['auth_userid']))
{
  echo "Please log in\n";
}
else
{

?>
<script type="text/javascript" src="tooltip.js"></script>
<script language="JavaScript">
var userid=<?php echo $_SESSION['auth_userid'];?>;
var waitcount=0;

function updateSubscription(entityclass, notifymethodid, setting)
{
  wait();
  new Ajax.Updater('ErrorMessage', 'preferencesajax.php',
                   { method: 'get',
                     parameters: {what: 'entitysubscription',
                                  entityclass: entityclass,
                                  notifymethodid: notifymethodid,
                                  setting: setting},
                     onComplete: function(transport) { endwait(); } });
}

function wait()
{
  Form.disable($("subscriptionform"));
  $("main").setStyle({cursor:"wait"});
  waitcount++;
}

function endwait()
{
  waitcount--;
  if (waitcount == 0)
  {
    Form.enable($("subscriptionform"));
    $("main").setStyle({cursor:"auto"});
  }
}
function updateView()
{
  new Ajax.Request('preferencesajax.php',
                   { method: 'post',
                     parameters: {what: 'getsubscriptions'},
                     onComplete: function(transport)
                                 {
                                   state = transport.responseText.evalJSON(true);
                                 } });

}
function saveProfile(field, value)
{
  if (value != '')
  {
    wait();
    new Ajax.Updater('ErrorMessage', 'preferencesajax.php',
                     { method: 'get',
                       parameters: {what: 'updateprofile',
                                    field: field,
                                    value: value},
                       onComplete: function(transport) { endwait(); } });
  }
}
</script>

<?php

  echo "<h2>Profile</h2>\n";
  $sql = "SELECT *\n".
         "FROM ovt_user\n".
         "WHERE userid='".$_SESSION['auth_userid']."'";
  $result = pg_query($ovtDB, $sql);

  echo "<form method=\"post\" action=\"#\">\n".
       "<table>\n".
       "<tr><th>Forename</th><td><input type=\"text\" class=\"textbox\" name=\"fname\" value=\"".
       htmlentities(pg_fetch_result($result, 0, "fname"))."\" onblur=\"saveProfile('fname',this.value);\"></td></tr>\n".
       "<tr><th>Surname</th><td><input type=\"text\" class=\"textbox\" name=\"sname\" value=\"".
       htmlentities(pg_fetch_result($result, 0, "sname"))."\" onblur=\"saveProfile('sname',this.value);\"></td></tr>\n".
       "<tr><th>E-mail</th><td><input type=\"text\" class=\"textbox\" name=\"email\" value=\"".
       htmlentities(pg_fetch_result($result, 0, "email"))."\" onblur=\"saveProfile('email',this.value);\"></td></tr>\n".
       "<tr><th>Desktop name (fqdn)</th><td><input type=\"text\" class=\"textbox\" name=\"growlhost\" value=\"".
       htmlentities(pg_fetch_result($result, 0, "growlhost"))."\" onblur=\"saveProfile('growlhost',this.value);\"></td></tr>\n".
       "<tr><th>Growl password</th><td><input type=\"text\" class=\"textbox\" name=\"growlpassword\" value=\"".
       htmlentities(pg_fetch_result($result, 0, "growlpassword"))."\" onblur=\"saveProfile('growlpassword',this.value);\"></td></tr>\n".
       "</table>\n".
       "</form>\n".
       "<br />\n";

  echo "<h2>Notification Options</h2>\n";
  $sql = "SELECT notifytypename, notifytypeid\n".
         "FROM ovt_notifytype\n".
         "ORDER BY notifytypename";
  $types = pg_query($ovtDB, $sql);
  $sql = "SELECT notifymethodname, notifymethodid\n".
         "FROM ovt_notifymethod\n".
         "ORDER BY notifymethodname";
  $methods = pg_query($ovtDB, $sql);
  
  echo "<form id=\"subscriptionform\">\n".
       "<table cellspacing=0>\n";
  echo "<tr><th></th>\n";
  for ($j = 0 ; $j < pg_num_rows($methods) ; $j++)
  {
    echo "<th>".pg_fetch_result($methods, $j, "notifymethodname")."</th>\n";
  }
  echo "<th></th></tr>\n";
  $tdopts = "onMouseOut=\"style.backgroundColor='white';style.cursor='default'\" onMouseOver=\"style.cursor='pointer';style.backgroundColor='#E1E8EE';\"";
  for ($i = 0 ; $i < pg_num_rows($types) ; $i++)
  {
    echo "<tr><th style=\"text-align:right\">".pg_fetch_result($types, $i, "notifytypename")."</th>\n";
    for ($j = 0 ; $j < pg_num_rows($methods) ; $j++)
    {
      echo "<td $tdopts style=\"padding:5px\">";
      $idstring = "nt".pg_fetch_result($types, $i, "notifytypeid")."nm".pg_fetch_result($methods, $j, "notifymethodid");
      echo "<span id=\"".$idstring."all\" class=\"clickable\" onclick=\"selectSubscription('".$idstring."all')\">All</span> ";
      echo "<span id=\"".$idstring."some\" class=\"clickable\" onclick=\"selectSubscription('".$idstring."some')\">Some</span> ";
      echo "<span id=\"".$idstring."none\" style=\"font-weight:bold\" class=\"clickable\" onclick=\"selectSubscription('".$idstring."none')\">None</span> ";
      echo "</td>";
    }
    if ($i == 0)
    {
      echo "<td rowspan=\"".pg_num_rows($types)."\" style=\"background-color:white\">howdi</td>\n";
    }
    echo "</tr>\n";
  }
  echo "</table>\n".
       "</form>\n";
}
htmlFooter()

?>
