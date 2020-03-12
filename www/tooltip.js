/* Copyright (C) 2012-2020 MIPS Tech LLC
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
   02110-1301, USA.  */
document.write("<div id=\"ttip\" style=\"display:none;border:1px solid black;background-color:white;position:absolute;max-width:200px;\"><\/div>");

xBump=yBump=10;
MSIE=document.all;
NS6=document.getElementById&&!document.all;

if(MSIE||NS6){
 ttipObj=document.all?document.all["ttip"]:document.getElementById?document.getElementById("ttip"):"";
}

function MSIEBodyReturn(){
 return(document.compatMode&&document.compatMode!="BackCompat")?document.documentElement:document.body;
}

function ShowTip(ttipText){
 ttipObj.innerHTML=ttipText;
 ttipObj.style.display="block";
 return false;
}

function MoveTip(e){
 xPos=(NS6)?e.pageX:event.x+MSIEBodyReturn().scrollLeft;
 yPos=(NS6)?e.pageY:event.y+MSIEBodyReturn().scrollTop;
 lEdge=(xBump<0)?xBump*(-1):-1000;
 rEdge=MSIE&&!window.opera?MSIEBodyReturn().clientWidth-event.clientX-xBump:window.innerWidth-e.clientX-xBump-20;
 bEdge=MSIE&&!window.opera?MSIEBodyReturn().clientHeight-event.clientY-yBump:window.innerHeight-e.clientY-yBump-20;
 if(rEdge<ttipObj.offsetWidth){
  ttipObj.style.left=MSIE?MSIEBodyReturn().scrollLeft+event.clientX-ttipObj.offsetWidth+"px":window.pageXOffset+e.clientX-ttipObj.offsetWidth+"px";
 }
 else if(xPos<lEdge){
  ttipObj.style.left=xBump+"px";
 }
 else{
  ttipObj.style.left=xPos+xBump+"px";
 }
 if(bEdge<ttipObj.offsetHeight){
  ttipObj.style.top=MSIE?MSIEBodyReturn().scrollTop+event.clientY-ttipObj.offsetHeight-yBump+"px":window.pageYOffset+e.clientY-ttipObj.offsetHeight-yBump+"px";
 }
 else{
  ttipObj.style.top=yPos+yBump+"px";
 }
}

function HideTip(){
 if(MSIE||NS6){
  ttipObj.style.display="none";
  ttipObj.innerText="";
 }
}


document.onmousemove=MoveTip;
