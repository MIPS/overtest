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
// The search system for overtest

var searchfield = '';
var search1 = '';
var search2 = '';
var search3 = '';
var myFilterTerms = new Array();
var selectedFilterTerm = -1;
var myGroupTerms = new Array();
var selectedGroupTerm = -1;
var controlmode='';
var groupIdentifier='';
var simpleView=true;

function updateSearch1(value)
{
  $('search1').update('');
  $('search2').update('');
  $('search2header').update('');
  $('search3').update('');
  $('search3header').update('');
  searchfield=value;
  disableAddFilterButton();
  disableAddGroupButton();

  switch (searchfield)
  {
  case 'Action':
  case 'Version of Action':
    $('search1header').update('Action Category');
    break;
  case 'Testsuite Config Setting':
  case 'Other Config Setting':
    $('search1header').update('Option Group');
    break;
  case 'Resource Attribute':
  case 'Requested Resource Attribute':
    $('search1header').update('Resource Type');
    break;
  case 'Started After':
  case 'Started Before':
    $('search1header').update('Date');
    break;
  case 'User':
  case 'Testrun Group':
    enableAddGroupButton();
  case 'Testrun':
    $('search1header').update('User');
    break;
  case '':
    $('search1header').update('');
    return;
    break;
  }
  wait();
  new Ajax.Updater('search1', 'searchtestrunsajax.php',
                   { method: 'post',
                     parameters: {what: 'search1',
                                  searchfield: value,
                                  testsuiteid: testsuiteid},
                     onComplete: function(transport) { endwait(); } });
}
function updateSearch2(value)
{
  $('search2').update('');
  $('search3').update('');
  $('search3header').update('');
  disableAddFilterButton();
  disableAddGroupButton();
 
  switch (searchfield)
  {
  case 'Action':
  case 'Version of Action':
    $('search2header').update('Action');
    break;
  case 'Testsuite Config Setting':
  case 'Other Config Setting':
    $('search2header').update('Option');
    break;
  case 'Resource Attribute':
  case 'Requested Resource Attribute':
    $('search2header').update('Attribute');
    break;
  case 'Testrun Group':
  case 'Testrun':
    $('search2header').update('Testrun Group');
    break;
  case 'Started After':
  case 'Started Before':
  case 'User':
    search1 = value;
    enableAddFilterButton();
    return;
    break;
  case '':
    $('search2header').update('');
    return;
    break;
  }
  wait();
  new Ajax.Updater('search2', 'searchtestrunsajax.php',
                   { method: 'post',
                     parameters: {what: 'search2',
                                  searchfield: searchfield,
                                  search1value: value,
                                  testsuiteid: testsuiteid},
                     onComplete: function(transport) { endwait(); } });
}
function updateSearch3(value)
{
  $('search3').update('');
  disableAddFilterButton();
  disableAddGroupButton();

  switch (searchfield)
  {
  case 'Version of Action':
    search2 = value;
    enableAddGroupButton();
    $('search3header').update('Version');
    break;
  case 'Testsuite Config Setting':
  case 'Other Config Setting':
    enableAddGroupButton();
    search2 = value;
    $('search3header').update('Setting');
    break;
  case 'Resource Attribute':
  case 'Requested Resource Attribute':
    search2 = value;
    enableAddGroupButton();
    $('search3header').update('Value');
    break;
  case 'Testrun':
    $('search3header').update('Testrun');
    break;
  case 'Action':
    enableAddGroupButton();
  case 'Testrun Group':
    search2 = value;
    enableAddFilterButton();
    return;
    break;
  case '':
    $('search3header').update('');
    return;
    break;
  }
  wait();
  new Ajax.Updater('search3', 'searchtestrunsajax.php',
                   { method: 'post',
                     parameters: {what: 'search3',
                                  searchfield: searchfield,
                                  search2value: value,
                                  testsuiteid: testsuiteid},
                     onComplete: function(transport) { endwait(); } });
}
function updateSearch4(value)
{
  disableAddGroupButton();
  search3 = value;
  enableAddFilterButton();
}
function enableAddFilterButton()
{
  $('add_filter_button').show();
}
function disableAddFilterButton()
{
  $('add_filter_button').hide();
}
function enableAddGroupButton()
{
  $('add_group_button').show();
}
function disableAddGroupButton()
{
  $('add_group_button').hide();
}

function addGroupTerm(autosearch)
{
  tempsearchfield = searchfield
  if (searchfield == 'Requested Resource Attribute')
  {
    tempsearchfield = 'Resource Attribute';
  }
  else if (searchfield == 'Testsuite Config Setting' ||
           searchfield == 'Other Config Setting')
  {
    tempsearchfield = 'Config Setting';
  }
  else if (searchfield == 'Version of Action')
  {
    tempsearchfield = 'Action';
  }

  switch (tempsearchfield)
  {
  case 'User':
  case 'Testrun Group':
  case 'Simple Equivalence':
  case 'Recursive Equivalence':
  case 'Producer Equivalence':
    for (i = 0 ; i < myGroupTerms.length ; i++)
    {
      if (myGroupTerms[i][0] == tempsearchfield)
      {
        return;
      }
    }
    myGroupTerms.push(new Array(tempsearchfield));
    break;
  case 'Action':
  case 'Resource Attribute':
  case 'Config Setting':
    for (i = 0 ; i < myGroupTerms.length ; i++)
    {
      if (myGroupTerms[i][0] == tempsearchfield
          && myGroupTerms[i][1] == search2)
      {
        return;
      }
    }
    myGroupTerms.push(new Array(tempsearchfield,search2));
    break;
  }
  updateGroupTerms(autosearch);
}

function addSearchTerm(autosearch)
{
  if (myFilterTerms.length != 0)
  {
    myFilterTerms.push('and');
  }
  switch (searchfield)
  {
  case 'Started After':
  case 'Started Before':
  case 'User':
    myFilterTerms.push(new Array(searchfield,search1));
    break;
  case 'Action':
  case 'Testrun Group':
    myFilterTerms.push(new Array(searchfield,search2));
    break;
  case 'Version of Action':
  case 'Resource Attribute':
  case 'Requested Resource Attribute':
  case 'Testrun':
    myFilterTerms.push(new Array(searchfield,search3));
    break;
  case 'Testsuite Config Setting':
  case 'Other Config Setting':
    myFilterTerms.push(new Array(searchfield,search2,search3));
    break;
  }
  updateFilterTerms(autosearch);
}

function updateFilterTerms(autosearch)
{
  wait();
  setSearchDirty();
  new Ajax.Updater('filter_strings', 'searchtestrunsajax.php',
                   { method: 'post',
                     parameters: {what: 'show_filter_string',
                                  filterstring: Object.toJSON(myFilterTerms)},
                     onComplete: function(transport)
                                 { 
                                   newSelection = selectedFilterTerm;
                                   selectedFilterTerm = -1;
                                   selectFilterTerm(newSelection);
                                   if (autosearch)
                                   {
                                     search();
                                   }
                                   endwait();
                                 } });
}
function updateGroupTerms(autosearch)
{
  wait();
  wait();
  new Ajax.Updater('group_strings', 'searchtestrunsajax.php',
                   { method: 'post',
                     parameters: {what: 'show_group_string',
                                  groupstring: Object.toJSON(myGroupTerms)},
                     onComplete: function(transport)
                                 { 
                                   newSelection = selectedGroupTerm;
                                   selectedGroupTerm = -1;
                                   selectGroupTerm(newSelection);
                                   if (autosearch)
                                   {
                                     if (!checkBrackets())
                                     {
                                       setSearchDirty();
                                     }
                                     else
                                       search();
                                   }
                                   endwait();
                                 } });
  new Ajax.Updater('showstabilitylevel', 'viewresultsajax.php',
                   { method: 'post',
                     parameters: {what: 'show_group_combo',
                                  groupstring: Object.toJSON(myGroupTerms),
                                  stabilitylevel: stabilityLevel },
                     onComplete: function(transport)
                                 { 
                                   endwait();
                                 } });

}


function selectFilterTerm(index)
{
  brackets_ok = checkBrackets();
  if (selectedFilterTerm != -1)
  {
    $('searchterm'+selectedFilterTerm).setStyle({backgroundColor: 'white'});
  }
  selectedFilterTerm = index;
  if (selectedFilterTerm == -1)
  {
    $('add_right_bracket').hide();
    $('move_up').hide();
    $('add_left_bracket').hide();
    $('move_down').hide();
    $('remove_term').hide();
    $('change_to_and').hide();
    $('change_to_or').hide();
    $('add_not').hide();
    return;
  }
  else
  {
    selectGroupTerm(-1);
  }
  $('searchterm'+index).setStyle({backgroundColor: '#8080ff'});
  controlmode='filter';

  switch (myFilterTerms[selectedFilterTerm])
  {
  case 'and':
  case 'or':
    $('add_right_bracket').hide();
    $('move_up').hide();
    $('add_left_bracket').hide();
    $('move_down').hide();
    $('remove_term').hide();
    $('add_not').hide();

    if (myFilterTerms[selectedFilterTerm] == 'and')
    {
      $('change_to_and').hide();
      $('change_to_or').show();
    }
    else
    {
      $('change_to_and').show();
      $('change_to_or').hide();
    }
    break;
  case '(':
  case ')':
  case 'not':
    $('add_right_bracket').hide();
    $('move_up').hide();
    if (myFilterTerms[selectedFilterTerm] == 'not')
    {
      $('add_left_bracket').show();
    }
    else
    {
      $('add_left_bracket').hide();
    }
    $('move_down').hide();
    $('change_to_and').hide();
    $('change_to_or').hide();
    if (myFilterTerms[selectedFilterTerm] == '(')
    {
      $('add_not').show();
    }
    else
    {
      $('add_not').hide();
    }
    $('remove_term').show();
    break;
  default:
    $('change_to_and').hide();
    $('change_to_or').hide();
    $('add_not').show();
    can_move_up = false;
    for (i = index-1 ; i >= 0 ; i--)
    {
      if (myFilterTerms[i].constructor == Array)
      {
        can_move_up = true;
        break;
      }
    }
    can_move_down = false;
    for (i = index+1 ; i < myFilterTerms.length ; i++)
    {
      if (myFilterTerms[i].constructor == Array)
      {
        can_move_down = true;
        break;
      }
    }
    has_left_bracket = (index != 0 && myFilterTerms[index-1] == '(');
    has_right_bracket = (index != myFilterTerms.length-1 && myFilterTerms[index+1] == ')');
    if (can_move_up)
    {
      $('add_right_bracket').show();
      $('move_up').show();
    }
    else
    {
      $('add_right_bracket').hide();
      $('move_up').hide();
    }
    if (can_move_down)
    {
      $('add_left_bracket').show();
      $('move_down').show();
    }
    else
    {
      $('add_left_bracket').hide();
      $('move_down').hide();
    }
    if (brackets_ok)
    {
      $('remove_term').show();
    }
    else
    {
      $('remove_term').hide();
    }
  }
}

function selectGroupTerm(index)
{
  brackets_ok = checkBrackets();
  if (selectedGroupTerm != -1)
  {
    $('groupterm'+selectedGroupTerm).setStyle({backgroundColor: 'white'});
  }
  selectedGroupTerm = index;

  if (selectedGroupTerm == -1)
  {
    $('add_right_bracket').hide();
    $('move_up').hide();
    $('add_left_bracket').hide();
    $('move_down').hide();
    $('remove_term').hide();
    $('change_to_and').hide();
    $('change_to_or').hide();
    $('add_not').hide();
    return;
  }
  else
  {
    selectFilterTerm(-1);
  }
  $('groupterm'+index).setStyle({backgroundColor: '#8080ff'});
  controlmode='group';

  $('remove_term').show();

  if (index != 0)
  {
    $('move_up').show();
  }
  else
  {
    $('move_up').hide();
  }
  if (index != myGroupTerms.length-1)
  {
    $('move_down').show()
  }
  else
  {
    $('move_down').hide()
  }

}

function checkBrackets()
{
  bracketCount = 0;
  for (i = 0 ; i < myFilterTerms.length ; i++)
  {
    if (myFilterTerms[i] == '(')
    {
      bracketCount++;
    }
    else if (myFilterTerms[i] == ')')
    {
      bracketCount--;
    }
    if (bracketCount < 0)
    {
      break;
    }
  }
  if (bracketCount != 0)
  {
    $('search_results_button').hide();
    $('bracket_match_error').show();
    $('filter_empty_error').hide();
    return false;
  }
  else if (myFilterTerms.length == 0)
  {
    $('search_results_button').hide();
    $('bracket_match_error').hide();
    $('filter_empty_error').show();
    return false;
  }
  else
  {
    checkBracketsCallback();
    $('search_results_button').show();
    $('bracket_match_error').hide();
    $('filter_empty_error').hide();
    return true;
  }
}
function addSearchTermLeftBracket()
{
  myFilterTerms.splice(selectedFilterTerm, 0, '(');
  selectedFilterTerm++;
  updateFilterTerms(false);
}
function addSearchTermNot()
{
  myFilterTerms.splice(selectedFilterTerm, 0, 'not');
  selectedFilterTerm++;
  updateFilterTerms(false);
}
function addSearchTermRightBracket()
{
  myFilterTerms.splice(selectedFilterTerm+1, 0, ')');
  updateFilterTerms(false);
}
function toggleAndOr()
{
  if (myFilterTerms[selectedFilterTerm] == 'and')
  {
    myFilterTerms[selectedFilterTerm] = 'or';
  }
  else
  {
    myFilterTerms[selectedFilterTerm] = 'and';
  }
  updateFilterTerms(false);
}
function removeTerm()
{
  if (controlmode == 'filter')
  {
    switch (myFilterTerms[selectedFilterTerm])
    {
    case '(':
    case ')':
    case 'not':
      myFilterTerms.splice(selectedFilterTerm, 1);
      break;
    default:
      if (selectedFilterTerm != 0 && myFilterTerms[selectedFilterTerm-1] == '(')
      {
        if (myFilterTerms[selectedFilterTerm+1] == ')')
        {
          myFilterTerms.splice(selectedFilterTerm+1,1);
          myFilterTerms.splice(selectedFilterTerm-1,1);
          selectedFilterTerm--;
          removeTerm();
          return;
        }
        else
        {
          myFilterTerms.splice(selectedFilterTerm,2);
        }
      }
      else if (selectedFilterTerm > 1 && myFilterTerms[selectedFilterTerm-1] == 'not' && myFilterTerms[selectedFilterTerm-2] == '(')
      {
        if (myFilterTerms[selectedFilterTerm+1] == ')')
        {
          myFilterTerms.splice(selectedFilterTerm+1,1);
          myFilterTerms.splice(selectedFilterTerm-2,1);
          selectedFilterTerm--;
          removeTerm();
          return;
        }
        else
        {
          myFilterTerms.splice(selectedFilterTerm-1,3);
        }     
      }
      else if (selectedFilterTerm == 0)
      {
        myFilterTerms.splice(0,2);
      }
      else if (selectedFilterTerm == 1 && myFilterTerms[0] == 'not')
      {
        myFilterTerms.splice(0,3);
      }
      else
      {
        if (myFilterTerms[selectedFilterTerm-1] == 'not')
        {
          myFilterTerms.splice(selectedFilterTerm-2,3);
        }
        else
        {
          myFilterTerms.splice(selectedFilterTerm-1,2);
        }
      }
    }
    selectedFilterTerm = -1;
    updateFilterTerms(false);
  }
  else if (controlmode == 'group')
  {
    myGroupTerms.splice(selectedGroupTerm,1);
    selectedGroupTerm = -1;
    updateGroupTerms(true);
  }
}
function moveTermUp()
{
  if (controlmode == 'filter')
  {
    /* Find the previous term */
    previousterm = selectedFilterTerm-1;
    for (previousterm = selectedFilterTerm-1 ; previousterm >= 0 ; previousterm--)
    {
      if (myFilterTerms[previousterm].constructor == Array)
      {
        break;
      }
    }
    prevtermarray = myFilterTerms[previousterm];
    myFilterTerms[previousterm] = myFilterTerms[selectedFilterTerm];
    myFilterTerms[selectedFilterTerm] = prevtermarray;
    selectedFilterTerm = previousterm;
    updateFilterTerms(false);
  }
  else if (controlmode == 'group')
  {
    prevtermarray = myGroupTerms[selectedGroupTerm-1];
    myGroupTerms[selectedGroupTerm-1] = myGroupTerms[selectedGroupTerm];
    myGroupTerms[selectedGroupTerm] = prevtermarray;
    selectedGroupTerm = selectedGroupTerm-1;
    updateGroupTerms(true);
  }
}
function moveTermDown()
{
  if (controlmode == 'filter')
  {
    /* Find the next term */
    nextterm = selectedFilterTerm+1;
    for (nextterm = selectedFilterTerm+1 ; nextterm < myFilterTerms.length ; nextterm++)
    {
      if (myFilterTerms[nextterm].constructor == Array)
      {
        break;
      }
    }
    nexttermarray = myFilterTerms[nextterm];
    myFilterTerms[nextterm] = myFilterTerms[selectedFilterTerm];
    myFilterTerms[selectedFilterTerm] = nexttermarray;
    selectedFilterTerm = nextterm;
    updateFilterTerms(false);
  }
  else if (controlmode == 'group')
  {
    nexttermarray = myGroupTerms[selectedGroupTerm+1];
    myGroupTerms[selectedGroupTerm+1] = myGroupTerms[selectedGroupTerm];
    myGroupTerms[selectedGroupTerm] = nexttermarray;
    selectedGroupTerm = selectedGroupTerm+1;
    updateGroupTerms(true);
  }
}
function selectGrouping(identifier)
{
  groupIdentifier = identifier;
  idtype=identifier.substring(0,2);
  if (idtype == 'co')
  {
    searchfield = 'Other Config Setting';
  }
  else if (idtype == 'ra')
  {
    searchfield = 'Requested Resource Attribute';
  }
  else if (idtype == 'ac')
  {
    searchfield = 'Version of Action';
  }
  else if (idtype == 'gr')
  {
    searchfield = 'Testrun Group';
  }
  else if (idtype == 'us')
  {
    searchfield = 'User';
  }
  else if (idtype == 'se')
  {
    searchfield = 'Simple Equivalence';
  }
  else if (idtype == 're')
  {
    searchfield = 'Recursive Equivalence';
  }
  else if (idtype == 'pe')
  {
    searchfield = 'Producer Equivalence';
  }
  else
  {
    alert ('Unknown identifier'+identifier);
    return;
  }
  search2 = identifier.substring(2); 
  $('add_group_button_simple').show();
  wait();
  new Ajax.Updater('filter_list', 'searchtestrunsajax.php',
                   { method: 'post',
                     parameters: {what: 'get_filter_list',
                                  testsuiteid: testsuiteid,
                                  searchfield: searchfield,
                                  search2: search2},
                     onComplete: function(transport) { endwait(); } });
 
}
function selectFilter(value)
{
  $('add_filter_button_simple').show();
  switch (searchfield)
  {
  case 'User':
    search1 = value;
    break;
  case 'Testrun Group':
    search2 = value;
    break;
  case 'Version of Action':
  case 'Requested Resource Attribute':
    search3 = value;
    break;
  case 'Other Config Setting':
    search3 = value;
    break;
  }
}
function toggleView()
{
  simpleView = !simpleView;

  $('search1').update('');
  $('search1header').update('');
  $('search2').update('');
  $('search2header').update('');
  $('search3').update('');
  $('search3header').update('');
  $('searchfield').setValue('');

  searchfield = '';
  search1 = '';
  search2 = '';
  search3 = '';

  if (simpleView)
  {
    $('toggle_view').update('Advanced View');
    $('advanced_search').hide();
    $('simple_search').show();
  }
  else
  {
    $('toggle_view').update('Simple View');
    $('advanced_search').show();
    $('simple_search').hide();
  }
}
