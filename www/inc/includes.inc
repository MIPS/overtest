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
session_start();
header ("Expires: Tue, 10 Sep 2002 00:00:00 GMT"); // date in the past
header ("Last-Modified: " . gmdate ("D, d M Y H:i:s") . " GMT"); // changes always
header ("Cache-Control: no-cache, must-revalidate");  // HTTP/1.1
header ("Pragma: no-cache");

$overtestroot="/home/overtest/root/";

include_once('connect_overtestdb_webuser.inc');
include_once('htmlHeadFoot.inc');

?>
