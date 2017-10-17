<?php

function htmlHeader($title, $onload="", $help="")
{
  global $ovtDB;
  echo "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\" \"http://www.w3.org/TR/html4/strict.dtd\">\n".
       "<html>\n".
       "<head>\n".
       "<meta http-equiv=\"content-type\" content=\"text/html; charset=UTF-8\">\n".
       "<title>Overtest - ".$title."</title>\n".
       "<script type=\"text/javascript\" src=\"/scripts/prototype.js\"></script>\n".
       "<script type=\"text/javascript\" src=\"/scripts/common.js\"></script>\n".
       "<link rel=\"StyleSheet\" href=\"/style.css\" type=\"text/css\" media=\"screen,print\">\n".
       "</head>\n".
       "<body id=\"main\"";
  if ($onload != "")
  {
    echo " onload=\"".$onload."\"";
  }
  echo ">\n";
  echo "<div id=\"LayoutTop\">\n".
       "<div class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"height:100px\" class=\"boxTopLeft\">\n".

       "<div id=\"Logo\">\n".
       "<a href=\"/index.php\"><img alt=\"Overtest\" src=\"/images/logo.gif\">\n</a>".
       "</div>\n".
       "<div id=\"ErrorMessage\">\n".
       "</div>\n".
       "<div id=\"ContentTop\">\n".
       "  <h1>Overtest - Test automation framework</h1>\n".
       "  <p class=\"loginStatus\">";
  if (!isset($_SESSION['auth_userid']))
  {
    echo "You are currently not logged in";
  }
  else
  {
    $sql = "SELECT fname || ' ' || sname AS name\n".
           "FROM ovt_user\n".
           "WHERE userid='".$_SESSION['auth_userid']."'";
    $result = pg_query($ovtDB, $sql);
    echo "You are logged in as ".pg_fetch_result($result, 0, "name");
  }
  echo "</p>\n".
       "  <p id=\"Menu\">\n".
       "    <span class=\"item\"><a href=\"/index.php\">Menu</a></span>\n".
       "    | <span class=\"item\"><a href=\"/viewtestsuites.php\">Testsuites</a></span>\n".
       "    | <span class=\"item\"><a href=\"/viewresources.php\">Resources</a></span>\n".
       "    | <span class=\"item\"><a href=\"/devstatus.php\">Development</a></span>\n";
  if (!isset($_SESSION['auth_userid']))
  {
    echo "    | <span class=\"item\"><a href=\"/login.php\">Login</a></span>\n";
  }
  else
  {
    echo "    | <span class=\"item\"><a href=\"/preferences.php\">Preferences</a></span>\n";
    echo "    | <span class=\"item\"><a href=\"/php/dologout.php\">Logout</a></span>\n";
  }
  echo "    | <span class=\"item\"><a href=\"/docs/\">API</a></span>\n";
  echo "    | <span class=\"item\"><a target=\"_new\" href=\"";
  if ($help == "")
  {
    echo "/help.php";
  }
  else
  {
    echo $help;
  }
  echo "\">Help</a></span>\n".
       "  </p>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "<p style=\"clear:both\"></p>\n".
       "<div id=\"ContentMain\">\n".
       "<div class=\"boxTop\">\n".
       "<div class=\"boxLeft\">\n".
       "<div class=\"boxBottom\">\n".
       "<div class=\"boxRight\">\n".
       "<div class=\"boxTopRight\">\n".
       "<div class=\"boxTopLeft\">\n".
       "<div class=\"boxBottomRight\">\n".
       "<div class=\"boxBottomLeft\">\n".
       "<div style=\"padding:10px;\">\n";

}

function htmlFooter()
{

  echo "</div>\n".
       "<p style=\"clear:both\"></p>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "</div>\n".
       "<p style=\"clear:both\"></p>\n".
       "</body>\n".
       "</html>";
  exit(0);
}
?>
