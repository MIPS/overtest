import postgresql.interface.proboscis.dbapi2 as dbapi2
import postgresql.strings as pg_str
import postgresql.exceptions
import types
from OvertestExceptions import *
import time
import socket
import re
from copy import copy

class Condition:
  def __init__(self, column, values):
    self.column = column
    self.values = values

class InCondition(Condition):
  def sql_string(self):
    return " IN ( %s )" % (', '.join(["%s"] * len(self.values)))

  def get_values(self):
    return self.values

class EqualCondition(Condition):
  def sql_string(self):
    return " = %s"

  def get_values(self):
    return [self.values]

class LikeCondition(Condition):
  def sql_string(self):
    return " LIKE %s"

  def get_values(self):
    return [self.values]

class OvtDBObject:
  def __init__(self, **kwargs):
    for member in self.member_to_col.keys():
      setattr(self, member, None)
      if member in kwargs:
        setattr(self, member, kwargs[member])
      else:
        raise AttributeError(member)

  @classmethod
  def all(cls, db):
    return cls.find(db)

  @classmethod
  def find(cls, db, **kwargs):
    sql = "SELECT " + ', '.join(cls.col_to_member.keys()) + " FROM " + cls.table
    conditions = []
    for x, y in kwargs.items():
      if x in cls.member_to_col:
        if isinstance(y, tuple):
          c = InCondition(cls.member_to_col[x], y)
        elif isinstance(y, Condition):
          c = copy(y)
          c.column = cls.member_to_col[x]
        else:
          c = EqualCondition(cls.member_to_col[x], y)
        conditions.append (c)
      else:
        raise AttributeError(x)

    if conditions:
      sql += " WHERE "
      cond_str = [ "%s%s"%(x.column,x.sql_string()) for x in conditions]
      sql += ' AND '.join(cond_str)
    values = [ y for x in conditions for y in x.get_values() ]
    # print sql, values
    db.execute(sql, tuple(values))
    rows = db.cursor.fetchall()
    if len(rows) > 0:
      return [ cls(**dict(zip(cls.col_to_member.values(), row))) for row in rows ]
    else:
      return None

  @classmethod
  def find_one(cls, db, **kwargs):
    lst = cls.find(db, **kwargs)
    if len(lst) == 0:
      return None
    assert len(lst) == 1
    return lst[0]

  def __str__(self):
    return "<%s %s>" % (self.__class__.__name__, ', '.join(["%s=%s"%(x,getattr(self,x)) for x in self.member_to_col.keys()]))

class OvtDBUser(OvtDBObject):
  table = "ovt_user"
  col_to_member = dict([("userid",        "id"),
                        ("username",      "name"),
                        ("fname",         "fname"),
                        ("sname",         "sname"),
                        ("altnames",      "altnames"),
                        ("email",         "email"),
                        ("growlhost",     "growlhost"),
                        ("growlpassword", "growlpassword"),
                       ])
  member_to_col = dict([(y,x) for x, y in col_to_member.items()])

class OvtDBAction(OvtDBObject):
  table = "ovt_action"
  col_to_member = dict([("actionid",         "id"),
                        ("actionname",       "name"),
                        ("shortname",        "shortname"),
                        ("actioncategoryid", "actioncategoryid"),
                        ("testsuiteid",      "testsuiteid"),
                        ("issecure",         "issecure"),
                        ("lifecyclestateid", "lifecyclestateid"),
                       ])
  member_to_col = dict([(y,x) for x, y in col_to_member.items()])

  def lifecyclestate(self, db):
    assert self.lifecyclestateid != None
    return self.find_one (db, id=self.lifecyclestateid)

  def versions(self, db, **kwargs):
    assert self.id != None
    return OvtDBVersionedAction.find(db, actionid=self.id, **kwargs)

class OvtDBActionCategory(OvtDBObject):
  table = "ovt_actioncategory"
  col_to_member = dict([("actioncategoryid",   "id"),
                        ("actioncategoryname", "name"),
                        ("lifecyclestateid",   "lifecyclestateid"),
                       ])
  member_to_col = dict([(y,x) for x, y in col_to_member.items()])

  def lifecyclestate(self, db):
    assert self.lifecyclestateid != None
    return OvtDBLifeCycleState.find_one (db, id=self.lifecyclestateid)

  def actions(self, db, **kwargs):
    assert self.id != None
    return OvtDBAction.find(db, actioncategoryid=self.id, **kwargs)

class OvtDBLifeCycleState(OvtDBObject):
  table = "ovt_lifecyclestate"
  col_to_member = dict([("lifecyclestateid",   "id"),
                        ("lifecyclestatename", "name"),
                        ("visible",            "visible"),
                        ("visiblebydefault",   "visiblebydefault"),
                        ("valid",              "valid"),
                       ])
  member_to_col = dict([(y,x) for x, y in col_to_member.items()])

class OvtDBTestrun(OvtDBObject):
  table = "ovt_testrun"
  col_to_member = dict([("testrunid",                 "id"),
                        ("userid",                    "userid"),
                        ("template",                  "template"),
                        ("testdate",                  "testdate"),
                        ("priority",                  "priority"),
                        ("createddate",               "createdate"),
                        ("startafter",                "startafter"),
                        ("completeddate",             "completeddate"),
                        ("runstatusid",               "runstatusid"),
                        ("concurrency",               "concurrency"),
                        ("description",               "description"),
                        ("testrungroupid",            "testrungrouppid"),
                        ("autoarchive",               "autoarchive"),
                       ])
  member_to_col = dict([(y,x) for x, y in col_to_member.items()])

  def testrun_actions(self, db):
    assert self.id != None
    return OvtDBTestrunAction.find (db, testrunid=self.id)

  def testrun_action_version_actions(self, db):
    assert self.id != None
    return OvtDBTestrunAction_VersionedAction_Action.find (db, testrun_action_testrunid=self.id)

class OvtDBTestrunAction(OvtDBObject):
  table = "ovt_testrunaction"
  col_to_member = dict([("testrunactionid",           "id"),
                        ("testrunid",                 "testrunid"),
                        ("versionedactionid",         "versionedactionid"),
                        ("modified",                  "modified"),
                        ("pid",                       "pid"),
                        ("providedbytestrunid",       "providedbytestrunid"),
                        ("starteddate",               "starteddate"),
                        ("completeddate",             "completeddate"),
                        ("passed",                    "passed"),
                        ("archived",                  "archived"),
                        ("simpleequivalenceid",       "simpleequivalenceid"),
                        ("recursiveequivalenceid",    "recursiveequivalenceid"),
                        ("subrecursiveequivalenceid", "subrecursiveequivalenceid"),
                       ])
  member_to_col = dict([(y,x) for x, y in col_to_member.items()])

  def testrun(self, db):
    assert self.id != None
    return OvtDBTestrun.find_one (db, id=self.testrunid)

  def version(self, db):
    assert self.id != None
    return OvtDBVersionedAction.find_one(db, id=self.versionedactionid)

class OvtDBVersionedAction(OvtDBObject):
  table = "ovt_versionedaction"
  col_to_member = dict([("versionedactionid", "id"),
                        ("versionname",       "name"),
                        ("actionid",          "actionid"),
                        ("lifecyclestateid",  "lifecyclestateid"),
                       ])
  member_to_col = dict([(y,x) for x, y in col_to_member.items()])

  def lifecyclestate(self, db):
    assert self.lifecyclestateid != None
    return OvtDBLifeCycleState.find_one (db, id=self.lifecyclestateid)

  def action(self, db):
    assert self.id != None
    return OvtDBAction.find_one (db, id=self.actionid)

  def testrun_actions(self, db):
    assert self.id != None
    return OvtDBTestrunAction.find (db, versionedactionid=self.id)

  def testrun_actions_testrun(self, db):
    assert self.id != None
    return OvtDBTestrunAction_Testrun.find (db, testrun_action_versionedactionid=self.id)

  @staticmethod
  def sortkey(value):
    lst = re.compile("[. ]").split(value.name)
    for i in range(len(lst)):
      try:
        lst[i] = int(lst[i])
      except ValueError:
        pass
    return tuple(lst)

class OvtDBMultiObject(OvtDBObject):
  def split(self):
    obj = dict([(x, {}) for x in self.obj_order])
    for member, map in self.member_to_obj.items():
      object, other_member = map
      obj[object][other_member] = getattr(self, member)

    lst = []
    for object_name in self.obj_order:
      lst.append (self.obj_to_classes[object_name](**obj[object_name]))
    return tuple(lst)

def make_multi_object_class(name, member_cls_lst, object_name_lst, join_lst):
  new_col_to_member = {}
  new_member_to_obj = {}
  for member_cls, object_name in zip(member_cls_lst, object_name_lst):
    for col, member in member_cls.col_to_member.items():
      member_name = "%s_%s" % (object_name,member)
      new_col_to_member["%s.%s" % (member_cls.table,col)] = member_name
      new_member_to_obj[member_name] = (object_name, member)

  # [a,b,c], [d, e] -> ' '.join([a,'JOIN',b,d,'JOIN',c,e])
  new_table = "%s" % member_cls_lst[0].table
  for t,j in zip(member_cls_lst[1:], join_lst):
    new_table += " JOIN %s %s" % (t.table, j)

  new_member_to_col = dict([(y,x) for x, y in new_col_to_member.items()])
  new_obj_to_classes = dict([(x, y) for x, y in zip (object_name_lst, member_cls_lst)])

  class cls(OvtDBMultiObject):
    table = new_table
    col_to_member = new_col_to_member
    member_to_col  = new_member_to_col
    obj_order = object_name_lst
    obj_to_classes = new_obj_to_classes
    member_to_obj = new_member_to_obj
  cls.__name__ = name

  return cls

OvtDBActionCategory_Action_VersionedAction = make_multi_object_class ('OvtDBActionCategory_Action_VersionedAction',
                                                                      [OvtDBActionCategory, OvtDBAction, OvtDBVersionedAction],
                                                                      ["category",          "action",    "version"],
                                                                      ["USING (actioncategoryid)", "USING (actionid)"])

OvtDBTestrunAction_VersionedAction_Action = make_multi_object_class ('OvtDBTestrunAction_VersionedAction_Action',
                                                                     [OvtDBTestrunAction, OvtDBVersionedAction, OvtDBAction],
                                                                     ["testrun_action",   "version",            "action"],
                                                                     ["USING (versionedactionid)", "USING (actionid)"])

OvtDBTestrunAction_Testrun = make_multi_object_class ('OvtDBTestrunAction_Testrun',
                                                      [OvtDBTestrunAction, OvtDBTestrun],
                                                      ["testrun_action",   "testrun"],
                                                      ["USING (testrunid)"])
# KNOWN BUGS:
# 1) There must be a transaction around any INSERT and the following SELECT currval to ensure atomicity
#    of inserts. This is not handled currently

class OvtDBSimple:
  def __init__(self, db):
    self.db = db

  def _getXByName(table, return_col, search_col):
    def fn(self, name):
      sql = "SELECT "+return_col+" FROM "+table+" WHERE "+search_col+"=%s LIMIT 1"
      self.db.execute(sql, (name))
      rows = self.db.cursor.fetchall()
      if len(rows) > 0:
        return rows[0][return_col]
      return None
    return fn

  def _getXByWildcard(table, return_col, search_col):
    def fn(self, name):
      sql = "SELECT "+search_col+","+return_col+" FROM "+table+" WHERE "+search_col+" LIKE %s"
      self.db.execute(sql, (name))
      rows = self.db.cursor.fetchall()
      if len(rows) > 0:
        return [ (x[search_col], x[return_col]) for x in rows ]
      return None
    return fn

  def _getXAttrById(table, search_col, return_cols, where=None):
    def fn(self, id):
      sql = "SELECT "+','.join(return_cols)+" FROM "+table+" WHERE "+search_col+"=%s "
      if where != None:
        sql += "AND " + where + " "
      sql += "LIMIT 1"
      self.db.execute(sql, (id))
      rows = self.db.cursor.fetchall()
      if len(rows) > 0:
        if len(return_cols) == 1:
          return rows[0][return_cols[0]]
        else:
          return rows[0]
      return None
    return fn

  def _getXByParentIdAndName(table, return_col, parent_search_col, search_col):
    def fn(self, parent_id, name):
      sql = "SELECT "+return_col+" FROM "+table+" WHERE " \
          + parent_search_col + "=%s AND " \
          + search_col        + "=%s " \
          + "LIMIT 1"
      self.db.execute(sql, (parent_id, name))
      rows = self.db.cursor.fetchall()
      if len(rows) > 0:
        return rows[0][return_col]
      return None
    return fn

  def _getXByParentIdAndWildcard(table, return_col, parent_search_col, search_col):
    def fn(self, parent_id, name):
      sql = "SELECT "+search_col+","+return_col+" FROM "+table+" WHERE " \
          + parent_search_col + "=%s AND " \
          + search_col        + " LIKE %s "
      self.db.execute(sql, (parent_id, name))
      rows = self.db.cursor.fetchall()
      if len(rows) > 0:
        return [ (x[search_col], x[return_col]) for x in rows ]
      return None
    return fn

  def _getLinkXToY(table, id, from_col, to_col):
    def fn(self, from_id, to_id):
      sql = "SELECT "+id+" FROM "+table+" WHERE " \
          + from_col + "=%s AND " \
          + to_col   + "=%s " \
          + "LIMIT 1"
      self.db.execute(sql, (from_id, to_id))
      rows = self.db.cursor.fetchall()
      if len(rows) > 0:
        return rows[0][id]
      return None
    return fn

  def _getXsByY(table, to_col, from_col):
    def fn(self, from_id):
      sql = "SELECT DISTINCT "+to_col+" FROM "+table+" WHERE "\
          + from_col + "=%s"
      self.db.execute(sql, (from_id))
      rows = self.db.cursor.fetchall()
      if len(rows) > 0:
        return [ x[to_col] for x in rows ]
      else:
        return None
    return fn

  def _setXY(table, search_col, val_col):
    def fn(self, name, val):
      sql = "UPDATE "+table+" SET "+val_col+"=%s WHERE "+search_col+"=%s"
      self.db.execute(sql, (val, name))
    return fn

  getTestrunGroupByName    = _getXByName("ovt_testrungroup",    "testrungroupid",    "testrungroupname")
  getActionCategoryByName    = _getXByName("ovt_actioncategory",    "actioncategoryid",    "actioncategoryname")
  getConfigOptionGroupByName = _getXByName("ovt_configoptiongroup", "configoptiongroupid", "configoptiongroupname")
  getResourceTypeByName      = _getXByName("ovt_resourcetype",      "resourcetypeid",      "resourcetypename")
  getDependencyGroupByName   = _getXByName("ovt_dependencygroup",   "dependencygroupid",   "dependencygroupname")
  getRunstatusByName         = _getXByName("ovt_runstatus",         "runstatusid",         "status")

  getActionCategoryByWildcard = _getXByWildcard("ovt_actioncategory",   "actioncategoryid",    "actioncategoryname")

  getActionCategoryById       = _getXAttrById("ovt_actioncategory", "actioncategoryid", ["actioncategoryname"])
  getTestsuiteById            = _getXAttrById("ovt_testsuite",      "testsuiteid",      ["testsuitename"])
  getTestrunById              = _getXAttrById("ovt_testrun",        "testrunid",        ["description", "priority", "concurrency", "deptestrunid", "autoarchive", "usegridengine", "userid", "testrungroupid"])
  getRunstatusById            = _getXAttrById("ovt_runstatus",      "runstatusid",      ["iseditable","goenabled","pauseenabled","abortenabled","archiveenabled","deleteenabled","checkenabled","externalenabled","equivcheck","isverbose"])
  getTestrunGroupById         = _getXAttrById("ovt_testrungroup",   "testrungroupid",   ["testrungroupname"])
  getDependencyAttributesById = _getXAttrById("ovt_dependency",     "dependencyid",     ['hostmatch', 'versiononly', 'defaultdep', 'dependencygroupid', 'versionedactionid', 'versionedactiondep'])
  getResourceTypeById         = _getXAttrById("ovt_resourcetype",   "resourcetypeid",   ['resourcetypename'])
  getAttributeById            = _getXAttrById("ovt_attribute",      "attributeid",      ['resourcetypeid', 'attributename', 'lookup'])
  getAttributeValueById       = _getXAttrById("ovt_attributevalue", "attributevalueid", ['attributeid', 'value'])

  getUserById                 = _getXAttrById("ovt_user",           "userid",           ['username','growlpassword','growlhost','email'])

  getActionByName             = _getXByParentIdAndName("ovt_action",            "actionid",            "actioncategoryid",    "actionname")
  getVersionedActionByName    = _getXByParentIdAndName("ovt_versionedaction",   "versionedactionid",   "actionid",            "versionname")
  getConfigOptionByName       = _getXByParentIdAndName("ovt_configoption",      "configoptionid",      "configoptiongroupid", "configoptionname")
  getConfigOptionLookupByName = _getXByParentIdAndName("ovt_configoptionlookup","configoptionlookupid","configoptionid",      "lookupname")
  getAttributeByName          = _getXByParentIdAndName("ovt_attribute",         "attributeid",         "resourcetypeid",      "attributename")
  getAttributeValueByName     = _getXByParentIdAndName("ovt_attributevalue",    "attributevalueid",    "attributeid",         "value")

  getActionByWildcard          = _getXByParentIdAndWildcard("ovt_action",          "actionid",          "actioncategoryid",    "actionname")
  getVersionedActionByWildcard = _getXByParentIdAndWildcard("ovt_versionedaction", "versionedactionid", "actionid",            "versionname")

  getLinkVersionedActionToConfigOption = _getLinkXToY("ovt_versionedactionconfigoption",
                                                      "versionedactionconfigoptionid",
                                                      "versionedactionid",
                                                      "configoptionid")
  getLinkVersionedActionToConfigOptionLookup = _getLinkXToY("ovt_versionedactionconfigoptionlookup",
                                                            "versionedactionconfigoptionlookupid",
                                                            "versionedactionid",
                                                            "configoptionlookupid")
  getLinkConsumerDependency = _getLinkXToY("ovt_dependency", "dependencyid", "versionedactiondep", "versionedactionid")
  getLinkProducerDependency = _getLinkXToY("ovt_dependency", "dependencyid", "versionedactionid",  "versionedactiondep")
  getLinkVersionedActionToAttributeValue = _getLinkXToY ("ovt_versionedactionattributevalue", "versionedactionattributevalueid",
                                                         "versionedactionid", "attributevalueid")

  getLifeCycleStateByName = _getXByName ("ovt_lifecyclestate", "lifecyclestateid", "lifecyclestatename")
  getLifeCycleStateNameById = _getXAttrById ("ovt_lifecyclestate", "lifecyclestateid", ["lifecyclestatename"])

  getVersionedActionLifeCycleState = _getXAttrById ("ovt_versionedaction", "versionedactionid", ["lifecyclestateid"])
  setVersionedActionLifeCycleState = _setXY ("ovt_versionedaction", "versionedactionid", "lifecyclestateid")

  getVersionedActionsByConfigOption = _getXsByY ("ovt_versionedactionconfigoption", "versionedactionid", "configoptionid")

  setDependencyDefault = _setXY("ovt_dependency", "dependencyid", "defaultdep")

  setActionName = _setXY("ovt_action", "actionid", "actionname")
  setVersionedActionName = _setXY("ovt_versionedaction", "versionedactionid", "versionname")
  setActionCategory = _setXY("ovt_action", "actionid", "actioncategoryid")
  setResourceName = _setXY("ovt_resource", "resourceid", "resourcename")
  setResourceConcurrency = _setXY("ovt_resource", "resourceid", "concurrency")
  setResourceHostname = _setXY("ovt_resource", "resourceid", "hostname")
  setResourceTypeName = _setXY("ovt_resourcetype", "resourcetypeid", "resourcetypename")
  setAttributeName = _setXY("ovt_attribute", "attributeid", "attributename")

class OvtDB:
  hostid = 0
  hostpid = 0
  ACTIONLOCKID = 1

  def __init__(self, log):
    self.simple = OvtDBSimple(self)
    self.ovtDB = None
    self.autocommit = AutoCommit()
    self.log = log
    self.debug = False
    self.always_reconnect = True

    holdoff = 5
    success = False
    while not success:
      try:
        self.ovtDB = dbapi2.connect( host="hhmipssw204.mipstec.com", port=5432, database="overtest", user="overtest", password="overtest")
        success = True
      except (socket.error, postgresql.exceptions.OIError, postgresql.exceptions.ConnectionError, \
              postgresql.exceptions.InFailedTransactionError, postgresql.exceptions.AbortTransaction), e:
        self.log.write("DB FAIL: %s" % e)
        self.log.write("<-- %s Database Connection lost, Waiting %u seconds -->"%(time.asctime(), holdoff))
        time.sleep(holdoff)
        if holdoff < 900:
          holdoff += holdoff
 
    self.cursor = self.ovtDB.cursor()

  def __del__(self):
    if self.ovtDB != None:
      try:
        self.ovtDB.close()
      except (postgresql.exceptions.Error, IOError):
        None

  def registerLog(self, log):
    """
    Register a log handler from an application
    """
    self.log = log

  def execute(self, sql, args):
    """
    Do the string escaping magic
    """
    if self.debug:
      self.log.write(sql)
      self.log.write(args)
    newargs = []
    if type(args) != types.ListType and  type(args) != types.TupleType:
      args = [args]
    for arg in args:
      if type(arg) in types.StringTypes:
        newargs.append(pg_str.quote_literal_strict(arg))
      elif type(arg) == types.FloatType:
        newargs.append("%f"%arg)
      elif type(arg) in (types.IntType, types.LongType):
        newargs.append("%d"%arg)
      elif type(arg) == types.BooleanType:
        if arg:
          newargs.append("'t'")
        else:
          newargs.append("'f'")
      elif arg == None:
        newargs.append("NULL")
      else:
        raise Exception("Unknown type of sql parameter %s" % str(type(arg)))

    success = False
    while not success:
      try:
        self.cursor.close()
        del self.cursor
        self.cursor = self.ovtDB.cursor()
        self.cursor.execute(sql % tuple(newargs), ())
        if self.autocommit.autoCommit():
          self.ovtDB.commit()
        success = True
      except (socket.error, postgresql.exceptions.OIError, postgresql.exceptions.ConnectionError, \
              postgresql.exceptions.InFailedTransactionError, postgresql.exceptions.AbortTransaction), e:
        # When the caller is in a time critical region a reconnect is deferred until
        # the next database call.
        if self.always_reconnect:
          self.log.write("DB FAIL: %s" % e)
          self.reconnect()
        if not self.always_reconnect or not self.autocommit.autoCommit():
          raise DatabaseRetryException("EXECUTE failed")

  def reconnect(self, quiet=False, log=None):
    self.__del__()
    if log == None:
      log = self.log
    self.__init__(log)
    if not quiet:
      self.log.write("<-- %s Database Connection Restored -->" % time.asctime())

  def setAutoCommit(self, value):
    return self.autocommit.setAutoCommit(value)

  def FORCECOMMIT(self):
    try:
      self.ovtDB.commit()
    except (socket.error, postgresql.exceptions.OIError, postgresql.exceptions.ConnectionError, \
            postgresql.exceptions.InFailedTransactionError, postgresql.exceptions.AbortTransaction), e:
      raise DatabaseRetryException("COMMIT failed")

  def FORCEROLLBACK(self):
    try:
      self.ovtDB.rollback()
    except (socket.error, postgresql.exceptions.OIError, postgresql.exceptions.ConnectionError, \
            postgresql.exceptions.InFailedTransactionError, postgresql.exceptions.AbortTransaction), e:
      raise DatabaseRetryException("ROLLBACK failed")

  def DELETETESTRUN(self, testrunid):
    """
    Delete a testrun forever!
    """
    sql = "DELETE FROM ovt_testrun "+\
          "WHERE testrunid=%s"
    self.execute(sql, (testrunid))

  def LOCKACTION(self, actionid):
    """
    Lock the specified action
    """
    sql = "SELECT pg_advisory_lock(%s, %s)";
    self.execute(sql, (OvtDB.ACTIONLOCKID, actionid))

  def TRYLOCKACTION(self, actionid):
    """
    Try to lock the specified action
    """
    sql = "SELECT pg_try_advisory_lock(%s, %s)";
    self.execute(sql, (OvtDB.ACTIONLOCKID, actionid))
    return self.cursor.fetchall()[0][0]

  def LOCKACTIONS(self, actionids):
    """
    Lock the specified actions
    """
    success = False
    while not success:
      success = True
      self.LOCKACTION (0) # Prevent livelock by ensuring only one multiple lock request
      locked = []
      for actionid in actionids:
        if self.TRYLOCKACTION(actionid):
          locked.append(actionid)
        else:
          success = False
          self.UNLOCKACTIONS(locked)
          break
      self.UNLOCKACTION (0)

  def UNLOCKACTION(self, actionid):
    """
    Lock the specified action
    """
    sql = "SELECT pg_advisory_unlock(%s, %s)";
    self.execute(sql, (OvtDB.ACTIONLOCKID, actionid))

  def UNLOCKACTIONS(self, actionids):
    for x in actionids:
      self.UNLOCKACTION (x)

  def __LOCKRESOURCES(self):
    """ 
    Locks out the resource management system!
    """
    sql = "LOCK TABLE ovt_testrunactionresource IN SHARE UPDATE EXCLUSIVE MODE"
    self.execute(sql, ())

  def getUserByName(self, username):
    """
    Find a user by username (or alternative name)
    """
    sql = "SELECT ovt_user.userid "+\
          "FROM ovt_user "+\
          "WHERE ovt_user.altnames LIKE '%%,'||%s "+\
          "OR ovt_user.altnames = %s "+\
          "OR ovt_user.altnames LIKE '%%,'||%s||',%%' "+\
          "OR ovt_user.altnames LIKE %s||',%%'"
    self.execute(sql, (username,username,username,username))
    users = self.cursor.fetchall()
    if len(users) == 1:
      return users[0]['userid']
    else:
      return None

  def getTestrungroupByName(self, groupname, userid=None):
    """
    Find a testrungroupid by groupname
    """
    values = [groupname]

    sql = "SELECT testrungroupid "+\
          "FROM ovt_testrungroup "+\
          "WHERE testrungroupname=%s"
    if userid != None:
      sql += " AND userid=%s LIMIT 1"
      values.append(userid)
    self.execute(sql, values)
    groups = self.cursor.fetchall()
    if len(groups) == 1:
      return groups[0]['testrungroupid']
    else:
      return None

  def findOrCreateGroup(self, groupname, userid):
    """
    Return the testrungroupid for groupname owned by userid or create it
    """
    sql = "SELECT testrungroupid "+\
          "FROM ovt_testrungroup "+\
          "WHERE testrungroupname=%s "+\
          "AND userid=%s"
    self.execute(sql, (groupname, userid))
    names = self.cursor.fetchall()
    if len(names) == 0:
      sql2 = "INSERT INTO ovt_testrungroup "+\
             "(testrungroupname, userid) "+\
             "VALUES "+\
             "(%s,%s)"
      try:
        self.execute(sql2, (groupname, userid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in testrungroup")
      self.execute(sql, (groupname, userid))
      names = self.cursor.fetchall()
    return names[0]['testrungroupid']

  def duplicateTestrungroup(self, testrungroupid, groupname, userid):
    """
    Duplicate the entire testrungroup naming the new group groupname
    owned by userid
    """
    sql = "SELECT ovt_duplicate_testrungroup(%s, %s, %s) AS testrungroupid;"
    self.execute(sql, (testrungroupid, groupname, userid))
    newinfo = self.cursor.fetchall()
    return newinfo[0]['testrungroupid']

  def duplicateTestrun(self, testrunid, testrungroupid, description, userid):
    """
    Duplicate the testrun naming the new testrun as description 
    owned by userid. When testrungroupid is None, the group will be the same
    as the original testrun
    """
    sql = "SELECT ovt_duplicate_testrun(%s, %s, %s, %s) AS testrunid;"
    self.execute(sql, (testrunid, description, userid, testrungroupid))
    newinfo = self.cursor.fetchall()
    return newinfo[0]['testrunid']

  def createTestrun(self, description, userid, testrungroupid):
    """
    Create a new testrun
    """
    sql = "SELECT ovt_create_testrun(%s, %s, %s) AS testrunid"
    self.execute(sql, (description, userid, testrungroupid))
    newinfo = self.cursor.fetchall()
    return newinfo[0]['testrunid']

  def updateTestrun(self, testrunid, userid, description = None, priority = None, concurrency = None, starttime = None, deptestrunid = None, autoarchive = None, usegridengine = None, testrungroupid = None):
    """
    Update the details of a testrun if editable
    """
    if starttime == "now":
      sql = "SELECT ovt_update_testrun(%s, %s, %s, %s, %s, now(), %s, %s, %s, %s) AS success"
      self.execute(sql, (testrunid, userid, description, priority, concurrency, deptestrunid, autoarchive, usegridengine, testrungroupid))
    else:
      sql = "SELECT ovt_update_testrun(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS success"
      self.execute(sql, (testrunid, userid, description, priority, concurrency, starttime, deptestrunid, autoarchive, usegridengine, testrungroupid))
    newinfo = self.cursor.fetchall()
    return newinfo[0]['success']

  def updateTestrunGroup(self, testrungroupid, userid, priority = None, concurrency = None, starttime = None, deptestrunid = None, autoarchive = None, usegridengine = None):
    """
    Update the details of a testrun group if editable
    """
    success = True
    testrunids = self.getTestrunsFromTestgroup(testrungroupid)
    for testrunid in testrunids:
      if not self.updateTestrun(testrunid, userid, None, priority, concurrency, starttime, deptestrunid, autoarchive, usegridengine):
	success = False

    return success

  def modifyTestrunTasks(self, testrunid, versionedactionids):
    """
    Add all the versioned actions in versionedactionids to the testrun
    """
    sql = "SELECT ovt_modify_tasks('testrun', 'add', %s, %s)"
    for vaid in versionedactionids:
      self.execute(sql, (testrunid, vaid))

  def modifyTestrunGroupTasks(self, testrungroupid, versionedactionids):
    """
    Add all the versioned actions in versionedactionids to the testrun group
    """
    testrunids = self.getTestrunsFromTestgroup(testrungroupid)
    for testrunid in testrunids:
      self.modifyTestrunTasks(testrunid, versionedactionids)

  def modifyTestrunRequirements(self, testrunid, attributevalueids):
    """
    Add all the resource requirements from attributevalueids to the testrun
    """
    sql = "SELECT ovt_modify_requirements('testrun', 'add', %s, %s)"
    for attributevalueid in attributevalueids:
      self.execute(sql, (testrunid, attributevalueid))

  def modifyTestrunGroupRequirements(self, testrungroupid, attributevalueids):
    """
    Add all the resource requirements from attributevalueids to the testrun group
    """
    testrunids = self.getTestrunsFromTestgroup(testrungroupid)
    for testrunid in testrunids:
      self.modifyTestrunRequirements(testrunid, attributevalueids)

  def modifyTestrunConfig(self, testrunid, configsettings):
    """
    Update all the config as specified in the configsettings dictionary
    """
    sql = "SELECT ovt_modify_config('testrun', %s, %s, %s)"
    for configoptionid in configsettings:
      self.execute(sql, (testrunid, configoptionid, str(configsettings[configoptionid][0])))

  def modifyTestrunGroupConfig(self, testrungroupid, configsettings):
    """
    Update all the config as specified in the configsettings dictionary
    """
    testrunids = self.getTestrunsFromTestgroup(testrungroupid)
    for testrunid in testrunids:
      self.modifyTestrunConfig(testrunid, configsettings)

  def updateTestrunStatus(self, testrunid, newstatus):
    """
    Progress a testrun to a new status
    """
    # WORK NEEDED: make this check success
    sql = "SELECT ovt_change_status('testrun', %s, %s)"
    self.execute(sql, (testrunid, newstatus))
    return True

  def findTestruns(self, testsuite, description, testrungroupid, userid, versionedactionids, configsettings, attributevalueids):
    """
    Find equivalent testruns
    """
    values = []
    sql = "SELECT DISTINCT ovt_testrun.testrunid, ovt_action.testsuiteid "+\
          "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid) "+\
           "                 INNER JOIN ovt_testrunaction USING (testrunid) "+\
           "             INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
           "             INNER JOIN ovt_action USING (actionid) "+\
          "WHERE ovt_runstatus.resultsvalid "+\
          "AND ovt_action.actionname=%s "+\
          "AND ovt_action.testsuiteid IS NOT NULL "
    values.append(testsuite)
    
    if testrungroupid != None:
      sql += "AND ovt_testrun.testrungroupid=%s "
      values.append(testrungroupid)
    
    if userid != None:
      sql += "AND ovt_testrun.userid=%s ";
      values.append(userid)
    
    if description != None:
      sql += "AND ovt_testrun.description LIKE %s ";
      values.append(description)
    
    for configoptionid in configsettings:
      (value, configoptionlookupid) = configsettings[configoptionid]
      if configoptionlookupid != None:
        sql += "AND EXISTS (SELECT ovt_configsetting.configoptionlookupid "+\
               "            FROM ovt_configsetting "+\
               "            WHERE ovt_configsetting.testrunid=ovt_testrun.testrunid "+\
               "            AND ovt_configsetting.configoptionlookupid=%s) "
        values.append(configoptionlookupid)
      else:
        sql += "AND EXISTS (SELECT ovt_configsetting.configoptionid "+\
               "            FROM ovt_configsetting "+\
               "            WHERE ovt_configsetting.testrunid=ovt_testrun.testrunid "+\
               "            AND ovt_configsetting.configoptionid=%s "+\
               "            AND ovt_configsetting.configvalue=%s) "
        values.append(configoptionid)
        values.append(value)
    for attributevalueid in attributevalueids:
      sql += "AND EXISTS (SELECT ovt_testrunattributevalue.attributevalueid "+\
             "            FROM ovt_testrunattributevalue "+\
             "            WHERE ovt_testrunattributevalue.testrunid=ovt_testrun.testrunid "+\
             "            AND ovt_testrunattributevalue.attributevalueid=%s) "
      values.append(attributevalueid)

    for vaid in versionedactionids:
      sql += "AND EXISTS (SELECT ovt_testrunaction.versionedactionid "+\
             "            FROM ovt_testrunaction "+\
             "            WHERE ovt_testrunaction.testrunid=ovt_testrun.testrunid "+\
             "            AND ovt_testrunaction.versionedactionid=%s) "
      values.append(vaid)

    self.execute(sql, values)
    testruns = self.cursor.fetchall()

    submissionids = []
    for t in testruns:
      trid = t['testrunid']
      testsuiteid = t['testsuiteid']
      submissionids.append("%d:%d:%d" % (trid, testsuiteid, 0))
    
    return submissionids

  def searchActions(self, search = {}, showunavailable = True):
    """
    A relatively flexible search function for interesting actions
    """
    sql = "SELECT actionname, actionid, ovt_actioncategory.actioncategoryid, actioncategoryname, "+\
          "actstate.lifecyclestatename AS actstatename, "+\
          "catstate.lifecyclestatename AS catstatename "+\
          "FROM (ovt_action INNER JOIN ovt_lifecyclestate AS actstate USING (lifecyclestateid)) "+\
                "INNER JOIN "+\
                "(ovt_actioncategory INNER JOIN ovt_lifecyclestate AS catstate USING (lifecyclestateid)) "+\
                "USING (actioncategoryid) "

    vars = []
    if "actionid" in search:
      vars.append(search['actionid'])
      sql += "WHERE actionid=%s "
    else:
      sql += "WHERE true "
      if "searchterm" in search:
        if not "method" in search or search['method'] == "wildi":
          sql += "AND actionname ILIKE %s "
        elif search['method'] == "wild":
          sql += "AND actionname LIKE %s "
        else:
          sql += "AND actionname = %s "
        vars.append(search['searchterm'])
      if "actioncategoryid" in search:
        sql += "AND actioncategoryid=%s "
        vars.append(search['actioncategoryid'])
      if "secure" in search:
        sql += "AND issecure "

      if not showunavailable:
        sql += "AND actstate.valid "+\
               "AND catstate.valid "
        
    sql += "ORDER BY actionname "
    if "offset" in search:
      sql += "OFFSET "+str(search['offset'])+" "
    if "limit" in search:
      sql += "LIMIT "+str(search['limit']) + " "
    self.execute(sql, vars)
    actions = self.cursor.fetchall()
    ret = ({},[])
    for action in actions:
      if not action['actioncategoryid'] in ret[0]:
        ret[1].append(action['actioncategoryid'])
        ret[0][action['actioncategoryid']] = {"data":action['actioncategoryname'], "note":action['catstatename'], "type":"Action Category", "id":action['actioncategoryid'], "related":({},[])}

      acts = ret[0][action['actioncategoryid']]['related']
      acts[1].append(action['actionid'])
      acts[0][action['actionid']] = {"data":action['actionname'], "note":action['actstatename'], "type":"Action", "id":action['actionid']}
      if "actionid" in search:
        vals = [search['actionid']]
        sql = "SELECT versionname, versionedactionid, lifecyclestatename "+\
              "FROM ovt_versionedaction INNER JOIN ovt_lifecyclestate USING (lifecyclestateid) "+\
              "WHERE actionid=%s "
        if "versionname" in search:
          if not "method" in search or search['method'] == "wildi":
            sql += "AND versionname ILIKE %s "
          elif search['method'] == "wild":
            sql += "AND versionname LIKE %s "
          else:
            sql += "AND versionname = %s "
          vals.append(search['versionname'])

        if not showunavailable:
          sql += "AND ovt_lifecyclestate.valid "

        sql +=  "ORDER BY versionname"
        self.execute(sql, vals)
        versions = self.cursor.fetchall()
        acts[0][action['actionid']]['related'] = ({},[])
        vers = acts[0][action['actionid']]['related']
        for version in versions:
          vers[1].append(version['versionedactionid'])
          vers[0][version['versionedactionid']] = {"data":version['versionname'], "note":version['lifecyclestatename'], "type":"Versioned Action", "id":version['versionedactionid']}
    return ret

  def getDependencyGroups(self, consumer=None, producer=None):
    terms = []
    if consumer == None and producer == None:
      sql = "SELECT dependencygroupname, dependencygroupid "+\
            "FROM ovt_dependencygroup "+\
            "ORDER BY dependencygroupname"
    else:
      sql = "SELECT DISTINCT ovt_dependencygroup.dependencygroupname, ovt_dependencygroup.dependencygroupid "+\
            "FROM ovt_dependencygroup INNER JOIN ovt_dependency USING (dependencygroupid) "+\
            "WHERE "
      if consumer != None:
        sql += "ovt_dependency.versionedactionid=%s "
        terms.append(consumer)
        if producer != None:
          sql += "AND "
      if producer != None:
        sql += "ovt_dependency.versionedactiondep=%s "
        terms.append(producer)
      sql += "ORDER BY ovt_dependencygroup.dependencygroupname"

    ret = ({},[])
    self.execute(sql, terms)
    groups = self.cursor.fetchall()
    for group in groups:
      ret[1].append(group['dependencygroupid'])
      ret[0][group['dependencygroupid']] = {"data":group['dependencygroupname'], "id":group['dependencygroupid'], "type":"Dependency Group"}
    return ret

  def getActionName(self, actionid):
    sql = "SELECT actionname "+\
          "FROM ovt_action "+\
          "WHERE actionid=%s LIMIT 1"
    self.execute(sql, (actionid))
    result = self.cursor.fetchall()
    if len(result) == 0:
      return False
    return result[0]['actionname']

  def getVersionedActionName(self, versionedactionid, actionid = None):
    sql = "SELECT actionname, versionname "+\
          "FROM ovt_versionedaction INNER JOIN ovt_action USING (actionid) "+\
          "WHERE versionedactionid=%s "
    terms = [versionedactionid]
    if actionid != None:
      sql += "AND ovt_action.actionid=%s"
      terms.append(actionid)
    sql += " LIMIT 1"
    self.execute(sql, terms)
    result = self.cursor.fetchall()
    if len(result) == 0:
      return False
    return result[0]['actionname'] + " [" + result[0]['versionname'] + "]"

  def getProducersInGroup(self, dependencygroupid, versiononly):
    """Returns all the producers that are part of dependencies with the
       specified group and versiononly status"""
    sql = "SELECT DISTINCT ovt_action.actionid, ovt_action.actionname "+\
          "FROM ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_versionedaction.versionedactionid=ovt_dependency.versionedactiondep) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "WHERE ovt_dependency.dependencygroupid=%s "+\
          "AND ovt_dependency.versiononly=%s "+\
          "ORDER BY ovt_action.actionname "
    self.execute(sql, (dependencygroupid, versiononly))
    actions = self.cursor.fetchall()
    ret = ({},[])
    for action in actions:
      ret[1].append(action['actionid'])
      ret[0][action['actionid']] = {"data":action['actionname'], "id":action['actionid'], "type":"Action", "related":({},[])}
      sql = "SELECT DISTINCT ovt_versionedaction.versionedactionid, ovt_versionedaction.versionname "+\
            "FROM ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_versionedaction.versionedactionid=ovt_dependency.versionedactiondep) "+\
            "WHERE ovt_dependency.dependencygroupid=%s "+\
            "AND ovt_dependency.versiononly=%s "+\
            "AND ovt_versionedaction.actionid=%s "+\
            "ORDER BY ovt_versionedaction.versionname "
      self.execute(sql, (dependencygroupid, versiononly, action['actionid']))
      versions = self.cursor.fetchall()
      acts = ret[0][action['actionid']]['related']
      for version in versions:
        acts[1].append(version['versionedactionid'])
        acts[0][version['versionedactionid']] = {"data":version['versionname'], "id":version['versionedactionid'], "type": "Versioned Action"}
    return ret

  def getVersionedActionDependencies(self, versionedactionid, type, showunavailable=True):
    if type == "Consumer":
      depfield = "versionedactiondep"
      invdepfield = "versionedactionid"
    elif type == "Producer":
      depfield = "versionedactionid"
      invdepfield = "versionedactiondep"
    else:
      return None
    sql = "SELECT DISTINCT ovt_dependency.dependencygroupid, dependencygroupname "+\
          "FROM ovt_dependency INNER JOIN ovt_dependencygroup USING (dependencygroupid) "+\
          "     INNER JOIN ovt_versionedaction ON (ovt_versionedaction.versionedactionid=ovt_dependency."+invdepfield+") "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "     INNER JOIN ovt_actioncategory USING (actioncategoryid) "+\
          "     INNER JOIN ovt_lifecyclestate AS catstate ON (ovt_actioncategory.lifecyclestateid=catstate.lifecyclestateid) "+\
          "     INNER JOIN ovt_lifecyclestate AS actstate ON (ovt_action.lifecyclestateid=actstate.lifecyclestateid) "+\
          "     INNER JOIN ovt_lifecyclestate AS verstate ON (ovt_versionedaction.lifecyclestateid=verstate.lifecyclestateid) "+\
          "WHERE ovt_dependency."+depfield+"=%s "
    if not showunavailable:
      sql += "AND catstate.valid "+\
             "AND actstate.valid "+\
             "AND verstate.valid "
    sql += "ORDER BY dependencygroupname"
    self.execute(sql, (versionedactionid))
    groups = self.cursor.fetchall()
    ret = ({}, [])
    for group in groups:
      ret[1].append(group['dependencygroupid'])
      ret[0][group['dependencygroupid']] = {"data":group['dependencygroupname'], "type":"Dependency Group", "id":group['dependencygroupid'], "related":({},[])}
      sql = "SELECT DISTINCT ovt_actioncategory.actioncategoryid, ovt_actioncategory.actioncategoryname, "+\
            "                catstate.visible "+\
            "FROM ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_versionedaction.versionedactionid=ovt_dependency."+invdepfield+") "+\
            "     INNER JOIN ovt_action USING (actionid) "+\
            "     INNER JOIN ovt_actioncategory USING (actioncategoryid) "+\
            "     INNER JOIN ovt_lifecyclestate AS catstate ON (ovt_actioncategory.lifecyclestateid=catstate.lifecyclestateid) "+\
            "     INNER JOIN ovt_lifecyclestate AS actstate ON (ovt_action.lifecyclestateid=actstate.lifecyclestateid) "+\
            "     INNER JOIN ovt_lifecyclestate AS verstate ON (ovt_versionedaction.lifecyclestateid=verstate.lifecyclestateid) "+\
            "WHERE ovt_dependency.dependencygroupid=%s "+\
            "AND ovt_dependency."+depfield+"=%s "
      if not showunavailable:
        sql += "AND catstate.valid "+\
               "AND actstate.valid "+\
               "AND verstate.valid "
      sql += "ORDER BY ovt_actioncategory.actioncategoryname"
      self.execute(sql, (group['dependencygroupid'], versionedactionid))
      categories = self.cursor.fetchall()
      cats = ret[0][group['dependencygroupid']]['related']
 
      for category in categories:
        cats[1].append(category['actioncategoryid'])
        cats[0][category['actioncategoryid']] = {"data":category['actioncategoryname'], "type":"Action Category", "id":category['actioncategoryid'], "visible":category['visible'], "related":({},[])}
        sql = "SELECT DISTINCT ovt_versionedaction.actionid, ovt_action.actionname, "+\
              "                actstate.visible "+\
              "FROM ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_versionedaction.versionedactionid=ovt_dependency."+invdepfield+") "+\
              "     INNER JOIN ovt_action USING (actionid) "+\
              "     INNER JOIN ovt_lifecyclestate AS actstate ON (ovt_action.lifecyclestateid=actstate.lifecyclestateid) "+\
              "     INNER JOIN ovt_lifecyclestate AS verstate ON (ovt_versionedaction.lifecyclestateid=verstate.lifecyclestateid) "+\
              "WHERE ovt_dependency.dependencygroupid=%s "+\
              "AND ovt_action.actioncategoryid=%s "+\
              "AND ovt_dependency."+depfield+"=%s "
        if not showunavailable:
          sql += "AND actstate.valid "+\
                 "AND verstate.valid "
        sql += "ORDER BY ovt_action.actionname"
        self.execute(sql, (group['dependencygroupid'], category['actioncategoryid'], versionedactionid))
        actions = self.cursor.fetchall()
        acts = cats[0][category['actioncategoryid']]['related']
        for action in actions:
          acts[1].append(action['actionid'])
          acts[0][action['actionid']] = {"data":action['actionname'], "type":"Action", "id":action['actionid'], "visible":action['visible'], "related":({},[])}
          sql = "SELECT ovt_versionedaction.versionname, ovt_dependency.dependencyid, "+\
                "       ovt_dependency.versiononly, ovt_dependency.hostmatch, "+\
                "       ovt_dependency.defaultdep, "+\
                "       ovt_versionedaction.versionedactionid, "+\
                "       verstate.visible "+\
                "FROM ovt_versionedaction INNER JOIN ovt_dependency ON (ovt_versionedaction.versionedactionid=ovt_dependency."+invdepfield+") "+\
                "     INNER JOIN ovt_lifecyclestate AS verstate ON (ovt_versionedaction.lifecyclestateid=verstate.lifecyclestateid) "+\
                "WHERE ovt_dependency."+depfield+"=%s "+\
                "AND ovt_dependency.dependencygroupid=%s "+\
                "AND ovt_versionedaction.actionid=%s "
          if not showunavailable:
            sql += "AND verstate.valid "
          sql += "ORDER BY ovt_versionedaction.versionname"
          self.execute(sql, (versionedactionid, group['dependencygroupid'], action['actionid']))
          versions = self.cursor.fetchall()
          vers = acts[0][action['actionid']]['related']
          for version in versions:
            vers[1].append(version['dependencyid'])
            vers[0][version['dependencyid']] = {"data":version['versionname'], "type":"Dependency", "id":version['dependencyid'],
                                                "versiononly":version['versiononly'], "hostmatch":version['hostmatch'],
                                                "defaultdep":version['defaultdep'], "visible":version['visible'],
                                                "versionedactionid":version['versionedactionid']}
            if version['defaultdep']:
              vers[0][version['dependencyid']]['note'] = "Default dependency"

    sql = "SELECT DISTINCT ovt_actioncategory.actioncategoryid, ovt_actioncategory.actioncategoryname, "+\
          "                catstate.visible "+\
          "FROM ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_versionedaction.versionedactionid=ovt_dependency."+invdepfield+") "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "     INNER JOIN ovt_actioncategory USING (actioncategoryid) "+\
          "     INNER JOIN ovt_lifecyclestate AS catstate ON (ovt_actioncategory.lifecyclestateid=catstate.lifecyclestateid) "+\
          "     INNER JOIN ovt_lifecyclestate AS actstate ON (ovt_action.lifecyclestateid=actstate.lifecyclestateid) "+\
          "     INNER JOIN ovt_lifecyclestate AS verstate ON (ovt_versionedaction.lifecyclestateid=verstate.lifecyclestateid) "+\
          "WHERE ovt_dependency.dependencygroupid IS NULL "+\
          "AND ovt_dependency."+depfield+"=%s "
    if not showunavailable:
      sql += "AND catstate.valid "+\
             "AND actstate.valid "+\
             "AND verstate.valid "
    sql += "ORDER BY ovt_actioncategory.actioncategoryname"
    self.execute(sql, (versionedactionid))
    categories = self.cursor.fetchall()
    if len(categories) != 0:
      ret[1].append(-1)
      ret[0][-1] = {"data":"[[NO GROUP]]", "type":"Dependency Group", "id":-1, "related":({},[])}
      cats = ret[0][-1]['related']

      for category in categories:
        cats[1].append(category['actioncategoryid'])
        cats[0][category['actioncategoryid']] = {"data":category['actioncategoryname'], "type":"Action Category", "id":category['actioncategoryid'], "visible":category['visible'], "related":({},[])}

        sql = "SELECT DISTINCT ovt_versionedaction.actionid, ovt_action.actionname, "+\
              "                actstate.visible "+\
              "FROM ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_versionedaction.versionedactionid=ovt_dependency."+invdepfield+") "+\
              "     INNER JOIN ovt_action USING (actionid) "+\
              "     INNER JOIN ovt_lifecyclestate AS actstate ON (ovt_action.lifecyclestateid=actstate.lifecyclestateid) "+\
              "     INNER JOIN ovt_lifecyclestate AS verstate ON (ovt_versionedaction.lifecyclestateid=verstate.lifecyclestateid) "+\
              "WHERE ovt_dependency.dependencygroupid IS NULL "+\
              "AND ovt_dependency."+depfield+"= %s "+\
              "AND ovt_action.actioncategoryid=%s "
        if not showunavailable:
          sql += "AND actstate.valid "+\
                 "AND verstate.valid "
        sql += "ORDER BY ovt_action.actionname"
        self.execute(sql, (versionedactionid, category['actioncategoryid']))
        actions = self.cursor.fetchall()
        acts = cats[0][category['actioncategoryid']]['related']
  
        for action in actions:
          acts[1].append(action['actionid'])
          acts[0][action['actionid']] = {"data":action['actionname'], "type":"Action", "id":action['actionid'], "visible":action['visible'], "related":({},[])}
          sql = "SELECT ovt_versionedaction.versionname, ovt_dependency.dependencyid, "+\
                "       ovt_dependency.versiononly, ovt_dependency.hostmatch, "+\
                "       ovt_dependency.defaultdep, "+\
                "       ovt_versionedaction.versionedactionid, "+\
                "       verstate.visible "+\
                "FROM ovt_versionedaction INNER JOIN ovt_dependency ON (ovt_versionedaction.versionedactionid=ovt_dependency."+invdepfield+") "+\
                "     INNER JOIN ovt_lifecyclestate AS verstate ON (ovt_versionedaction.lifecyclestateid=verstate.lifecyclestateid) "+\
                "WHERE ovt_dependency."+depfield+"=  %s "+\
                "AND ovt_dependency.dependencygroupid IS NULL "+\
                "AND ovt_versionedaction.actionid=  %s "
          if not showunavailable:
            sql += "AND verstate.valid "
          sql += "ORDER BY ovt_versionedaction.versionname"
          self.execute(sql, (versionedactionid, action['actionid']))
          versions = self.cursor.fetchall()
          vers = acts[0][action['actionid']]['related']
          for version in versions:
            vers[1].append(version['dependencyid'])
            vers[0][version['dependencyid']] = {"data":version['versionname'], "type":"Dependency", "id":version['dependencyid'],
                                                "versiononly":version['versiononly'], "hostmatch":version['hostmatch'],
                                                "defaultdep":version['defaultdep'], "visible":version['visible'],
                                                "versionedactionid":version['versionedactionid']}
            if version['defaultdep']:
              vers[0][version['dependencyid']]['note'] = "Default dependency"
    return ret

  def getResourceRequirements(self, versionedactionid):
    """
    Fetches all resource requirements for a given versionedaction grouping by resource type
    """
    sql = "SELECT DISTINCT ovt_resourcetype.resourcetypeid, ovt_resourcetype.resourcetypename "+\
          "FROM ovt_resourcetype INNER JOIN ovt_attribute USING (resourcetypeid) "+\
          "     INNER JOIN ovt_attributevalue USING (attributeid) "+\
          "     INNER JOIN ovt_versionedactionattributevalue USING (attributevalueid) "+\
          "WHERE ovt_versionedactionattributevalue.versionedactionid=%s "+\
          "ORDER BY resourcetypename"
    self.execute(sql, (versionedactionid))
    groups = self.cursor.fetchall()
    ret = ({},[])
    for group in groups:
      ret[1].append(group['resourcetypeid'])
      ret[0][group['resourcetypeid']] = {"data":group['resourcetypename'], "id":group['resourcetypeid'], "type":"Resource Type", "related":({},[])}
      sql = "SELECT DISTINCT ovt_attribute.attributename, ovt_attribute.attributeid "+\
            "FROM ovt_attribute INNER JOIN ovt_attributevalue USING (attributeid) "+\
            "     INNER JOIN ovt_versionedactionattributevalue USING (attributevalueid) "+\
            "WHERE ovt_versionedactionattributevalue.versionedactionid=%s "+\
            "AND ovt_attribute.resourcetypeid=%s "+\
            "ORDER BY ovt_attribute.attributename"
      self.execute(sql, (versionedactionid, group['resourcetypeid']))
      attributes = self.cursor.fetchall()
      atts = ret[0][group['resourcetypeid']]['related']
      for attribute in attributes:
        atts[1].append(attribute['attributeid'])
        atts[0][attribute['attributeid']] = {"data":attribute['attributename'],"type":"Attribute", "id":attribute['attributeid'], "related":({},[])}
        sql = "SELECT ovt_attributevalue.value, ovt_attributevalue.attributevalueid "+\
              "FROM ovt_attributevalue INNER JOIN ovt_versionedactionattributevalue USING (attributevalueid) "+\
              "WHERE ovt_versionedactionattributevalue.versionedactionid=%s "+\
              "AND ovt_attributevalue.attributeid=%s "+\
              "ORDER BY ovt_attributevalue.value "
        self.execute(sql, (versionedactionid, attribute['attributeid']))
        values = self.cursor.fetchall()
        vals = atts[0][attribute['attributeid']]['related']
        for value in values:
          vals[1].append(value['attributevalueid'])
          vals[0][value['attributevalueid']] = {"data":value['value'], "type":"Attribute Value", "id":value['attributevalueid']}
    return ret

  def getAvailableResources(self, resourcetypeid=None, resourceid=None):
    """
    Return a list of resources for the specified group
    """
    if resourceid == None:
      sql = "SELECT ovt_resource.resourceid, ovt_resourceattribute.attributevalueid, ovt_attributevalue.mustrequest "+\
            "FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
            "     INNER JOIN ovt_resourceattribute USING (resourceid) "+\
            "     INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
            "WHERE ovt_resource.resourcetypeid=%s "+\
            "AND ovt_resourcestatus.status = 'OK'"
      self.execute(sql, (resourcetypeid))
    else:
      sql = "SELECT ovt_resource.resourceid, ovt_resourceattribute.attributevalueid, ovt_attributevalue.mustrequest "+\
            "FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
            "     INNER JOIN ovt_resourceattribute USING (resourceid) "+\
            "     INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
            "WHERE ovt_resource.resourceid=%s "+\
            "AND ovt_resourcestatus.status = 'OK'"
      self.execute(sql, (resourceid))

    resources = self.cursor.fetchall()

    ret = {}
    for resource in resources:
      if not resource['resourceid'] in ret:
        ret[resource['resourceid']] = {"attributes":set(), "mustrequestattributes":set()}

      ret[resource['resourceid']]['attributes'].add(resource['attributevalueid'])
      if resource['mustrequest']:
        ret[resource['resourceid']]['mustrequestattributes'].add(resource['attributevalueid'])

    return ret

  def getTestrunDefinition(self, testrunid):
    """
    Returns a structure representing the versioned actions in a testrun
    """
    sql = "SELECT DISTINCT ovt_actioncategory.actioncategoryid, actioncategoryname, "+\
          "                ovt_action.actionid, actionname, "+\
          "                ovt_versionedaction.versionedactionid, versionname "+\
          "FROM ovt_actioncategory INNER JOIN ovt_action USING (actioncategoryid) "+\
          "     INNER JOIN ovt_versionedaction USING (actionid) "+\
          "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "WHERE testrunid=%s "+\
          "ORDER BY actioncategoryname, actionname, versionname"

    self.execute(sql, (testrunid))
    definition = self.cursor.fetchall()
    retval = ({}, [])
    for version in definition:
      if not version['actioncategoryid'] in retval[0]:
        retval[0][version['actioncategoryid']] = {"data":version['actioncategoryname'], "type":"Action Category", "id":version['actioncategoryid'], 'related':({},[])}
        retval[1].append(version['actioncategoryid'])
      tmpval = retval[0][version['actioncategoryid']]['related']
      if not version['actionid'] in tmpval[0]:
        tmpval[0][version['actionid']] = {"data":version['actionname'], "type":"Action", "id":version['actionid'], 'related':({},[])}
        tmpval[1].append(version['actionid'])
      tmpval = tmpval[0][version['actionid']]['related']
      if not version['versionedactionid'] in tmpval[0]:
        tmpval[0][version['versionedactionid']] = {"data":version['versionname'], "type":"Versioned Action", "id":version['versionedactionid']}
        tmpval[1].append(version['versionedactionid'])
    return retval

  def getTestrunConfiguration(self, testrunid):
    """
    Returns a structure representing the configuration for a testrun
    """
    sql = "SELECT DISTINCT ovt_configoptiongroup.configoptiongroupid, configoptiongroupname, "+\
          "                ovt_configoption.configoptionid, configoptionname, "+\
          "                ovt_configsetting.configsettingid, configvalue, "+\
          "                ovt_configoptionlookup.lookupname "+\
          "FROM ovt_configoptiongroup INNER JOIN ovt_configoption USING (configoptiongroupid) "+\
          "     INNER JOIN ovt_configsetting USING (configoptionid) "+\
          "     LEFT OUTER JOIN ovt_configoptionlookup USING (configoptionlookupid) "+\
          "WHERE testrunid=%s "+\
          "AND NOT ovt_configoptiongroup.automatic "+\
          "ORDER BY configoptiongroupname, configoptionname"

    self.execute(sql, (testrunid))
    settings = self.cursor.fetchall()
    retval = ({}, [])
    for setting in settings:
      if not setting['configoptiongroupid'] in retval[0]:
        retval[0][setting['configoptiongroupid']] = {"data":setting['configoptiongroupname'], "type":"Config Option Group", "id":setting['configoptiongroupid'], 'related':({},[])}
        retval[1].append(setting['configoptiongroupid'])
      tmpval = retval[0][setting['configoptiongroupid']]['related']
      if not setting['configoptionid'] in tmpval[0]:
        tmpval[0][setting['configoptionid']] = {"data":setting['configoptionname'], "type":"Config Option", "id":setting['configoptionid'], 'related':({},[])}
        tmpval[1].append(setting['configoptionid'])
      tmpval = tmpval[0][setting['configoptionid']]['related']
      if not setting['configsettingid'] in tmpval[0]:
        if setting['configvalue'] != None:
          value = setting['configvalue']
        else:
          value = setting['lookupname']
        tmpval[0][setting['configsettingid']] = {"data":value, "type":"Config Setting", "id":setting['configsettingid']}
        tmpval[1].append(setting['configsettingid'])
    return retval

  def getTestrunRequirements(self, testrunid):
    """
    Returns a structure representing the requirements of a testrun
    """
    sql = "SELECT DISTINCT ovt_resourcetype.resourcetypeid, resourcetypename, "+\
          "                ovt_attribute.attributeid, attributename, "+\
          "                ovt_attributevalue.attributevalueid, value "+\
          "FROM ovt_resourcetype INNER JOIN ovt_attribute USING (resourcetypeid) "+\
          "     INNER JOIN ovt_attributevalue USING (attributeid) "+\
          "     INNER JOIN ovt_testrunattributevalue USING (attributevalueid) "+\
          "WHERE testrunid=%s "+\
          "ORDER BY resourcetypename, attributename"

    self.execute(sql, (testrunid))
    requirements = self.cursor.fetchall()
    retval = ({}, [])
    for requirement in requirements:
      if not requirement['resourcetypeid'] in retval[0]:
        retval[0][requirement['resourcetypeid']] = {"data":requirement['resourcetypename'], "type":"Resource Type", "id":requirement['resourcetypeid'], 'related':({},[])}
        retval[1].append(requirement['resourcetypeid'])
      tmpval = retval[0][requirement['resourcetypeid']]['related']
      if not requirement['attributeid'] in tmpval[0]:
        tmpval[0][requirement['attributeid']] = {"data":requirement['attributename'], "type":"Attribute", "id":requirement['attributeid'], 'related':({},[])}
        tmpval[1].append(requirement['attributeid'])
      tmpval = tmpval[0][requirement['attributeid']]['related']
      if not requirement['attributevalueid'] in tmpval[0]:
        tmpval[0][requirement['attributevalueid']] = {"data":requirement['value'], "type":"Attribute Value", "id":requirement['attributevalueid']}
        tmpval[1].append(requirement['attributevalueid'])
    return retval

  def getTestrunActionResourceRequirements(self, testrunactionid):
    """
    Fetches all resource requirements for a given testrun grouping by resource type
    """
    sql = "SELECT DISTINCT * "+\
          "FROM "+\
          "((SELECT DISTINCT ovt_attributevalue.attributevalueid, ovt_attribute.resourcetypeid "+\
          "  FROM ovt_attributevalue INNER JOIN ovt_versionedactionattributevalue USING (attributevalueid) "+\
          "       INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "       INNER JOIN ovt_attribute USING (attributeid) "+\
          "  WHERE ovt_testrunaction.testrunactionid=%s) " +\
          " UNION "+\
          " (SELECT DISTINCT ovt_testrunattributevalue.attributevalueid, ovt_attribute.resourcetypeid "+\
          "  FROM ovt_testrunaction INNER JOIN ovt_testrunattributevalue USING (testrunid) "+\
          "       INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
          "       INNER JOIN ovt_attribute USING (attributeid) "+\
          "       INNER JOIN ovt_attribute AS a2 ON (ovt_attribute.resourcetypeid=a2.resourcetypeid) "+\
          "       INNER JOIN ovt_attributevalue as av2 ON (a2.attributeid=av2.attributeid) "+\
          "       INNER JOIN ovt_versionedactionattributevalue ON (av2.attributevalueid=ovt_versionedactionattributevalue.attributevalueid) "+\
          "  WHERE ovt_testrunaction.testrunactionid=%s "+\
          "  AND ovt_testrunaction.versionedactionid=ovt_versionedactionattributevalue.versionedactionid) "+\
          " UNION "+\
          " (SELECT DISTINCT ovt_configoptionlookupattributevalue.attributevalueid, ovt_attribute.resourcetypeid "+\
          "  FROM ovt_testrunaction INNER JOIN ovt_configsetting USING (testrunid) "+\
          "       INNER JOIN ovt_versionedactionconfigoption USING (configoptionid) "+\
          "       INNER JOIN ovt_configoptionlookupattributevalue USING (configoptionlookupid) "+\
          "       INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
          "       INNER JOIN ovt_attribute USING (attributeid) "+\
          "       INNER JOIN ovt_attribute AS a2 ON (ovt_attribute.resourcetypeid=a2.resourcetypeid) "+\
          "       INNER JOIN ovt_attributevalue as av2 ON (a2.attributeid=av2.attributeid) "+\
          "       INNER JOIN ovt_versionedactionattributevalue ON (av2.attributevalueid=ovt_versionedactionattributevalue.attributevalueid) "+\
          "  WHERE ovt_testrunaction.testrunactionid=%s "+\
          "  AND ovt_testrunaction.versionedactionid=ovt_versionedactionattributevalue.versionedactionid "+\
          "  AND ovt_testrunaction.versionedactionid=ovt_versionedactionconfigoption.versionedactionid)) AS temp"
    self.execute(sql, (testrunactionid, testrunactionid, testrunactionid))
    values = self.cursor.fetchall()
    ret = {}
    for value in values:
      if not value['resourcetypeid'] in ret:
        ret[value['resourcetypeid']] = set()
      ret[value['resourcetypeid']].add(value['attributevalueid'])
    return ret

  def getClaimInfo(self, userclaimid, type, attribute):
    """
    Get an array of attribute values about a claim
    """
    sql = "SELECT ovt_resourceattribute.value AS simplevalue, ovt_attributevalue.value, "+\
          "       ovt_attributevalue.attributevalueid "+\
          "FROM ovt_userclaimresource INNER JOIN ovt_resourceattribute USING (resourceid) "+\
          "     INNER JOIN ovt_resource ON (ovt_userclaimresource.resourceid=ovt_resource.resourceid) "+\
          "     INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
          "     INNER JOIN ovt_attribute USING (attributeid) "+\
          "     INNER JOIN ovt_resourcetype ON (ovt_attribute.resourcetypeid=ovt_resourcetype.resourcetypeid) "+\
          "     LEFT OUTER JOIN ovt_attributevalue USING (attributevalueid) "+\
          "WHERE ovt_userclaimresource.userclaimid=%s "+\
          "AND ovt_resourcetype.resourcetypename=%s "+\
          "AND ovt_attribute.attributename=%s "+\
          "AND ovt_resourcestatus.status='HISTORIC' "+\
          "ORDER BY ovt_attributevalue.value"

    self.execute(sql, (userclaimid, type, attribute))
    values = self.cursor.fetchall()

    if len(values) == 0:
      return []
    elif len(values) == 1:
      if values[0]['simplevalue'] != None:
        return [values[0]['simplevalue']]
      else:
        return [values[0]['value']]
    else:
      retval = []
      for value in values:
        retval.append(value['value'])
      return retval

  def setUserClaimAttributeValue(self, userclaimid, type, name, value):
    """
    Sets the specified attribute value as having been requested
    """
    sql = "SELECT ovt_attributevalue.attributevalueid "+\
          "FROM ovt_attributevalue INNER JOIN ovt_attribute USING (attributeid) "+\
          "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
          "WHERE ovt_attributevalue.value=%s "+\
          "AND ovt_attribute.attributename=%s "+\
          "AND ovt_resourcetype.resourcetypename=%s"
    self.execute(sql, (value, name, type))
    id = self.cursor.fetchall()
    if len(id) == 0:
      return
    attributevalueid=id[0]['attributevalueid']
    sql = "SELECT ovt_userclaimattributevalue.* "+\
          "FROM ovt_userclaimattributevalue "+\
          "WHERE userclaimid=%s "+\
          "AND attributevalueid=%s"
    self.execute(sql, (userclaimid, attributevalueid))
    existing = self.cursor.fetchall()

    if len(existing) == 0:
      sql = "INSERT INTO ovt_userclaimattributevalue "+\
            "(userclaimid, attributevalueid) "+\
            "VALUES "+\
            "(%s, %s)"
      try:
        self.execute(sql, (userclaimid, attributevalueid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in userclaimattributevalue")

  def getUserResourceRequirements(self, userclaimid):
    """
    Fetches all resource requirements for a given testrun grouping by resourcetype
    """
    sql = "SELECT DISTINCT ovt_attributevalue.attributevalueid, ovt_attribute.resourcetypeid "+\
          "FROM ovt_attributevalue INNER JOIN ovt_userclaimattributevalue USING (attributevalueid) "+\
          "     INNER JOIN ovt_attribute USING (attributeid) "+\
          "WHERE ovt_userclaimattributevalue.userclaimid=%s"

    self.execute(sql, (userclaimid))
    values = self.cursor.fetchall()
    ret = {}
    for value in values:
      if not value['resourcetypeid'] in ret:
        ret[value['resourcetypeid']] = set()
      ret[value['resourcetypeid']].add(value['attributevalueid'])
    return ret


  def createResourceRequirement(self, versionedactionid, attributevalueid):
    """Creates a requirement for the specified versioned action using the attribute value"""
    sql = "SELECT versionedactionattributevalueid "+\
          "FROM ovt_versionedactionattributevalue "+\
          "WHERE versionedactionid=%s "+\
          "AND attributevalueid=%s LIMIT 1"
    self.execute(sql, (versionedactionid, attributevalueid))
    existing = self.cursor.fetchall()
    if len(existing) == 0:
      sql = "INSERT INTO ovt_versionedactionattributevalue "+\
            "(versionedactionid, attributevalueid) "+\
            "VALUES "+\
            "(%s, %s)"
      try:
        self.execute(sql, (versionedactionid, attributevalueid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in versionedactionattributevalue")
        return False
      return True
    return False

  def removeResourceRequirement(self, versionedactionid, attributevalueid):
    """
    Removes the specified attributevalue link to the given action
    """
    sql = "DELETE FROM ovt_versionedactionattributevalue "+\
          "WHERE versionedactionid=%s "+\
          "AND attributevalueid=%s"
    self.execute(sql, (versionedactionid, attributevalueid))

  def getConfigOptionGroups(self, conf):
    sql = "SELECT * "+\
          "FROM ovt_configoptiongroup "+\
          "ORDER BY ordering "
    self.execute(sql, ())
    groups = self.cursor.fetchall()
    ret = ({},[])
    for group in groups:
      ret[1].append(group['configoptiongroupid'])
      auto = ""
      if group['automatic']:
        auto = " [AUTO]"
      ret[0][group['configoptiongroupid']] = {"data":"(%s) %s%s"%(str(group['ordering']),group['configoptiongroupname'], auto), "type":"Config Group", "id":group['configoptiongroupid'], "automatic":group['automatic']}
    return ret

  def getConfigSetting(self, testrunid, versionedactionid, configname):
    """
    Get a config setting for the specified instance of a test
    """
    sql = "SELECT ovt_configoption.configoptionid, configoptiontypename, islookup, defaultvalue, lookupvalue "+\
          "FROM ovt_versionedactionconfigoption INNER JOIN ovt_configoption USING (configoptionid) "+\
          "     INNER JOIN ovt_configoptiontype USING (configoptiontypeid) "+\
          "     LEFT OUTER JOIN ovt_configoptionlookup ON (ovt_configoption.configoptionid=ovt_configoptionlookup.configoptionid "+\
          "                                                AND ovt_configoptionlookup.defaultlookup) "+\
          "WHERE ovt_versionedactionconfigoption.versionedactionid = %s "+\
          "AND ovt_configoption.configoptionname = %s"
    self.execute(sql, (versionedactionid, configname))
    option = self.cursor.fetchall()
    if len(option) == 0:
      return None
    configoptionid = option[0]['configoptionid']
    sql = "SELECT configvalue, lookupvalue "+\
          "FROM ovt_configsetting LEFT OUTER JOIN ovt_configoptionlookup USING (configoptionlookupid) "+\
          "WHERE testrunid = %s "+\
          "AND ovt_configsetting.configoptionid = %s"
    self.execute(sql, (testrunid, configoptionid))
    setting = self.cursor.fetchall()

    if len(setting) == 0:
      # Use the defaults
      if option[0]['islookup']:
        value = option[0]['lookupvalue']
      else:
        value = option[0]['defaultvalue']
    else:
      if option[0]['islookup']:
        value = setting[0]['lookupvalue']
      else:
        value = setting[0]['configvalue']

    if value != None:
      value = self.__convertConfigValueToType(option[0]['configoptiontypename'], value)

    return value

  def setConfigSetting(self, testrunid, versionedactionid, name, value):
    """
    Set a config value checking that it is valid for the versionedactionid
    and that the type of value is correct
    """
    sql = "SELECT ovt_configoption.configoptionid, ovt_configoptiontype.configoptiontypename "+\
          "FROM ovt_configoption INNER JOIN ovt_configoptiontype USING (configoptiontypeid) "+\
          "     INNER JOIN ovt_versionedactionconfigoption USING (configoptionid) "+\
          "WHERE ovt_versionedactionconfigoption.versionedactionid=%s "+\
          "AND ovt_configoption.configoptionname=%s "+\
          "AND NOT ovt_configoption.islookup"
    self.execute(sql, (versionedactionid, name))

    option = self.cursor.fetchall()

    if len(option) == 1:
      # The option exists and is linked to the specified versioned action

      # Check the type is correct
      if not ((option[0]['configoptiontypename'] == "string" and type(value) in types.StringTypes) \
               or (option[0]['configoptiontypename'] == "integer" and type(value) in (types.IntType, types.LongType)) \
               or (option[0]['configoptiontypename'] == "boolean" and type(value) == types.BooleanType)):
        raise ConfigException("Testrun: %u, vaid: %u... Variable: %s expected type: %s and got type %s"%(testrunid, versionedactionid, name, option[0]['configoptiontypename'], type(value)))

      # Check if the testrun already has a value and overwrite it or create as appropriate
      sql = "SELECT ovt_configsetting.configsettingid "+\
            "FROM ovt_configsetting "+\
            "WHERE testrunid=%s "+\
            "AND configoptionid=%s"
      self.execute(sql, (testrunid, option[0]['configoptionid']))

      existing = self.cursor.fetchall()

      if type(value) == types.BooleanType:
        if value:
          value = 'true'
        else:
          value = 'false'

      if len(existing) == 1:
        sql = "UPDATE ovt_configsetting "+\
              "SET configvalue=%s "+\
              "WHERE configsettingid=%s "
        self.execute(sql, (value, existing[0]['configsettingid']))
      else:
        sql = "INSERT INTO ovt_configsetting "+\
              "(testrunid, configoptionid, configvalue) "+\
              "VALUES "+\
              "(%s, %s, %s)"
        try:
          self.execute(sql, (testrunid, option[0]['configoptionid'], value))
        except postgresql.exceptions.UniqueError:
          self.FORCEROLLBACK()
          if not self.autocommit.autoCommit():
            raise DatabaseRetryException("Unique violation in configsetting")
          return False
      return True
    else:
      return False

  def getVersionedActionConfig(self, versionedactionid):
    """
    Fetches all configuration options linked to the specified versionedactionid
    these are returned grouped by configoptiongroup
    """
    sql = "SELECT DISTINCT ovt_configoptiongroup.configoptiongroupid, configoptiongroupname, automatic, ovt_configoptiongroup.ordering "+\
          "FROM ovt_configoption INNER JOIN ovt_versionedactionconfigoption USING (configoptionid) "+\
          "     INNER JOIN ovt_configoptiongroup USING (configoptiongroupid) "+\
          "WHERE ovt_versionedactionconfigoption.versionedactionid=%s "+\
          "ORDER BY ovt_configoptiongroup.ordering"
    self.execute(sql, (versionedactionid))
    groups = self.cursor.fetchall()
    ret = ({},[])
    for group in groups:
      ret[1].append(group['configoptiongroupid'])
      ret[0][group['configoptiongroupid']] = {"data":group['configoptiongroupname'],
                                              "type":"Config Option Group", 
                                              "id":group['configoptiongroupid'], 
                                              "automatic":group['automatic'],
                                              "related":({},[])}
      sql = "SELECT ovt_configoption.*, ovt_configoptiontype.configoptiontypename, ovt_configoptionlookup.lookupvalue "+\
            "FROM (ovt_configoption INNER JOIN ovt_versionedactionconfigoption USING (configoptionid) "+\
            "      INNER JOIN ovt_configoptiontype USING (configoptiontypeid)) "+\
            "     LEFT OUTER JOIN ovt_configoptionlookup ON (ovt_configoption.configoptionid=ovt_configoptionlookup.configoptionid "+\
            "                                                AND ovt_configoptionlookup.defaultlookup) "+\
            "WHERE ovt_versionedactionconfigoption.versionedactionid=%s "+\
            "AND ovt_configoption.configoptiongroupid=%s "+\
            "ORDER BY ovt_configoption.ordering"
      self.execute(sql, (versionedactionid, group['configoptiongroupid']))
      options = self.cursor.fetchall()
      self.__processOptions(ret[0][group['configoptiongroupid']]['related'], options, versionedactionid)
    return ret

  def getInfoForVersionedAction(self, testrunid, versionedactionid):
    """
    Returns the actionid for the versionedaciton
    """
    sql = "SELECT ovt_action.actionid, actionname, ovt_testrunaction.testrunactionid "+\
          "FROM ovt_versionedaction INNER JOIN ovt_action USING (actionid) "+\
          "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "WHERE ovt_testrunaction.versionedactionid=%s "+\
          "AND ovt_testrunaction.testrunid=%s"
    self.execute(sql, (versionedactionid, testrunid))
    actions = self.cursor.fetchall()

    if len(actions) == 0:
      return None
    else:
      return actions[0]

  def searchConfigOptions(self, searchterm = None, actionid = None, configoptionid = None, extend=None):
    """Find an arbitrary config option"""
    if extend == None:
      extend = ({},[])

    if actionid == None and searchterm == None and configoptionid == None:
      return extend
    if actionid != None:
      sql = "SELECT DISTINCT ovt_configoptiongroup.configoptiongroupid, configoptiongroupname, ovt_configoptiongroup.ordering "+\
            "FROM ovt_configoption INNER JOIN ovt_configoptiongroup USING (configoptiongroupid) "+\
            "                      INNER JOIN ovt_versionedactionconfigoption USING (configoptionid) "+\
            "                      INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
            "WHERE ovt_versionedaction.actionid = %s "+\
            "ORDER BY ordering"
      self.execute(sql, (actionid))
    else:
      values = []
      sql = "SELECT DISTINCT ovt_configoptiongroup.configoptiongroupid, configoptiongroupname, ovt_configoptiongroup.ordering "+\
            "FROM ovt_configoption INNER JOIN ovt_configoptiongroup USING (configoptiongroupid) "
      if searchterm != None:
        sql +="WHERE ovt_configoption.configoptionname LIKE %s "
        values = [searchterm]
      elif configoptionid != None:
        sql +="WHERE ovt_configoption.configoptionid=%s "
        values = [configoptionid]
      sql +="ORDER BY ordering"
      self.execute(sql, values)
    groups = self.cursor.fetchall()
    ret = extend
    for group in groups:
      if not group['configoptiongroupid'] in ret[1]:
        ret[1].append(group['configoptiongroupid'])
        ret[0][group['configoptiongroupid']] = {"data":group['configoptiongroupname'], "type":"Config Option Group", "id":group['configoptiongroupid'], "related":({},[])}
      if actionid != None:
        sql = "SELECT ovt_configoption.*, ovt_configoptiontype.configoptiontypename, ovt_configoptionlookup.lookupvalue "+\
              "FROM ovt_configoption INNER JOIN ovt_configoptiontype USING (configoptiontypeid) "+\
              "                      INNER JOIN ovt_versionedactionconfigoption USING (configoptionid) "+\
              "                      INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
              "     LEFT OUTER JOIN ovt_configoptionlookup ON (ovt_configoption.configoptionid=ovt_configoptionlookup.configoptionid "+\
              "                                                AND ovt_configoptionlookup.defaultlookup) "+\
              "WHERE ovt_configoption.configoptiongroupid = %s "+\
              "AND ovt_versionedaction.actionid = %s "+\
              "ORDER BY ovt_configoption.configoptionname"
        self.execute(sql, (group['configoptiongroupid'], actionid))
      else:
        values = []
        sql = "SELECT ovt_configoption.*, ovt_configoptiontype.configoptiontypename, ovt_configoptionlookup.lookupvalue "+\
              "FROM ovt_configoption INNER JOIN ovt_configoptiontype USING (configoptiontypeid) "+\
              "     LEFT OUTER JOIN ovt_configoptionlookup ON (ovt_configoption.configoptionid=ovt_configoptionlookup.configoptionid "+\
              "                                                AND ovt_configoptionlookup.defaultlookup) "
        if searchterm != None:
          sql += "WHERE ovt_configoption.configoptiongroupid = %s "+\
                 "AND ovt_configoption.configoptionname LIKE %s "
          values = [group['configoptiongroupid'], searchterm]
        elif configoptionid != None:
          sql += "WHERE ovt_configoption.configoptionid = %s "
          values = [configoptionid]
        sql+= "ORDER BY ovt_configoption.configoptionname"
        self.execute(sql, values)
      options = self.cursor.fetchall()
      self.__processOptions(ret[0][group['configoptiongroupid']]['related'], options)
    return ret

  def __processOptions(self, target, options, versionedactionid = None):
    for option in options:
      if not option['configoptionid'] in target[1]:
        target[1].append(option['configoptionid'])
        target[0][option['configoptionid']] = {"data":option['configoptionname'], "type":"Config Option", "id":option['configoptionid']}
      opt = target[0][option['configoptionid']]
      opt['ordering'] = option['ordering']
      opt['islookup'] = option['islookup']
      opt['configtype'] = option['configoptiontypename']
      if opt['islookup']:
        opt['default'] = option['lookupvalue']
      else:
        opt['default'] = option['defaultvalue']
      opt['default'] = self.__convertConfigValueToType(opt['configtype'], opt['default'])

      if opt['islookup']:
        if not 'related' in opt:
          opt['related'] = ({},[])
        if versionedactionid != None:
          sql = "SELECT * "+\
                "FROM ovt_configoptionlookup INNER JOIN ovt_versionedactionconfigoptionlookup USING (configoptionlookupid) "+\
                "WHERE configoptionid=%s "+\
                "AND versionedactionid=%s "+\
                "ORDER BY lookupname"
          self.execute(sql, (option['configoptionid'], versionedactionid))
        else:
          sql = "SELECT * "+\
                "FROM ovt_configoptionlookup "+\
                "WHERE configoptionid=%s "+\
                "ORDER BY lookupname"
          self.execute(sql, (option['configoptionid']))
        lookups = self.cursor.fetchall()
        for lookup in lookups:
          if not lookup['configoptionlookupid'] in opt['related'][1]:
            opt['related'][1].append(lookup['configoptionlookupid'])
            opt['related'][0][lookup['configoptionlookupid']] = {}
          lookupopt = opt['related'][0][lookup['configoptionlookupid']]
          lookupopt["data"] = lookup['lookupname']
          lookupopt["type"] = "Config Option Lookup"
          lookupopt["id"] = lookup['configoptionlookupid']
          sql = "SELECT configoptionlookupattributevalueid, "+\
                "       resourcetypename || ' - ' || attributename || ' - ' || ovt_attributevalue.value AS name "+\
                "FROM ovt_configoptionlookupattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
                "     INNER JOIN ovt_attribute USING (attributeid) "+\
                "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
                "WHERE configoptionlookupid = %s "+\
                "ORDER BY ovt_resourcetype.resourcetypename, ovt_attribute.attributename, ovt_attributevalue.value"
          self.execute(sql, (lookup['configoptionlookupid']))
          requirements = self.cursor.fetchall()
          
          if len(requirements) != 0:
            if not 'related' in lookupopt:
              lookupopt["related"] = ({},[])
            for requirement in requirements:
              if not requirement['configoptionlookupattributevalueid'] in lookupopt["related"][1]:
                lookupopt["related"][1].append(requirement['configoptionlookupattributevalueid'])
                lookupopt["related"][0][requirement['configoptionlookupattributevalueid']] = {}
              reqs = lookupopt["related"][0][requirement['configoptionlookupattributevalueid']]
              reqs["data"] = requirement['name']
              reqs["type"] = "Resource Requirement"
              reqs["id"] = requirement['configoptionlookupattributevalueid']

  def __convertConfigValueToType(self, type, value):
    if type == "string":
      return value
    elif type == "integer":
      return int(value)
    elif type == "boolean":
      return value == "true"
    else:
      self.log.write("Error config type not found: %s"%type)
      return "TYPE NOT FOUND string value: "+value

  def unlinkConfigOptionLookup(self, versionedactionid, configoptionlookupid):
    """
    Unlink the specified config option lookup
    """
    sql = "DELETE FROM ovt_versionedactionconfigoptionlookup "+\
          "WHERE versionedactionid=%s "+\
          "AND configoptionlookupid=%s"

    self.execute(sql, (versionedactionid, configoptionlookupid))

  def unlinkAndMaybeRemoveOption(self, versionedactionid, configoptionid):
    """
    Unlink the specified option from the versioned action.
    Unlink all lookups for the option (doesn't matter if it is lookup or not, the SQL is safe)
    Remove the config option if it is not linked to anything else.
    Remove the config option group if it is not linked to any other options
    """
    sql = "DELETE FROM ovt_versionedactionconfigoption "+\
          "WHERE versionedactionid = %s "+\
          "AND configoptionid = %s"
    self.execute(sql, (versionedactionid, configoptionid))

    sql = "DELETE FROM ovt_versionedactionconfigoptionlookup "+\
          "USING ovt_configoptionlookup "+\
          "WHERE versionedactionid = %s "+\
          "AND ovt_configoptionlookup.configoptionlookupid=ovt_versionedactionconfigoptionlookup.configoptionlookupid "+\
          "AND ovt_configoptionlookup.configoptionid = %s"
    self.execute(sql, (versionedactionid, configoptionid))

    sql = "SELECT ovt_configoption.configoptionid, ovt_configoption.configoptiongroupid, count(versionedactionconfigoptionid) AS usecount "+\
          "FROM ovt_versionedactionconfigoption RIGHT OUTER JOIN ovt_configoption USING (configoptionid) "+\
          "WHERE ovt_configoption.configoptionid=%s "+\
          "GROUP BY ovt_configoption.configoptionid, ovt_configoption.configoptiongroupid"

    self.execute(sql, (configoptionid))
    group = self.cursor.fetchall()
    if len(group) == 0:
      return
    configoptiongroupid = group[0]['configoptiongroupid']

    if group[0]['usecount'] == 0:
      sql = "DELETE FROM ovt_configoption "+\
            "WHERE configoptionid = %s"
      self.execute(sql, (configoptionid))

      sql = "SELECT count(configoptionid) AS usecount "+\
            "FROM ovt_configoption "+\
            "WHERE configoptiongroupid=%s"
      self.execute(sql, (configoptiongroupid))
      group = self.cursor.fetchall()
      if group[0]['usecount'] == 0:
        sql = "DELETE FROM ovt_configoptiongroup "+\
              "WHERE configoptiongroupid=%s"
        self.execute(sql, (configoptiongroupid))

  def getVersionedActionFromTestrun(self, testrunid, actionname):
    """
    Get the version of the specified action that appears in the specified testrun
    """
    sql = "SELECT versionedactionid "+\
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "WHERE actionname=%s "+\
          "AND testrunid=%s"
    self.execute(sql, (actionname, testrunid))
    version = self.cursor.fetchall()
    if len(version) != 1:
      return None
    return version[0]['versionedactionid']

  def getConfigTypes(self, conf):
    """Fetch all the config option types"""
    sql = "SELECT * "+\
          "FROM ovt_configoptiontype "+\
          "ORDER BY configoptiontypename"
    self.execute(sql, ())
    types = self.cursor.fetchall()
    ret = ({},[])
    for type in types:
      ret[1].append(type['configoptiontypeid'])
      ret[0][type['configoptiontypeid']] = {"data":type['configoptiontypename'], "id":type['configoptiontypeid'], "type":"Type"}
    return ret

  def createConfigOptionLink(self, newversionedactionid, configoptionid):
    """Links an existing config option to a version of an action"""
    sql = "SELECT versionedactionconfigoptionid "+\
          "FROM ovt_versionedactionconfigoption "+\
          "WHERE versionedactionid=%s "+\
          "AND configoptionid=%s"
    self.execute(sql, (newversionedactionid, configoptionid))
    existing = self.cursor.fetchall()
    if len(existing) == 0:
      sql = "INSERT INTO ovt_versionedactionconfigoption "+\
            "(versionedactionid, configoptionid) "+\
            "VALUES "+\
            "(%s, %s)"
      try:
        self.execute(sql, (newversionedactionid, configoptionid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in versionedactionconfigoption")
        return False
      return True
    return False

  def createConfigOptionLookupLink(self, newversionedactionid, configoptionlookupid):
    """
    Links an existing config option lookup to a version of an action
    """
    # Check that the config option is linked to the versioned action
    sql = "SELECT versionedactionconfigoptionid "+\
          "FROM ovt_versionedactionconfigoption INNER JOIN ovt_configoptionlookup USING (configoptionid) "+\
          "WHERE versionedactionid=%s "+\
          "AND configoptionlookupid=%s "+\
          "LIMIT 1"
    self.execute(sql, (newversionedactionid, configoptionlookupid))
    if len(self.cursor.fetchall()) != 1:
      return False

    sql = "SELECT versionedactionconfigoptionlookupid "+\
          "FROM ovt_versionedactionconfigoptionlookup "+\
          "WHERE versionedactionid=%s "+\
          "AND configoptionlookupid=%s"
    self.execute(sql, (newversionedactionid, configoptionlookupid))
    existing = self.cursor.fetchall()
    if len(existing) == 0:
      sql = "INSERT INTO ovt_versionedactionconfigoptionlookup "+\
            "(versionedactionid, configoptionlookupid) "+\
            "VALUES "+\
            "(%s, %s)"
      try:
        self.execute(sql, (newversionedactionid, configoptionlookupid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in versionedactionconfigoptionlookup")
        return False
      return True
    return False

  def removeDependency(self, dependencyid):
    """
    Remove a dependency
    This will only allow a dependency to be removed if the consumer is not part of /any/ testrun
    """
    sql = "SELECT ovt_testrunaction.testrunactionid "+\
          "FROM ovt_testrunaction INNER JOIN ovt_dependency USING (versionedactionid) "+\
          "     INNER JOIN ovt_testrunaction AS foo ON (ovt_dependency.versionedactiondep=foo.versionedactionid AND foo.testrunid=ovt_testrunaction.testrunid) "+\
          "WHERE ovt_dependency.dependencyid=%s"
    self.execute(sql, (dependencyid))
    existing = self.cursor.fetchall()
    if len(existing) != 0:
      return False

    sql = "DELETE FROM ovt_dependency "+\
          "WHERE dependencyid=%s"
    self.execute(sql, (dependencyid))

    return True

  def createDependency(self, producer=None, consumer=None, dependencyid = None, values = {}):
    """NO COMMIT"""
    dependencygroupid = "NOT SET"
    versiononly = None
    hostmatch = None
    defaultdep = None
    if dependencyid != None:
      sql = "SELECT * "+\
            "FROM ovt_dependency "+\
            "WHERE dependencyid=%s"
      self.execute(sql, (dependencyid))
      dependencies = self.cursor.fetchall()
      if len(dependencies) == 0:
        return (False, "INVALID DEPENDENCYID")
      dependency = dependencies[0]
      dependencygroupid = dependency['dependencygroupid']
      versiononly = dependency['versiononly']
      hostmatch = dependency['hostmatch']
      defaultdep = dependency['defaultdep']
      if producer == None:
        producer = dependency['versionedactiondep']
      if consumer == None:
        consumer = dependency['versionedactionid']
    if dependencygroupid == "NOT SET":
      if "dependencygroupid" in values:
        dependencygroupid = values['dependencygroupid']
      else:
        dependencygroupid = None
    if versiononly == None:
      if "versiononly" in values and values['versiononly'] != None:
        versiononly = values['versiononly']
      else:
        versiononly = False
    if hostmatch == None:
      if "hostmatch" in values and values['hostmatch'] != None:
        hostmatch = values['hostmatch']
      else:
        hostmatch = False

    if defaultdep == None:
      if "defaultdep" in values and values['defaultdep'] != None:
        defaultdep = values['defaultdep']
      else:
        defaultdep = True

    # All dependency attributes have now been set
    # verify the dependency
    suggestions = self.__verifyDependency(producer, consumer)
    if suggestions == False:
      return (False, "CANNOT DEPEND ON SELF or\nINVERSE DEPENDENCY EXISTS or\nEXISTING AND DEPENDENCY SET ON SAME ACTION DOES NOT INCLUDE THIS VERSION")
    sql = "SELECT * "+\
          "FROM ovt_dependency "+\
          "WHERE versionedactionid = %s "+\
          "AND versionedactiondep = %s LIMIT 1"
    self.execute(sql, (consumer, producer))
    existing = self.cursor.fetchall()
    if len(existing) != 0:
      if dependencygroupid != existing[0]['dependencygroupid']:
        self.ovtDB.rollback()
        return (False, "MISMATCH BETWEEN EXISTING/CREATED DEPENDENCY AND SPECIFIED DEPENDENCYGROUPID")
      if versiononly != None and versiononly != existing[0]['versiononly']:
        self.ovtDB.rollback()
        return (False, "MISMATCH BETWEEN EXISTING/CREATED DEPENDENCY AND SPECIFIED VERSIONONLY STATE")
      if hostmatch != None and hostmatch != existing[0]['hostmatch']:
        self.ovtDB.rollback()
        return (False, "MISMATCH BETWEEN EXISTING/CREATED DEPENDENCY AND SPECIFIED HOSTMATCH STATE")

      return (True, suggestions)
    # Now check if the defaultdep is valid
    if defaultdep:
      existing = self.__getDefaultDependency(producer, consumer, dependencygroupid)
      if len(existing) != 0:
        # Silently disable the default dependency flag
        defaultdep = False
    self.__addDependency(producer, consumer, dependencygroupid, versiononly, hostmatch, defaultdep)
    return (True, suggestions)

  def __addDependency(self, producer, consumer, dependencygroupid, versiononly, hostmatch, defaultdep):
    """NO COMMIT"""
    fieldextra = ""
    valueextra = ""
    vals = [consumer, producer, versiononly, hostmatch, defaultdep]
    if dependencygroupid != None:
      fieldextra += ", dependencygroupid"
      valueextra = ", %s"
      vals.append(dependencygroupid)
    sql = "INSERT INTO ovt_dependency "+\
          "(versionedactionid, versionedactiondep, versiononly, hostmatch, defaultdep"+fieldextra+") "+\
          "VALUES "+\
          "(%s, %s, %s, %s, %s"+valueextra+")"
    self.execute(sql, vals)

  def __verifyDependency(self, producer, consumer):
    """NO COMMIT"""
    # prologue:
    # Find the producer's action
    # 1) Ensure producer's action does not depend on consumer's action EVER
    # 2) Starting from consumer find all dependencies that point to versions of 'action'. These dependency sets must include producer.
    # 3) Follow all dependencies from consumer and repeat 2
    sql = "SELECT versionedactionid, actionid "+\
          "FROM ovt_versionedaction "+\
          "WHERE versionedactionid=%s "+\
          "OR versionedactionid=%s "
    self.execute(sql, (producer, consumer))
    actions = self.cursor.fetchall()
    for action in actions:
      if action['versionedactionid'] == consumer:
        consumeractionid = action['actionid']
      if action['versionedactionid'] == producer:
        produceractionid = action['actionid']
    # 1) Ensure producer's action does not depend on consumer's action EVER (note the inversion of consumer and producer)
    if self.__checkDependencyChain(consumeractionid, produceractionid):
      # This means that the dependency cannot be made as there is an inverse relationship between the associated actionids already
      return False
    # 2) Starting from consumer find all dependencies that point to versions of 'action'. If a dependency set is found make a dependency suggestion
    # 3) Follow all dependencies from consumer and repeat 2
    suggestions = self.__recursiveVerifyNoSameActionConflict(produceractionid, producer, consumer)
    return suggestions

  def __checkDependencyChain(self, produceractionid, consumeractionid):
    """NO COMMIT Determine if there is any relationship from consumeractionid to produceractionid"""
    if consumeractionid == produceractionid:
      return True
    sql = "SELECT DISTINCT va2.actionid "+\
          "FROM ovt_dependency INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_versionedaction AS va2 ON (va2.versionedactionid=ovt_dependency.versionedactiondep)"+\
          "WHERE ovt_versionedaction.actionid=%s"
    self.execute(sql, (consumeractionid))
    dependencies = self.cursor.fetchall()
    for dependency in dependencies:
      if self.__checkDependencyChain(produceractionid, dependency['actionid']):
        return True
    return False

  def __recursiveVerifyNoSameActionConflict(self, actionid, producer, consumer):
    """NO COMMIT"""
    suggestions = []
    # WORK NEEDED: What was I going to do with suggestions anyway
    #              Don't bother looking for suggestions until they are 'used'
    return suggestions
    suggest = self.__verifyNoSameActionConflict(actionid, producer, consumer)
    if suggest != None:
      suggestions.append(suggest)
    sql = "SELECT versionedactiondep "+\
          "FROM ovt_dependency "+\
          "WHERE versionedactionid=%s"
    self.execute(sql, (consumer))
    dependencies = self.cursor.fetchall()
    for dependency in dependencies:
      suggestions.extend(self.__recursiveVerifyNoSameActionConflict(actionid, producer, dependency['versionedactiondep']))
    return suggestions

  def __verifyNoSameActionConflict(self, actionid, producer, consumer):
    """NO COMMIT"""
    # Fetch all dependencies from consumer to versions of actionid
    sql = "SELECT ovt_dependency.versionedactionid, ovt_dependency.dependencygroupid, versiononly  "+\
          "FROM ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_versionedaction.versionedactionid = ovt_dependency.versionedactiondep) "+\
          "WHERE ovt_versionedaction.actionid=%s "+\
          "AND ovt_dependency.versionedactionid=%s"
    self.execute(sql, (actionid, consumer))
    versions = self.cursor.fetchall()
    if len(versions) != 0:
      found = False
      for version in versions:
        if version['versionedactionid'] == producer:
          found = True
      if not found:
        return (producer, consumer, versions[0]['dependencygroupid'], versions[0]['versiononly'])
    return None

  def toggleDefaultDependency(self, dependencyid):
    """
    :param dependencyid: The dependency to modify
    :type dependencyid: Database identifier
    :return: Whether the change was successful
    :rtype: boolean
    
    Toggles the default flag on the dependency. Toggle off always works but
    toggle on may fail if a conflicting dependency (i.e. in the same group)
    is already set default.
    """
    depattrs = self.simple.getDependencyAttributesById(dependencyid)
    defaultdep = self.__getDefaultDependency(depattrs['versionedactiondep'],
                                             depattrs['versionedactionid'],
                                             depattrs['dependencygroupid'])
    if len(defaultdep) == 0:
      # Toggle on the default
      self.simple.setDependencyDefault(dependencyid, True)
    elif defaultdep[0]['dependencyid'] == dependencyid:
      # Toggle off the default
      self.simple.setDependencyDefault(dependencyid, False)
    else:
      return False
    return True

  def __getDefaultDependency(self, producer, consumer, dependencygroupid):
    """
    :param producer: A versioned action used as a producer in a dependency
    :type producer: Database identifier
    :param consumer: A versioned action used as a consumer in a dependency
    :type consumer: Database identifier
    :param dependencygroupid: The dependency group
    :type dependencygroupid: Database identifier
    :return: The existing default dependency in the same class as the specified
             dependency.
    :rtype: Database rows
    """
    sql = "SELECT * "+\
          "FROM ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_dependency.versionedactiondep=ovt_versionedaction.versionedactionid) "+\
          "WHERE ovt_dependency.defaultdep " +\
          "AND ovt_dependency.versionedactionid=%s "
    values = [consumer]
    if dependencygroupid == None:
      sql += "AND ovt_versionedaction.actionid=(SELECT actionid FROM ovt_versionedaction WHERE versionedactionid=%s)"
      values.append(producer)
    else:
      sql += "AND ovt_dependency.dependencygroupid=%s"
      values.append(dependencygroupid)
    self.execute(sql, values)
    return self.cursor.fetchall()

  def findTestrunAction(self, actionnameorid, testrunid):
    if type(actionnameorid) in (types.IntType, types.LongType) :
      sql = "SELECT ovt_testrunaction.testrunactionid, ovt_testrunaction.versionedactionid "+\
            "FROM ovt_versionedaction INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
            "WHERE ovt_testrunaction.testrunid=%s "+\
            "AND ovt_versionedaction.actionid=%s"
    else:
      sql = "SELECT ovt_testrunaction.testrunactionid, ovt_testrunaction.versionedactionid "+\
            "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid) "+\
            "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
            "WHERE ovt_testrunaction.testrunid=%s "+\
            "AND ovt_action.actionname=%s"
    self.execute(sql, (testrunid, actionnameorid))
    result = self.cursor.fetchall()
    if len(result) == 1:
      return result[0]['testrunactionid']
    return None

  def getActionCategories(self, conf):
    sql = "SELECT * "+\
          "FROM ovt_actioncategory INNER JOIN ovt_lifecyclestate USING (lifecyclestateid) "+\
          "ORDER BY actioncategoryname"
    self.execute(sql, ())
    actioncategories = self.cursor.fetchall()
    ret = ({}, [])
    for actioncategory in actioncategories:
      ret[1].append(actioncategory['actioncategoryid'])
      ret[0][actioncategory['actioncategoryid']] = {"data":actioncategory['actioncategoryname'], "note":actioncategory['lifecyclestatename'], "id":actioncategory['actioncategoryid'], "type":"Action Category"}
    return ret

  def addActionCategory(self, values):
    sql = "SELECT actioncategoryid "+\
          "FROM ovt_actioncategory "+\
          "WHERE actioncategoryname=%s"
    self.execute(sql, (values['name']))
    existing = self.cursor.fetchall()
    if len(existing) == 0:
      sql2 = "INSERT INTO ovt_actioncategory "+\
            "(actioncategoryname) "+\
            "VALUES "+\
            "(%s)"
      try:
        self.execute(sql2, (values['name']))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in actioncategory")
      self.execute(sql, (values['name']))
      existing = self.cursor.fetchall()
    return existing[0]['actioncategoryid']

  def getDefaultDependenciesInTestrun(self, testrunid):
    sql = "SELECT consumeraction.actionname AS consumername, produceraction.actionname AS producername "+\
          "FROM ovt_action AS consumeraction "+\
          "     INNER JOIN ovt_versionedaction AS consumerversion USING (actionid) "+\
          "     INNER JOIN ovt_testrunaction AS consumertra USING (versionedactionid) "+\
          "     INNER JOIN ovt_dependency ON (ovt_dependency.versionedactionid = consumerversion.versionedactionid) "+\
          "     INNER JOIN ovt_testrunaction AS producertra ON (ovt_dependency.versionedactiondep = producertra.versionedactionid) "+\
          "     INNER JOIN ovt_versionedaction AS producerversion ON (producertra.versionedactionid = producerversion.versionedactionid) "+\
          "     INNER JOIN ovt_action AS produceraction ON (producerversion.actionid = produceraction.actionid) "+\
          "WHERE producertra.testrunid=consumertra.testrunid "+\
          "AND producertra.testrunid=%s "+\
          "AND ovt_dependency.defaultdep"
    self.execute(sql, (testrunid))
    result = self.cursor.fetchall()
    ret = {}
    for row in result:
      if not row['consumername'] in ret:
        ret[row['consumername']] = []
      ret[row['consumername']].append(row['producername'])
    return ret

  def getDependencies(self, versionedactionid):
    sql = "SELECT ovt_versionedaction.versionedactionid, ovt_dependencygroup.dependencygroupid, dependencygroupname, " +\
          "       actionname, versionname, defaultdep " +\
          "FROM (ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_dependency.versionedactiondep=ovt_versionedaction.versionedactionid)" +\
          "      INNER JOIN ovt_action USING (actionid)) " +\
          "     LEFT OUTER JOIN ovt_dependencygroup USING (dependencygroupid) " +\
          "WHERE ovt_dependency.versionedactionid= %s " +\
          "ORDER BY dependencygroupname, actionname, versionname"
    self.execute(sql, (versionedactionid))
    result = self.cursor.fetchall()
    res = {}
    groupname = None
    actionname = None
    for row in result:
      newgroupname = row['dependencygroupname']
      if newgroupname == None:
        newgroupname = ""
      if groupname != newgroupname:
        groupname = newgroupname
        res[groupname] = {}
      if actionname != row['actionname']:
        actionname = row['actionname']
        res[groupname][actionname] = []
      res[groupname][actionname].append(row)
    return res

  def getDependenciesMulti(self, versionedactionids):
    if len(versionedactionids) == 0:
      return {}
    # This is an optimisation! Gather the dependencies in batches and merge
    # This method gives a x10 improvement in speed, and spends less time in
    # the database. ~40000 dependencies in 16 seconds
    res = {}

    for versionedactionid in versionedactionids:
      res[versionedactionid] = {}
      sql = "SELECT ovt_dependency.versionedactionid AS keyid, "+\
            "       ovt_versionedaction.versionedactionid, "+\
            "       ovt_dependencygroup.dependencygroupid, "+\
            "       dependencygroupname, " +\
            "       actionname, versionname, defaultdep " +\
            "FROM (ovt_dependency INNER JOIN ovt_versionedaction ON (ovt_dependency.versionedactiondep=ovt_versionedaction.versionedactionid)" +\
            "      INNER JOIN ovt_action USING (actionid)) " +\
            "     LEFT OUTER JOIN ovt_dependencygroup USING (dependencygroupid) " +\
            "WHERE ovt_dependency.versionedactionid=%s " +\
            "ORDER BY keyid, dependencygroupname, actionname, versionname"
      self.execute(sql, (versionedactionid))
      result = self.cursor.fetchall()
      groupname = None
      actionname = None
      for row in result:
        newgroupname = row['dependencygroupname']
        if newgroupname == None:
          newgroupname = ""
        if groupname != newgroupname or not groupname in res[row['keyid']]:
          groupname = newgroupname
          res[row['keyid']][groupname] = {}
        if actionname != row['actionname'] or not actionname in res[row['keyid']][groupname]:
          actionname = row['actionname']
          res[row['keyid']][groupname][actionname] = []
        res[row['keyid']][groupname][actionname].append(row)
    return res

  def checkSingleActionPerTestrun(self, testrunid):
    """
    Determine if there are multiple versions of any action in
    the specified testrun. Return a list of action names
    for those with multiple versions
    """
    sql = "SELECT ovt_action.actionname, count(ovt_action.actionid) AS duplicatecount "+\
          "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid) "+\
          "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "WHERE ovt_testrunaction.testrunid=%s "+\
          "GROUP BY ovt_action.actionid, ovt_action.actionname "+\
          "HAVING count(ovt_action.actionid) > 1"

    self.execute(sql, (testrunid))
    result = self.cursor.fetchall()
    res = {}
    for row in result:
      res[row['actionname']] = row['duplicatecount']
    return res

  def checkValidVersionedActionsInTestrun(self, testrunid):
    """
    Determine if any of the versioned actions in the testrun are invalid
    This may be because the category or action is invalid
    """
    sql = "SELECT ovt_action.actionname, ovt_versionedaction.versionname "+\
          "FROM ovt_actioncategory INNER JOIN ovt_action USING (actioncategoryid) "+\
          "     INNER JOIN ovt_versionedaction USING (actionid) "+\
          "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_lifecyclestate AS l1 ON (l1.lifecyclestateid=ovt_actioncategory.lifecyclestateid) "+\
          "     INNER JOIN ovt_lifecyclestate AS l2 ON (l2.lifecyclestateid=ovt_action.lifecyclestateid) "+\
          "     INNER JOIN ovt_lifecyclestate AS l3 ON (l3.lifecyclestateid=ovt_versionedaction.lifecyclestateid) "+\
          "WHERE ovt_testrunaction.testrunid=%s "+\
          "AND ((NOT l1.valid) "+\
          "     OR (NOT l2.valid) "+\
          "     OR (NOT l3.valid))"
    self.execute(sql, (testrunid))
    result = self.cursor.fetchall()
    res = []
    for row in result:
      res.append("%s:%s" % (row['actionname'], row['versionname']))
    return res


  def getFullVersionName(self, versionedactionid):
    sql = "SELECT ovt_action.actionname || ' [' || ovt_versionedaction.versionname || ']' AS version " +\
          "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid) " +\
          "WHERE ovt_versionedaction.versionedactionid=%s"
    self.execute(sql, (versionedactionid))
    result = self.cursor.fetchall()
    if len(result) == 0:
      return "Invalid"
    else:
      return result[0]['version']

  def checkTestrun(self, testrunid, userid):
    """
    Check that the testrun specified both exists and is owned by the user specified
    """
    sql = "SELECT testrunid "+\
          "FROM ovt_testrun "+\
          "WHERE testrunid=%s "+\
          "AND userid=%s"
    self.execute(sql, (testrunid, userid))
    ret = (len(self.cursor.fetchall()) != 0)
    return ret

  def getUserid(self, username):
    sql = "SELECT userid " +\
          "FROM ovt_user " +\
          "WHERE username=%s"

    self.execute(sql, (username))
    result = self.cursor.fetchall()
    if len(result) == 0:
      return None
    return result[0]['userid']

  def registerPID(self, testrunid, versionedactionid, pid):
    sql = "UPDATE ovt_testrunaction "+\
          "SET pid=%s "+\
          "WHERE testrunid=%s "+\
          "AND versionedactionid=%s"
    self.execute(sql, (pid, testrunid, versionedactionid))
    return True


  def getVersionedActionidDict(self, testrunid):
    sql = "SELECT ovt_testrunaction.versionedactionid "+\
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "WHERE testrunid=%s "
    
    self.execute(sql, (testrunid))
    result = self.cursor.fetchall()
    versionedactioniddict = {}
    for row in result:
      versionedactioniddict[row['versionedactionid']] = {}
    return versionedactioniddict

  def getVersionedActionid(self, testrunid, actionid):
    sql = "SELECT ovt_testrunaction.versionedactionid "+\
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "WHERE testrunid=%s AND actionid=%s"
    
    self.execute(sql, (testrunid, actionid))
    result = self.cursor.fetchall()

    if len(result) > 0:
      if len(result[0]) > 0:
        return result[0][0]
    
    return None

  def findTestrunactionResources(self, testrunactionid):
    """
    Find all the resources assigned to the testrun that are needed
    for the versionedaction that the testrunaction refers to
    """
    None

  def getUserResources(self, userclaimid, held=False):
    """
    :param userclaimid: The user claim to query
    :type userclaimid: Database identifier
    :return: All claimed resources
    :rtype: List of resource identifiers

    Retrieve a list of all resources that have been claimed. This will return
    historic resources wherever possible.
    """
    sql = "SELECT ovt_userclaimresource.resourceid, ucr.resourceid AS historicresourceid "+\
          "FROM (ovt_resource INNER JOIN ovt_userclaimresource AS ucr "+\
          "                              ON (ovt_resource.resourceid = ucr.resourceid "+\
          "                                  AND ucr.userclaimid=%s)) "+\
          "     RIGHT OUTER JOIN ovt_userclaimresource "+\
          "                      ON (ovt_resource.baseresourceid=ovt_userclaimresource.resourceid)"+\
          "WHERE ovt_userclaimresource.userclaimid=%s "
    if held:
      sql += "AND ovt_userclaimresource.held"
    self.execute(sql, (userclaimid, userclaimid))
    resources = self.cursor.fetchall()
    result = []
    historic = False
    for resource in resources:
      if resource['historicresourceid'] != None:
        historic = True
        result.append(resource['historicresourceid'])
      else:
        result.append(resource['resourceid'])
    return result, historic

  def getFormattedResource(self, resourceid):
    """
    Fetch and format resource info
    """
    details = self.getResources(None, resourceid)
    resourceinfo = {'attributes': {}}
    if len(details[0]) > 0:
      resource = details[0][details[1][0]]
      resourceinfo['name'] = resource['name']
      resourceinfo['hostname'] = resource['hostname']
      resourceinfo['resourceid'] = resource['id']
      for resourcetypeid in resource['related'][0]:
        resourcetype = resource['related'][0][resourcetypeid]
        resourceinfo['type'] = resourcetype['data']
        resourceinfo['typeid'] = resourcetype['id']
        for attributeid in resourcetype['related'][0]:
          attribute = resourcetype['related'][0][attributeid]
          resourceinfo['attributes'][attribute['data']] = []
          att = resourceinfo['attributes'][attribute['data']]
          for resourceattributeid in attribute['related'][0]:
            att.append(attribute['related'][0][resourceattributeid]['data'])
    return resourceinfo


  def getUserResource(self, userclaimid, resourceid):
    """
    Get the resource information for the specified resource
    """
    resourceinfo = self.getFormattedResource(resourceid)

    sql = "SELECT ovt_attributevalue.value, ovt_attribute.attributename "+\
          "FROM ovt_userclaimattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
          "     INNER JOIN ovt_attribute USING (attributeid) "+\
          "     INNER JOIN ovt_resourceattribute ON (ovt_attributevalue.attributevalueid=ovt_resourceattribute.attributevalueid) "+\
          "WHERE ovt_userclaimattributevalue.userclaimid=%s "+\
          "AND ovt_resourceattribute.resourceid=%s"
    self.execute(sql, (userclaimid, resourceid))

    result = self.cursor.fetchall()

    requests = {}
    for row in result:
      if not row['attributename'] in requests:
        requests[row['attributename']] = []
      requests[row['attributename']].append(row['value'])

    resourceinfo['requested'] = requests 
    return resourceinfo

  def getTestrunResources(self, testrunid, versionedactionid):
    """
    Get the resource information for the resource with attribute(s) in the specified group
    """
    groups = set()
    groups.add("Execution Host")

    sql = "SELECT DISTINCT ovt_resourcetype.resourcetypename "+\
          "FROM ovt_resourcetype INNER JOIN ovt_resource USING (resourcetypeid) "+\
          "     INNER JOIN ovt_testrunactionresource USING (resourceid) "+\
          "     INNER JOIN ovt_testrunaction USING (testrunactionid) "+\
          "WHERE ovt_testrunaction.testrunid=%s "+\
          "AND ovt_testrunaction.versionedactionid=%s"

    self.execute(sql, (testrunid, versionedactionid))
    result = self.cursor.fetchall()
    for group in result:
      groups.add(group['resourcetypename'])

    returnarray = []

    for groupname in groups:
      if groupname == "Execution Host":
        sql = "SELECT ovt_resource.resourceid "+\
              "FROM ovt_testrunresource INNER JOIN ovt_resource USING (resourceid) "+\
              "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
              "     INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
              "WHERE ovt_resourcetype.resourcetypename = %s "+\
              "AND ovt_resourcestatus.status != 'HISTORIC' "+\
              "AND ovt_testrunresource.testrunid = %s "+\
              "AND ovt_resource.resourceid=%s"
        self.execute(sql, (groupname, testrunid, OvtDB.hostid))
        result = self.cursor.fetchall()
      else:
        sql = "SELECT ovt_resource.resourceid "+\
              "FROM ovt_testrunactionresource INNER JOIN ovt_resource USING (resourceid) "+\
              "     INNER JOIN ovt_testrunaction USING (testrunactionid) "+\
              "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
              "     INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
              "WHERE ovt_resourcetype.resourcetypename = %s "+\
              "AND ovt_resourcestatus.status != 'HISTORIC' "+\
              "AND ovt_testrunaction.versionedactionid = %s "+\
              "AND ovt_testrunaction.testrunid = %s"
        self.execute(sql, (groupname, versionedactionid, testrunid))
        result = self.cursor.fetchall()

      if len(result) == 0:
        return []
      else:
        resourceinfo = self.getFormattedResource(result[0]['resourceid'])
        sql = "SELECT DISTINCT * "+\
              "FROM ((SELECT ovt_attribute.attributename, ovt_attributevalue.value "+\
              "       FROM ovt_testrunattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
              "            INNER JOIN ovt_attribute USING (attributeid) "+\
              "       WHERE testrunid=%s "+\
              "       AND ovt_attribute.resourcetypeid=%s) "+\
              "      UNION "+\
              "      (SELECT ovt_attribute.attributename, ovt_attributevalue.value "+\
              "       FROM ovt_versionedactionattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
              "            INNER JOIN ovt_attribute USING (attributeid) "+\
              "       WHERE ovt_versionedactionattributevalue.versionedactionid=%s "+\
              "       AND ovt_attribute.resourcetypeid=%s) "+\
              "      UNION "+\
              "      (SELECT ovt_attribute.attributename, ovt_attributevalue.value "+\
              "       FROM ovt_versionedactionconfigoption INNER JOIN ovt_configsetting USING (configoptionid) "+\
              "            INNER JOIN ovt_configoptionlookupattributevalue USING (configoptionlookupid) "+\
              "            INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
              "            INNER JOIN ovt_attribute USING (attributeid) "+\
              "       WHERE ovt_versionedactionconfigoption.versionedactionid=%s "+\
              "       AND ovt_attribute.resourcetypeid=%s "+\
              "       AND ovt_configsetting.testrunid=%s)) AS t3"
        self.execute(sql, (testrunid, resourceinfo['typeid'],
                           versionedactionid, resourceinfo['typeid'],
                           versionedactionid, resourceinfo['typeid'], testrunid))
        result = self.cursor.fetchall()
  
        requests = {}
        for row in result:
          if not row['attributename'] in requests:
            requests[row['attributename']] = []
          requests[row['attributename']].append(row['value'])
  
        resourceinfo['requested'] = requests 
        returnarray.append(resourceinfo)

    return returnarray

  def cloneResource(self, resourceid, attributes, testrunactionid = None, userclaimid = None):
    """
    Clone the resource but use a new set of attributes
    Each historic (cloned) resource must be unique
    The versionedaction in the testrun must be linked to the (new) resource
    """
    success = False
    while not success:
      try:
        oldautocommit = self.setAutoCommit(False)

        oldresource = self.getResources(None, resourceid=resourceid)
        # Search for existing resources
        attributevalueids = {}
        attributeids = {}
        # Nasty hack to obtain the resource type. This can be simplified
        resourcetypeid = oldresource[0][resourceid]['related'][1][0]
        # determine the style of attribute (lookup or not) and separate in to two dictionaries
        for attribute in attributes:
          attributeid = self.simple.getAttributeByName(resourcetypeid, attribute)
          details = self.simple.getAttributeById(attributeid)
          if details['lookup']:
            for attributevalue in attributes[attribute]:
              attributevalueid = self.simple.getAttributeValueByName(attributeid, attributevalue)
              if attributevalueid == None:
                raise ResourceException("There is no %s value for %s attribute"%(attributevalue, attribute))
              # Only the attributevalueid is required for a search but the attribute id is needed
              # When constructing the new resource
              attributevalueids[attributevalueid] = attributeid
          else:
            if len(attributes[attribute]) != 1:
              raise ResourceException("%s attribute is non lookup and can only have one value"%attribute)
            # Both attributeid and the value are needed for search and when constructing the
            # new resource.
            attributeids[attributeid] = attributes[attribute][0]
    
        # Lock the resource!
        sql = "SELECT resourceid "+\
              "FROM ovt_resource "+\
              "WHERE resourceid=%s "+\
              "FOR UPDATE"
        self.execute(sql, (resourceid))
    
        # Now use the attributevalueids, attributeids to perform an equivalence
        # 1) check that the ovt_resource fields match (INNER JOIN & hostname)
        # 2) check that the historic resource was derived from the current resource
        #    (ovt_resource.baseresourceid=orig_res.resourceid)
        # 3) Find only resources with an exact matching set of attributes compared
        #    to the original resource. No more and no less
        #    (the EXCEPT clauses with UNION)
        # 4) Ensure that the original resource (still) has all the attributes that
        #    the newly derived resource will have. If this is not true then we will
        #    find a derived resource that has fewer attributes than we asked for.
        #    (This check is done in python code as there is some unusual behaviour
        #     in postgres relating to aggregating fields in a CTE)
    
        values = [resourceid]
        sql = "WITH findattrs(attributeid, attributevalueid, value) AS "+\
              "     (SELECT attributeid, attributevalueid, value "+\
              "      FROM ovt_resourceattribute "+\
              "      WHERE ovt_resourceattribute.resourceid=%s "+\
              "      AND (attributevalueid IN ("+(",".join(map(str,attributevalueids.keys())))+") "

        for attributeid in attributeids:
          sql+="          OR (attributeid=%s AND value=%s) "
          values.append(attributeid)
          values.append(attributeids[attributeid])
        values.append(resourceid)
        sql += "             )) "+\
               "  SELECT ovt_resource.resourceid, (SELECT count(*) FROM findattrs) AS attrcount "+\
               "  FROM ovt_resource INNER JOIN ovt_resource AS orig_res USING "+\
               "               (resourcename, concurrency, nouserqueue, resourcetypeid) "+\
               "  WHERE ovt_resource.resourcestatusid=(SELECT resourcestatusid "+\
               "                                       FROM ovt_resourcestatus "+\
               "                                       WHERE status='HISTORIC') "+\
               "  AND orig_res.resourceid=%s "+\
               "  AND ovt_resource.baseresourceid=orig_res.resourceid "+\
               "  AND ((ovt_resource.hostname IS NULL AND orig_res.hostname IS NULL) "+\
               "       OR ovt_resource.hostname=orig_res.hostname) "+\
               "  AND NOT EXISTS "+\
               "      (WITH resattrs(attributeid, attributevalueid, value) AS "+\
               "           (SELECT attributeid, attributevalueid, value "+\
               "            FROM ovt_resourceattribute "+\
               "            WHERE ovt_resourceattribute.resourceid=ovt_resource.resourceid) "+\
               "     (((SELECT * FROM resattrs) EXCEPT (SELECT * FROM findattrs)) "+\
               "      UNION ALL "+\
               "      ((SELECT * FROM findattrs) EXCEPT (SELECT * FROM resattrs))))"


        self.execute(sql, values)
        result = self.cursor.fetchall()
    
        # If a derived resource already exists (exactly 1) then use it
        if len(result) != 0:
          if len(result) != 1:
            raise ResourceException("Unable to find cloned resource due to multiple matching historic resources")
          if result[0]['attrcount'] != len(attributeids) + len(attributevalueids):
            raise ResourceException("Unable to find cloned resource due to changes since initialisation")
          new_resourceid = result[0]['resourceid']
        # Otherwise create a new derived resource
        else:
          # Creating a new resource relies on the caller making a sensible request.
          # Nobody trusts a caller though, so check that all the new attributes exist
          # on the original resource
          values = [len(attributeids) + len(attributevalueids), resourceid]
          sql = "SELECT count(attributeid) = %s AS validated "+\
                "      FROM ovt_resourceattribute "+\
                "      WHERE ovt_resourceattribute.resourceid=%s "+\
                "      AND (attributevalueid IN ("+(",".join(map(str,attributevalueids.keys())))+") "
          for attributeid in attributeids:
            sql+="          OR (attributeid=%s AND value=%s) "
            values.append(attributeid)
            values.append(attributeids[attributeid])
          sql += "             )"
          self.execute(sql, values)

          if not self.cursor.fetchall()[0]['validated']:
            raise ResourceException("Unable to clone resource due to changes since initialisation")

          # Create the resource inheriting all the basic fields
          sql = "INSERT INTO ovt_resource "+\
                "(resourcename, concurrency, hostname, extradata, nouserqueue, baseresourceid, resourcetypeid, resourcestatusid) "+\
                "(SELECT resourcename, concurrency, hostname, extradata, nouserqueue, resourceid, resourcetypeid,"+\
                "        (SELECT resourcestatusid "+\
                "         FROM ovt_resourcestatus "+\
                "         WHERE status='HISTORIC') "+\
                " FROM ovt_resource "+\
                " WHERE resourceid=%s)"
          self.execute(sql, (resourceid))
    
          # This must be kept in the same transaction (which is also true because of the
          # resource lock above)
          sql = "SELECT currval('ovt_resource_resourceid_seq') AS resourceid"
          self.execute(sql, ())

          new_resourceid = self.cursor.fetchall()[0]['resourceid']

          # Attach all the requested attributevalueids
          for attributevalueid in attributevalueids:
            sql = "INSERT INTO ovt_resourceattribute "+\
                  "(resourceid, attributeid, attributevalueid) "+\
                  "VALUES "+\
                  "(%s, %s, %s)"
            self.execute(sql, (new_resourceid, attributevalueids[attributevalueid], attributevalueid))

          # Create all the other attributes
          for attributeid in attributeids:
            sql = "INSERT INTO ovt_resourceattribute "+\
                  "(resourceid, attributeid, value) "+\
                  "VALUES "+\
                  "(%s, %s, %s)"
            self.execute(sql, (new_resourceid, attributeid, attributeids[attributeid]))

        if testrunactionid != None:
          # Place dead unheld requests on the cloned resource
          sql = "INSERT INTO ovt_testrunactionresource "+\
                "(testrunactionid, resourceid, held, dead) "+\
                "VALUES "+\
                "(%s, %s, 'f', 't')"
          self.execute(sql, (testrunactionid, new_resourceid))

        if userclaimid != None:
          # Place dead unheld requests on the cloned resource
          sql = "INSERT INTO ovt_userclaimresource "+\
                "(userclaimid, resourceid, held, dead) "+\
                "VALUES "+\
                "(%s, %s, 'f', 't')"
          self.execute(sql, (userclaimid, new_resourceid))

        # Atomic commit the clone process (~100-200ms locked per resource, should not affect
        # runtime as the resource is already allocated to this testrun)
        self.FORCECOMMIT()
        success = True
        self.setAutoCommit(oldautocommit)
      except DatabaseRetryException, e:
        pass

    # return the new resource
    return new_resourceid


  def getResourceStatus(self, resourceid):
    """
    Get the status of a resource as a string
    """
    sql = "SELECT ovt_resourcestatus.status "+\
          "FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
          "WHERE ovt_resource.resourceid=%s"
    self.execute(sql, (resourceid))
    result = self.cursor.fetchall()

    if len(result) == 0:
      return None
    
    return result[0]['status']

  def setResourceStatus(self, resourceid, status):
    """
    Set the status of a resource
    """
    sql = "UPDATE ovt_resource "+\
          "SET resourcestatusid=(SELECT resourcestatusid "+\
          "                      FROM ovt_resourcestatus "+\
          "                      WHERE status=%s) "+\
          "WHERE resourceid=%s"

    self.execute(sql, (status, resourceid))
    return

  def getResources(self, conf, resourceid = None):
    if resourceid == None:
      values = []
      sql = "SELECT ovt_resource.* "+\
            "FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
            "WHERE ovt_resourcestatus.status != 'HISTORIC' "

      if 'resourcetypeid' in conf:
         sql += "AND resourcetypeid=%s "
         values.append(conf['resourcetypeid'])
      
      sql += "ORDER BY resourcename "

      self.execute(sql, values) 
    else:
      values = [resourceid]
      sql = "SELECT * "+\
            "FROM ovt_resource "+\
            "WHERE resourceid = %s"

      self.execute(sql, values)
    result = self.cursor.fetchall()
    ret = ({}, [])
    for row in result:
      resourceid = row['resourceid']
      ret[1].append(resourceid)
      ret[0][resourceid] = {"name":row['resourcename'], "hostname":row['hostname'], "related":({},[]), "type":"Resource", "id":resourceid}
      ret[0][resourceid]['data'] = row['resourcename'] +" ["+str(row['concurrency'])+"] - " + str(row['hostname'])
      sql = "SELECT ovt_attributevalue.value AS attributevalue, "+\
            "       ovt_attribute.attributename, "+\
            "       ovt_resourceattribute.value, "+\
            "       ovt_attribute.attributeid, "+\
            "       ovt_attribute.resourcetypeid, "+\
            "       ovt_resourceattribute.resourceattributeid "+\
            "FROM ovt_attribute INNER JOIN ovt_resourceattribute USING (attributeid) "+\
            "     LEFT OUTER JOIN ovt_attributevalue USING (attributevalueid) "+\
            "WHERE resourceid = %s "+\
            "ORDER BY ovt_attribute.attributename, ovt_attributevalue.value"
      self.execute(sql, (resourceid))
      attributes = self.cursor.fetchall()
      for attribute in attributes:
        if not attribute['resourcetypeid'] in ret[0][resourceid]['related'][0]:
          resourcetypename = self.getResourceType2(attribute['resourcetypeid'])['resourcetypename']
          ret[0][resourceid]['related'][1].append(attribute['resourcetypeid'])
          ret[0][resourceid]['related'][0][attribute['resourcetypeid']] = {"data":resourcetypename,"related":({},[]), "type":"Resource Type", "id":attribute['resourcetypeid']}
          attlist = ret[0][resourceid]['related'][0][attribute['resourcetypeid']]['related']
        if not attribute['attributeid'] in attlist[0]:
          attlist[1].append(attribute['attributeid'])
          attlist[0][attribute['attributeid']] = {"data":attribute['attributename'], "related":({},[]), "type":"Attribute", "id":attribute['attributeid']}
        value = attribute['attributevalue']
        if value== None:
          value = attribute['value']
        attlist[0][attribute['attributeid']]['related'][1].append(attribute['resourceattributeid'])
        attlist[0][attribute['attributeid']]['related'][0][attribute['resourceattributeid']] = {"data":value, "type":"Resource Attribute", "id":attribute['resourceattributeid']}
    return ret

  def getAttributeValues(self):
    sql = "SELECT DISTINCT ovt_resourcetype.* "+\
          "FROM ovt_resourcetype INNER JOIN ovt_attribute USING (resourcetypeid) "+\
          "     INNER JOIN ovt_attributevalue USING (attributeid) "+\
          "ORDER BY ovt_resourcetype.resourcetypename"
    self.execute(sql, ())
    groups = self.cursor.fetchall()
    ret = ({},[])
    for group in groups:
      ret[1].append(group['resourcetypeid'])
      ret[0][group['resourcetypeid']] = {"data":group['resourcetypename'], "related":({},[]), "type":"Resource Type", "id":group['resourcetypeid']}
      sql = "SELECT DISTINCT ovt_attribute.* "+\
            "FROM ovt_attribute INNER JOIN ovt_attributevalue USING (attributeid) "+\
            "WHERE ovt_attribute.resourcetypeid=%s "+\
            "ORDER BY ovt_attribute.attributename "
      self.execute(sql, (group['resourcetypeid']))
      attributes = self.cursor.fetchall()
      atts = ret[0][group['resourcetypeid']]['related']
      for attribute in attributes:
        atts[1].append(attribute['attributeid'])
        atts[0][attribute['attributeid']] = {"data":attribute['attributename'], "related":({},[]), "type":"Attribute", "id":attribute['attributeid']}
        sql = "SELECT ovt_attributevalue.* "+\
              "FROM ovt_attributevalue "+\
              "WHERE attributeid=%s "+\
              "ORDER BY ovt_attributevalue.value"
        self.execute(sql, (attribute['attributeid']))
        values = self.cursor.fetchall()
        vals = atts[0][attribute['attributeid']]['related']
        for value in values:
          vals[1].append(value['attributevalueid'])
          vals[0][value['attributevalueid']] = {"data":value['value'], "type":"Attribute Value", "id":value['attributevalueid']}
    return ret

  def getResourceType2(self, resourcetypeid):
    sql = "SELECT * "+\
          "FROM ovt_resourcetype "+\
          "WHERE resourcetypeid=%s"
    self.execute(sql, (resourcetypeid))
    result = self.cursor.fetchall()
    if len(result) == 1:
      return result[0]
    else:
      return None

  def addConfigOptionLookups(self, configoptionid, values):
    """
    Add some extra lookup options to a config option
    """
    # Check that the configoption is a lookup option
    # Find out the maximum ordering number of current options
    sql = "SELECT islookup, configoptiontypename "+\
          "FROM ovt_configoption INNER JOIN ovt_configoptiontype USING (configoptiontypeid) "+\
          "WHERE configoptionid=%s"
    self.execute(sql, (configoptionid))
    result = self.cursor.fetchall()
    if not result[0]['islookup']:
      return False

    values['type'] = result[0]['configoptiontypename']
    return self._addConfigOptionLookupHelper(configoptionid, values, False)

  def _addConfigOptionLookupHelper(self, configoptionid, values, allowdefault = True):
    """
    A helper to insert lookup values to a configoption
    """
    defaultseen = False
    newids = []
    for (name, value, resourceRequirements, default) in values['lookups']:
      if defaultseen or not allowdefault:
        default = False
      if default:
        defaultseen = True
      vals = [configoptionid, name]
      if values['type'] == "boolean":
        if value:
          value = "true"
        else:
          value = "false"
      vals.append(value)
      vals.append(default)
      sql = "INSERT INTO ovt_configoptionlookup "+\
            "(configoptionid, lookupname, lookupvalue, defaultlookup) "+\
            "VALUES "+\
            "(%s, %s, %s, %s)"
      self.execute(sql, vals)

      sql = "SELECT currval('ovt_configoptionlookup_configoptionlookupid_seq') AS configoptionlookupid"
      self.execute(sql, ())
      new = self.cursor.fetchall()
      configoptionlookupid = new[0]['configoptionlookupid']
      newids.append(configoptionlookupid)
        
      if len(resourceRequirements) != 0:
        for attributevalueid in resourceRequirements:
          sql = "INSERT INTO ovt_configoptionlookupattributevalue "+\
                "(configoptionlookupid, attributevalueid) "+\
                "VALUES "+\
                "(%s, %s)"
          self.execute(sql, (configoptionlookupid, attributevalueid))
    return newids

  def addConfigOption(self, values):
    sql = "SELECT configoptionid "+\
          "FROM ovt_configoption "+\
          "WHERE configoptionname=%s "+\
          "AND configoptiongroupid=%s"
    self.execute(sql, (values['name'], values['configoptiongroupid']))
    existing = self.cursor.fetchall()
    if len(existing) == 0:
      defaultfield = ""
      defaultvalue = ""
      vals = [values['name'], values['configoptiongroupid'], values['ordering'], values['configoptiontypeid'], values['affectsequivalence'], values['islookup']]
      if not values['islookup']:
        defaultfield = ", defaultvalue"
        defaultvalue = ", %s"
        val = values['defaultvalue']
        if values['type'] == "boolean":
          if val:
            val = "true"
          else:
            val = "false"
        vals.append(str(val))
      sql = "INSERT INTO ovt_configoption "+\
            "(configoptionname, configoptiongroupid, ordering, configoptiontypeid, affects_equivalence, islookup "+defaultfield+") "+\
            "VALUES "+\
            "(%s, %s, %s, %s, %s, %s"+defaultvalue+")"
      try:
        self.execute(sql, (vals))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in configoption")
        return None
      sql = "SELECT currval('ovt_configoption_configoptionid_seq') AS configoptionid"
      self.execute(sql, ())
      new = self.cursor.fetchall()
      configoptionid = new[0]['configoptionid']
      if values['islookup']:
        self._addConfigOptionLookupHelper (configoptionid, values)
      return configoptionid
    return None

  def addConfigOptionGroup(self, values):
    sql = "SELECT configoptiongroupid, ordering "+\
          "FROM ovt_configoptiongroup "+\
          "WHERE configoptiongroupname=%s"
    self.execute(sql, (values['name']))
    existing = self.cursor.fetchall()
    if len(existing) == 0:
      sql2 = "INSERT INTO ovt_configoptiongroup "+\
             "(configoptiongroupname, ordering, automatic) "+\
             "VALUES "+\
             "(%s, %s, %s)"
      try:
        self.execute(sql2, (values['name'], values['ordering'], values['automatic']))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in configoptiongroup")
      self.execute(sql, (values['name']))
      existing = self.cursor.fetchall()
    
    if values['ordering'] == existing[0]['ordering']:
      configoptiongroupid = existing[0]['configoptiongroupid']
    else:
      configoptiongroupid = None
    return configoptiongroupid

  def addDependencyGroup(self, values):
    sql = "SELECT dependencygroupid "+\
          "FROM ovt_dependencygroup "+\
          "WHERE dependencygroupname=%s"
    self.execute(sql, (values['name']))
    existing = self.cursor.fetchall()
    if len(existing) == 0:
      sql2 = "INSERT INTO ovt_dependencygroup "+\
            "(dependencygroupname) "+\
            "VALUES "+\
            "(%s)"
      try:
        self.execute(sql2, (values['name']))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in dependencygroup")
      self.execute(sql, (values['name']))
      existing = self.cursor.fetchall()
    return existing[0]['dependencygroupid']

  def addAction(self, values):
    sql = "SELECT actionid "+\
          "FROM ovt_action "+\
          "WHERE actionname=%s "+\
          "AND actioncategoryid=%s"

    self.execute(sql, (values['name'], values['actioncategoryid']))
    existing = self.cursor.fetchall()
    if len(existing) == 0:
      field_extra = ""
      value_extra = ""
      sqlvalues=[values['name'], values['actioncategoryid']]

      if values['istestsuite']:
        sql = "INSERT INTO ovt_testsuite "+\
              "(testsuitename) "+\
              "VALUES "+\
              "(%s)"
        try:
          self.execute(sql, (values['name']))
        except postgresql.exceptions.UniqueError:
          self.FORCEROLLBACK()
          if not self.autocommit.autoCommit():
            raise DatabaseRetryException("Unique violation in testsuite")

        field_extra = ", testsuiteid"
        value_extra = ", (SELECT testsuiteid FROM ovt_testsuite WHERE testsuitename=%s)"
        sqlvalues.append(values['name'])

      sql = "INSERT INTO ovt_action "+\
            "(actionname, actioncategoryid"+field_extra+") "+\
            "VALUES "+\
            "(%s, %s"+value_extra+")"
      try:
        self.execute(sql, (sqlvalues))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in action")
        return None
      sql = "SELECT currval('ovt_action_actionid_seq') AS actionid"
      self.execute(sql, ())
      existing = self.cursor.fetchall()
      return existing[0]['actionid']
    return None

  def getTestsuite(self, actionid):
    """
    Find the testsuiteid for actionid or return None
    """
    sql = "SELECT testsuiteid "+\
          "FROM ovt_action "+\
          "WHERE actionid=%s"
    self.execute(sql, (actionid))
    testsuites = self.cursor.fetchall()
    if len(testsuites) == 0:
      return None
    else:
      return testsuites[0]['testsuiteid']

  def getActionForTestsuite(self, testsuiteid):
    """
    Find the actionid for testsuiteid or return None
    """
    sql = "SELECT actionid "+\
          "FROM ovt_action "+\
          "WHERE testsuiteid=%s"
    self.execute(sql, (testsuiteid))
    testsuites = self.cursor.fetchall()
    if len(testsuites) == 0:
      return None
    else:
      return testsuites[0]['actionid']

  def getTestsuiteidForTestsuite(self, testsuitename):
    """
    returns the testsuiteid for the given name
    """
    sql = "SELECT ovt_testsuite.testsuiteid "+\
          "FROM ovt_testsuite "+\
          "WHERE testsuitename=%s "
    self.execute(sql, (testsuitename))
    result = self.cursor.fetchall()
    if len(result) == 0:
      return None
    else:
      return result[0]['testsuiteid']

  def getTestsuitesInTestrun(self, testrunid):
    """
    Fetch a dictionary of all testsuiteids along with their controlling actionids
    """
    sql = "SELECT ovt_action.actionid, ovt_action.testsuiteid "+\
          "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid) "+\
          "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "WHERE ovt_action.testsuiteid IS NOT NULL "+\
          "AND testrunid=%s"
    self.execute(sql, (testrunid))
    testsuites = self.cursor.fetchall()
    ret = {}
    for testsuite in testsuites:
      ret[testsuite['testsuiteid']] = testsuite['actionid']

    return ret

  def isTestsuiteRunning (self, testrunid, testsuiteid, external=False):
    """
    Check if the specified testsuite exists, is part of the testrun
    and is currently running
    """
    sql = "SELECT ovt_testrunaction.testrunactionid "+\
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "WHERE ovt_action.testsuiteid=%s "+\
          "AND ovt_testrunaction.testrunid=%s "
    if not external:
      sql +="AND ovt_testrunaction.passed IS NULL "+\
            "AND ovt_testrunaction.starteddate<now() "+\
            "AND ovt_testrunaction.completeddate IS NULL"

    self.execute(sql, (testsuiteid, testrunid))
    success = self.cursor.fetchall()
    return (len(success) == 1)

  def addVersionedAction(self, values):
    sql = "SELECT versionedactionid "+\
          "FROM ovt_versionedaction "+\
          "WHERE versionname=%s "+\
          "AND actionid=%s "
    vals = [values['name'], values['actionid']]
    inssql = ""
    self.execute(sql, vals)
    versionedaction = self.cursor.fetchall()
    if len(versionedaction) == 0:
      lifecyclesql = ""
      vals2 = vals[:]
      if 'lifecyclestateid' in values and values['lifecyclestateid'] != None:
        vals2.append(values['lifecyclestateid'])
        lifecyclesql = ", lifecyclestateid"
        inssql += ", %s"
      sql2 = "INSERT INTO ovt_versionedaction "+\
            "(versionname, actionid"+lifecyclesql+") "+\
            "VALUES "+\
            "(%s, %s"+inssql+")"
      try:
        self.execute(sql2, vals2)
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in versionedaction")
      self.execute(sql, vals)
      versionedaction =  self.cursor.fetchall()
    return versionedaction[0]['versionedactionid']

  def addResource(self, values):
    sql = "SELECT resourceid "+\
          "FROM ovt_resource "+\
          "WHERE resourcename=%s "+\
          "AND resourcetypeid=%s"

    self.execute(sql, (values['name'], values['resourcetypeid']))
    resource = self.cursor.fetchall()
    if len(resource) == 0:
      sql = "INSERT INTO ovt_resource "+\
            "(resourcename, resourcetypeid) "+\
            "VALUES "+\
            "(%s, %s)"
      try:
        self.execute(sql, (values['name'], values['resourcetypeid']))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in resource")

  def getResourceByName(self, resourcename):
    """
    Fetches a resourceid by resourcename
    """
    sql = "SELECT resourceid "+\
          "FROM ovt_resource "+\
          "WHERE resourcename=%s"
    self.execute(sql, (resourcename))
    resource = self.cursor.fetchall()
    if len(resource) == 0:
      return None
    else:
      return resource[0]['resourceid']


  def getResourceLinks(self, resourceid):
    """
    Fetch all the resources linked to resourceid (but not resourceid itself)
    """

    sql = "SELECT DISTINCT ovt_resource.resourceid, ovt_resource.resourcename, ovt_resource.resourcetypeid "+\
          "FROM ovt_resource "+\
          "WHERE resourceid != %s "+\
          "AND linkedresourcegroupid=(SELECT ovt_resource.linkedresourcegroupid "+\
          "                           FROM ovt_resource "+\
          "                           WHERE resourceid=%s)"
    self.execute(sql, (resourceid, resourceid))
    resourcelinks = self.cursor.fetchall()
    return resourcelinks

  def addResourceLink(self, resourceid, linkresourceid):
    if resourceid == linkresourceid:
      return

    sql = "SELECT ovt_resource.resourceid, ovt_resource.linkedresourcegroupid "+\
          "FROM ovt_resource "+\
          "WHERE resourceid=%s "+\
          "OR resourceid=%s"

    self.execute(sql, (resourceid, linkresourceid))
    resourcegroups = self.cursor.fetchall()

    group1 = None
    group2 = None
    selectedgroup = None
    for group in resourcegroups:
      if group['resourceid'] == resourceid:
        group1 = group['linkedresourcegroupid']
      if group['resourceid'] == linkresourceid:
        group2 = group['linkedresourcegroupid']

    if group1 != None:
      selectedgroup = group1
    if group2 != None:
      selectedgroup = group2

    if selectedgroup == None:
      sql = "SELECT nextval('ovt_resource_linkedresourcegroupid_seq') AS nextid"
      self.execute(sql, ())
      id = self.cursor.fetchall()
      selectedgroup = id[0]['nextid']
    
    sql = "UPDATE ovt_resource "+\
          "SET linkedresourcegroupid=%s "+\
          "WHERE resourceid=%s "+\
          "OR resourceid=%s "+\
          "OR linkedresourcegroupid=%s "+\
          "OR linkedresourcegroupid=%s"
    self.execute(sql, (selectedgroup, resourceid, linkresourceid, group1, group2))

    return

  def removeResourceLink(self, resourceid, linkresourceid):
    sql = "UPDATE ovt_resource "+\
          "SET linkedresourcegroupid=NULL "+\
          "WHERE resourceid=%s"
    self.execute(sql, (linkresourceid))

  def clearResourceAttribute(self, resourceid, resourceattributeid):
    sql = "DELETE FROM ovt_resourceattribute "+\
          "WHERE resourceid=%s "+\
          "AND resourceattributeid=%s"
    self.execute(sql, (resourceid, resourceattributeid))

  def specifyAttribute(self, resourceid, attributeid, value):
    sql = "SELECT lookup "+\
          "FROM ovt_attribute "+\
          "WHERE attributeid=%s"

    self.execute(sql, (attributeid))
    lookup = self.cursor.fetchall()
    if len(lookup) != 0:
      lookup = lookup[0]['lookup']
      if lookup:
        sql = "SELECT resourceattributeid "+\
              "FROM ovt_resourceattribute "+\
              "WHERE resourceid=%s "+\
              "AND attributeid=%s "+\
              "AND attributevalueid=%s"
        self.execute(sql, (resourceid, attributeid, value))
        existing = self.cursor.fetchall()
        if len(existing) == 0:
          sql = "INSERT INTO ovt_resourceattribute "+\
                "(resourceid, attributeid, attributevalueid) "+\
                "VALUES "+\
                "(%s, %s, %s)"
          try:
            self.execute(sql, (resourceid, attributeid, value))
          except postgresql.exceptions.UniqueError:
            self.FORCEROLLBACK()
            if not self.autocommit.autoCommit():
              raise DatabaseRetryException("Unique violation in resourceattribute")
      else:
        sql = "SELECT resourceattributeid "+\
              "FROM ovt_resourceattribute "+\
              "WHERE resourceid=%s "+\
              "AND attributeid=%s"
        self.execute(sql, (resourceid, attributeid))
        existing = self.cursor.fetchall()
        if len(existing) == 0:
          sql = "INSERT INTO ovt_resourceattribute "+\
                "(resourceid, attributeid, value) "+\
                "VALUES "+\
                "(%s, %s, %s)"
          try:
            self.execute(sql, (resourceid, attributeid, value))
          except postgresql.exceptions.UniqueError:
            self.FORCEROLLBACK()
            if not self.autocommit.autoCommit():
              raise DatabaseRetryException("Unique violation in resourceattribute")
        else:
          sql = "UPDATE ovt_resourceattribute "+\
                "SET value=%s "+\
                "WHERE resourceid=%s "+\
                "AND attributeid=%s"
          self.execute(sql, (value, resourceid, attributeid))

  def getResourceTypes(self, conf):
    values = []
    sql = "SELECT * "+\
          "FROM ovt_resourcetype "
    if 'resourcetypeid' in conf:
      sql += "WHERE resourcetypeid=%s "
      values.append(conf['resourcetypeid'])
    sql +=   "ORDER BY resourcetypename" 
    self.execute(sql, values)
    groups = self.cursor.fetchall()
    ret = ({},[])
    for group in groups:
      ret[1].append(group['resourcetypeid'])
      ret[0][group['resourcetypeid']] = {"data":group['resourcetypename'], "id":group['resourcetypeid'],"type":"Resource Type","related":({},[])}
      sql = "SELECT ovt_attribute.* "+\
            "FROM ovt_attribute "+\
            "WHERE resourcetypeid=%s"
      self.execute(sql, (group['resourcetypeid']))
      attributes = self.cursor.fetchall()
      atts = ret[0][group['resourcetypeid']]['related']
      for attribute in attributes:
        atttype = " [value]"
        if attribute['lookup']:
          atttype = " [lookup]"
        atts[1].append(attribute['attributeid'])
        atts[0][attribute['attributeid']] = {"data":attribute['attributename']+atttype, "id":attribute['attributeid'],"type":"Attribute"}
    return ret

  def addResourceType(self, values):
    sql = "SELECT resourcetypeid "+\
          "FROM ovt_resourcetype "+\
          "WHERE resourcetypename=%s"

    self.execute(sql, (values['name']))
    resourcetype = self.cursor.fetchall()
    if len(resourcetype) == 0:
      sql = "INSERT INTO ovt_resourcetype "+\
            "(resourcetypename) "+\
            "VALUES "+\
            "(%s)"
      try:
        self.execute(sql, (values['name']))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in resourcetype")

  def __getAttributesHelper(self, attributeid):
    ret = ({},[])
    sql = "SELECT * "+\
        "FROM ovt_attributevalue "+\
        "WHERE attributeid=%s "+\
        "ORDER BY value"
    self.execute(sql, (attributeid))
    related = ret
    values = self.cursor.fetchall()
    for value in values:
      related[1].append(value['attributevalueid'])
      related[0][value['attributevalueid']] = {"data":value['value'], "id":value['attributevalueid'], "type":"Attribute Value"}
    return ret

  def getAttributes(self, conf):
    resourcetypeid = conf['resourcetypeid']
    sql = "SELECT * "+\
          "FROM ovt_attribute "+\
          "WHERE resourcetypeid=%s "+\
          "ORDER BY attributename"

    self.execute(sql, (resourcetypeid))
    ret = ({},[])
    attributes = self.cursor.fetchall()
    for attribute in attributes:
      ret[1].append(attribute['attributeid'])
      ret[0][attribute['attributeid']] = {"data":attribute['attributename'], "id":attribute['attributeid'], "type":"Attribute"}
      if attribute['lookup']:
        ret[0][attribute['attributeid']]['related'] = self.__getAttributesHelper(attribute['attributeid'])
    return ret

  def getAttributesByName(self, resourcetypeid, name):
    sql = "SELECT * "+\
          "FROM ovt_attribute "+\
          "WHERE resourcetypeid=%s "+\
          "AND attributename=%s "+\
          "ORDER BY attributename"

    self.execute(sql, (resourcetypeid, name))
    attribute = self.cursor.fetchall()
    if len(attribute) == 1 and attribute[0]['lookup']:
      return self.__getAttributesHelper(attribute[0]['attributeid'])
    else:
      return False

  def addAttribute(self, values):
    sql = "SELECT attributeid "+\
          "FROM ovt_attribute "+\
          "WHERE resourcetypeid=%s" +\
          "AND attributename=%s "

    self.execute(sql, (values['resourcetypeid'], values['name']))
    attribute = self.cursor.fetchall()
    if len(attribute) == 0:
      sql2 = "INSERT INTO ovt_attribute "+\
             "(resourcetypeid, attributename, lookup) "+\
             "VALUES "+\
             "(%s, %s, %s)"
      try:
        self.execute(sql2, (values['resourcetypeid'], values['name'], values['islookup']))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in attribute")
      self.execute(sql, (values['resourcetypeid'], values['name']))
      attribute = self.cursor.fetchall()

    return attribute[0]['attributeid']

  def addAttributeValue(self, attributeid, valuename, mustrequest):
    sql = "SELECT attributevalueid "+\
          "FROM ovt_attributevalue "+\
          "WHERE attributeid=%s" +\
          "AND value=%s "

    self.execute(sql, (attributeid, valuename))
    value = self.cursor.fetchall()
    if len(value) == 0:
      sql2 = "INSERT INTO ovt_attributevalue "+\
             "(attributeid, value, mustrequest) "+\
             "VALUES "+\
             "(%s, %s, %s)"
      try:
        self.execute(sql2, (attributeid, valuename, mustrequest))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in attributevalue")
      self.execute(sql, (attributeid, valuename))
      value = self.cursor.fetchall()

    return value[0]['attributevalueid']

  def addResultField(self, fieldname, pytype):
    """
    :param fieldname: The name of the new field
    :type fieldname: string
    :param pytype: Python type of new field
    :type pytype: type object
    """

    typename = ""
    if pytype in (types.IntType, types.LongType):
      typename="integer"
    elif pytype == types.FloatType:
      typename="float"
    elif pytype in types.StringTypes:
      typename="string"
    elif pytype == types.BooleanType:
      typename="boolean"
    else:
      errorstring = ("Typename: %s not known when adding "+\
                     "result field: %s") % \
                    (pytype, fieldname)
      self.log.write("Error: %s"%errorstring)
      raise ResultSubmissionException (errorstring)

    sql = "SELECT ovt_resultfield.resultfieldid, ovt_resulttype.resulttypename "+\
          "FROM ovt_resultfield INNER JOIN ovt_resulttype USING (resulttypeid) "+\
          "WHERE ovt_resultfield.resultfieldname=%s "+\
          "AND ovt_resulttype.resulttypename=%s"
    self.execute(sql, (fieldname, typename))

    existing = self.cursor.fetchall()

    if len(existing) == 0:
      sql2 = "INSERT INTO ovt_resultfield "+\
             "(resultfieldname, resulttypeid) "+\
             "VALUES "+\
             "(%s, (SELECT resulttypeid FROM ovt_resulttype WHERE resulttypename=%s))"
      try:
        self.execute(sql2, (fieldname, typename))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in resultfield")
      self.execute(sql, (fieldname, typename))
      existing = self.cursor.fetchall()

    return (existing[0]['resultfieldid'], typename)

  def setExtendedResult(self, testrunactionid, fieldname, value):
    """
    Store a result related to a testrunaction
    """
    resultfieldid, typename = self.addResultField (fieldname, type(value))

    sql = "SELECT result"+typename+"id AS id "+\
          "FROM ovt_result"+typename+" "+\
          "WHERE resultfieldid=%s "+\
          "AND testrunactionid=%s"
    self.execute(sql, (resultfieldid, testrunactionid))
    existing =  self.cursor.fetchall()
    updateit = True

    if len(existing) == 0:
      updateit = False
      sql = "INSERT INTO ovt_result"+typename+" "+\
            "(result"+typename+", resultfieldid, testrunactionid) "+\
            "VALUES "+\
            "(%s, %s, %s)"
      try:
        self.execute(sql, (value, resultfieldid, testrunactionid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in result<type>")
        updateit = True

    if updateit:
      sql = "UPDATE ovt_result"+typename+" "+\
            "SET result"+typename+"=%s "+\
            "WHERE result"+typename+"id=%s"
      self.execute(sql, (value, existing[0]['id']))

    return True

  def setTestExtendedResult(self, testruntestid, fieldname, value):
    """
    Store a result related to a testrunaction
    When share is non null it represents an actioncategory that result fields are shared in
    """

    resultfieldid, typename = self.addResultField (fieldname, type(value))

    sql = "SELECT testresult"+typename+"id AS id "+\
          "FROM ovt_testresult"+typename+" "+\
          "WHERE resultfieldid=%s "+\
          "AND testruntestid=%s"
    self.execute(sql, (resultfieldid, testruntestid))
    existing =  self.cursor.fetchall()
    updateit = True

    if len(existing) == 0:
      updateit = False
      sql = "INSERT INTO ovt_testresult"+typename+" "+\
            "(testresult"+typename+", resultfieldid, testruntestid) "+\
            "VALUES "+\
            "(%s, %s, %s)"
      try:
        self.execute(sql, (value, resultfieldid, testruntestid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in testresult<type>")
        updateit = True

    if updateit:
      sql = "UPDATE ovt_testresult"+typename+" "+\
            "SET testresult"+typename+"=%s "+\
            "WHERE testresult"+typename+"id=%s"
      self.execute(sql, (value, existing[0]['id']))

    return True

  def getActionResult (self, testrunid, actionname, options=None):
    """
    Get a dictionary describing an action result
    options    -- A dictionary of options to enable inference techniques
    """
    if options == None:
      options = {}

    sql = "SELECT ovt_testrunaction.testrunactionid, ovt_testrunaction.providedbytestrunid, "+\
          "       ovt_action.actionname, ovt_versionedaction.versionname, ovt_testrunaction.passed "+\
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "     INNER JOIN ovt_actioncategory USING (actioncategoryid) "+\
          "WHERE ovt_testrunaction.testrunid=%s "+\
          "AND ovt_action.actionname=%s"

    self.execute(sql, (testrunid, actionname))
    result = self.cursor.fetchall()

    if len(result) == 0 or result[0]['passed'] is None:
      return None

    return self.__getActionResultDetail(result[0], options)

  def __getActionResultDetail(self, data, options):
    """
    Create a dictionary describing the full result
    """
    info = {}

    testrunactionid = data['testrunactionid']
    info['testrunactionid'] = testrunactionid
    info['version'] = data['versionname']
    info['pass'] = data['passed']
    info['extended'] = {}

    if 'hide_extended' in options and options['hide_extended']:
      return info

    sql = "SELECT ovt_resultfloat.resultfloat, ovt_resultfield.resultfieldname "+\
          "FROM ovt_resultfloat INNER JOIN ovt_resultfield USING (resultfieldid) "+\
          "WHERE ovt_resultfloat.testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    results = self.cursor.fetchall()
    for result in results:
      info['extended'][result['resultfieldname']] = result['resultfloat']

    sql = "SELECT ovt_resultinteger.resultinteger, ovt_resultfield.resultfieldname "+\
          "FROM ovt_resultinteger INNER JOIN ovt_resultfield USING (resultfieldid) "+\
          "WHERE ovt_resultinteger.testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    results = self.cursor.fetchall()
    for result in results:
      info['extended'][result['resultfieldname']] = result['resultinteger']

    sql = "SELECT ovt_resultboolean.resultboolean, ovt_resultfield.resultfieldname "+\
          "FROM ovt_resultboolean INNER JOIN ovt_resultfield USING (resultfieldid) "+\
          "WHERE ovt_resultboolean.testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    results = self.cursor.fetchall()
    for result in results:
      info['extended'][result['resultfieldname']] = result['resultboolean']

    sql = "SELECT ovt_resultstring.resultstring, ovt_resultfield.resultfieldname "+\
          "FROM ovt_resultstring INNER JOIN ovt_resultfield USING (resultfieldid) "+\
          "WHERE ovt_resultstring.testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    results = self.cursor.fetchall()
    for result in results:
      info['extended'][result['resultfieldname']] = result['resultstring']

    return info

  def getTestResult (self, testrunid, tests, testsuiteid, options=None):
    """
    Get a dictionary describing a test result
    tests      -- A dictionary of test names mapping to versions
    testuiteid -- The testsuite that the tests must relate to
    options    -- A dictionary of options to enable inference techniques
    """
    if options == None:
      options = {}

    sql = "SELECT ovt_testruntest.testruntestid, ovt_testruntest.providedbytestrunid, "+\
          "       ovt_test.testname, ovt_versionedtest.versionname, ovt_testruntest.passed "+\
          "FROM ovt_testruntest INNER JOIN ovt_versionedtest USING (versionedtestid) "+\
          "     INNER JOIN ovt_test USING (testid) "+\
          "WHERE ovt_testruntest.testrunid=%s "+\
          "AND (false "
    values = [testrunid]
    for test in tests:
      sql += "OR (ovt_test.testname=%s "
      values.append(test)
      if tests[test] != None:
        sql += "AND ovt_versionedtest.versionname=%s "
        values.append(tests[test])
      sql += ")"

    if len(tests) == 0:
      sql += "OR true "
    sql += ") "

    sql += "AND ovt_test.testsuiteid=%s "
    values.append(testsuiteid)

    self.execute(sql, values)
    result = self.cursor.fetchall()

    testdata = {}

    found_tests = []
    for test in result:
      if test['passed'] == None:
        continue

      # Found a test
      found_tests.append(test['testname'])

      testdata[test['testname']] = self.__getTestResultDetail(test, options)
      if test['providedbytestrunid'] != None:
        testdata[test['testname']]['inferredfrom'] = test['providedbytestrunid']

    if 'use_simple_equivalence' in options and options['use_simple_equivalence'] and testsuiteid != None:
      # Search for the tests with versions using a simple equivalence
      values = [testsuiteid, testrunid]
      search = ""
      for testname in tests:
        if testname in found_tests:
          continue
        if tests[testname] != None:
          search += "OR (ovt_test.testname=%s "+\
                    "    AND ovt_versionedtest.versionname=%s) "
          values.extend([testname, tests[testname]])
      # Do all the tests at once. This should be faster than many individual queries
      sql = "SELECT ovt_testruntest.testruntestid, ovt_testruntest.testrunid, "+\
            "       ovt_test.testname, ovt_versionedtest.versionname, ovt_testruntest.passed "+\
            "FROM ovt_testruntest INNER JOIN ovt_versionedtest USING (versionedtestid) "+\
            "     INNER JOIN ovt_test USING (testid) "+\
            "     INNER JOIN ovt_testrunaction AS trafoundsim ON (ovt_testruntest.testrunid=trafoundsim.testrunid) "+\
            "     INNER JOIN ovt_testrunaction AS trasim ON (trafoundsim.simpleequivalenceid=trasim.simpleequivalenceid) "+\
            "     INNER JOIN ovt_versionedaction AS trasimva ON (trasim.versionedactionid=trasimva.versionedactionid) "+\
            "     INNER JOIN ovt_action AS trasima ON (trasimva.actionid=trasima.actionid) "+\
            "WHERE trasima.testsuiteid=%s "+\
            "AND trasim.testrunid=%s "+\
            "AND (false "+search+") "+\
            "AND ovt_test.testsuiteid=%s"
      values.append(testsuiteid)
      self.execute(sql, values)
      result = self.cursor.fetchall()
      for test in result:
        if test['passed'] != None:
          if test['testname'] in testdata:
            if testdata[test['testname']]['pass'] != test['passed']:
              testdata[test['testname']]['pass'] = None
          else:
            testdata[test['testname']] = self.__getTestResultDetail(test, options)
            testdata[test['testname']]['inferredfrom'] = test['testrunid']
            testdata[test['testname']]['inferred'] = True

    return testdata

  def __getTestResultDetail(self, data, options):
    """
    Create a dictionary describing the full result
    """
    info = {}

    testruntestid = data['testruntestid']
    info['testruntestid'] = testruntestid
    info['version'] = data['versionname']
    info['pass'] = data['passed']
    info['extended'] = {}

    if 'hide_extended' in options and options['hide_extended']:
      return info

    sql = "SELECT ovt_testresultfloat.testresultfloat, ovt_resultfield.resultfieldname "+\
          "FROM ovt_testresultfloat INNER JOIN ovt_resultfield USING (resultfieldid) "+\
          "WHERE ovt_testresultfloat.testruntestid=%s"
    self.execute(sql, (testruntestid))
    results = self.cursor.fetchall()
    for result in results:
      info['extended'][result['resultfieldname']] = result['testresultfloat']

    sql = "SELECT ovt_testresultinteger.testresultinteger, ovt_resultfield.resultfieldname "+\
          "FROM ovt_testresultinteger INNER JOIN ovt_resultfield USING (resultfieldid) "+\
          "WHERE ovt_testresultinteger.testruntestid=%s"
    self.execute(sql, (testruntestid))
    results = self.cursor.fetchall()
    for result in results:
      info['extended'][result['resultfieldname']] = result['testresultinteger']

    sql = "SELECT ovt_testresultboolean.testresultboolean, ovt_resultfield.resultfieldname "+\
          "FROM ovt_testresultboolean INNER JOIN ovt_resultfield USING (resultfieldid) "+\
          "WHERE ovt_testresultboolean.testruntestid=%s"
    self.execute(sql, (testruntestid))
    results = self.cursor.fetchall()
    for result in results:
      info['extended'][result['resultfieldname']] = result['testresultboolean']

    sql = "SELECT ovt_testresultstring.testresultstring, ovt_resultfield.resultfieldname "+\
          "FROM ovt_testresultstring INNER JOIN ovt_resultfield USING (resultfieldid) "+\
          "WHERE ovt_testresultstring.testruntestid=%s"
    self.execute(sql, (testruntestid))
    results = self.cursor.fetchall()
    for result in results:
      info['extended'][result['resultfieldname']] = result['testresultstring']

    return info

  def verifyTestsuiteInTestrun(self, testrunid, testsuiteid):
    """
    Check that the action that runs the testsuiteid is in the testrun
    """
    sql = "SELECT ovt_action.actionid "+\
          "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid) "+\
          "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "WHERE ovt_action.testsuiteid=%s "+\
          "AND ovt_testrunaction.testrunid=%s"
    self.execute(sql, (testsuiteid, testrunid))

    return (len(self.cursor.fetchall()) == 1)

  def findOrCreateTestsuiteTest (self, testsuiteid, testnameorid, version):
    """
    Find an existing test in the specified testsuite or create a new one
    This function assumes that testsuiteid is valid
    """
    if type(testnameorid) in (types.IntType, types.LongType):
      criteria = "ovt_test.testid=%s"
    else:
      criteria = "ovt_test.testname=%s"

    selsql = "SELECT ovt_test.testid "+\
             "FROM ovt_test "+\
             "WHERE "+criteria+\
             "AND ovt_test.testsuiteid=%s"

    self.execute(selsql, (testnameorid, testsuiteid))
    tests = self.cursor.fetchall()

    if len(tests) == 0:
      if type(testnameorid) in (types.IntType, types.LongType):
        return False
      sql = "INSERT INTO ovt_test "+\
            "(testname, testsuiteid) "+\
            "VALUES "+\
            "(%s, %s)"
      try:
        self.execute(sql, (testnameorid, testsuiteid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in test")
      self.execute(selsql, (testnameorid, testsuiteid))
      tests = self.cursor.fetchall()

    # Now the test exists, find or create the version
    testid=tests[0]['testid']
    selsql = "SELECT ovt_versionedtest.versionedtestid "+\
             "FROM ovt_versionedtest "+\
             "WHERE testid=%s "+\
             "AND versionname=%s"
    self.execute(selsql, (testid, version))
    versions = self.cursor.fetchall()

    if len(versions) == 0:
      sql = "INSERT INTO ovt_versionedtest "+\
            "(testid, versionname) "+\
            "VALUES "+\
            "(%s, %s)"
      try:
        self.execute(sql, (testid, version))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in versionedtest")
      self.execute(selsql, (testid, version))
      versions = self.cursor.fetchall()

    return versions[0]['versionedtestid']

  def findOrAddTestsuiteTestToTestrun (self, testrunid, versionedtestid):
    """
    Add the specified versionedtest to the testrun if it doesn't already exist
    """
    selsql = "SELECT ovt_testruntest.testruntestid "+\
             "FROM ovt_testruntest "+\
             "WHERE ovt_testruntest.testrunid=%s "+\
             "AND ovt_testruntest.versionedtestid=%s"
    self.execute(selsql, (testrunid, versionedtestid))
    tas = self.cursor.fetchall()
    if len(tas) == 0:
      sql = "INSERT INTO ovt_testruntest "+\
            "(testrunid, versionedtestid, starteddate, completeddate) "+\
            "VALUES "+\
            "(%s, %s, now(), now())"
      try:
        self.execute(sql, (testrunid, versionedtestid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in testruntest")
      self.execute(selsql, (testrunid, versionedtestid))
      tas = self.cursor.fetchall()
    else:
      sql = "UPDATE ovt_testruntest "+\
            "SET starteddate=now(), completeddate=now() "+\
            "WHERE testruntestid=%s"
      self.execute(sql, (tas[0]['testruntestid']))

    return tas[0]['testruntestid']

  def getTestruns(self, userid, active, page = None):
    """
    Returns some basic information about all testruns that have
    not yet completed
    """

    if active == True:
      active = ""
    else:
      active = "NOT"

    sql = "SELECT ovt_testrun.testrunid, ovt_testrun.description, "+\
          "       ovt_runstatus.status, to_char(ovt_testrun.createddate, 'YYYY/MM/DD HH24:MI') AS createddate, "+\
          "       ovt_testrungroup.testrungroupname "+\
          "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid) "+\
          "     INNER JOIN ovt_testrungroup USING (testrungroupid) "+\
          "WHERE ovt_testrun.userid=%s "+\
          "AND ovt_testrun.completeddate IS "+active+" NULL "+\
          "ORDER BY ovt_runstatus.runstatusid, ovt_testrun.createddate DESC "
    if page != None:
      sql += "OFFSET "+str((page-1)*10)+" LIMIT 10"
    self.execute(sql, (userid))
    testruns = self.cursor.fetchall()
    return testruns

  def setResult(self, testrunactionid, result):
    """
    Sets a test to pass or fail
    """
    if type(result) in types.StringTypes:
      result = (result == "PASS")

    sql = "UPDATE ovt_testrunaction "+\
          "SET passed=%s "
    values = [result]
    sql += "WHERE testrunactionid=%s"
    values.append(testrunactionid)
    self.execute(sql, values)
    return True

  def setTestResult(self, testruntestid, result, inferredfrom = None):
    """
    Sets a test to pass or fail
    """
    if type(result) in types.StringTypes:
      result = (result == "PASS")

    sql = "UPDATE ovt_testruntest "+\
          "SET passed=%s "
    values = [result]
    if inferredfrom != None:
      sql += ", providedbytestrunid=%s"
      values.append(inferredfrom)
    sql += "WHERE testruntestid=%s"
    values.append(testruntestid)
    self.execute(sql, values)
    return True

  def getTestrungroupDescription(self, testrungroupid):
    """
    Returns description of particular testrungroup
    """
    sql = "SELECT testrungroupname "+\
          "FROM ovt_testrungroup "+\
          "WHERE testrungroupid=%s"

    self.execute(sql, (testrungroupid))
    result = self.cursor.fetchall()

    if len(result) > 0:
      return result[0]["testrungroupname"]
    else:
      return None

  def getTestrunDetails(self, testrunid, sconv=lambda x:x):
    """
    Return a dictionary of interesting information about a testrun
    """
    sql = "SELECT ovt_testrun.*, ovt_runstatus.status, "+\
          "       ovt_testrungroup.testrungroupname, "+\
          "       to_char(ovt_testrun.createddate, 'YYYY/MM/DD HH24:MI') AS createddate "+\
          "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid) "+\
          "     INNER JOIN ovt_testrungroup USING (testrungroupid) "+\
          "WHERE ovt_testrun.testrunid=%s"
    self.execute(sql, (testrunid))
    info = self.cursor.fetchall()
    if len(info) == 0:
      return {}
    details = {}
    details['createddate'] = sconv(info[0]['createddate'])
    details['status'] = sconv(info[0]['status'])
    details['usegridengine'] = sconv(info[0]['usegridengine'])
    details['description'] = sconv(info[0]['description'])
    details['testrungroupname'] = sconv(info[0]['testrungroupname'])

    sql = "SELECT CASE WHEN passed IS NULL THEN 'NOT RUN' "+\
          "            WHEN passed THEN 'PASS' "+\
          "            WHEN NOT passed THEN 'FAIL' "+\
          "       END as result, "+\
          "       count(ovt_testrunaction.testrunactionid) AS resultcount "+\
          "FROM ovt_testrunaction "+\
          "WHERE ovt_testrunaction.testrunid=%s "+\
          "GROUP BY ovt_testrunaction.passed"
    self.execute(sql, (testrunid))
    info =  self.cursor.fetchall()
    details['resultcounts'] = {}
    for result in info:
      details['resultcounts'][result['result']] = result['resultcount']

    sql = "SELECT ovt_resourcetype.resourcetypename, ovt_resource.resourcename "+\
          "FROM ovt_testrunresource INNER JOIN ovt_resource USING (resourceid) "+\
          "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
          "WHERE ovt_testrunresource.testrunid=%s"
    self.execute(sql, (testrunid))
    info =  self.cursor.fetchall()
    details['resources']=  {}
    for res in info:
      details['resources'][sconv(res['resourcetypename'])] = sconv(res['resourcename'])

    # Extract the definition of the testrun
    sql = "SELECT ovt_actioncategory.actioncategoryname, ovt_action.actionname, "+\
          "       ovt_versionedaction.versionname "+\
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "     INNER JOIN ovt_actioncategory USING (actioncategoryid) "+\
          "WHERE ovt_testrunaction.testrunid=%s "+\
          "ORDER BY ovt_actioncategory.actioncategoryname, ovt_action.actionname"

    self.execute(sql, (testrunid))
    info =  self.cursor.fetchall()
    details['definition'] = {}
    for res in info:
      if not sconv(res['actioncategoryname']) in details['definition']:
        details['definition'][sconv(res['actioncategoryname'])] = {}
      if not sconv(res['actionname']) in details['definition'][sconv(res['actioncategoryname'])]:
        details['definition'][sconv(res['actioncategoryname'])][sconv(res['actionname'])] = sconv(res['versionname'])

    # Extract the configuration of the testrun
    sql = "SELECT ovt_configsetting.configvalue, ovt_configoptionlookup.lookupname, "+\
          "       ovt_configoptiongroup.configoptiongroupname, ovt_configoption.configoptionname "+\
          "FROM ovt_configsetting INNER JOIN ovt_configoption USING (configoptionid) "+\
          "     INNER JOIN ovt_configoptionlookup USING (configoptionlookupid) "+\
          "     INNER JOIn ovt_configoptiongroup USING (configoptiongroupid) "+\
          "WHERE ovt_configsetting.testrunid=%s "+\
          "AND NOT ovt_configoptiongroup.automatic "+\
          "ORDER BY configoptiongroupname, configoptionname"

    self.execute(sql, (testrunid))
    info =  self.cursor.fetchall()
    details['configuration'] = {}
    for res in info:
      if not sconv(res['configoptiongroupname']) in details['configuration']:
        details['configuration'][sconv(res['configoptiongroupname'])] = {}
      if not sconv(res['configoptionname']) in details['configuration'][sconv(res['configoptiongroupname'])]:
        if res['lookupname'] == None:
          details['configuration'][sconv(res['configoptiongroupname'])][sconv(res['configoptionname'])] = sconv(res['configvalue'])
        else:
          details['configuration'][sconv(res['configoptiongroupname'])][sconv(res['configoptionname'])] = sconv(res['lookupname'])

    # Extract the resource requirements
    sql = "SELECT ovt_resourcetype.resourcetypename, ovt_attribute.attributename, "+\
          "       ovt_attributevalue.value "+\
          "FROM ovt_testrunattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
          "     INNER JOIN ovt_attribute USING (attributeid) "+\
          "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
          "WHERE ovt_testrunattributevalue.testrunid=%s "+\
          "ORDER BY resourcetypename, attributename, value"
    self.execute(sql, (testrunid))
    info =  self.cursor.fetchall()
    details['requirements'] = {}
    for res in info:
      if not sconv(res['resourcetypename']) in details['requirements']:
        details['requirements'][sconv(res['resourcetypename'])] = {}
      if not sconv(res['attributename']) in details['requirements'][sconv(res['resourcetypename'])]:
        details['requirements'][sconv(res['resourcetypename'])][sconv(res['attributename'])] = []
      details['requirements'][sconv(res['resourcetypename'])][sconv(res['attributename'])].append(sconv(res['value']))

    return details

  def getHostInfo(self, hostname):
    """
    Get information relating to an overtest host.
    Hosts are normal resources with a specific attribute
    """
    sql = "SELECT DISTINCT ovt_resource.resourceid, hostname, concurrency, extradata "+\
          "FROM ovt_resource INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
          "     INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
          "WHERE ovt_resourcetype.resourcetypename='Execution Host' "+\
          "AND ovt_resourcestatus.status != 'HISTORIC' "+\
          "AND ovt_resource.resourcename=%s"

    self.execute(sql, (hostname))
    host = self.cursor.fetchall()
    ret = None
    if len(host) == 1:
      ret = {}
      if host[0]['extradata'] != None:
        ret['pid'] = int(host[0]['extradata'])
      else:
        ret['pid'] = None

      ret['hostname'] = host[0]['hostname']
      ret['hostid'] = host[0]['resourceid']
      ret['concurrency'] = host[0]['concurrency']
    return ret

  def getTaskIdentifiers(self, testrunactionid):
    """
    Returns a tuple of actionid and versionedactionid for the testrunaction
    """
    sql = "SELECT ovt_versionedaction.actionid, ovt_versionedaction.versionedactionid "+\
          "FROM ovt_versionedaction INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "WHERE ovt_testrunaction.testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    ids = self.cursor.fetchall()
    if len(ids) == 0:
      return (None, None)
    else:
      return (ids[0]['actionid'], ids[0]['versionedactionid'])

  def getVersionInfo(self, versionedactionid):
    """
    Return the version name / other info
    """
    sql = "SELECT versionname "+\
          "FROM ovt_versionedaction "+\
          "WHERE versionedactionid=%s"
    self.execute(sql, (versionedactionid))
    version = self.cursor.fetchall()
    if len(version) == 1:
      return version[0]['versionname']
    else:
      return None

  def getVersionInfoForAction (self, testrunid, actionname):
    """
    Return the version of the specified action in the specified testrun
    """
    sql = "SELECT versionname "+\
          "FROM ovt_versionedaction INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "WHERE ovt_action.actionname=%s "+\
          "AND ovt_testrunaction.testrunid=%s"

    self.execute(sql, (actionname, testrunid))
    version = self.cursor.fetchall()
    if len(version) == 1:
      return version[0]['versionname']
    else:
      return None

  def setTaskStarted(self, testrunactionid):
    """
    Updates a task to mark is as executing
    """
    sql = "UPDATE ovt_testrunaction "+\
          "SET starteddate=now() "+\
          "WHERE testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    return True

  def setTaskCompleted(self, testrunactionid):
    """
    Updates a task to mark is as completed
    """
    sql = "UPDATE ovt_testrunaction "+\
          "SET completeddate=now() "+\
          "WHERE testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    return True

  def getTestrunsToCheck(self, userid=None):
    """
    Finds all testruns that are ready to be allocated
    """
    sql = "SELECT testrunid "+\
          "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid) "+\
          "WHERE ovt_runstatus.status='READYTOCHECK' "

    values = []
    if userid != None:
      sql += "AND ovt_testrun.userid=%s "+\
             "AND ovt_testrun.usegridengine"
      values.append(userid)
    else:
      sql += "AND NOT ovt_testrun.usegridengine"

    self.execute(sql, values)
    testruns = self.cursor.fetchall()
    ret = []
    for testrun in testruns:
      ret.append(testrun['testrunid'])
    return ret

  def getGridTestrunsToArchiveOrDelete(self, userid):
    """
    Finds all testruns that are ready to be deleted (grid engine)
    """
    sql = "SELECT testrunid, status "+\
          "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid) "+\
          "WHERE (ovt_runstatus.status='READYTODELETE' "+\
	  "       OR ovt_runstatus.status='READYTOARCHIVE') "+\
          "AND ovt_testrun.userid=%s "+\
          "AND ovt_testrun.usegridengine"

    self.execute(sql, (userid))
    testruns = self.cursor.fetchall()
    ret = []
    for testrun in testruns:
      ret.append((testrun['testrunid'], testrun['status']))
    return ret

  def getTestrunsToAllocate(self, forcetestrunid = None, userid = None):
    """
    Finds all testruns that are ready to be allocated
    When forcetestrunid is set then the function proceeds as if the specified testrun is ready
    to allocate immediately, regardless of its actual state
    """
    if forcetestrunid == None:
      sql = "SELECT testrunid, "+\
            "       deptestrunid, "+\
	    "       (SELECT successful "+\
	    "        FROM ovt_testrun AS t1 "+\
	    "        WHERE t1.testrunid=ovt_testrun.deptestrunid) AS depsuccessful "+\
            "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid) "+\
            "WHERE (ovt_runstatus.status='CHECKED' "+\
	    "       OR ovt_runstatus.status='CHECKEDGRID') "+\
            "AND startafter<=now() "
      values = []
      if userid != None:
	sql += "AND ovt_testrun.userid=%s "+\
	       "AND ovt_testrun.usegridengine "
	values.append(userid)
      else:
	sql += "AND NOT ovt_testrun.usegridengine "

      sql += "ORDER BY priority, createddate"

      self.execute(sql, values)
      testruns = self.cursor.fetchall()
    else:
      testruns = [{'testrunid':forcetestrunid, 'deptestrunid':None, 'depsuccessful':None}]

    ret = {}

    for testrun in testruns:
      if testrun['deptestrunid'] is not None:
        # There is a producer testrun
        if testrun['depsuccessful'] is not None:
	  # The producer testrun has completed
	  if testrun['depsuccessful'] is False:
            # The producer failed
	    self.setTestrunRunstatus(testrun['testrunid'], "DEPTESTRUNFAILED")
	    continue
	else:
	  # The producer is yet to complete
	  continue

      sql = "SELECT DISTINCT ovt_attributevalue.attributevalueid "+\
            "FROM ovt_attributevalue INNER JOIN ovt_attribute USING (attributeid) "+\
            "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
            "     INNER JOIN ovt_versionedactionattributevalue USING (attributevalueid) "+\
            "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
            "WHERE ovt_testrunaction.testrunid=%s "+\
            "AND ovt_resourcetype.resourcetypename='Execution Host' "
      ret[testrun['testrunid']] = {"attributes":[]}
      self.execute(sql, (testrun['testrunid']))
      attributevalues = self.cursor.fetchall()
      for attributevalue in attributevalues:
        ret[testrun['testrunid']]['attributes'].append(attributevalue['attributevalueid'])

      sql = "SELECT DISTINCT ovt_testrunattributevalue.attributevalueid "+\
            "FROM ovt_testrunattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
            "     INNER JOIN ovt_attribute USING (attributeid) "+\
            "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
            "WHERE testrunid=%s "+\
            "AND ovt_resourcetype.resourcetypename='Execution Host' "
      self.execute(sql, (testrun['testrunid']))
      attributevalues = self.cursor.fetchall()
      for attributevalue in attributevalues:
        if not attributevalue['attributevalueid'] in ret[testrun['testrunid']]['attributes']:
          ret[testrun['testrunid']]['attributes'].append(attributevalue['attributevalueid'])

      sql = "SELECT DISTINCT ovt_configoptionlookupattributevalue.attributevalueid "+\
            "FROM ovt_configsetting INNER JOIN ovt_configoptionlookupattributevalue USING (configoptionlookupid) "+\
            "     INNER JOIN ovt_attributevalue USING (attributevalueid) "+\
            "     INNER JOIN ovt_attribute USING (attributeid) "+\
            "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
            "WHERE testrunid=%s "+\
            "AND ovt_resourcetype.resourcetypename='Execution Host' "
      self.execute(sql, (testrun['testrunid']))
      attributevalues = self.cursor.fetchall()
      for attributevalue in attributevalues:
        if not attributevalue['attributevalueid'] in ret[testrun['testrunid']]['attributes']:
          ret[testrun['testrunid']]['attributes'].append(attributevalue['attributevalueid'])

    return ret

  def getLiveHostData(self):
    """
    Fetches the status of all overtest host resources along with their associated attributes
    """
    sql = "SELECT ovt_resource.* "+\
          "FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
          "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
          "WHERE ovt_resourcetype.resourcetypename='Execution Host' "+\
          "AND ovt_resourcestatus.status != 'HISTORIC'"
    self.execute(sql, ())
    hosts = self.cursor.fetchall()
    ret = {}
    for host in hosts:
      # Fetch all the attributes for this host
      ret[host['resourceid']] = {"data":host, "attributes":[]}
      sql = "SELECT ovt_attributevalue.attributevalueid "+\
            "FROM ovt_attributevalue INNER JOIN ovt_resourceattribute USING (attributevalueid) "+\
            "WHERE ovt_resourceattribute.resourceid=%s"
      self.execute(sql, (host['resourceid']))
      attributes = self.cursor.fetchall()
      for attribute in attributes:
        ret[host['resourceid']]['attributes'].append(attribute['attributevalueid'])
      # Fetch the loading for this host
      sql = "SELECT sum(ovt_testrun.concurrency) AS activecount "+\
            "FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid) "+\
            "     INNER JOIN ovt_testrunresource USING (testrunid) "+\
            "WHERE ovt_testrunresource.resourceid=%s "+\
            "AND (ovt_runstatus.status='RUNNING' "+\
            "     OR ovt_runstatus.status='HOSTALLOCATED')"
      self.execute(sql, (host['resourceid']))
      activecount = self.cursor.fetchall()
      ret[host['resourceid']]['activecount'] = activecount[0]['activecount']
      if ret[host['resourceid']]['activecount'] == None:
        ret[host['resourceid']]['activecount'] = 0
    return ret

  def getHostFileSystems(self):
    """
    Return an array containing all the shared file system attributevalues
    """
    sql = "SELECT ovt_attributevalue.attributevalueid "+\
          "FROM ovt_attributevalue INNER JOIN ovt_attribute USING (attributeid) "+\
          "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
          "WHERE ovt_resourcetype.resourcetypename='Execution Host' "+\
          "AND ovt_attribute.attributename='Shared Filesystem'"
    self.execute(sql, ())
    filesystems = self.cursor.fetchall()
    ret = []
    for filesystem in filesystems:
      ret.append(filesystem['attributevalueid'])
    return ret

  def getRunningTasks(self, hostid):
    """
    Find all currently running tasks on the specified hostid
    This function is intended for use with host recovery.
    """
    tasks = []

    sql = "SELECT ovt_testrunaction.testrunactionid, ovt_versionedaction.actionid, ovt_testrunaction.testrunid, "+\
          "       ovt_testrunaction.archived "+\
          "FROM ovt_testrunaction INNER JOIN ovt_testrunactionresource USING (testrunactionid) "+\
          "     INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "WHERE ovt_testrunactionresource.resourceid=%s "+\
          "AND ((ovt_testrunaction.starteddate IS NOT NULL "+\
          "      AND ovt_testrunaction.completeddate IS NULL) "+\
          "     OR NOT ovt_testrunaction.archived)"
    self.execute (sql, (hostid))
    results = self.cursor.fetchall ()

    for result in results:
      tasks.append ((result['testrunid'], result['testrunactionid'], result['actionid'], result['archived']))

    return tasks

  def resetArchived(self, testrunactionid):
    """
    Clear the archived flag on testrunactionid
    """
    sql = "UPDATE ovt_testrunaction "+\
          "SET archived=NULL "+\
          "WHERE testrunactionid=%s"
    self.execute (sql, (testrunactionid))

  def addToTestrun(self, testrunid, versionedactionid, autodependency = False):
    """
    Adds a new versioned action to a testrun
    """
    status = self.getTestrunRunstatus(testrunid) 
    if status == "CHECKFAILED" or status == "CREATION" or (autodependency and status=="READYTOCHECK"):
      sql = "SELECT testrunactionid "+\
            "FROM ovt_testrunaction "+\
            "WHERE testrunid=%s "+\
            "AND versionedactionid=%s"
      self.execute(sql, (testrunid, versionedactionid))
      existing = self.cursor.fetchall()
      if len(existing) == 0:
        sql = "INSERT INTO ovt_testrunaction "+\
              "(testrunid, versionedactionid) "+\
              "VALUES "+\
              "(%s, %s)"
        try:
          self.execute(sql, (testrunid, versionedactionid))
        except postgresql.exceptions.UniqueError:
          self.FORCEROLLBACK()
          if not self.autocommit.autoCommit():
            raise DatabaseRetryException("Unique violation in testrunaction")
          return False
      return True
    else:
      return False

  def getTestrunRunstatus(self, testrunid, forupdate = False):
    """
    Fetches the current run status of a testrun
    """
    sql = "SELECT ovt_runstatus.status "+\
          "FROM ovt_runstatus INNER JOIN ovt_testrun USING (runstatusid) "+\
          "WHERE ovt_testrun.testrunid=%s"
    if forupdate:
      sql += " FOR UPDATE OF ovt_testrun"
    self.execute(sql, (testrunid))
    status = self.cursor.fetchall()
    if len(status) == 0:
      return None
    else:
      return status[0]['status']

  def setTestrunRunstatus(self, testrunid, status):
    """
    Sets a new status for a testrun
    """
    current = self.getTestrunRunstatus (testrunid, forupdate=True)
    if status == "RUNNING" and \
       current != "PAUSED" and current != "HOSTALLOCATED":
      # Do not transition to running unless we are at HOSTALLOCATED
      # But if we are RUNNING already return True
      return current == status

    if status == "PAUSED" and \
       current != "RUNNING" and current != "HOSTALLOCATED)":
      # Only pause when running or about to run
      return current == status

    if (status == "COMPLETED" or status == "ABORTING") \
       and current != "RUNNING" and current != "PAUSED":
      # Only transition towards an end state from a running one
      # Return true if the current state matches the requested state
      return current == status

    if status == "ABORTED" and current != "ABORTING":
      # Only finalise an abort via the ABORTING state
      return current == status

    if status == "MANUALCHECK" and current != "CREATION" \
       and current != "CHECKFAILED" and current != "ALLOCATIONFAILED":
      return current == status

    if status == "CHECKFAILED" and current != "MANUALCHECK" \
       and current != "READYTOCHECK":
      return current == status

    if status == "CHECKEDGRID" and current != "MANUALCHECK" \
       and current != "READYTOCHECK":
      return current == status

    if status == "GRIDARCHIVE" and current != "READYTOARCHIVE":
      return current == status

    if status == "GRIDDELETE" and current != "READYTODELETE":
      return current == status

    if status == "ARCHIVING" and current != "READYTOARCHIVE" \
       and current != "GRIDARCHIVE":
      return current == status

    if status == "DELETING" and current != "READYTODELETE" \
       and current != "GRIDDELETE":
      return current == status

    # Shunt the state machine
    # WORK NEEDED: should be checked in database too
    sql = "UPDATE ovt_testrun "+\
          "SET runstatusid=(SELECT runstatusid "+\
          "                 FROM ovt_runstatus "+\
          "                 WHERE status=%s) "+\
          "WHERE testrunid=%s"
    self.execute(sql, (status, testrunid))

    # Set the testrun test date when the first task starts running
    if status == "RUNNING":
      sql = "UPDATE ovt_testrun "+\
            "SET testdate=now() "+\
            "WHERE testrunid=%s "+\
            "AND testdate IS NULL"
      self.execute(sql, (testrunid))

    # Add an end date to the testrun
    if status == "COMPLETED" or status == "ABORTED":
      sql = "UPDATE ovt_testrun "+\
            "SET completeddate=now(), "+\
	    "    successful=%s "+\
            "WHERE testrunid=%s "+\
            "AND completeddate IS NULL"
      self.execute(sql, ((status=="COMPLETED"), testrunid))

    return True

  def isTestrunArchived(self, testrunid):
    """
    Check if all executable tasks in a testrun are complete
    """
    sql = "SELECT testrunid "+\
          "FROM ovt_testrun "+\
          "WHERE testrunid=%s "+\
          "FOR UPDATE OF ovt_testrun"
    self.execute(sql, (testrunid))

    sql = "SELECT count(ovt_testrunaction.testrunactionid) AS remaining "+\
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "WHERE ovt_testrunaction.testrunid=%s "+\
          "AND (ovt_testrunaction.archived IS NULL "+\
          "     OR NOT ovt_testrunaction.archived)"

    self.execute(sql, (testrunid))
    return self.cursor.fetchall()[0]['remaining'] == 0

  def allocateHost(self, testrunid, hostid):
    """
    Sets the host that will execute the specified testrun.
    """
    status = self.getTestrunRunstatus(testrunid)
    if status == None or (status != "CHECKED" and status != "CHECKEDGRID"):
      return False

    sql = "SELECT ovt_testrunresource.testrunresourceid "+\
          "FROM ovt_testrunresource "+\
          "WHERE testrunid=%s "+\
          "AND resourceid=%s"
    self.execute(sql, (testrunid, hostid))
    existing = self.cursor.fetchall()

    if len(existing) == 0:
      sql = "INSERT INTO ovt_testrunresource "+\
            "(testrunid, resourceid) "+\
            "VALUES "+\
            "(%s, %s)"
      try:
        self.execute(sql, (testrunid, hostid))
      except postgresql.exceptions.UniqueError:
        self.FORCEROLLBACK()
        if not self.autocommit.autoCommit():
          raise DatabaseRetryException("Unique violation in testrunresource")

    return True

  def getTestrunHosts(self, testrunid):
    """
    Obtain the list of hosts that can execute this testrun
    """
    sql = "SELECT resourceid "+\
	  "FROM ovt_testrunresource "+\
	  "WHERE testrunid=%s"
    self.execute(sql, (testrunid))
    hosts = self.cursor.fetchall()

    retval = []
    for host in hosts:
      retval.append(host['resourceid'])
    return retval

  def clearHosts(self, testrunid):
    """
    Remove all allocated hosts
    """
    status = self.getTestrunRunstatus(testrunid)
    if status == None or status != "CHECKED":
      return False

    sql = "DELETE FROM ovt_testrunresource "+\
          "WHERE testrunid=%s"
    self.execute(sql, (testrunid))
    return True

  def setHostPID(self, hostid, pid):
    """
    The database layer really needs to know where it is running for an execution host
    and set the current PID for the overtest process running on a given host
    """
    OvtDB.hostid = hostid
    OvtDB.hostpid = pid
    sql = "UPDATE ovt_resource "+\
          "SET extradata=%s "+\
          "WHERE resourceid=%s"
    self.execute(sql, (str(pid), hostid))

  def appendToResourceLog(self, resourceid, message, index = None):
    """
    Appends to the log for the given resource, with an optional numeric category
    """
    fieldextra = ""
    valueextra = ""
    values = [resourceid, message]
    if index != None:
      fieldextra = ", index"
      valueextra = ", %s"
      values.append(index)
    sql = "INSERT INTO ovt_resourcelog "+\
          "(resourceid, message"+fieldextra+") "+\
          "VALUES "+\
          "(%s, %s"+valueextra+")"

    self.execute(sql, values)

  def getNextTestruns(self, hostid):
    """
    Return a set of testruns that could be executed next
    Logic elsewhere will determine if a given testrun should be executed
    """
    sql = "SELECT ovt_testrun.testrunid "+\
          "FROM ovt_testrun INNER JOIN ovt_testrunresource USING (testrunid) "+\
          "     INNER JOIN ovt_runstatus USING (runstatusid) "+\
          "WHERE ovt_testrunresource.resourceid=%s "+\
          "AND ovt_testrun.startafter < now() "+\
          "AND ovt_testrun.completeddate IS NULL "+\
          "AND (ovt_runstatus.status='RUNNING' "+\
          "     OR ovt_runstatus.status='HOSTALLOCATED') "+\
          "ORDER BY ovt_testrun.priority, ovt_testrun.createddate"
    self.execute(sql, (hostid))
    testruns = self.cursor.fetchall()
    ret = []
    for row in testruns:
      ret.append(row['testrunid'])
    return ret

  def checkAbortedTestruns(self, testrunid=None):
    """
    Find any aborting testruns, check if they have aborted and update the status
    """
    sql = "SELECT ovt_testrun.testrunid "+\
          "FROM ovt_testrun "+\
          "WHERE runstatusid=(SELECT runstatusid "+\
          "                   FROM ovt_runstatus "+\
          "                   WHERE status='ABORTING') "+\
          "AND NOT EXISTS (SELECT testrunactionid "+\
          "                FROM ovt_testrunaction "+\
          "                WHERE starteddate IS NOT NULL "+\
          "                AND completeddate IS NULL "+\
          "                AND testrunid=ovt_testrun.testrunid) "

    values = []
    if testrunid is not None:
      sql += "AND testrunid=%s"
      values.append(testrunid)

    self.execute(sql, values)
    testruns = self.cursor.fetchall()

    ret = []
    # All testruns in testruns have successfully aborted all actions
    for testrun in testruns:
      ret.append(testrun['testrunid'])

    return ret


  def getTestrunsToArchiveOrDelete(self, hostid):
    """
    Return a set of testruns that are due for archiving or deletion by this host
    """
    sql = "SELECT ovt_testrun.testrunid "+\
          "FROM ovt_testrun INNER JOIN ovt_testrunresource USING (testrunid) "+\
          "     INNER JOIN ovt_runstatus USING (runstatusid) "+\
          "WHERE ovt_testrunresource.resourceid=%s "+\
          "AND (ovt_runstatus.status='READYTOARCHIVE' "+\
          "     OR ovt_runstatus.status='ARCHIVING' "+\
          "     OR ovt_runstatus.status='READYTODELETE' "+\
          "     OR ovt_runstatus.status='DELETING') "+\
          "ORDER BY ovt_testrun.priority, ovt_testrun.createddate"
    self.execute(sql, (hostid))
    testruns = self.cursor.fetchall()
    ret = []
    for row in testruns:
      ret.append(row['testrunid'])
    return ret

  def getTaskUsage(self, testrunid):
    """
    Returns true when the testrun's concurrency quota is larger than the amount
    of tasks currently executing
    """
    sql = "SELECT testrunid "+\
          "FROM ovt_testrun "+\
          "WHERE testrunid=%s "+\
          "FOR UPDATE OF ovt_testrun"
    self.execute(sql, (testrunid))

    sql = "SELECT concurrency AS maximum, (SELECT count(testrunactionid) "+\
          "                                FROM ovt_testrunaction "+\
          "                                WHERE testrunid=%s "+\
          "                                AND starteddate IS NOT NULL "+\
          "                                AND completeddate IS NULL) AS used "+\
          "FROM ovt_testrun "+\
          "WHERE testrunid=%s"

    self.execute(sql, (testrunid, testrunid))
    space = self.cursor.fetchall()
    if len(space) == 0:
      return (0,0)
    return (space[0]['maximum'], space[0]['used'])

  def getAvailableTestrunActions(self, testrunid):
    """
    Returns a testrunactionid that is part of the testrun, if its dependecies are fulfilled
    """
    # This must check that the intra-testrun dependencies are met (that dependencies have passed)
    sql= "SELECT DISTINCT testrunactionid, "+\
         "      (SELECT 1 "+\
         "              FROM ovt_testrunactionresource "+\
         "              WHERE lastchecked IS NOT NULL "+\
         "              AND lastchecked > (now()-'5 minutes'::interval) "+\
         "              AND ovt_testrunactionresource.testrunactionid=ot.testrunactionid "+\
         "              LIMIT 1) AS deferred "+\
         "FROM ovt_testrunaction AS ot INNER JOIN ovt_versionedaction ON (ot.versionedactionid=ovt_versionedaction.versionedactionid) "+\
         "     INNER JOIN ovt_action USING (actionid) "+\
         "WHERE NOT EXISTS (SELECT ovt_testrunaction.testrunactionid "+\
         "                  FROM ovt_testrunaction INNER JOIN ovt_dependency "+\
         "                       ON (ovt_testrunaction.versionedactionid=ovt_dependency.versionedactiondep)  "+\
         "                  WHERE ovt_testrunaction.testrunid = %s "+\
         "                  AND (ovt_testrunaction.passed IS NULL "+\
         "                       OR NOT ovt_testrunaction.passed) "+\
         "                  AND ovt_dependency.versionedactionid=ot.versionedactionid) "+\
         "AND ot.testrunid = %s "+\
         "AND ot.starteddate IS NULL "+\
         "AND ot.passed IS NULL "+\
         "LIMIT 10"
    self.execute(sql, (testrunid, testrunid))
    tasks = self.cursor.fetchall()
    ret = {}
    for task in tasks:
      ret[task['testrunactionid']] = task['deferred']
    return ret

  def getAvailableTestrunActionsToArchive(self, testrunid):
    """
    Fetch a selection of actions that still need archiving
    """
    sql = "SELECT testrunid "+\
          "FROM ovt_testrun "+\
          "WHERE testrunid=%s "+\
          "FOR UPDATE OF ovt_testrun"
    self.execute(sql, (testrunid))

    sql = "SELECT testrunactionid "+\
          "FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid) "+\
          "     INNER JOIN ovt_action USING (actionid) "+\
          "     INNER JOIN ovt_testrun USING (testrunid) "+\
          "WHERE testrunid=%s "+\
          "AND archived IS NULL "+\
          "LIMIT 10"
    self.execute(sql, (testrunid))
    tasks = self.cursor.fetchall()

    ret = []
    for task in tasks:
      ret.append(task['testrunactionid'])
    return ret

  def setTaskArchiving(self, testrunactionid):
    """
    Mark the testrunaction as not yet archived (but therefore started)
    """
    sql = "UPDATE ovt_testrunaction "+\
          "SET archived='f' "+\
          "WHERE testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    return True

  def setTaskArchived(self, testrunactionid):
    """
    Mark the testrunaction as archived
    """
    sql = "UPDATE ovt_testrunaction "+\
          "SET archived='t' "+\
          "WHERE testrunactionid=%s"
    self.execute(sql, (testrunactionid))
    return True

  def checkHostMatch(self, testrunactionid, hostid):
    """
    Ensure that any host matching dependencies on testrunactionid match hostid
    """
    sql = "SELECT ovt_testrunaction.testrunactionid "+\
          "FROM ovt_testrunaction INNER JOIN ovt_dependency ON (ovt_testrunaction.versionedactionid=ovt_dependency.versionedactiondep) "+\
          "     INNER JOIN ovt_testrunaction AS tra ON (ovt_dependency.versionedactionid=tra.versionedactionid) "+\
          "WHERE tra.testrunactionid=%s "+\
          "AND ovt_dependency.hostmatch "+\
          "AND ovt_testrunaction.testrunid=(SELECT testrunid "+\
          "                                 FROM ovt_testrunaction "+\
          "                                 WHERE testrunactionid=%s)"

    self.execute(sql, (testrunactionid, testrunactionid))
    tasks = self.cursor.fetchall()

    success = True

    for task in tasks:
      sql = "SELECT DISTINCT ovt_testrunactionresource.resourceid "+\
            "FROM ovt_testrunactionresource INNER JOIN ovt_resource USING (resourceid) "+\
            "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
            "     INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
            "WHERE ovt_testrunactionresource.testrunactionid=%s "+\
            "AND ovt_resourcestatus.status != 'HISTORIC' "+\
            "AND ovt_resourcetype.resourcetypename='Execution Host'"
      self.execute(sql, (task['testrunactionid']))
      hostmatch = self.cursor.fetchall()
      if len(hostmatch) == 0:
        success = False
        break
      hostmatch = hostmatch[0]['resourceid']
      if hostmatch != hostid:
        success = False
        break

    return success

  def checkTaskExecutedOnHost(self, testrunactionid, hostid):
    """
    Determine if the task executed on the given host.
    Return None if the task did not execute (i.e. there is no host for the task)
    """
    sql = "SELECT DISTINCT ovt_testrunactionresource.resourceid "+\
          "FROM ovt_testrunactionresource INNER JOIN ovt_resource USING (resourceid) "+\
          "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
          "     INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
          "WHERE ovt_testrunactionresource.testrunactionid=%s "+\
          "AND ovt_resourcestatus.status != 'HISTORIC' "+\
          "AND ovt_resourcetype.resourcetypename='Execution Host' "

    # WORK NEEDED: This may want to throw an exception if multiple hosts are found
    self.execute(sql, (testrunactionid))
    resources = self.cursor.fetchall()
    if len(resources) == 0:
      return None

    return resources[0]['resourceid'] == hostid

  def __getAllResourceLinks(self):
    """
    Construct a cache of all resource links in existence
    """
    sql = "SELECT resourceid, resourcetypeid, linkedresourcegroupid "+\
          "FROM ovt_resource "+\
          "WHERE linkedresourcegroupid IS NOT NULL"
    self.execute(sql, ())
    resourcelinks = self.cursor.fetchall()
    ret = {}
    linkgroups = {}
    for resourcelink in resourcelinks:
      if not resourcelink['linkedresourcegroupid'] in linkgroups:
        linkgroups[resourcelink['linkedresourcegroupid']] = {}
      linkgroups[resourcelink['linkedresourcegroupid']][resourcelink['resourceid']] = resourcelink['resourcetypeid']
      ret[resourcelink['resourceid']] = linkgroups[resourcelink['linkedresourcegroupid']]

    for resourceid in ret:
      ret[resourceid] = ret[resourceid].copy()
      del ret[resourceid][resourceid]
    return ret

  def __getValidTestrunActionResourceSets(self, testrunactionid):
    """
    Get a list of the potential resource sets for a testrunaction
    """
    sql = "SELECT ovt_resourcetype.resourcetypeid "+\
          "FROM ovt_resourcetype INNER JOIN ovt_attribute USING (resourcetypeid) "+\
          "     INNER JOIN ovt_attributevalue USING (attributeid) "+\
          "     INNER JOIN ovt_versionedactionattributevalue USING (attributevalueid) "+\
          "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "WHERE ovt_testrunaction.testrunactionid=%s "+\
          "AND ovt_resourcetype.resourcetypename!='Execution Host'"
    self.execute(sql, (testrunactionid))
    attgroups = self.cursor.fetchall()

    # Get the exact resource requirements for this testrunaction
    requiredattributes = self.getTestrunActionResourceRequirements(testrunactionid)

    return (attgroups, requiredattributes)

  def __getValidUserResourceSets(self, userclaimid):
    """
    Get a list of the potential resource sets for a userclaim
    """
    sql = "SELECT ovt_resourcetype.resourcetypeid "+\
          "FROM ovt_resourcetype INNER JOIN ovt_attribute USING (resourcetypeid) "+\
          "     INNER JOIN ovt_attributevalue USING (attributeid) "+\
          "     INNER JOIN ovt_userclaimattributevalue USING (attributevalueid) "+\
          "WHERE ovt_userclaimattributevalue.userclaimid=%s "+\
          "AND ovt_resourcetype.resourcetypename!='Execution Host'"
    self.execute(sql, (userclaimid))
    attgroups = self.cursor.fetchall()

    # Get the exact resource requirements for this testrunaction
    requiredattributes = self.getUserResourceRequirements(userclaimid)

    return (attgroups, requiredattributes)

  def __getValidResourceSets(self, attgroups, requiredattributes):
    """
    Collect all the resource groups that need filling (except the overtest host category)
    """

    # Early success if there is nothing to do!
    if len(attgroups) == 0:
      return None

    # Create an empty structure showing the potential resources allowed for each group
    potentialresources = {}
    for resourcetype in attgroups:
      potentialresources[resourcetype['resourcetypeid']] = None

    # Find suitable resources for each group (this explicitly excludes overtest hosts)
    for resourcetypeid in potentialresources:
      # Find the resources in the group
      potentialresources[resourcetypeid] = self.getAvailableResources(resourcetypeid=resourcetypeid)

      # Now remove all resources that are not suitable
      removethese = []
      for resource in potentialresources[resourcetypeid]:
        # A suitable resource has attributes that include all required attributes
        if not requiredattributes[resourcetypeid].issubset(potentialresources[resourcetypeid][resource]['attributes']):
          removethese.append(resource)
        # A suitable resource with mustrequest attributes must have all such attributes explcitly requested
        elif not potentialresources[resourcetypeid][resource]['mustrequestattributes'].issubset(requiredattributes[resourcetypeid]):
          removethese.append(resource)

      # Remove resources in a second pass because you cannot change an iterator mid iteration!
      for resource in removethese:
        del potentialresources[resourcetypeid][resource]

      # There had better be some resources left!
      if len(potentialresources[resourcetypeid]) == 0:
        # No resources exist that meet the requirements
        groupname = self.getResourceType2(resourcetypeid)['resourcetypename']
        raise AllocationException("No suitable resources available for resource type: %s"% groupname)

    # potentialresources now contains all the permissible resources
    # The data in potentialresources[resourcetypeid][resource] is no longer required and is in fact
    # overwritten in the next pass

    # Use a cache for resource links
    resourcelinks = self.__getAllResourceLinks()

    # Next check the linked resources (this is recursive as removing one resource invalidates the check)
    changed = True
    while changed:
      changed = False
      for group in potentialresources:
        removethese = []
        for resource in potentialresources[group]:
          if resource in resourcelinks:
            resourcedict = resourcelinks[resource]
            for linkedresource in resourcedict:
              # Check that all linked resources are acceptable
              # This means that they must either be in a group that is not in potentialresources
              # or the specific resource must be in potentialresources[samegroup]
              # WORK NEEDED: If an overtest host is linked then it must be one of the hosts that
              #              the testrun can run on. If it is then the overtest host should be part
              #              of the resource request (the testrun/test selection process must then
              #              be changed to observe this restriction)
              linkedgroup = resourcedict[linkedresource]
              if linkedgroup in potentialresources \
                  and not linkedresource in potentialresources[linkedgroup]:
                changed = True
                removethese.append(resource)
          else:
            resourcedict = {}
  
          potentialresources[group][resource] = resourcedict
  
        # As before remove the resources in a post processing step as you cannot alter an active iterator
        for resource in removethese:
          del potentialresources[group][resource]
  
        # Hopefully there are still some resources available
        if len(potentialresources[group]) == 0:
          # No resources exist that meet the requirements
          groupname = self.getResourceType2(group)['resourcetypename']
          raise AllocationException("No suitable resources available for resource type: %s (due to linked resources not satisfying requested attributes)" % groupname)

    # Now verify that all candidate resource sets contain linked resources that satisfy the must request requirements
    for group in potentialresources:
      remove = []
      for resource in potentialresources[group]:
        resourcedict = potentialresources[group][resource]
        for linkedresource in resourcedict:
          if not resourcedict[linkedresource] in potentialresources or \
             not linkedresource in potentialresources[resourcedict[linkedresource]]:
            # Need to verify the must request attributes
            resinfo = self.getAvailableResources(resourceid=linkedresource)
            if len(resinfo) == 0:
              # The resource is disabled
              remove.append(resource)
              break

            # The resource is enabled but if there are any must request attributes then
            # this resource cannot possibly be suitable. This is because if the user
            # requested an attribute it would have made an entry in the original
            # potential resources dictionary and would already have been checked!
            if len(resinfo[linkedresource]['mustrequestattributes']) != 0:
              remove.append(resource)
              break

      # Remove the unsuitable requested resources that failed resource links
      for resource in remove:
        del potentialresources[group][resource]

      # Hopefully there are still some resources available
      if len(potentialresources[group]) == 0:
        # No resources exist that meet the requirements
        groupname = self.getResourceType2(group)['resourcetypename']
        raise AllocationException("No suitable resources available for resource type: %s (due to linked resources having attributes that must be requested)" % groupname)

    # potentialresources now contains all the resources that satisfy the requirements and the 
    # relevant linked resources are also noted and are acceptable

    resourcesets = []
    firstgroup = True
    
    for group in potentialresources:
      newresourcesets = []
      # Create a new resource set for each resource in each group until a full matrix is created
      # This will drop any invalid combinations as it progresses!
      for resource in potentialresources[group]:
        links = potentialresources[group][resource]
        thisresourceset = set([resource]).union(set(links.keys()))
        thisgroupset = set([group]).union(set(links.values()))
        # For the first group the matrix needs to be unconditionally initialised with every resource
        if firstgroup:
          newresourcesets.append((thisresourceset, thisgroupset))
        for resourceset in resourcesets:
          # Check that the resource has not already been included due to resource links
          # If it is included pass through the set
          if not resource in resourceset[0]:
            # If the current resource set doesn't already have a resource for any group in thisresourceset
            # Then it can be extended and used
            commongroups = resourceset[1].intersection(thisgroupset)
            if len(commongroups) == 0:
              newresourcesets.append((resourceset[0].union(thisresourceset), resourceset[1].union(thisgroupset)))
          else:
            newresourcesets.append(resourceset)
            
      firstgroup = False
      # Build a bigger matrix!
      resourcesets = newresourcesets
    
    # If the above code actually works then there will be no resource sets if there is an impossible requirement
    if len(resourcesets) == 0:
      # There are no complete resource sets available!
      raise AllocationException("Complex resource allocation failure. No full resource set exists to meet requirements")
    
    # Now resourcesets contains all valid resource combinations and the groups involved
    return resourcesets

  def fetchPotentialResources(self, testrunactionid):
    """
    Finds one potential set of resources for the given testrunaction
    """
    (attgroups, requiredattributes) = self.__getValidTestrunActionResourceSets(testrunactionid)
    if len(attgroups) == 0:
      return []
    else:
      resourcesets = self.__getValidResourceSets(attgroups, requiredattributes)
      return resourcesets[0][0]

  def __chooseResourceSet(self, resourcesets, testrunactionid=None, userclaimid=None):
    """
    Calculate the cost of each set of resources and select the best set
    1) Cost in terms of status of each resource
    2) Cost in terms of number of unique testrunactions waiting for any resource in the set
    3) Cost in terms of number of unique userclaims waiting for any resource in the set
    4) How many groups are involved in the request
    """
    # An optimisation to save requesting the same resource's cost multiple times
    resourcecosts = {}
    resourcestatecosts = {}
    # This array will show the cost for each resourceset related by index position
    setcosts = []

    for resourceset in resourcesets:
      resources = resourceset[0]
      # The cost relating to other testrun actions
      tracost = set()
      # The cost relating to other user requests
      usercost = set()
      resourcestatecost = 0
      # Collect all unique testrunactions that will cause a block on this resource
      for resource in resources:
        # Save the resource cost for other resourceset cost calculations
        if not resource in resourcestatecosts:
          resourcestatecosts[resource] = self.getResourceStateCost(resource)
        resourcestatecost += resourcestatecosts[resource]
        if not resource in resourcecosts:
          resourcecosts[resource] = self.getResourceBlocks(resource, testrunactionid, userclaimid)
        tracost = tracost.union(resourcecosts[resource][0])
        usercost = usercost.union(resourcecosts[resource][1])
      # Only store the total cost of testrun actions
      totalcost = len(tracost)
      # User requests trump all other requests
      totalcost += len(usercost) * 10
      # Add any resource cost too (disabled resources can be used... if they ever become enabled)
      totalcost += resourcestatecost
      setcosts.append(totalcost)

    # Best cost is the lowest
    bestcost = min(setcosts)
    # Now we have the smallest cost, there may still be multiple possibilities
    # Take the one with the smallest groupcost
    startindex = 0
    chosenset = None
    bestgroupcost = -1
    while startindex < len(setcosts):
      try:
        # This will succeed at least once!
        possibleset = setcosts.index(bestcost, startindex)
      except ValueError:
        break
      if bestgroupcost == -1 or len(resourcesets[possibleset][1]) < bestgroupcost:
        chosenset = possibleset
        bestgroupcost = len(resourcesets[possibleset][1])
      startindex = possibleset+1

    # Get the actual resource list
    return (resourcesets[chosenset][0],setcosts,bestgroupcost)

  def acquireUserResources(self, userclaimid):
    """
    Try to allocate a collection of valid resources.
    """
    try:
      # Do not take the resource lock unless there is a required resource
      (attgroups, requiredattributes) = self.__getValidUserResourceSets(userclaimid)
      if len(attgroups) == 0:
        return True

      self.__LOCKRESOURCES()
      resourcesets = self.__getValidResourceSets(attgroups, requiredattributes)
 
      # We must now either check that the requested resource set (in the database) is one of the allowed sets
      # Or we create a set of requests
  
      sql = "SELECT resourceid, dead, held "+\
            "FROM ovt_userclaimresource INNER JOIN ovt_resource USING (resourceid) "+\
            "     INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
            "WHERE userclaimid=%s "+\
            "AND ovt_resourcestatus.status != 'HISTORIC'"

      self.execute(sql, (userclaimid))
      dbresources = self.cursor.fetchall()
  
      mustchooseresourceset = True
  
      # Always do cost analysis so that requests can move queues
      (chosenset,setcosts,bestgroupcost) = self.__chooseResourceSet(resourcesets, userclaimid=userclaimid)

      # If there are resources then we must check the set is still valid
      if len(dbresources) != 0:
        success = self.__checkExistingRequests( dbresources, resourcesets, setcosts, bestgroupcost)
        if success == None:
          return True
 
        # Should the database resource set have been invalidated for some reason then destroy it
        if not success:
          sql = "DELETE FROM ovt_userclaimresource "+\
                "WHERE userclaimid=%s"
          self.execute(sql, (userclaimid))
        else:
          mustchooseresourceset = False
  
      # We need a new resource set unfortunately
      if mustchooseresourceset:

        # Create the requests
        for resource in chosenset:
          sql = "INSERT INTO ovt_userclaimresource "+\
                "(userclaimid, resourceid) "+\
                "VALUES "+\
                "(%s, %s)"
          self.execute(sql, (userclaimid, resource))

  
      # Now there is a valid set of requests in the database for this userrequest...
      # All that is needed now is to see if they are free!

      # BE SCARED, BE VERY SCARED...
  
      sql = "SELECT ovt_userclaimresource.resourceid, "+\
            "       (SELECT testrunactionid "+\
            "        FROM ovt_testrunactionresource AS tar "+\
            "        WHERE tar.resourceid=ovt_userclaimresource.resourceid "+\
            "        AND tar.held) AS heldtra, "+\
            "       (SELECT userclaimid "+\
            "        FROM ovt_userclaimresource AS ucr "+\
            "        WHERE ucr.resourceid=ovt_userclaimresource.resourceid "+\
            "        AND ucr.held) AS helduser, "+\
            "       (SELECT ovt_userclaim.userclaimid "+\
            "        FROM ovt_userclaim INNER JOIN ovt_userclaimresource AS ucr USING (userclaimid) "+\
            "        WHERE ucr.resourceid=ovt_userclaimresource.resourceid "+\
            "        AND NOT ucr.dead "+\
            "        ORDER BY ovt_userclaim.requestdate, ovt_userclaim.userclaimid "+\
            "        LIMIT 1) AS top "+\
            "FROM ovt_userclaimresource INNER JOIN ovt_resource USING (resourceid) "+\
            "WHERE userclaimid=%s"
  
      # This gives:
      # a) resourceid -> A required resource
      # b) helduser -> A manual claim has been made
      # c) top -> Whether or not we are the next request
      # d) heldtra -> The testrunaction currently holding the resource
      
      self.execute(sql, (userclaimid))
      resources = self.cursor.fetchall()
    
      success = True
    
      for resource in resources:
        resourcesuccess = False
        # Check that the automation system doesn't hold the resource
        if resource['heldtra'] == None:
          # Check that another user request doesn't hold the resource
          if resource['helduser'] == None:
            # If this request is the oldest
            if resource['top'] == userclaimid:
              resourcesuccess = True
        if not resourcesuccess:
          success = False
    
      if success:
        sql = "UPDATE ovt_userclaimresource "+\
              "SET held='t' "+\
              "WHERE userclaimid=%s"
    
        self.execute(sql, (userclaimid))

        sql = "UPDATE ovt_userclaim "+\
              "SET grantdate=now() "+\
              "WHERE userclaimid=%s"
        self.execute(sql, (userclaimid))

        return True
      else:
        # BUGGER failed after all that work
        return False
    finally:
      # Do not commit or release locks etc etc. This is done by the caller
      None

  def __checkExistingRequests(self, dbresources, resourcesets, setcosts, bestgroupcost):
    """
    Verify that an existing request is still valid and still the most suitable
    """
    # Build a set of resources from the database
    resources = set()
    allheld = True
    anyheld = False
    for resource in dbresources:
      #if resource['dead'] or resource['held']:
      #  raise AllocationException("Dead or held requests already placed, has this action already been run/is running?")
      if resource['dead']:
        raise AllocationAbortException("Dead requests already placed, has this request already been dropped?")
      if resource['held']:
        anyheld = True
      else:
        allheld = False
      resources.add(resource['resourceid'])
    if allheld:
      return None

    if anyheld:
      raise AllocationAbortException("Internal consistency error: Some requests already held but not all.")
  
    # Pessimistic assumption, we shall fail
    success = False

    # The index of the current resource set
    resourcesetindex = 0

    for resourceset in resourcesets:
      if resources == resourceset[0]:
        # If there is a permitted resource set to match the one in the database it is allowed
        success = True
        break
      resourcesetindex += 1

    # Check if the request is on the best queue
    if success:
      # Get the best cost
      bestcost = min(setcosts)
      thiscost = setcosts[resourcesetindex]
      # Check the resource cost
      if thiscost > bestcost:
        success = False
      elif thiscost == bestcost:
        # Check the group cost
        if len(resourcesets[resourcesetindex][1]) > bestgroupcost:
          success = False

    return success

  def acquireResources(self, testrunactionid):
    """
    Try to allocate a collection of valid resources.
    """
    allocationsuccess = False
    try:
      # Do not take the resource lock unless there is a required resource
      (attgroups, requiredattributes) = self.__getValidTestrunActionResourceSets(testrunactionid)
      if len(attgroups) == 0:
        allocationsuccess = True
        return True

      self.__LOCKRESOURCES()
      resourcesets = self.__getValidResourceSets(attgroups, requiredattributes)
 
      # We must now either check that the requested resource set (in the database) is one of the allowed sets
      # Or we create a set of requests
  
      sql = "SELECT resourceid, dead, held "+\
            "FROM ovt_testrunactionresource "+\
            "WHERE testrunactionid=%s"
      self.execute(sql, (testrunactionid))
      dbresources = self.cursor.fetchall()
  
      mustchooseresourceset = True
  
      # Always do cost analysis to allow requests to move queues
      (chosenset,setcosts,bestgroupcost) = self.__chooseResourceSet(resourcesets, testrunactionid=testrunactionid)

      # If there are resources then we must check the set is still valid
      if len(dbresources) != 0:
        success = self.__checkExistingRequests( dbresources, resourcesets, setcosts, bestgroupcost)
        if success == None:
          return True

        # Should the database resource set have been invalidated for some reason then destroy it
        if not success:
          sql = "DELETE FROM ovt_testrunactionresource "+\
                "WHERE testrunactionid=%s"
          self.execute(sql, (testrunactionid))
        else:
          mustchooseresourceset = False
  
      # We need a new resource set unfortunately
      if mustchooseresourceset:
        # Create the requests
        for resource in chosenset:
          sql = "INSERT INTO ovt_testrunactionresource "+\
                "(testrunactionid, resourceid) "+\
                "VALUES "+\
                "(%s, %s)"
          self.execute(sql, (testrunactionid, resource))

  
      # Now there is a valid set of requests in the database for this testrunaction...
      # All that is needed now is to see if they are free!

      # BE SCARED, BE VERY SCARED...
  
      sql = "SELECT ovt_testrunactionresource.resourceid, "+\
            "       (testrunactionresourceid=(SELECT min(testrunactionresourceid) "+\
            "                                 FROM ovt_testrunactionresource AS tar INNER JOIN ovt_testrunaction USING (testrunactionid) "+\
            "                                      INNER JOIN ovt_testrun USING (testrunid) "+\
            "                                      INNER JOIN ovt_runstatus USING (runstatusid) "+\
            "                                 WHERE tar.resourceid=ovt_testrunactionresource.resourceid "+\
            "                                 AND NOT tar.dead "+\
            "                                 AND ovt_runstatus.status='RUNNING' "+\
            "                                 AND ovt_testrun.priority=(SELECT min(priority) "+\
            "                                                           FROM ovt_testrun AS tr INNER JOIN ovt_testrunaction AS tra USING (testrunid) "+\
            "                                                                INNER JOIN ovt_testrunactionresource AS tar2 USING (testrunactionid) "+\
            "                                                                INNER JOIN ovt_runstatus USING (runstatusid) "+\
            "                                                           WHERE tar2.resourceid=ovt_testrunactionresource.resourceid "+\
            "                                                           AND ovt_runstatus.status='RUNNING' "+\
            "                                                           AND NOT tar2.dead))) AS top, "+\
            "       (SELECT testrunactionid "+\
            "        FROM ovt_testrunactionresource AS tar "+\
            "        WHERE tar.resourceid=ovt_testrunactionresource.resourceid "+\
            "        AND tar.held) AS heldtra, "+\
            "       (SELECT ovt_userclaimresource.userclaimresourceid "+\
            "        FROM ovt_userclaimresource "+\
            "        WHERE ovt_userclaimresource.resourceid=ovt_testrunactionresource.resourceid "+\
            "        AND NOT ovt_userclaimresource.dead "+\
            "        LIMIT 1) AS userrequest "+\
            "FROM ovt_testrunactionresource INNER JOIN ovt_resource USING (resourceid) "+\
            "WHERE testrunactionid=%s"
  
      # This gives:
      # a) resourceid -> A required resource
      # b) userrequest -> A manual claim has been made
      # c) top -> Whether or not we are the top request
      # d) heldtra -> The testrunaction currently holding the resource
      
      self.execute(sql, (testrunactionid))
      resources = self.cursor.fetchall()
    
      success = True
    
      for resource in resources:
        resourcesuccess = False
        if resource['heldtra'] == None:
          # The resource is not held by someone else
          if resource['top']:
            # We are next in line for the resource (top of the top priority queue)
            if resource['userrequest'] == None:
              resourcesuccess = True
        if not resourcesuccess:
          success = False
    
      if success:
        sql = "UPDATE ovt_testrunactionresource "+\
              "SET held='t' "+\
              "WHERE testrunactionid=%s"
    
        self.execute(sql, (testrunactionid))
        allocationsuccess = True
        return True
      else:
        # BUGGER failed after all that work
        sql = "UPDATE ovt_testrunactionresource "+\
              "SET lastchecked=now() "+\
              "WHERE testrunactionid=%s"
    
        self.execute(sql, (testrunactionid))
        return False
    finally:
      # if we succeeded mark the task as started
      if allocationsuccess:
        self.setTaskStarted(testrunactionid)
      # Do not commit or release locks etc etc. This is done by the task selectaction code

  def registerExecutionHost (self, testrunactionid, hostid):
    """
    Create a dead non-held resource request to specify the host the action executed on
    """
    sql = "INSERT INTO ovt_testrunactionresource "+\
          "(testrunactionid, resourceid, held, dead) "+\
          "VALUES "+\
          "(%s, %s, 'f', 't')"
    self.execute(sql, (testrunactionid, hostid))
    # WORK NEEDED: Potential place for duplicating the resources

  def getTestrunUser(self, testrunid):
    """
    Retrieve the username for the owner of the testrun
    """
    sql = "SELECT ovt_user.username "+\
          "FROM ovt_user INNER JOIN ovt_testrun USING (userid) "+\
          "WHERE ovt_testrun.testrunid=%s"
    self.execute(sql, (testrunid))
    user = self.cursor.fetchall()
    return user[0]['username']

  def cancelAllResourceRequests(self, testrunid):
    """
    Release all unused resource requests
    """
    success = False
    while not success:
      try:
        self.__LOCKRESOURCES()
        self.setAutoCommit(False)

        sql = "UPDATE ovt_testrunactionresource "+\
              "SET dead='t' "+\
              "FROM ovt_testrunaction "+\
              "WHERE ovt_testrunaction.testrunactionid=ovt_testrunactionresource.testrunactionid "+\
              "AND ovt_testrunaction.testrunid=%s "+\
              "AND NOT ovt_testrunactionresource.dead "+\
              "AND NOT ovt_testrunactionresource.held"
        self.execute(sql, (testrunid))

        self.FORCECOMMIT()
        success = True
        self.setAutoCommit(True)
      except DatabaseRetryException, e:
        pass

  def listUserClaims(self, userid = None, userclaimid = None):
    """
    Put together a list of all active claims for a given user
    """
    sql = "SELECT ovt_userclaim.reason, "+\
          "       ovt_userclaim.userclaimid, "+\
          "       to_char(ovt_userclaim.grantdate, 'YYYY/MM/DD HH24:MI') AS grantdate, "+\
          "       to_char(ovt_userclaim.requestdate, 'YYYY/MM/DD HH24:MI') AS requestdate, "+\
          "       to_char(ovt_userclaim.returndate, 'YYYY/MM/DD HH24:MI') AS returndate, "+\
          "       ovt_user.username "+\
          "FROM ovt_userclaim INNER JOIN ovt_user USING (userid) "+\
          "WHERE true "

    values = []
    if userid != None:
      sql += "AND userid=%s "
      values.append(userid)

    if userclaimid != None:
      sql += "AND ovt_userclaim.userclaimid=%s "
      values.append(userclaimid)
    else:
      sql += "AND returndate IS NULL "

    sql += "ORDER BY ovt_user.username, ovt_userclaim.requestdate"

    self.execute(sql, values)
    claims = {}
    claimorder = []
    dbclaims = self.cursor.fetchall()
    shownresources=[]
    for claim in dbclaims:
      claimorder.append(claim['userclaimid'])
      claims[claim['userclaimid']] = {'details':claim, 'resources':{}}
      sql = "SELECT ovt_resource.resourcename, ovt_resource.resourceid, ovt_userclaimresource.held, "+\
            "       ovt_resource.nouserqueue, "+\
            "       (SELECT count(ucr.userclaimresourceid) "+\
            "        FROM ovt_userclaimresource AS ucr INNER JOIN ovt_userclaim AS uc USING (userclaimid) "+\
            "        WHERE ucr.resourceid=ovt_userclaimresource.resourceid "+\
            "        AND ((uc.requestdate < ovt_userclaim.requestdate) "+\
            "             OR (uc.requestdate = ovt_userclaim.requestdate "+\
            "                 AND uc.userclaimid < ovt_userclaim.userclaimid)) "+\
            "        AND NOT ucr.dead) AS position, "+\
            "       ovt_testrunactionresource.testrunactionresourceid IS NOT NULL AS heldbyautomation "+\
            "FROM ovt_userclaimresource LEFT OUTER JOIN ovt_testrunactionresource ON "+\
            "              (ovt_userclaimresource.resourceid=ovt_testrunactionresource.resourceid "+\
            "               AND ovt_testrunactionresource.held) "+\
            "     INNER JOIN ovt_resource ON (ovt_userclaimresource.resourceid=ovt_resource.resourceid) "+\
            "     INNER JOIN ovt_userclaim USING (userclaimid) "+\
            "     INNER JOIN ovt_resourcestatus USING (resourcestatusid) "+\
            "WHERE ovt_userclaimresource.userclaimid=%s "+\
            "AND ovt_resourcestatus.status!='HISTORIC' "+\
            "ORDER BY ovt_resource.resourcename"
      self.execute(sql, (claim['userclaimid']))
      resources = self.cursor.fetchall()
      resresult = claims[claim['userclaimid']]['resources']
      for resource in resources:
        shownresources.append(str(resource['resourceid']))
        resresult[resource['resourcename']] = {'heldbyautomation': resource['heldbyautomation'], 'held':resource['held'], 'position':resource['position'], 'nouserqueue':resource['nouserqueue']}

    if userclaimid == None:
      values = []
      sql = "SELECT ovt_resource.resourcename, to_char(ovt_testrunaction.starteddate, 'YYYY/MM/DD HH24:MI') AS grantdate, "+\
            "       ovt_testrunaction.testrunactionid, ovt_testrun.description, ovt_user.username, ovt_testrun.testrunid "+\
            "FROM ovt_resource INNER JOIN ovt_testrunactionresource USING (resourceid) "+\
            "     INNER JOIN ovt_testrunaction USING (testrunactionid) "+\
            "     INNER JOIN ovt_testrun USING (testrunid) "+\
            "     INNER JOIN ovt_user USING (userid) "+\
            "WHERE held "
      if userid != None:
        sql += "AND ovt_user.userid=%s "
        values.append(userid)
      sql +="ORDER BY ovt_testrunaction.testrunactionid, ovt_resource.resourcename"

      self.execute(sql, values)
      resources = self.cursor.fetchall()
      fake_userclaimid = 0
      currentTestrunactionid = None
      if len(resources) != 0:
        for resource in resources:
          if currentTestrunactionid != resource['testrunactionid']:
            currentTestrunactionid = resource['testrunactionid']
            fake_userclaimid = -int(resource['testrunid'])
            claim = {}
            claim['reason'] = resource['description']
            claim['userclaimid'] = fake_userclaimid
            claim['grantdate'] = resource['grantdate']
            claim['requestdate'] = None
            claim['returndate'] = None
            claim['username'] = resource['username']
            claims[fake_userclaimid] = {'details':claim, 'resources':{}}
            claimorder.append(fake_userclaimid)

          claims[fake_userclaimid]['resources'][resource['resourcename']] = {'heldbyautomation':True, 'held':True, 'position':-1, 'nouserqueue':False}

    return (claims, claimorder)

  def getUserClaim(self, userclaimid, userid=None, reason=None):
    """
    Return information about the specified claim
    """

    sql = "SELECT ovt_userclaim.reason, "+\
          "       ovt_userclaim.userclaimid, "+\
          "       to_char(ovt_userclaim.grantdate, 'YYYY/MM/DD HH24:MI') AS grantdate, "+\
          "       to_char(ovt_userclaim.requestdate, 'YYYY/MM/DD HH24:MI') AS requestdate, "+\
          "       to_char(ovt_userclaim.returndate, 'YYYY/MM/DD HH24:MI') AS returndate, "+\
          "       ovt_user.userid, " +\
          "       ovt_user.username " +\
          "FROM ovt_userclaim INNER JOIN ovt_user USING (userid) "

    if userclaimid != None:
      sql += "WHERE userclaimid=%s"
      self.execute(sql, (userclaimid))
    elif userid!=None and reason!=None:
      sql += "WHERE ovt_userclaim.reason=%s "+\
             "AND ovt_userclaim.userid=%s "+\
             "AND ovt_userclaim.returndate IS NULL"
      self.execute(sql, (reason, userid))
    else:
      return None

    dbclaims = self.cursor.fetchall()
    if len(dbclaims) == 0:
      return None
    else:
      return dbclaims[0]

  def checkUniqueClaimReason(self, userid, reason):
    """
    Check if any active claim has the given reason
    """
    sql = "SELECT ovt_userclaim.userclaimid "+\
          "FROM ovt_userclaim "+\
          "WHERE userid=%s "+\
          "AND reason=%s "+\
          "AND returndate IS NULL"

    self.execute(sql, (userid, reason))
    dbclaims = self.cursor.fetchall()
    return len(dbclaims) == 0

  def releaseUserResources(self, userclaimid):
    """
    Release all held resources
    """
    success = False
    while not success:
      try:
        self.__LOCKRESOURCES()
        self.setAutoCommit(False)

        sql = "UPDATE ovt_userclaimresource "+\
              "SET dead='t', held='f' "+\
              "WHERE userclaimid=%s"
        self.execute(sql, (userclaimid))

        sql = "UPDATE ovt_userclaim "+\
              "SET returndate=now() "+\
              "WHERE userclaimid=%s "+\
              "AND returndate IS NULL"
        self.execute(sql, (userclaimid))

        self.FORCECOMMIT()
        success = True
        self.setAutoCommit(True)
      except DatabaseRetryException, e:
        pass

  def releaseResources(self, testrunactionid):
    """
    Release all held resources
    """
    success = False
    while not success:
      try:
        self.__LOCKRESOURCES()
        self.setAutoCommit(False)

        sql = "UPDATE ovt_testrunactionresource "+\
              "SET dead='t', held='f' "+\
              "WHERE testrunactionid=%s"
        self.execute(sql, (testrunactionid))

        self.FORCECOMMIT()
        success = True
        self.setAutoCommit(True)
      except DatabaseRetryException, e:
        pass

  def rewindTask (self, testrunactionid):
    """
    Rewind a task to its state prior to selection
    Maintain the same resource requests

    This rewind is currently only suitable for rewinding a task that
    has had a resource initialisation error. If a task progresses
    to execution then this rewind is both not sufficient and even
    if it were, then it would be unsafe.
    """
    success = False
    while not success:
      try:
        self.setAutoCommit(False)
        # 1) Remove the host resource request
        sql = "DELETE FROM ovt_testrunactionresource "+\
              "USING ovt_resource INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
              "WHERE ovt_testrunactionresource.testrunactionid=%s "+\
              "AND ovt_testrunactionresource.resourceid = ovt_resource.resourceid "+\
              "AND ovt_resourcetype.resourcetypename = 'Execution Host'"
        self.execute(sql, (testrunactionid))
    
        # 2) Unallocate the remaining resources
        sql = "UPDATE ovt_testrunactionresource "+\
              "SET held='f', dead='f' "+\
              "WHERE testrunactionid=%s"
        self.execute(sql, (testrunactionid))

        # 3) Rewind the task state
        sql = "UPDATE ovt_testrunaction "+\
              "SET passed=NULL, pid=NULL, "+\
              "    starteddate=NULL, completeddate=NULL, "+\
              "    archived=NULL "+\
              "WHERE testrunactionid=%s"
        self.execute(sql, (testrunactionid))

        self.FORCECOMMIT()
        success = True
        self.setAutoCommit(True)
      except DatabaseRetryException, e:
        pass

  def makeUserClaim(self, userid, reason, attributevalueids):
    """
    Place a resource request
    """
    success = False
    userclaimid = None
    while not success:
      try:
        self.setAutoCommit(False)
        sql = "INSERT INTO ovt_userclaim "+\
              "(userid, reason) "+\
              "VALUES "+\
              "(%s, %s)"
        self.execute(sql, (userid, reason))
    
        sql = "SELECT currval('ovt_userclaim_userclaimid_seq') AS userclaimid"
        self.execute(sql, ())
        userclaimid = self.cursor.fetchall()[0]['userclaimid']
    
        # Now insert all the attribute values
        for attributevalueid in attributevalueids:
          sql = "INSERT INTO ovt_userclaimattributevalue "+\
                "(userclaimid, attributevalueid) "+\
                "VALUES "+\
                "(%s, %s)"
          self.execute(sql, (userclaimid, attributevalueid))
    
        self.FORCECOMMIT()
        success = True
        self.setAutoCommit(True)
      except DatabaseRetryException, e:
        pass

    return userclaimid

  def getResourceTypeByName(self, typename):
    """
    Fetch the resourcetypeid for the given name
    """
    return self.simple.getResourceTypeByName (typename)

  def getAttributeValueByName(self, typename, attributename, value):
    """
    return the attributevalueid for the named value
    """
    sql = "SELECT ovt_attributevalue.attributevalueid "+\
          "FROM ovt_attributevalue INNER JOIN ovt_attribute USING (attributeid) "+\
          "     INNER JOIN ovt_resourcetype USING (resourcetypeid) "+\
          "WHERE ovt_resourcetype.resourcetypename ILIKE %s "+\
          "AND ovt_attribute.attributename ILIKE %s "+\
          "AND ovt_attributevalue.value ILIKE %s"
    self.execute(sql, (typename, attributename, value))
    result = self.cursor.fetchall()
    if len(result) == 1:
      return result[0]['attributevalueid']
    else:
      return None

  def getNonAutoConfigOptionByName(self, configgroup, configoption, value):
    """
    Fetch a tuple of configoptionid and configoptionlookupid that relates
    to the specified config group, option and value. Only non automatic
    options can be found.

    This function verifies that the value is suitable for the type of the
    option
    """
    sql = "SELECT ovt_configoption.configoptionid, ovt_configoptiontype.configoptiontypename, "+\
          "       ovt_configoption.islookup "+\
          "FROM ovt_configoption INNER JOIN ovt_configoptiontype USING (configoptiontypeid) "+\
          "     INNER JOIN ovt_configoptiongroup USING (configoptiongroupid) "+\
          "WHERE ovt_configoptiongroup.configoptiongroupname ILIKE %s "+\
          "AND ovt_configoption.configoptionname ILIKE %s "+\
          "AND NOT ovt_configoptiongroup.automatic"

    self.execute(sql, (configgroup, configoption))
    result = self.cursor.fetchall()

    # Not found
    if len(result) == 0:
      return (False, None)

    type = result[0]['configoptiontypename']
    configoptionid = result[0]['configoptionid']

    if result[0]['islookup']:
      sql = "SELECT configoptionlookupid "+\
            "FROM ovt_configoptionlookup "+\
            "WHERE configoptionid=%s "+\
            "AND lookupname ILIKE %s"
      self.execute(sql, (configoptionid, value))
      result = self.cursor.fetchall()

      if len(result) == 0:
        return (False, None)

      return (configoptionid, result[0]['configoptionlookupid'])
    else:
      # Check that the value is of the correct type
      if type == "integer":
        try:
          int(value)
        except ValueError:
          return (False, None)
      elif type == "float":
        try:
          float(value)
        except ValueError:
          return (False, None)
      return (configoptionid, None)

  def getActionByName(self, category, action):
    """
    Fetch the versionedactionid matching the category and action
    """
    sql = "SELECT ovt_action.actionid "+\
          "FROM ovt_action INNER JOIN ovt_actioncategory USING (actioncategoryid) "+\
          "WHERE ovt_actioncategory.actioncategoryname ILIKE %s "+\
          "AND ovt_action.actionname ILIKE %s"
    self.execute(sql, (category, action))
    result = self.cursor.fetchall()

    if len(result) == 0:
      return None

    return result[0]['actionid']

  def getVersionedactionByName(self, category, action, version):
    """
    Fetch the versionedactionid matching the category, action and version
    """
    sql = "SELECT ovt_versionedaction.versionedactionid "+\
          "FROM ovt_versionedaction INNER JOIN ovt_action USING (actionid) "+\
          "     INNER JOIN ovt_actioncategory USING (actioncategoryid) "+\
          "WHERE ovt_actioncategory.actioncategoryname ILIKE %s "+\
          "AND ovt_action.actionname ILIKE %s "+\
          "AND ovt_versionedaction.versionname ILIKE %s"
    self.execute(sql, (category, action, version))
    result = self.cursor.fetchall()

    if len(result) == 0:
      return None

    return result[0]['versionedactionid']

  def getMaxVersionedactionFuzzy(self, actionid, version):
    """
    Returns the maximum version of the specified action using the string version as the basis
    """
    version += "%"
    sql = "SELECT versionedactionid, versionname "+\
          "FROM ovt_versionedaction "+\
          "WHERE versionname LIKE %s "+\
          "AND actionid=%s "+\
          "ORDER BY versionname DESC "+\
          "LIMIT 1"
    self.execute(sql, (version, actionid))
    result = self.cursor.fetchall()

    if len(result) == 0:
      return None

    return result[0]['versionedactionid']

  def getResourceBlocks(self, resourceid, testrunactionid, userclaimid):
    """
    Returns the set of testrunactions that will cause a request for the given
    resource to stall.
    The testrunaction is used to indicate what priority the request will have
    """

    values = [resourceid]
    sql = "SELECT DISTINCT testrunactionid "+\
          "FROM ovt_testrunactionresource INNER JOIN ovt_testrunaction USING (testrunactionid) "+\
          "     INNER JOIN ovt_testrun USING (testrunid) "+\
          "WHERE resourceid=%s "+\
          "AND NOT dead "
    if testrunactionid != None:
      sql += "AND priority >= (SELECT priority "+\
             "                 FROM ovt_testrun INNER JOIN ovt_testrunaction USING (testrunid) "+\
             "                 WHERE testrunactionid=%s) "+\
             "AND NOT ovt_testrunactionresource.testrunactionid=%s"
      values.append(testrunactionid)
      values.append(testrunactionid)

    self.execute(sql, values)
    blocks = self.cursor.fetchall()
    trablocks = set()
    for block in blocks:
      trablocks.add(block['testrunactionid'])

    sql = "SELECT DISTINCT userclaimid "+\
          "FROM ovt_userclaimresource "+\
          "WHERE resourceid=%s "+\
          "AND NOT dead "
    values = [resourceid]

    if userclaimid != None:
      sql += "AND NOT ovt_userclaimresource.userclaimid=%s"
      values.append(userclaimid)
    self.execute(sql, values)

    blocks = self.cursor.fetchall()
    userblocks = set()
    for block in blocks:
      userblocks.add(block['userclaimid'])
    return (trablocks, userblocks)

  def getResourceStateCost(self, resourceid):
    """
    Returns the cost of using a resource based on it status
    """
    sql = "SELECT status "+\
          "FROM ovt_resourcestatus INNER JOIN ovt_resource USING (resourcestatusid) "+\
          "WHERE ovt_resource.resourceid=%s"
    self.execute(sql, (resourceid))
    status = self.cursor.fetchall()
    status = status[0]['status']
    if status == "OK" or status == "CLAIMED":
      return 0
    elif status == "DISABLED":
      return 1000000

    return 1000000

  def getResourceGroup(self, resourceid):
    """
    Get the group that a resource belongs to
    """
    sql = "SELECT ovt_resource.resourcetypeid "+\
          "FROM ovt_resource "+\
          "WHERE ovt_resource.resourceid=%s"
    self.execute(sql, (resourceid))
    group = self.cursor.fetchall()
    if len(group) == 1:
      return group[0]['resourcetypeid']
    else:
      return None

  def sanitizeConfigSettings(self, testrunid):
    """
    Remove all configsettings that are not related to any versionedaction
    Set defaults for any missing configsettings relating to any versionedaction
    """
    sql = "DELETE FROM ovt_configsetting "+\
          "WHERE ovt_configsetting.testrunid=%s "+\
          "AND NOT EXISTS (SELECT ovt_versionedactionconfigoption.configoptionid "+\
          "                FROM ovt_versionedactionconfigoption INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "                WHERE ovt_versionedactionconfigoption.configoptionid=ovt_configsetting.configoptionid "+\
          "                AND ovt_testrunaction.testrunid=ovt_configsetting.testrunid) ";
    self.execute(sql, (testrunid))

    sql = "INSERT INTO ovt_configsetting "+\
          "(testrunid, configoptionid, configvalue) "+\
          "((SELECT DISTINCT ovt_testrunaction.testrunid, ovt_configoption.configoptionid, ovt_configoption.defaultvalue "+\
          "  FROM ovt_configoption INNER JOIN ovt_versionedactionconfigoption USING (configoptionid) "+\
          "       INNER JOIN ovt_configoptiongroup USING (configoptiongroupid) "+\
          "       INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "  WHERE ovt_testrunaction.testrunid=%s "+\
          "  AND NOT ovt_configoption.islookup "+\
          "  AND NOT ovt_configoptiongroup.automatic) "+\
          " EXCEPT "+\
          " (SELECT DISTINCT ovt_configsetting.testrunid, ovt_configoption.configoptionid, ovt_configoption.defaultvalue "+\
          "  FROM ovt_configoption INNER JOIN ovt_configsetting USING (configoptionid) "+\
          "  WHERE ovt_configsetting.testrunid=%s)) ";

    self.execute(sql, (testrunid, testrunid))

    sql = "INSERT INTO ovt_configsetting "+\
          "(testrunid, configoptionid, configoptionlookupid) "+\
          "((SELECT DISTINCT ovt_testrunaction.testrunid, ovt_configoption.configoptionid, ovt_configoptionlookup.configoptionlookupid "+\
          "  FROM ovt_configoption INNER JOIN ovt_versionedactionconfigoption USING (configoptionid) "+\
          "       INNER JOIN ovt_configoptiongroup USING (configoptiongroupid) "+\
          "       INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "       INNER JOIN ovt_configoptionlookup ON (ovt_configoptionlookup.configoptionid=ovt_configoption.configoptionid) "+\
          "  WHERE ovt_testrunaction.testrunid=%s "+\
          "  AND ovt_configoptionlookup.defaultlookup "+\
          "  AND ovt_configoption.islookup "+\
          "  AND NOT ovt_configoptiongroup.automatic) "+\
          " EXCEPT "+\
          " (SELECT DISTINCT ovt_configsetting.testrunid, ovt_configsetting.configoptionid, ovt_configoptionlookup.configoptionlookupid "+\
          "  FROM ovt_configsetting INNER JOIN ovt_configoptionlookup USING (configoptionid) "+\
          "  WHERE ovt_configsetting.testrunid=%s "+\
          "  AND ovt_configoptionlookup.defaultlookup)) ";

    self.execute(sql, (testrunid, testrunid))

    sql = "SELECT configoptiongroupname, configoptionname, lookupname "+\
          "FROM ovt_configoptionlookup INNER JOIN ovt_configoption USING (configoptionid) "+\
          "     INNER JOIN ovt_configoptiongroup USING (configoptiongroupid) "+\
          "     INNER JOIN ovt_configsetting USING (configoptionlookupid) "+\
          "WHERE NOT ovt_configoptionlookup.defaultlookup "+\
          "AND (SELECT count(versionedactionconfigoptionid) "+\
          "     FROM ovt_versionedactionconfigoption INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "     WHERE ovt_versionedactionconfigoption.configoptionid=ovt_configoption.configoptionid "+\
          "     AND testrunid=%s) != "+\
          "    (SELECT count(versionedactionconfigoptionlookupid) "+\
          "     FROM ovt_versionedactionconfigoptionlookup INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
          "     WHERE ovt_versionedactionconfigoptionlookup.configoptionlookupid=ovt_configoptionlookup.configoptionlookupid "+\
          "     AND testrunid=%s) "+\
          "AND testrunid=%s "+\
          "ORDER BY configoptiongroupname, configoptionname, lookupname"

    self.execute(sql, (testrunid, testrunid, testrunid))
    return self.cursor.fetchall()
 
  def getHistory(self):
    """
    Fetch a list of all current notifications.
    This list will be used to clear the notifications later so locks are not necessary
    """
    sql = "SELECT historyid, updateid, notifytypeid, fromvalue, tovalue, to_char(eventdate, 'YYYY/MM/DD HH24:MI') AS eventdate "+\
          "FROM ovt_history INNER JOIN ovt_notifytype USING (notifytypeid) "+\
          "WHERE NOT notificationsent "+\
          "ORDER BY ovt_history.eventdate"
    self.execute(sql, ())
    history = self.cursor.fetchall()
    return history

  def getEmailsToBeNotified(self, historyid):
    """
    Return list of emails
    """
    sql = "SELECT ovt_user.email "+\
          "FROM ovt_subscription "+\
          "     INNER JOIN ovt_user USING (userid) "+\
          "     INNER JOIN ovt_history USING (notifytypeid) "+\
          "     INNER JOIN ovt_notifymethod USING (notifymethodid) "+\
          "WHERE ovt_history.historyid=%s "+\
          "AND ovt_notifymethod.notifymethodname = 'Email' "+\
          "AND NOT EXISTS ((SELECT notifyentityid, pkid "+\
          "                 FROM ovt_subscriptionentity "+\
          "                 WHERE ovt_subscriptionentity.subscriptionid = ovt_subscription.subscriptionid) "+\
          "                EXCEPT "+\
          "                (SELECT notifyentityid, pkid "+\
          "                 FROM ovt_historypk "+\
          "                 WHERE ovt_historypk.historyid = ovt_history.historyid))"

    self.execute(sql, (historyid))
    addresses = self.cursor.fetchall()
    return addresses

  def getGrowlsToBeNotified(self, historyid):
    """
    Return growlhosts and passwords
    """
    sql = "SELECT ovt_user.growlhost, ovt_user.growlpassword "+\
          "FROM ovt_subscription "+\
          "     INNER JOIN ovt_user USING (userid) "+\
          "     INNER JOIN ovt_history USING (notifytypeid) "+\
          "     INNER JOIN ovt_notifymethod USING (notifymethodid) "+\
          "WHERE ovt_history.historyid=%s "+\
          "AND ovt_notifymethod.notifymethodname = 'Growl' "+\
          "AND NOT EXISTS ((SELECT notifyentityid, pkid "+\
          "                 FROM ovt_subscriptionentity "+\
          "                 WHERE ovt_subscriptionentity.subscriptionid = ovt_subscription.subscriptionid) "+\
          "                EXCEPT "+\
          "                (SELECT notifyentityid, pkid "+\
          "                 FROM ovt_historypk "+\
          "                  WHERE ovt_historypk.historyid = ovt_history.historyid))"

    self.execute(sql, (historyid))
    addresses = self.cursor.fetchall()
    return addresses

  def setHistorySent(self, historyids):
    """
    Set all history entries with ids in historyids as sent
    """
    if len(historyids) == 0:
      return
    idstring = ",".join(map(str,historyids))
    sql = "UPDATE ovt_history "+\
          "SET notificationsent=true "+\
          ("WHERE historyid IN (%s)" % idstring)
    self.execute(sql, ())

  def getHistoryRelatedEntites(self, historyid):
    """
    Returns the set of entity classes and entities that a history entry relates to
    """
    sql = "SELECT ovt_historypk.pkid, ovt_notifyentity.notifyentityname "+\
          "FROM ovt_historypk INNER JOIN ovt_notifyentity USING (notifyentityid) "+\
          "WHERE historyid=%s"
    self.execute(sql, (historyid))
    related = self.cursor.fetchall()
    res = {}
    for row in related:
      res[row['notifyentityname']] = row['pkid']
    return res

  def getSubscriptions(self, notifytypeid, entityclass, entity = None):
    """
    Returns a list of users subscribed to various entities that
    notifications are related to.
    """
    if entityclass == "all":
      sql = "SELECT userid, notifymethodname "+\
            "FROM ovt_subscription INNER JOIN ovt_notifymethod USING (notifymethodid) "+\
            "WHERE NOT EXISTS (SELECT subscriptionentityid "+\
            "                  FROM ovt_subscriptionentity "+\
            "                  WHERE subscriptionid=ovt_subscription.subscriptionid) "+\
            "AND notifytypeid=%s"
      self.execute(sql, (notifytypeid))
    else:
      sql = "SELECT userid, notifymethodname "+\
            "FROM ovt_subscription INNER JOIN ovt_notifymethod USING (notifymethodid) "+\
            "     INNER JOIN ovt_subscriptionentity USING (subscriptionid) "+\
            "WHERE notifytypeid=%s "+\
            "AND ovt_subscriptionentity.notifyentityid=%s "+\
            "AND ovt_subscriptionentity.pkid=%s"
      self.execute(sql, (notifytypeid, entityclass, entity))
      
    users = self.cursor.fetchall()

    result = {}
    for user in users:
      if not user['userid'] in result:
        result[user['userid']] = []
      result[user['userid']].append(user['notifymethodname'])
    return result

  def getNotifyTypes(self):
    """
    Fetch a list of notification types
    """
    sql = "SELECT * "+\
          "FROM ovt_notifytype "
    self.execute(sql, ())
    types = self.cursor.fetchall()
    result = {}
    for type in types:
      result[type['notifytypeid']] = type
    return result

  def getTestrunsFromTestgroup(self, testrungroupid):
    """
    Return list of testruns
    """
    sql = "SELECT ovt_testrun.testrunid "+\
          "FROM ovt_testrun "+\
          "WHERE testrungroupid=%s"
 
    self.execute(sql, (testrungroupid))
    testruns = self.cursor.fetchall()
    testrunIdList = []
    for testrunid in testruns:
      testrunIdList.append(testrunid['testrunid'])
    return testrunIdList

  def getNotifyEntities(self, notifytypeid):
    """
    Find the classes of notify entities that the notify type relates to
    """
    sql = "SELECT notifyentityname "+\
          "FROM ovt_notifyentity INNER JOIN ovt_notifytypeentity USING (notifyentityid) "+\
          "WHERE ovt_notifytypeentity.notifytypeid=%s"
    self.execute(sql, (notifytypeid))
    entities = self.cursor.fetchall()
    result = []
    for entity in entities:
      result.append(entity['notifyentityname'])
    return result

  def getNotifyEntityDescription(self, entity, pkid):
    """
    Fetch a description of the entry of type entity with key pkid
    """
    sql = "SELECT description "+\
         ("FROM ovt_view_describe_%s " % entity)+\
          "WHERE pkid=%s"
    self.execute(sql, (pkid))
    description = self.cursor.fetchall()
    if len(description) == 0:
      return '**DELETED %s**' % pkid
    else:
      return description[0]['description']

  def registerGridJob(self, testrunid, job_id):
    """
    Register a job number against a testrun
    """
    sql = "UPDATE ovt_testrun "+\
          "SET gridjobid=%s "+\
	  "WHERE testrunid=%s"
    self.execute(sql, (int(job_id), testrunid))

  def getKeyActions(self, testrunid):
    """
    Get a list of the actionids that are marked as keyaction in the testrun with
    testrunid
    """
    sql = "SELECT ovt_action.actionid "+\
          "FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid) "+\
	  "     INNER JOIN ovt_testrunaction USING (versionedactionid) "+\
	  "WHERE testrunid=%s "+\
	  "AND keyaction"
    self.execute(sql, (testrunid))
    actionids = []
    result = self.cursor.fetchall()
    for res in result:
      actionids.append(res['actionid'])
    return actionids

  def resetTestrun(self, testrunid, status="CREATION", testrunactionids=None):
    """
    Don't use this, it is for development only
    """
    extratestrunactions = ""
    if testrunactionids != None and len(testrunactionids) > 0:
      extratestrunactions = "OR ovt_testrunaction.testrunactionid IN (%s) " % (",".join(map(str,map(int,testrunactionids))))

    if status == "CREATION" or status == "HOSTALLOCATED":
      sql = "UPDATE ovt_testrunaction "+\
            "SET passed=NULL, completeddate=NULL, starteddate=NULL, archived=NULL "+\
            "WHERE testrunid=%s"
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_testrunactionresource "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_testrunactionresource.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s"
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_resultfloat "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_resultfloat.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s"
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_resultstring "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_resultstring.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s"
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_resultinteger "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_resultinteger.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s"
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_resultboolean "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_resultboolean.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s"
      self.execute(sql, (testrunid))
      if status == "CREATION":
        sql = "DELETE from ovt_testrunresource "+\
              "WHERE testrunid=%s"
        self.execute(sql, (testrunid))
        sql = "UPDATE ovt_testrun "+\
              "SET runstatusid=1, successful=NULL, gridjobid=NULL, completeddate=NULL, testdate=NULL "+\
              "WHERE testrunid=%s"
        self.execute(sql, (testrunid))
      else:
        sql = "UPDATE ovt_testrun "+\
              "SET runstatusid=5, completeddate=NULL "+\
              "WHERE testrunid=%s"
        self.execute(sql, (testrunid))

    elif status == "RUNNING":
      sql = "DELETE FROM ovt_testrunactionresource "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_testrunactionresource.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s "+\
            "AND (NOT ovt_testrunaction.passed "+\
            "     OR ovt_testrunaction.passed IS NULL %s) " % extratestrunactions
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_resultfloat "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_resultfloat.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s "+\
            "AND (NOT ovt_testrunaction.passed "+\
            "     OR ovt_testrunaction.passed IS NULL %s)" % extratestrunactions
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_resultstring "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_resultstring.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s "+\
            "AND (NOT ovt_testrunaction.passed "+\
            "     OR ovt_testrunaction.passed IS NULL %s)" % extratestrunactions
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_resultinteger "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_resultinteger.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s "+\
            "AND (NOT ovt_testrunaction.passed "+\
            "     OR ovt_testrunaction.passed IS NULL %s)" % extratestrunactions
      self.execute(sql, (testrunid))
      sql = "DELETE FROM ovt_resultboolean "+\
            "USING ovt_testrunaction "+\
            "WHERE ovt_resultboolean.testrunactionid=ovt_testrunaction.testrunactionid "+\
            "AND ovt_testrunaction.testrunid=%s "+\
            "AND (NOT ovt_testrunaction.passed "+\
            "     OR ovt_testrunaction.passed IS NULL %s)" % extratestrunactions
      self.execute(sql, (testrunid))
      sql = "UPDATE ovt_testrunaction "+\
            "SET pid=NULL, passed=NULL, archived=NULL, completeddate=NULL, starteddate=NULL "+\
            "WHERE testrunid=%s "+\
            "AND (NOT ovt_testrunaction.passed "+\
            "     OR ovt_testrunaction.passed IS NULL %s)" % extratestrunactions
      self.execute(sql, (testrunid))
      sql = "UPDATE ovt_testrun "+\
            "SET runstatusid=6, completeddate=NULL "+\
            "WHERE testrunid=%s"
      self.execute(sql, (testrunid))

class AutoCommit:
  autocommit = True

  def __init__(self):
    self.autocommit = True

  def setAutoCommit(self, value):
    tmp = self.autocommit
    self.autocommit = value
    return tmp

  def autoCommit(self):
    return self.autocommit

