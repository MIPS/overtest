--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: overtest; Type: DATABASE; Schema: -; Owner: overtest
--

CREATE DATABASE overtest WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_GB.UTF-8' LC_CTYPE = 'en_GB.UTF-8';


ALTER DATABASE overtest OWNER TO overtest;

\connect overtest

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

--
-- Name: plpgsql; Type: PROCEDURAL LANGUAGE; Schema: -; Owner: overtest
--

CREATE PROCEDURAL LANGUAGE plpgsql;


ALTER PROCEDURAL LANGUAGE plpgsql OWNER TO overtest;

SET search_path = public, pg_catalog;

--
-- Name: ovtversion; Type: SHELL TYPE; Schema: public; Owner: mfortune
--

CREATE TYPE ovtversion;


--
-- Name: ovtversionin(cstring); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversionin(cstring) RETURNS ovtversion
    LANGUAGE internal IMMUTABLE STRICT
    AS $$textin$$;


ALTER FUNCTION public.ovtversionin(cstring) OWNER TO mfortune;

--
-- Name: ovtversionout(ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversionout(ovtversion) RETURNS cstring
    LANGUAGE internal IMMUTABLE STRICT
    AS $$textout$$;


ALTER FUNCTION public.ovtversionout(ovtversion) OWNER TO mfortune;

--
-- Name: ovtversionrecv(internal); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversionrecv(internal) RETURNS ovtversion
    LANGUAGE internal STABLE STRICT
    AS $$textrecv$$;


ALTER FUNCTION public.ovtversionrecv(internal) OWNER TO mfortune;

--
-- Name: ovtversionsend(ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversionsend(ovtversion) RETURNS bytea
    LANGUAGE internal STABLE STRICT
    AS $$textsend$$;


ALTER FUNCTION public.ovtversionsend(ovtversion) OWNER TO mfortune;

--
-- Name: ovtversion; Type: TYPE; Schema: public; Owner: mfortune
--

CREATE TYPE ovtversion (
    INTERNALLENGTH = variable,
    INPUT = ovtversionin,
    OUTPUT = ovtversionout,
    RECEIVE = ovtversionrecv,
    SEND = ovtversionsend,
    CATEGORY = 'S',
    ALIGNMENT = int4,
    STORAGE = extended
);


ALTER TYPE public.ovtversion OWNER TO mfortune;

--
-- Name: TYPE ovtversion; Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON TYPE ovtversion IS 'Overtest version number';


--
-- Name: ovt_change_status(character varying, integer, character varying); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_change_status(edittype character varying, sourceid integer, action character varying) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

BEGIN
IF edittype = 'testrun' THEN
  PERFORM testrunid
  FROM ovt_testrun
  WHERE testrunid=sourceid
  FOR UPDATE;
ELSE
  PERFORM testrunid
  FROM ovt_testrun
  WHERE testrungroupid=sourceid
  FOR UPDATE;
END IF;

  IF (action = 'go') THEN

    PERFORM ovt_change_status_helper(edittype, sourceid, 'goenabled', 'RUNNING');

    PERFORM ovt_change_status_helper(edittype, sourceid, 'checkenabled', 'READYTOCHECK');

  ELSEIF (action = 'pause') THEN

    PERFORM ovt_change_status_helper(edittype, sourceid, 'pauseenabled', 'PAUSED');

  ELSEIF (action = 'abort') THEN

    PERFORM ovt_change_status_helper(edittype, sourceid, 'abortenabled', 'ABORTING');

  ELSEIF (action = 'archive') THEN

    PERFORM ovt_change_status_helper(edittype, sourceid, 'archiveenabled', 'READYTOARCHIVE');

  ELSEIF (action = 'delete') THEN

    PERFORM ovt_change_status_helper(edittype, sourceid, 'deleteenabled', 'READYTODELETE');

  ELSEIF (action = 'external') THEN

    PERFORM ovt_change_status_helper(edittype, sourceid, 'externalenabled', 'EXTERNAL');

  END IF;

  RETURN 0;

END;$$;


ALTER FUNCTION public.ovt_change_status(edittype character varying, sourceid integer, action character varying) OWNER TO overtest;

--
-- Name: FUNCTION ovt_change_status(edittype character varying, sourceid integer, action character varying); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_change_status(edittype character varying, sourceid integer, action character varying) IS 'This function will progress the testrun state machine based on several commands. the ovt_change_status_helper performs the work and ensures that testruns only make valid transitions';


--
-- Name: ovt_change_status_helper(character varying, integer, character varying, character varying); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_change_status_helper(edittype character varying, sourceid integer, guard character varying, newstatus character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$DECLARE

fieldname character varying;

BEGIN

  IF (edittype = 'testrun') THEN

    fieldname = 'testrunid';

  ELSEIF (edittype = 'group') THEN

    fieldname = 'testrungroupid';

  ELSE

    RAISE EXCEPTION 'Unknown type for updating status';

  END IF;

  EXECUTE 'UPDATE ovt_testrun ' ||

          'SET runstatusid=(SELECT runstatusid ' ||

          '                 FROM ovt_runstatus ' ||

          '                 WHERE status='|| quote_literal(newstatus) || ') ' ||

          'FROM ovt_runstatus '  ||

          'WHERE ovt_runstatus.runstatusid = ovt_testrun.runstatusid ' ||

          'AND ' || quote_ident(fieldname) || '=' || quote_literal(sourceid) || ' ' ||

          'AND ovt_runstatus.' || quote_ident(guard);

  RETURN;

END;$$;


ALTER FUNCTION public.ovt_change_status_helper(edittype character varying, sourceid integer, guard character varying, newstatus character varying) OWNER TO overtest;

--
-- Name: FUNCTION ovt_change_status_helper(edittype character varying, sourceid integer, guard character varying, newstatus character varying); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_change_status_helper(edittype character varying, sourceid integer, guard character varying, newstatus character varying) IS 'Transitions testruns between states. Only valid transitions are permitted, this can transition both testruns or testrun groups.';


--
-- Name: ovt_configoption_equivcheck(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_configoption_equivcheck() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
oldautomatic boolean;
newautomatic boolean;
BEGIN
  IF OLD.affects_equivalence != NEW.affects_equivalence THEN
    RAISE EXCEPTION 'Unable to change whether a config option affects equivalences';
  END IF;

  IF OLD.configoptiongroupid != NEW.configoptiongroupid THEN
    SELECT automatic INTO oldautomatic
    FROM ovt_configoptiongroup
    WHERE configoptiongroupid=OLD.configoptiongroupid;

    SELECT automatic INTO newautomatic
    FROM ovt_configoptiongroup
    WHERE configoptiongroupid=NEW.configoptiongroupid;
   
    IF oldautomatic != newautomatic THEN
      RAISE EXCEPTION 'Unable to change whether a config option is automatic or not';
    END IF;
  END IF;    
  RETURN NEW;
END;$$;


ALTER FUNCTION public.ovt_configoption_equivcheck() OWNER TO overtest;

--
-- Name: ovt_configoptionlookupattributevalue_alter_equivcheck(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_configoptionlookupattributevalue_alter_equivcheck() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
  the_row RECORD;
  is_checked boolean;
BEGIN

  IF TG_OP = 'INSERT' THEN
    the_row := NEW;
  ELSEIF TG_OP = 'UPDATE' THEN
    the_row := NEW;
    IF (OLD.configoptionlookupid != NEW.configoptionlookupid)
       OR (OLD.attributevalueid != NEW.attributevalueid) THEN
      RAISE EXCEPTION 'Config option resource requirements cannot be updated';
    END IF;
  ELSEIF TG_OP = 'DELETE' THEN
    the_row := OLD;
  END IF;

  PERFORM *
  FROM ovt_view_configoptionlookup_usedequivcheck
  WHERE configoptionlookupid = the_row.configoptionlookupid
  LIMIT 1;

  IF FOUND THEN
    RAISE EXCEPTION 'Unable to add or remove resource requirements to/from config options, used in a checked testrun';
  END IF;

  RETURN the_row;
END;$$;


ALTER FUNCTION public.ovt_configoptionlookupattributevalue_alter_equivcheck() OWNER TO overtest;

--
-- Name: ovt_configsetting_equivcheck(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_configsetting_equivcheck() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
  the_row RECORD;
  is_automatic boolean;
  is_checked boolean;
BEGIN

  IF TG_OP = 'INSERT' THEN
    the_row := NEW;
  ELSEIF TG_OP = 'UPDATE' THEN
    the_row := NEW;
    IF (OLD.testrunid != NEW.testrunid)
       OR (OLD.configoptionid != NEW.configoptionid) THEN
      RAISE EXCEPTION 'config settings can not move between testrun or options';
    END IF;
  ELSEIF TG_OP = 'DELETE' THEN
    the_row := OLD;
  END IF;

  SELECT ovt_configoptiongroup.automatic INTO is_automatic
  FROM ovt_configoptiongroup INNER JOIN ovt_configoption USING (configoptiongroupid)
  WHERE ovt_configoption.configoptionid=the_row.configoptionid;

  /* Non-automatic options can only be changed when the testrun is not checked */
  IF NOT is_automatic THEN
    SELECT equivcheck INTO is_checked
    FROM ovt_view_testrun_runstatus
    WHERE testrunid = the_row.testrunid;
    IF is_checked THEN
      RAISE EXCEPTION 'Unable to change config settings on checked testrun';
    END IF;
  END IF;
  RETURN the_row;
END;$$;


ALTER FUNCTION public.ovt_configsetting_equivcheck() OWNER TO overtest;

--
-- Name: FUNCTION ovt_configsetting_equivcheck(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_configsetting_equivcheck() IS 'Used as a trigger on ovt_configsetting for INSERT|UPDATE|DELETE. Prevents updates when the testrun is in a checked state. Also prevents moving settings between options or testruns';


--
-- Name: ovt_create_testrun(character varying, integer, integer, integer, integer, boolean); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_create_testrun(basename character varying, ownerid integer, groupid integer, maxconcurrency integer, prioritylevel integer, trybasename boolean) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

startindex integer;

newtrid integer;

testrunname character varying;

BEGIN

  IF (trybasename) THEN

    startindex = 0;

  ELSE

    startindex = 1;

  END IF;

  IF (maxconcurrency <= 0) THEN

    RAISE EXCEPTION 'Concurrency must be greater than 0';

  END IF;

  LOOP

    testrunname = basename;

    IF (startindex != 0) THEN

      testrunname = basename || ' (' || startindex || ')';

    END IF;

    PERFORM ovt_testrun.testrunid

            FROM ovt_testrun

            WHERE description=testrunname 

            AND testrungroupid=groupid;

    EXIT WHEN NOT FOUND;

    startindex = startindex + 1;

  END LOOP;

  INSERT INTO ovt_testrun

  (userid, description, testrungroupid, concurrency, priority)

  VALUES

  (ownerid, testrunname, groupid, maxconcurrency, prioritylevel);

  SELECT currval('ovt_testrun_testrunid_seq') INTO newtrid;

  RETURN newtrid;

END;$$;


ALTER FUNCTION public.ovt_create_testrun(basename character varying, ownerid integer, groupid integer, maxconcurrency integer, prioritylevel integer, trybasename boolean) OWNER TO overtest;

--
-- Name: ovt_create_testrun(character varying, integer, integer, integer, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_create_testrun(basename character varying, ownerid integer, groupid integer, maxconcurrency integer, prioritylevel integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

startindex integer;

newtrid integer;

testrunname character varying;

BEGIN

  startindex = 0;

  IF (maxconcurrency <= 0) THEN

    RAISE EXCEPTION 'Concurrency must be greater than 0';

  END IF;

  LOOP

    testrunname = basename;

    IF (startindex != 0) THEN

      testrunname = basename || ' (' || startindex || ')';

    END IF;

    PERFORM ovt_testrun.testrunid

            FROM ovt_testrun

            WHERE description=testrunname 

            AND testrungroupid=groupid;

    EXIT WHEN NOT FOUND;

    startindex = startindex + 1;

  END LOOP;

  INSERT INTO ovt_testrun

  (userid, description, testrungroupid, concurrency, priority)

  VALUES

  (ownerid, testrunname, groupid, maxconcurrency, prioritylevel);

  SELECT currval('ovt_testrun_testrunid_seq') INTO newtrid;

  RETURN newtrid;

END;$$;


ALTER FUNCTION public.ovt_create_testrun(basename character varying, ownerid integer, groupid integer, maxconcurrency integer, prioritylevel integer) OWNER TO overtest;

--
-- Name: ovt_create_testrun(character varying, integer, integer, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_create_testrun(basename character varying, ownerid integer, groupid integer, maxconcurrency integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

newtrid integer;

BEGIN

  SELECT ovt_create_testrun(basename, ownerid, groupid, maxconcurrency, 1000)

         INTO newtrid;

  RETURN newtrid;

END;$$;


ALTER FUNCTION public.ovt_create_testrun(basename character varying, ownerid integer, groupid integer, maxconcurrency integer) OWNER TO overtest;

--
-- Name: ovt_create_testrun(character varying, integer, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_create_testrun(basename character varying, ownerid integer, groupid integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

newtrid integer;

BEGIN

  SELECT ovt_create_testrun(basename, ownerid, groupid, 1)

         INTO newtrid;

  RETURN newtrid;

END;$$;


ALTER FUNCTION public.ovt_create_testrun(basename character varying, ownerid integer, groupid integer) OWNER TO overtest;

--
-- Name: ovt_create_testrungroup(character varying, integer, character varying); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_create_testrungroup(basename character varying, ownerid integer, description character varying, OUT newtestrungroupid integer, OUT newtestrunid integer) RETURNS record
    LANGUAGE plpgsql
    AS $$DECLARE

startindex integer = 0;

groupname character varying;

BEGIN

  LOOP

    groupname = basename;

    IF (startindex != 0) THEN

      groupname = basename || ' (' || startindex || ')';

    END IF;

    PERFORM testrungroupid

            FROM ovt_testrungroup

            WHERE testrungroupname=groupname 

            AND userid=ownerid;

    EXIT WHEN NOT FOUND;

    startindex = startindex + 1;

  END LOOP;

  INSERT INTO ovt_testrungroup

         (userid, testrungroupname)

         VALUES

         (ownerid, groupname);

  SELECT currval('ovt_testrungroup_testrungroupid_seq')

         INTO newtestrungroupid;

  newtestrunid = NULL;

  IF (description IS NOT NULL) THEN

    SELECT ovt_create_testrun(description, ownerid, newtestrungroupid)

           INTO newtestrunid;

  END IF;

  RETURN;

END;$$;


ALTER FUNCTION public.ovt_create_testrungroup(basename character varying, ownerid integer, description character varying, OUT newtestrungroupid integer, OUT newtestrunid integer) OWNER TO overtest;

--
-- Name: ovt_dependency_equivcheck(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_dependency_equivcheck() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
  the_row RECORD;
  is_checked boolean;
  consumer_found boolean;
BEGIN

  IF TG_OP = 'INSERT' THEN
    the_row := NEW;
    PERFORM *
    FROM ovt_view_versionedaction_usedequivcheck
    WHERE versionedactionid = NEW.versionedactionid
    LIMIT 1;

    IF FOUND THEN
      PERFORM *
      FROM ovt_view_versionedaction_usedequivcheck AS u1
           INNER JOIN ovt_view_versionedaction_usedequivcheck AS u2
           USING (testrunid)
      WHERE u1.versionedactionid = NEW.versionedactionid
      AND u2.versionedactionid = NEW.versionedactiondep
      LIMIT 1;

      IF FOUND THEN
        RAISE EXCEPTION 'Unable to add dependencies where producer and consumer are already used in a checked testrun';
      END IF;

      IF NEW.dependencygroupid IS NULL THEN
        PERFORM *
        FROM ovt_dependency AS d
             INNER JOIN ovt_versionedaction AS v
             ON (d.versionedactiondep=v.versionedactionid)
        WHERE d.versionedactionid=NEW.versionedactionid
        AND v.actionid=(SELECT actionid
                        FROM ovt_versionedaction
                        WHERE versionedactionid=NEW.versionedactiondep);
        
        IF NOT FOUND THEN
          RAISE EXCEPTION 'Unable to add dependencies without a group where consumer is in a checked testrun and there is no other producer with the same action as the new producer';
        END IF;
      ELSE
        PERFORM *
        FROM ovt_dependency AS d
        WHERE d.versionedactionid=NEW.versionedactionid
        AND d.dependencygroupid=NEW.dependencygroupid;
        
        IF NOT FOUND THEN
          RAISE EXCEPTION 'Unable to add dependencies with a group where consumer is in a checked testrun and there is no other producer with the same group';
        END IF;
      END IF;
    END IF;
    
  ELSEIF TG_OP = 'UPDATE' THEN
    the_row := NEW;
    IF (OLD.versionedactionid != NEW.versionedactionid)
       OR (OLD.dependencygroupid != NEW.dependencygroupid)
       OR (OLD.dependencygroupid IS NOT NULL AND NEW.dependencygroupid IS NULL)
       OR (OLD.dependencygroupid IS NULL AND NEW.dependencygroupid IS NOT NULL)
       OR (OLD.versionedactiondep!= NEW.versionedactiondep) THEN
      RAISE EXCEPTION 'Dependencies cannot be altered after creation';
    END IF;
  ELSEIF TG_OP = 'DELETE' THEN
    the_row := OLD;
    PERFORM *
    FROM ovt_view_versionedaction_usedequivcheck AS u1
         INNER JOIN ovt_view_versionedaction_usedequivcheck AS u2
         USING (testrunid)
    WHERE u1.versionedactionid = OLD.versionedactionid
    AND u2.versionedactionid = OLD.versionedactiondep
    LIMIT 1;

    IF FOUND THEN
      RAISE EXCEPTION 'Unable to remove dependencies with producer and consumer used in a checked testrun';
    END IF;
  END IF;

  RETURN the_row;
END;$$;


ALTER FUNCTION public.ovt_dependency_equivcheck() OWNER TO overtest;

--
-- Name: FUNCTION ovt_dependency_equivcheck(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_dependency_equivcheck() IS 'Used as a trigger on ovt_dependency for INSERT|UPDATE|DELETE. Prevents updates, refuses to allow new dependencies that would form a new set of dependencies (i.e. no group with a new action or grouped with a new group), refuses to allow dependencies to be deleted when consumer and producer are both used in the same checked testrun';


--
-- Name: ovt_duplicate_testrun(integer, integer, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_duplicate_testrun(sourcetestrunid integer, ownerid integer, groupid integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

newtrid integer;
trinfo RECORD;

BEGIN

  SELECT description, concurrency, priority
         INTO trinfo
         FROM ovt_testrun
         WHERE testrunid=sourcetestrunid;

  IF (NOT FOUND) THEN
    RAISE EXCEPTION 'Cannot duplicate. Original testrun not found';
  END IF;

  SELECT ovt_create_testrun(trinfo.description, ownerid, groupid, trinfo.concurrency, trinfo.priority)
         INTO newtrid;

  INSERT INTO ovt_testrunaction
         (testrunid, versionedactionid)
         (SELECT newtrid, versionedactionid
          FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid)
               INNER JOIN ovt_action USING (actionid)
               INNER JOIN ovt_actioncategory USING (actioncategoryid)
          WHERE testrunid=sourcetestrunid);

  INSERT INTO ovt_configsetting
         (testrunid, configoptionid, configoptionlookupid, configvalue)
         (SELECT newtrid, ovt_configsetting.configoptionid, ovt_configsetting.configoptionlookupid, ovt_configsetting.configvalue
          FROM ovt_configsetting INNER JOIN ovt_configoption USING (configoptionid)
               INNER JOIN ovt_configoptiongroup USING (configoptiongroupid)
          WHERE ovt_configsetting.testrunid=sourcetestrunid
          AND NOT ovt_configoptiongroup.automatic);

  INSERT INTO ovt_testrunattributevalue
         (testrunid, attributevalueid)
         (SELECT newtrid, attributevalueid
          FROM ovt_testrunattributevalue
          WHERE testrunid=sourcetestrunid);

  RETURN newtrid;

END;$$;


ALTER FUNCTION public.ovt_duplicate_testrun(sourcetestrunid integer, ownerid integer, groupid integer) OWNER TO overtest;

--
-- Name: ovt_duplicate_testrun(integer, character varying, integer, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_duplicate_testrun(sourcetestrunid integer, basename character varying, ownerid integer, groupid integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

newtrid integer;
newgroupid integer = groupid;
trinfo RECORD;

realbasename character varying = basename;

BEGIN

  SELECT description, concurrency, priority
         INTO trinfo
         FROM ovt_testrun
         WHERE testrunid=sourcetestrunid;

  IF (NOT FOUND) THEN
    RAISE EXCEPTION 'Cannot duplicate. Original testrun not found';
  END IF;

  IF (basename IS NULL) THEN
    realbasename = trinfo.description;
  END IF;

  IF (newgroupid IS NULL) THEN
    SELECT testrungroupid INTO newgroupid
    FROM ovt_testrun
    WHERE testrunid=sourcetestrunid;
  END IF;

  SELECT ovt_create_testrun(realbasename, ownerid, newgroupid, trinfo.concurrency, trinfo.priority)
         INTO newtrid;

  INSERT INTO ovt_testrunaction
         (testrunid, versionedactionid)
         (SELECT newtrid, versionedactionid
          FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid)
               INNER JOIN ovt_action USING (actionid)
               INNER JOIN ovt_actioncategory USING (actioncategoryid)
          WHERE testrunid=sourcetestrunid);

  INSERT INTO ovt_configsetting
         (testrunid, configoptionid, configoptionlookupid, configvalue)
         (SELECT newtrid, ovt_configsetting.configoptionid, ovt_configsetting.configoptionlookupid, ovt_configsetting.configvalue
          FROM ovt_configsetting INNER JOIN ovt_configoption USING (configoptionid)
               INNER JOIN ovt_configoptiongroup USING (configoptiongroupid)
          WHERE ovt_configsetting.testrunid=sourcetestrunid
          AND NOT ovt_configoptiongroup.automatic);

  INSERT INTO ovt_testrunattributevalue
         (testrunid, attributevalueid)
         (SELECT newtrid, attributevalueid
          FROM ovt_testrunattributevalue
          WHERE testrunid=sourcetestrunid);

  RETURN newtrid;

END;$$;


ALTER FUNCTION public.ovt_duplicate_testrun(sourcetestrunid integer, basename character varying, ownerid integer, groupid integer) OWNER TO overtest;

--
-- Name: ovt_duplicate_testrungroup(integer, character varying, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_duplicate_testrungroup(sourcetestrungroupid integer, basename character varying, ownerid integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

newtrgid integer;

testrun RECORD;

realbasename character varying = basename;

BEGIN

  IF (basename IS NULL) THEN

    SELECT ovt_testrungroup.testrungroupname INTO realbasename

           FROM ovt_testrungroup

           WHERE testrungroupid=sourcetestrungroupid;

  END IF;

  SELECT newtestrungroupid INTO newtrgid

         FROM ovt_create_testrungroup(realbasename, ownerid, NULL);

  FOR testrun IN SELECT testrunid

                        FROM ovt_testrun

                        WHERE testrungroupid=sourcetestrungroupid

                 LOOP

    PERFORM ovt_duplicate_testrun(testrun.testrunid, ownerid, newtrgid);

  END LOOP;

  RETURN newtrgid;

END;$$;


ALTER FUNCTION public.ovt_duplicate_testrungroup(sourcetestrungroupid integer, basename character varying, ownerid integer) OWNER TO overtest;

--
-- Name: ovt_modify_config(character varying, integer, integer, character varying); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_modify_config(edittype character varying, keyid integer, optionid integer, value character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$DECLARE
lookupid integer;
typeinfo RECORD;
realvalue character varying;

BEGIN

/*
type is either 'testrun' or 'group'
keyid is a testrunid or testrungroupid
optionid is the configoptionid to use
value is a string representation of the value
*/

-- First determine if this is a lookup option or not

SELECT ovt_configoptiontype.configoptiontypename INTO typeinfo
       FROM ovt_configoption INNER JOIN ovt_configoptiontype USING (configoptiontypeid)
       WHERE ovt_configoption.configoptionid = optionid
       AND NOT islookup;

IF FOUND THEN
  -- This means that it is not a lookup option so type checking is required
  IF typeinfo.configoptiontypename = 'string' THEN
    -- This is always OK
    realvalue = value;
  ELSEIF typeinfo.configoptiontypename = 'boolean' THEN
    -- Check if it is convertable to boolean
    SELECT CAST(CAST(value AS boolean) AS character varying) INTO realvalue;
  ELSEIF typeinfo.configoptiontypename = 'integer' THEN
    -- Check if it is convertable to integer
    SELECT CAST(CAST(value AS integer) AS character varying) INTO realvalue;
  ELSE
    RAISE EXCEPTION 'Unknown type found';
  END IF;

  lookupid = NULL;
ELSE
  -- This means it is a lookup option so find the option
  SELECT configoptionlookupid INTO typeinfo
         FROM ovt_configoptionlookup
         WHERE configoptionid = optionid
         AND lookupname ILIKE value;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Unable to find lookup option for specified value';
  END IF;

  lookupid = typeinfo.configoptionlookupid;
  realvalue = NULL;

END IF;

IF edittype = 'testrun' THEN
  PERFORM ovt_testrun.testrunid
         FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)
         WHERE ovt_runstatus.iseditable
         AND ovt_testrun.testrunid=keyid;

  IF (NOT FOUND) THEN
    RETURN 'f';
  END IF;

  UPDATE ovt_configsetting
         SET configoptionlookupid = lookupid,
             configvalue = realvalue
         WHERE ovt_configsetting.testrunid = keyid
         AND ovt_configsetting.configoptionid = optionid;

  INSERT INTO ovt_configsetting
         (testrunid, configoptionid, configoptionlookupid, configvalue)
         (SELECT testrunid, optionid, lookupid, realvalue
          FROM ((SELECT keyid AS testrunid)
                EXCEPT
                (SELECT testrunid
                 FROM ovt_configsetting
                 WHERE configoptionid = optionid
                 AND testrunid = keyid)) AS trs);

ELSEIF edittype = 'group' THEN

  UPDATE ovt_configsetting
         SET configoptionlookupid = lookupid,
             configvalue = realvalue
         FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)
         WHERE ovt_configsetting.testrunid = ovt_testrun.testrunid
         AND ovt_testrun.testrungroupid = keyid
         AND ovt_runstatus.iseditable
         AND ovt_configsetting.configoptionid = optionid;

  INSERT INTO ovt_configsetting
         (testrunid, configoptionid, configoptionlookupid, configvalue)
         (SELECT testrunid, optionid, lookupid, realvalue
          FROM ((SELECT DISTINCT ovt_testrun.testrunid
                 FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)
                      INNER JOIN ovt_testrunaction USING (testrunid)
                      INNER JOIN ovt_versionedactionconfigoption USING (versionedactionid)
                 WHERE ovt_runstatus.iseditable
                 AND ovt_testrun.testrungroupid = keyid
                 AND ovt_versionedactionconfigoption.configoptionid = optionid)
                EXCEPT
                (SELECT DISTINCT testrunid
                 FROM ovt_configsetting INNER JOIN ovt_testrun USING (testrunid)
                 WHERE ovt_configsetting.configoptionid = optionid
                 AND testrungroupid = keyid)) AS trs);

END IF;

RETURN 't';

END$$;


ALTER FUNCTION public.ovt_modify_config(edittype character varying, keyid integer, optionid integer, value character varying) OWNER TO overtest;

--
-- Name: FUNCTION ovt_modify_config(edittype character varying, keyid integer, optionid integer, value character varying); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_modify_config(edittype character varying, keyid integer, optionid integer, value character varying) IS 'This function will update the config settings for either a single testrun or all editable testruns in a group. It will ensure that there are never two entries for a single option in any testrun and perform type checking on non-lookup options.';


--
-- Name: ovt_modify_requirements(character varying, character varying, integer, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_modify_requirements(edittype character varying, editmode character varying, keyid integer, reqid integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$DECLARE

BEGIN

/*

type is either 'testrun' or 'group'

op is either 'add' or 'remove'

keyid is a testrunid or testrungroupid

reqd is the attributevalueid to use

*/

IF edittype = 'testrun' THEN

  PERFORM ovt_testrun.testrunid

         FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)

         WHERE ovt_runstatus.iseditable

         AND ovt_testrun.testrunid=keyid;

  IF (NOT FOUND) THEN

    RETURN 'f';

  END IF;

  IF editmode = 'remove' THEN

    DELETE FROM ovt_testrunattributevalue

           WHERE attributevalueid = reqid

           AND testrunid = keyid;

  ELSEIF editmode = 'add' THEN

    INSERT INTO ovt_testrunattributevalue

           (testrunid, attributevalueid)

           ((SELECT keyid, reqid)

            EXCEPT

            (SELECT ovt_testrunattributevalue.testrunid, reqid

             FROM ovt_testrunattributevalue

             WHERE ovt_testrunattributevalue.testrunid = keyid

             AND ovt_testrunattributevalue.attributevalueid = reqid));

  END IF;

ELSEIF edittype = 'group' THEN

  IF editmode = 'remove' THEN

    DELETE FROM ovt_testrunattributevalue

           USING ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)

           WHERE attributevalueid = reqid

           AND ovt_testrun.testrunid = ovt_testrunattributevalue.testrunid

           AND ovt_testrun.testrungroupid = keyid

           AND ovt_runstatus.iseditable;

  ELSEIF editmode = 'add' THEN

    INSERT INTO ovt_testrunattributevalue

           (testrunid, attributevalueid)

           ((SELECT ovt_testrun.testrunid, reqid

             FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)

             WHERE ovt_testrun.testrungroupid = keyid

             AND ovt_runstatus.iseditable)

            EXCEPT

            (SELECT ovt_testrunattributevalue.testrunid, reqid

             FROM ovt_testrunattributevalue INNER JOIN ovt_testrun USING (testrunid)

                  INNER JOIN ovt_runstatus USING (runstatusid)

             WHERE ovt_testrun.testrungroupid = keyid

             AND ovt_testrunattributevalue.attributevalueid = reqid

             AND ovt_runstatus.iseditable));

  END IF;

END IF;

RETURN FOUND;

END$$;


ALTER FUNCTION public.ovt_modify_requirements(edittype character varying, editmode character varying, keyid integer, reqid integer) OWNER TO overtest;

--
-- Name: FUNCTION ovt_modify_requirements(edittype character varying, editmode character varying, keyid integer, reqid integer); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_modify_requirements(edittype character varying, editmode character varying, keyid integer, reqid integer) IS 'This function will add or remove a resource requirement from either a single testrun or all editable testruns in a group. It will only add a requirement if it does not already exist.';


--
-- Name: ovt_modify_tasks(character varying, character varying, integer, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_modify_tasks(edittype character varying, editmode character varying, keyid integer, vaid integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$DECLARE

BEGIN

/*

type is either 'testrun' or 'group'

op is either 'add' or 'remove'

keyid is a testrunid or testrungroupid

vaid is the versionedactionid to use

*/

IF edittype = 'testrun' THEN

  PERFORM ovt_testrun.testrunid

         FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)

         WHERE ovt_runstatus.iseditable

         AND ovt_testrun.testrunid=keyid;

  IF (NOT FOUND) THEN

    RETURN 'f';

  END IF;

  IF editmode = 'remove' THEN

    DELETE FROM ovt_testrunaction

           WHERE versionedactionid=vaid

           AND testrunid=keyid;

  ELSEIF editmode = 'add' THEN

    -- Delete any conflicting versions of the same action

    DELETE FROM ovt_testrunaction

           USING ovt_versionedaction

           WHERE ovt_versionedaction.versionedactionid = ovt_testrunaction.versionedactionid

           AND ovt_testrunaction.versionedactionid != vaid

           AND ovt_versionedaction.actionid = (SELECT actionid

                                               FROM ovt_versionedaction

                                               WHERE versionedactionid=vaid)

           AND ovt_testrunaction.testrunid=keyid;

    -- This next statement only inserts if the task does not already exist

    INSERT INTO ovt_testrunaction

           (testrunid, versionedactionid)

           ((SELECT keyid, vaid)

            EXCEPT

            (SELECT ovt_testrunaction.testrunid, vaid

             FROM ovt_testrunaction

             WHERE ovt_testrunaction.testrunid = keyid

             AND ovt_testrunaction.versionedactionid = vaid));

  END IF;

ELSEIF edittype = 'group' THEN

  IF editmode = 'remove' THEN

    DELETE FROM ovt_testrunaction

           USING ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)

           WHERE versionedactionid=vaid

           AND ovt_testrun.testrunid = ovt_testrunaction.testrunid

           AND ovt_testrun.testrungroupid=keyid

           AND ovt_runstatus.iseditable;

  ELSEIF editmode = 'add' THEN

    -- Delete any conflicting versions of the same action

    DELETE FROM ovt_testrunaction

           USING ovt_versionedaction, ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)

           WHERE ovt_versionedaction.versionedactionid = ovt_testrunaction.versionedactionid

           AND ovt_testrunaction.versionedactionid != vaid

           AND ovt_versionedaction.actionid = (SELECT actionid

                                               FROM ovt_versionedaction

                                               WHERE versionedactionid = vaid)

           AND ovt_runstatus.iseditable

           AND ovt_testrun.testrunid = ovt_testrunaction.testrunid

           AND ovt_testrun.testrungroupid = keyid;

    -- This next statement only inserts if the task does not already exist

    INSERT INTO ovt_testrunaction

           (testrunid, versionedactionid)

           ((SELECT ovt_testrun.testrunid, vaid

             FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)

             WHERE ovt_testrun.testrungroupid = keyid

             AND ovt_runstatus.iseditable)

            EXCEPT

            (SELECT ovt_testrunaction.testrunid, vaid

             FROM ovt_testrunaction INNER JOIN ovt_testrun USING (testrunid)

                  INNER JOIN ovt_runstatus USING (runstatusid)

             WHERE ovt_testrun.testrungroupid = keyid

             AND ovt_testrunaction.versionedactionid = vaid

             AND ovt_runstatus.iseditable));

  END IF;

END IF;

RETURN FOUND;

END$$;


ALTER FUNCTION public.ovt_modify_tasks(edittype character varying, editmode character varying, keyid integer, vaid integer) OWNER TO overtest;

--
-- Name: FUNCTION ovt_modify_tasks(edittype character varying, editmode character varying, keyid integer, vaid integer); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_modify_tasks(edittype character varying, editmode character varying, keyid integer, vaid integer) IS 'This function will add or remove a versionedaction from either a single testrun or all editable testruns in a group. It will implicitly remove tasks when adding a new one if they definitely conflict (simple dependency analysis stating that only one version of any action can be present in a testrun).';


--
-- Name: ovt_recursive_equivalence(integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_recursive_equivalence(equiv_traid integer) RETURNS void
    LANGUAGE plpgsql
    AS $$DECLARE

current_equivalence integer = NULL;
BEGIN

        /*
           Absolutely guarantee that equivalences are serialised
        */
        LOCK ovt_recursiveequivalence IN SHARE ROW EXCLUSIVE MODE;

        /* No magic here, just wizardry...
         * This query performs an equivalence over all testruns using one or more testrunactions
         * in the same testrun as a starting point. The full chain of dependent testrunactions
         * are used in the equivalence starting with the requested testrunaction(s). Config
         * settings are also part of the equivalence ensuring that any config settings have
         * the same value in the testruns returned. Only config options attached the the
         * relevant testrunactions are used in the equivalance, and only the manual ones */

        WITH RECURSIVE

          /* Set up a CTE to hold the search terms */

          filter(vaid, traid) AS (
            SELECT versionedactionid AS vaid, testrunactionid AS traid
            FROM ovt_testrunaction
            WHERE testrunactionid = equiv_traid),

          /* Perform the recursive search for testrunactions relating to the original
           * testrunactions that are being used */

          searchtestrunactions(traid, vaid) AS (
               SELECT traid, vaid
               FROM filter
              UNION ALL
               SELECT tra.testrunactionid AS traid,  tra.versionedactionid AS vaid
               FROM ovt_testrunaction INNER JOIN ovt_dependency USING (versionedactionid)
                    INNER JOIN ovt_testrunaction AS tra ON (tra.testrunid=ovt_testrunaction.testrunid
                                                            AND tra.versionedactionid=ovt_dependency.versionedactiondep)
                    , searchtestrunactions
               WHERE ovt_testrunaction.testrunactionid=searchtestrunactions.traid),

          /* Precalculte the relevant settings according to the set of testrunactions
           * that are in the searchtestrunactions table. The recursion will be performed
           * first, followed by this query. This query ensures it is only calculated once
           * for the overall query instead of once per result row. Only search for manual
           * options */

          settings(configoptionid, configvalue, configoptionlookupid) AS (
               SELECT ovt_configsetting.configoptionid, ovt_configsetting.configvalue, ovt_configsetting.configoptionlookupid
               FROM ovt_configsetting INNER JOIN ovt_versionedactionconfigoption USING (configoptionid)
                    INNER JOIN ovt_testrunaction ON (ovt_testrunaction.versionedactionid=ovt_versionedactionconfigoption.versionedactionid
                                                     AND ovt_testrunaction.testrunid=ovt_configsetting.testrunid)
                    /* This is the link to the recursively defined table above */
                    INNER JOIN searchtestrunactions ON (ovt_testrunaction.testrunactionid=searchtestrunactions.traid)
                    INNER JOIN ovt_configoption ON (ovt_configsetting.configoptionid=ovt_configoption.configoptionid)
                    INNER JOIN ovt_configoptiongroup USING (configoptiongroupid)
               WHERE NOT ovt_configoptiongroup.automatic
               AND ovt_configoption.affects_equivalence),

           /* Precalculate the relevant resource requirements according to the set of
            * testrunactions that are in the search testrunactions table. This will
            * be calculated once and used many times. */

           requirements(attributevalueid, resourcetypeid) AS (
                SELECT DISTINCT ovt_testrunattributevalue.attributevalueid, ovt_attribute.resourcetypeid
                FROM ovt_testrunattributevalue INNER JOIN ovt_testrunaction USING (testrunid)
                     INNER JOIN ovt_attributevalue USING (attributevalueid)
                     INNER JOIN ovt_attribute USING (attributeid)
                     INNER JOIN ovt_versionedactionattributevalue USING (versionedactionid)
                     INNER JOIN searchtestrunactions ON (searchtestrunactions.traid=ovt_testrunaction.testrunactionid)
                     INNER JOIN ovt_attributevalue AS av ON (ovt_versionedactionattributevalue.attributevalueid=av.attributevalueid)
                     INNER JOIN ovt_attribute AS a ON (av.attributeid=a.attributeid
                                                       AND a.resourcetypeid=ovt_attribute.resourcetypeid))

        /* This is the actual query and defines the result of this statement */

        SELECT ovt_testrunaction.recursiveequivalenceid INTO current_equivalence
        FROM ovt_testrun INNER JOIN ovt_testrunaction USING (testrunid)
             INNER JOIN ovt_runstatus USING (runstatusid)
        WHERE versionedactionid=(SELECT vaid FROM filter)
        AND NOT testrunactionid=(SELECT traid FROM filter)
        AND recursiveequivalenceid IS NOT NULL
        AND ovt_runstatus.equivcheck

        /* Find all testruns that have matching (not identical) contents to the one
         * being searched. This uses the precalculated table of testrunactionids and
         * versionedactionids for the testrun being searched along with performing a
         * recursive search for the relevant testrunactions in testruns that are found.
         * The relevant testrunactions are found using the versionedactionid(s) relating
         * to the original testrunactions being searched. */

        AND NOT EXISTS
        (WITH RECURSIVE
         foundtestrunactions(traid, vaid) AS (
              SELECT testrunactionid AS traid, versionedactionid AS vaid
              FROM ovt_testrunaction INNER JOIN filter ON (filter.vaid=ovt_testrunaction.versionedactionid)
              /* This is the link to the ovt_testrun table that the results are actually
               * returned from */
              AND ovt_testrun.testrunid=ovt_testrunaction.testrunid
             UNION ALL
              SELECT tra.testrunactionid AS traid, tra.versionedactionid AS vaid
              FROM ovt_testrunaction INNER JOIN ovt_dependency USING (versionedactionid)
                   INNER JOIN ovt_testrunaction AS tra ON (tra.testrunid=ovt_testrunaction.testrunid
                                                           AND tra.versionedactionid=ovt_dependency.versionedactiondep)
                   , foundtestrunactions
              WHERE ovt_testrunaction.testrunactionid=foundtestrunactions.traid)

          /* Check for equivalence. All (relevant) versionedactions in the testrun being searched
           * must be present in the testrun that is found, AND NO OTHERS. Believe it or not
           * this is the best solution available and by using the cacheing feature of WITH it
           * is not as inefficient as one may expect */

          (((SELECT vaid FROM searchtestrunactions) EXCEPT (SELECT vaid FROM foundtestrunactions))
           UNION ALL
           ((SELECT vaid FROM foundtestrunactions) EXCEPT (SELECT vaid FROM searchtestrunactions))))

        /* Ensure that the relevant config from the testrun being checked is included
         * in the testruns that are found. It does not matter if there are more config
         * settings than the original testrun as all the required options are in the
         * 'settings' table. Split this in to two parts to reduce overheads. Each check
         * is faster than the combined check and this is useful even though the combined
         * check is shorter than the total of the two parts. This SQL is reducing a set
         * of rows down to a minimum so a short check that removes many of rows is
         * better than a long check that removes all rows. (Each query is executed once
         * per returned row.) */

        AND NOT EXISTS
          /* Reference the precalculated table in the original WITH clause */
          ((SELECT configoptionid, configvalue FROM settings where configvalue IS NOT NULL)
           EXCEPT
           (SELECT ovt_configsetting.configoptionid, ovt_configsetting.configvalue
            FROM ovt_configsetting
            /* This is the link to the ovt_testrun table that the results are actually
             * returned from */
            WHERE ovt_configsetting.testrunid=ovt_testrun.testrunid AND configvalue IS NOT NULL))

        AND NOT EXISTS
          /* Reference the precalculated table in the original WITH clause */
          ((SELECT configoptionid,configoptionlookupid FROM settings where configvalue is null)
           EXCEPT
           (SELECT ovt_configsetting.configoptionid, ovt_configsetting.configoptionlookupid
            FROM ovt_configsetting
            /* This is the link to the ovt_testrun table that the results are actually
             * returned from */
            WHERE ovt_configsetting.testrunid=ovt_testrun.testrunid and configvalue is  null))

        /* Check that all relevant testrun resource requirements match for the
           checked testrunactions */

        AND NOT EXISTS
          (WITH foundrequirements(attributevalueid) AS (
             SELECT ovt_testrunattributevalue.attributevalueid
             FROM ovt_testrunattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid)
                  INNER JOIN ovt_attribute USING (attributeid)
                  INNER JOIN requirements USING (resourcetypeid)
             WHERE ovt_testrun.testrunid=ovt_testrunattributevalue.testrunid)
             (((SELECT attributevalueid FROM foundrequirements) EXCEPT (SELECT attributevalueid FROM requirements))
              UNION ALL
              ((SELECT attributevalueid FROM requirements) EXCEPT (SELECT attributevalueid FROM foundrequirements))))
        LIMIT 1;

IF (current_equivalence IS NULL) THEN
    INSERT INTO ovt_recursiveequivalence
    DEFAULT VALUES;
    SELECT currval('ovt_recursiveequivalence_recursiveequivalenceid_seq') INTO current_equivalence;
END IF;

UPDATE ovt_testrunaction
SET recursiveequivalenceid=current_equivalence
WHERE testrunactionid=equiv_traid;

END;$$;


ALTER FUNCTION public.ovt_recursive_equivalence(equiv_traid integer) OWNER TO overtest;

--
-- Name: FUNCTION ovt_recursive_equivalence(equiv_traid integer); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_recursive_equivalence(equiv_traid integer) IS 'Determine an equivalance class for a testrunaction based on the entire chain of producers.';


--
-- Name: ovt_resource_resourcename_check(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_resource_resourcename_check() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
id INT;
BEGIN
    IF (SELECT resourcestatusid
        FROM ovt_resourcestatus
        WHERE status='HISTORIC') = NEW.resourcestatusid THEN
        RETURN NEW;
    END IF;

    id := (SELECT ovt_resource.resourceid
           FROM ovt_resource INNER JOIN ovt_resourcestatus USING (resourcestatusid)
           WHERE ovt_resource.resourceid != new.resourceid
           AND ovt_resourcestatus.status != 'HISTORIC'
           AND ovt_resource.resourcename = new.resourcename
           LIMIT 1);

    IF id IS NOT NULL THEN
        RAISE EXCEPTION 'Violation of unique non-historic resource name';
        RETURN NULL;
    ELSE 
        RETURN NEW;
    END IF;

END$$;


ALTER FUNCTION public.ovt_resource_resourcename_check() OWNER TO overtest;

--
-- Name: FUNCTION ovt_resource_resourcename_check(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_resource_resourcename_check() IS 'Resources must have unique names until they become historic.';


--
-- Name: ovt_simple_equivalence(integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_simple_equivalence(equiv_traid integer) RETURNS void
    LANGUAGE plpgsql
    AS $$DECLARE

current_equivalence integer = NULL;
BEGIN
        /*
           Absolutely guarantee that equivalences are serialised
        */
        LOCK ovt_simpleequivalence IN SHARE ROW EXCLUSIVE MODE;

        /* No magic here, just wizardry...
         * This query performs an equivalence over all testruns using one or more testrunactions
         * in the same testrun as a starting point. The full chain of dependent testrunactions
         * are used in the equivalence starting with the requested testrunaction(s). Config
         * settings are also part of the equivalence ensuring that any config settings have
         * the same value in the testruns returned. Only config options attached the the
         * relevant testrunactions are used in the equivalance, and only the manual ones */

        WITH RECURSIVE

          /* Set up a CTE to hold the search terms */

          filter(vaid, traid) AS (
            SELECT versionedactionid AS vaid, testrunactionid AS traid
            FROM ovt_testrunaction
            WHERE testrunactionid = equiv_traid),

          /* Precalculte the relevant settings according to the set of testrunactions
           * that are in the searchtestrunactions table. The recursion will be performed
           * first, followed by this query. This query ensures it is only calculated once
           * for the overall query instead of once per result row. Only search for manual
           * options */

          settings(configoptionid, configvalue, configoptionlookupid) AS (
               SELECT ovt_configsetting.configoptionid, ovt_configsetting.configvalue, ovt_configsetting.configoptionlookupid
               FROM ovt_configsetting INNER JOIN ovt_versionedactionconfigoption USING (configoptionid)
                    INNER JOIN ovt_testrunaction ON (ovt_testrunaction.versionedactionid=ovt_versionedactionconfigoption.versionedactionid
                                                     AND ovt_testrunaction.testrunid=ovt_configsetting.testrunid)
                    /* This is the link to the recursively defined table above */
                    INNER JOIN filter ON (ovt_testrunaction.testrunactionid=filter.traid)
                    INNER JOIN ovt_configoption ON (ovt_configsetting.configoptionid=ovt_configoption.configoptionid)
                    INNER JOIN ovt_configoptiongroup USING (configoptiongroupid)
               WHERE NOT ovt_configoptiongroup.automatic
               AND ovt_configoption.affects_equivalence),

           /* Precalculate the relevant resource requirements according to the set of
            * testrunactions that are in the search testrunactions table. This will
            * be calculated once and used many times. */

           requirements(attributevalueid, resourcetypeid) AS (
                SELECT DISTINCT ovt_testrunattributevalue.attributevalueid, ovt_attribute.resourcetypeid
                FROM ovt_testrunattributevalue INNER JOIN ovt_testrunaction USING (testrunid)
                     INNER JOIN ovt_attributevalue USING (attributevalueid)
                     INNER JOIN ovt_attribute USING (attributeid)
                     INNER JOIN ovt_versionedactionattributevalue USING (versionedactionid)
                     INNER JOIN filter ON (filter.traid=ovt_testrunaction.testrunactionid)
                     INNER JOIN ovt_attributevalue AS av ON (ovt_versionedactionattributevalue.attributevalueid=av.attributevalueid)
                     INNER JOIN ovt_attribute AS a ON (av.attributeid=a.attributeid
                                                       AND a.resourcetypeid=ovt_attribute.resourcetypeid))

        /* This is the actual query and defines the result of this statement */

        SELECT ovt_testrunaction.simpleequivalenceid INTO current_equivalence
        FROM ovt_testrun INNER JOIN ovt_testrunaction USING (testrunid)
             INNER JOIN ovt_runstatus USING (runstatusid)
        WHERE versionedactionid=(SELECT vaid FROM filter)
        AND NOT testrunactionid=(SELECT traid FROM filter)
        AND simpleequivalenceid IS NOT NULL
        AND ovt_runstatus.equivcheck

        /* Ensure that the relevant config from the testrun being checked is included
         * in the testruns that are found. It does not matter if there are more config
         * settings than the original testrun as all the required options are in the
         * 'settings' table. Split this in to two parts to reduce overheads. Each check
         * is faster than the combined check and this is useful even though the combined
         * check is shorter than the total of the two parts. This SQL is reducing a set
         * of rows down to a minimum so a short check that removes many of rows is
         * better than a long check that removes all rows. (Each query is executed once
         * per returned row.) */

        AND NOT EXISTS
          /* Reference the precalculated table in the original WITH clause */
          ((SELECT configoptionid, configvalue FROM settings where configvalue IS NOT NULL)
           EXCEPT
           (SELECT ovt_configsetting.configoptionid, ovt_configsetting.configvalue
            FROM ovt_configsetting
            /* This is the link to the ovt_testrun table that the results are actually
             * returned from */
            WHERE ovt_configsetting.testrunid=ovt_testrun.testrunid AND configvalue IS NOT NULL))

        AND NOT EXISTS
          /* Reference the precalculated table in the original WITH clause */
          ((SELECT configoptionid,configoptionlookupid FROM settings where configvalue is null)
           EXCEPT
           (SELECT ovt_configsetting.configoptionid, ovt_configsetting.configoptionlookupid
            FROM ovt_configsetting
            /* This is the link to the ovt_testrun table that the results are actually
             * returned from */
            WHERE ovt_configsetting.testrunid=ovt_testrun.testrunid and configvalue is  null))

        /* Check that all relevant testrun requirements match for the testrunactions
           being checked */

        AND NOT EXISTS
          (WITH foundrequirements(attributevalueid) AS (
             SELECT ovt_testrunattributevalue.attributevalueid
             FROM ovt_testrunattributevalue INNER JOIN ovt_attributevalue USING (attributevalueid)
                  INNER JOIN ovt_attribute USING (attributeid)
                  INNER JOIN requirements USING (resourcetypeid)
             WHERE ovt_testrun.testrunid=ovt_testrunattributevalue.testrunid)
             (((SELECT attributevalueid FROM foundrequirements) EXCEPT (SELECT attributevalueid FROM requirements))
              UNION ALL
              ((SELECT attributevalueid FROM requirements) EXCEPT (SELECT attributevalueid FROM foundrequirements))))
        LIMIT 1;

IF (current_equivalence IS NULL) THEN
    INSERT INTO ovt_simpleequivalence
    DEFAULT VALUES;
    SELECT currval('ovt_simpleequivalence_simpleequivalenceid_seq') INTO current_equivalence;
END IF;

UPDATE ovt_testrunaction
SET simpleequivalenceid=current_equivalence
WHERE testrunactionid=equiv_traid;

END;$$;


ALTER FUNCTION public.ovt_simple_equivalence(equiv_traid integer) OWNER TO overtest;

--
-- Name: FUNCTION ovt_simple_equivalence(equiv_traid integer); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_simple_equivalence(equiv_traid integer) IS 'Determine an equivalance class for a single testrunaction ignoring and producers.';


--
-- Name: ovt_subrecursive_equivalence(integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_subrecursive_equivalence(equiv_traid integer) RETURNS void
    LANGUAGE plpgsql
    AS $$DECLARE

current_equivalence integer = NULL;
firstrec integer = NULL;
BEGIN

        /*
           Absolutely guarantee that equivalences are serialised
        */
        LOCK ovt_subrecursiveequivalence IN SHARE ROW EXCLUSIVE MODE;


SELECT ovt_testrunaction.recursiveequivalenceid INTO firstrec
FROM ovt_testrunaction INNER JOIN ovt_dependency ON (ovt_dependency.versionedactiondep = ovt_testrunaction.versionedactionid)
     INNER JOIN ovt_testrunaction AS tra ON (tra.testrunid=ovt_testrunaction.testrunid
                                             AND ovt_dependency.versionedactionid=tra.versionedactionid)
WHERE tra.testrunactionid=equiv_traid
LIMIT 1;

IF firstrec IS NULL THEN

        SELECT ovt_testrunaction.subrecursiveequivalenceid INTO current_equivalence
        FROM ovt_testrunaction
        WHERE ovt_testrunaction.subrecursiveequivalenceid IS NOT NULL
        AND NOT EXISTS (SELECT tra.testrunactionid
                        FROM ovt_testrunaction AS tra INNER JOIN ovt_dependency ON (tra.versionedactionid = ovt_dependency.versionedactiondep)
                        WHERE ovt_dependency.versionedactionid=ovt_testrunaction.versionedactionid
                        AND tra.testrunid=ovt_testrunaction.testrunid
                        LIMIT 1)
        LIMIT 1;

ELSE

        WITH subrecursion(recursiveequivalenceid) AS
                       (SELECT ovt_testrunaction.recursiveequivalenceid
                        FROM ovt_testrunaction INNER JOIN ovt_dependency ON (ovt_dependency.versionedactiondep = ovt_testrunaction.versionedactionid)
                             INNER JOIN ovt_testrunaction AS tra ON (tra.testrunid=ovt_testrunaction.testrunid
                                                                     AND ovt_dependency.versionedactionid=tra.versionedactionid)
                        WHERE tra.testrunactionid=equiv_traid)
                SELECT ovt_testrunaction.subrecursiveequivalenceid INTO current_equivalence
                FROM ovt_testrunaction INNER JOIN ovt_testrunaction AS firstsubrecoptimisation USING (testrunid)
                     INNER JOIN ovt_dependency ON (ovt_dependency.versionedactionid=ovt_testrunaction.versionedactionid AND firstsubrecoptimisation.versionedactionid=ovt_dependency.versionedactiondep)
                WHERE firstsubrecoptimisation.recursiveequivalenceid=firstrec
                AND ovt_testrunaction.subrecursiveequivalenceid IS NOT NULL
                AND NOT EXISTS (WITH foundsubrecursion(recursiveequivalenceid) AS
                                  (SELECT tra.recursiveequivalenceid
                                   FROM ovt_testrunaction AS tra INNER JOIN ovt_dependency ON (ovt_dependency.versionedactiondep = tra.versionedactionid)
                                   WHERE ovt_testrunaction.testrunid = tra.testrunid
                                   AND ovt_dependency.versionedactionid=ovt_testrunaction.versionedactionid)
                                (SELECT * FROM ((SELECT * FROM foundsubrecursion) EXCEPT (SELECT * FROM subrecursion)) AS diff1 LIMIT 1)
                                UNION ALL
                                (SELECT * FROM ((SELECT * FROM subrecursion) EXCEPT (SELECT * FROM foundsubrecursion)) AS diff1 LIMIT 1))
                LIMIT 1;
END IF;

IF (current_equivalence IS NULL) THEN
    INSERT INTO ovt_subrecursiveequivalence
    DEFAULT VALUES;
    SELECT currval('ovt_subrecursiveequivalence_subrecursiveequivalenceid_seq') INTO current_equivalence;
END IF;

UPDATE ovt_testrunaction
SET subrecursiveequivalenceid=current_equivalence
WHERE testrunactionid=equiv_traid;

END;$$;


ALTER FUNCTION public.ovt_subrecursive_equivalence(equiv_traid integer) OWNER TO overtest;

--
-- Name: ovt_testperf(integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_testperf(equiv_traid integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$DECLARE

current_equivalence integer = NULL;
firstrec integer = NULL;
BEGIN

        /*
           Absolutely guarantee that equivalences are serialised
        */
        LOCK ovt_subrecursiveequivalence IN SHARE ROW EXCLUSIVE MODE;


SELECT ovt_testrunaction.recursiveequivalenceid INTO firstrec
FROM ovt_testrunaction INNER JOIN ovt_dependency ON (ovt_dependency.versionedactiondep = ovt_testrunaction.versionedactionid)
     INNER JOIN ovt_testrunaction AS tra ON (tra.testrunid=ovt_testrunaction.testrunid
                                             AND ovt_dependency.versionedactionid=tra.versionedactionid)
WHERE tra.testrunactionid=equiv_traid
LIMIT 1;

IF firstrec IS NULL THEN

        SELECT ovt_testrunaction.subrecursiveequivalenceid INTO current_equivalence
        FROM ovt_testrunaction
        WHERE ovt_testrunaction.subrecursiveequivalenceid IS NOT NULL
        AND NOT EXISTS (SELECT tra.testrunactionid
                        FROM ovt_testrunaction AS tra INNER JOIN ovt_dependency ON (tra.versionedactionid = ovt_dependency.versionedactiondep)
                        WHERE ovt_dependency.versionedactionid=ovt_testrunaction.versionedactionid
                        AND tra.testrunid=ovt_testrunaction.testrunid
                        LIMIT 1)
        LIMIT 1;

ELSE

        WITH subrecursion(recursiveequivalenceid) AS
                       (SELECT ovt_testrunaction.recursiveequivalenceid
                        FROM ovt_testrunaction INNER JOIN ovt_dependency ON (ovt_dependency.versionedactiondep = ovt_testrunaction.versionedactionid)
                             INNER JOIN ovt_testrunaction AS tra ON (tra.testrunid=ovt_testrunaction.testrunid
                                                                     AND ovt_dependency.versionedactionid=tra.versionedactionid)
                        WHERE tra.testrunactionid=equiv_traid)
                SELECT ovt_testrunaction.subrecursiveequivalenceid INTO current_equivalence
                FROM ovt_testrunaction INNER JOIN ovt_testrunaction AS firstsubrecoptimisation USING (testrunid)
                     INNER JOIN ovt_dependency ON (ovt_dependency.versionedactionid=ovt_testrunaction.versionedactionid AND firstsubrecoptimisation.versionedactionid=ovt_dependency.versionedactiondep)
                WHERE firstsubrecoptimisation.recursiveequivalenceid=firstrec
                AND ovt_testrunaction.subrecursiveequivalenceid IS NOT NULL
                AND NOT EXISTS (WITH foundsubrecursion(recursiveequivalenceid) AS
                                  (SELECT tra.recursiveequivalenceid
                                   FROM ovt_testrunaction AS tra INNER JOIN ovt_dependency ON (ovt_dependency.versionedactiondep = tra.versionedactionid)
                                   WHERE ovt_testrunaction.testrunid = tra.testrunid
                                   AND ovt_dependency.versionedactionid=ovt_testrunaction.versionedactionid)
                                (SELECT * FROM ((SELECT * FROM foundsubrecursion) EXCEPT (SELECT * FROM subrecursion)) AS diff1 LIMIT 1)
                                UNION ALL
                                (SELECT * FROM ((SELECT * FROM subrecursion) EXCEPT (SELECT * FROM foundsubrecursion)) AS diff1 LIMIT 1))
                LIMIT 1;
END IF;

IF (current_equivalence IS NULL) THEN
    INSERT INTO ovt_subrecursiveequivalence
    DEFAULT VALUES;
    SELECT currval('ovt_subrecursiveequivalence_subrecursiveequivalenceid_seq') INTO current_equivalence;
END IF;

UPDATE ovt_testrunaction
SET subrecursiveequivalenceid=current_equivalence
WHERE testrunactionid=equiv_traid;

RETURN current_equivalence;
END;$$;


ALTER FUNCTION public.ovt_testperf(equiv_traid integer) OWNER TO overtest;

--
-- Name: ovt_testrun_performequivalance(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_testrun_performequivalance() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
  is_oldchecked boolean;
  is_newchecked boolean;
  is_verbose_level boolean;
  verbose_type_text character varying = '';
BEGIN
  IF TG_OP != 'UPDATE' THEN
    RAISE EXCEPTION 'Trigger only valid on update';
  END IF;

  SELECT equivcheck INTO is_oldchecked
  FROM ovt_runstatus
  WHERE runstatusid=OLD.runstatusid;

  SELECT equivcheck, isverbose INTO is_newchecked, is_verbose_level
  FROM ovt_runstatus
  WHERE runstatusid=NEW.runstatusid;

  IF is_verbose_level THEN
    verbose_type_text = ' Verbose';
  END IF;

  IF is_newchecked AND NOT is_oldchecked THEN

    PERFORM ovt_simple_equivalence(testrunactionid),
            ovt_recursive_equivalence(testrunactionid)
    FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid)
         INNER JOIN ovt_action USING (actionid)
         INNER JOIN ovt_actioncategory USING (actioncategoryid)
    WHERE testrunid=NEW.testrunid;

    PERFORM ovt_subrecursive_equivalence(testrunactionid)
    FROM ovt_testrunaction INNER JOIN ovt_versionedaction USING (versionedactionid)
         INNER JOIN ovt_action USING (actionid)
         INNER JOIN ovt_actioncategory USING (actioncategoryid)
    WHERE testrunid=NEW.testrunid;

  ELSEIF is_oldchecked AND NOT is_newchecked THEN
    UPDATE ovt_testrunaction
    SET simpleequivalenceid=NULL,
        recursiveequivalenceid=NULL,
        subrecursiveequivalenceid=NULL
    WHERE testrunid=NEW.testrunid;
  END IF; 

  IF OLD.runstatusid != NEW.runstatusid THEN
    INSERT INTO ovt_history
    (notifytypeid, updateid, fromvalue, tovalue)
    VALUES 
    ((SELECT ovt_notifytype.notifytypeid 
      FROM ovt_notifytype 
      WHERE ovt_notifytype.notifytypename = 'Testrun Status Change'||verbose_type_text),  
     OLD.testrunid,
     (SELECT ovt_runstatus.description
      FROM ovt_runstatus
      WHERE ovt_runstatus.runstatusid = OLD.runstatusid),
     (SELECT ovt_runstatus.description
      FROM ovt_runstatus
      WHERE ovt_runstatus.runstatusid = NEW.runstatusid));

    INSERT INTO ovt_historypk
    (historyid, notifyentityid, pkid)
    VALUES
    ((SELECT currval('ovt_history_historyid_seq')),
     (SELECT notifyentityid
      FROM ovt_notifyentity
      WHERE notifyentityname='testrunid'),
     NEW.testrunid);

    INSERT INTO ovt_historypk
    (historyid, notifyentityid, pkid)
    VALUES
    ((SELECT currval('ovt_history_historyid_seq')),
     (SELECT notifyentityid
      FROM ovt_notifyentity
      WHERE notifyentityname='testrungroupid'),
     NEW.testrungroupid);

    INSERT INTO ovt_historypk
    (historyid, notifyentityid, pkid)
    VALUES
    ((SELECT currval('ovt_history_historyid_seq')),
     (SELECT notifyentityid
      FROM ovt_notifyentity
      WHERE notifyentityname='userid'),
     NEW.userid);

    IF (SELECT status='COMPLETED' OR status='ABORTED'
        FROM ovt_runstatus INNER JOIN ovt_testrun USING (runstatusid)
        WHERE testrunid=NEW.testrunid) THEN
      -- Determine if any runs are still in progress
      PERFORM testrunid
      FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)
      WHERE testrungroupid=NEW.testrungroupid
      AND ovt_runstatus.status != 'ABORTED'
      AND ovt_runstatus.status != 'COMPLETED'
      AND ovt_runstatus.status != 'ARCHIVED'
      AND NOT ovt_runstatus.iseditable;
      
      IF NOT FOUND THEN
        INSERT INTO ovt_history
        (notifytypeid, updateid, fromvalue, tovalue)
        VALUES 
        ((SELECT ovt_notifytype.notifytypeid 
          FROM ovt_notifytype 
          WHERE ovt_notifytype.notifytypename = 'Testrun Group Completed'),  
         NEW.testrungroupid,
         'none',
         'complete');

        INSERT INTO ovt_historypk
        (historyid, notifyentityid, pkid)
        VALUES
        ((SELECT currval('ovt_history_historyid_seq')),
         (SELECT notifyentityid
          FROM ovt_notifyentity
          WHERE notifyentityname='testrungroupid'),
         NEW.testrungroupid);

        INSERT INTO ovt_historypk
        (historyid, notifyentityid, pkid)
        VALUES
        ((SELECT currval('ovt_history_historyid_seq')),
         (SELECT notifyentityid
          FROM ovt_notifyentity
          WHERE notifyentityname='userid'),
         NEW.userid);
      END IF;
    END IF;

  END IF;

  -- Perform auto-archive transition when necessary
  IF (SELECT status='COMPLETED' AND autoarchive
      FROM ovt_runstatus INNER JOIN ovt_testrun USING (runstatusid)
      WHERE testrunid=NEW.testrunid) THEN
    PERFORM ovt_change_status('testrun', NEW.testrunid, 'archive');
  END IF;

  RETURN NEW;
END;$$;


ALTER FUNCTION public.ovt_testrun_performequivalance() OWNER TO overtest;

--
-- Name: FUNCTION ovt_testrun_performequivalance(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_testrun_performequivalance() IS 'Invalidate all equivalences when moving from a checked state to an unchecked state. Detect and/or create new equivalences when moving from an unchecked state to a checked state.';


--
-- Name: ovt_testrunaction_equivcheck(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_testrunaction_equivcheck() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
  the_row RECORD;
  is_checked boolean;
  remove_equiv boolean;
BEGIN

  IF TG_OP = 'INSERT' THEN
    the_row := NEW;
  ELSEIF TG_OP = 'UPDATE' THEN
    the_row := NEW;
    IF (OLD.testrunid != NEW.testrunid)
       OR (OLD.versionedactionid!= NEW.versionedactionid) THEN
      RAISE EXCEPTION 'Testrun tasks can not be changed';
    END IF;
  ELSEIF TG_OP = 'DELETE' THEN
    the_row := OLD;
  END IF;

  SELECT equivcheck INTO is_checked
  FROM ovt_view_testrun_runstatus
  WHERE testrunid = the_row.testrunid;

  IF TG_OP = 'UPDATE' THEN
    IF is_checked THEN
      /* When in a checked state simple and recursive equivalences can be set
         exactly once */
      IF OLD.simpleequivalenceid IS NOT NULL
         AND (NEW.simpleequivalenceid != OLD.simpleequivalenceid 
              OR NEW.simpleequivalenceid IS NULL) THEN
        RAISE EXCEPTION 'Unable to update simple equivalence in checked state';
      END IF;
      IF OLD.recursiveequivalenceid IS NOT NULL
         AND (NEW.recursiveequivalenceid != OLD.recursiveequivalenceid
              OR NEW.recursiveequivalenceid IS NULL) THEN
        RAISE EXCEPTION 'Unable to update recursive equivalence in checked state';
      END IF;
      IF OLD.subrecursiveequivalenceid IS NOT NULL
         AND (NEW.subrecursiveequivalenceid != OLD.subrecursiveequivalenceid
              OR NEW.subrecursiveequivalenceid IS NULL) THEN
        RAISE EXCEPTION 'Unable to update sub-recursive equivalence in checked state';
      END IF;
    ELSE
      /* When in an unchecked state equivalences can only be cleared */
      IF NEW.simpleequivalenceid IS NOT NULL
         AND NEW.simpleequivalenceid != OLD.simpleequivalenceid THEN
        RAISE EXCEPTION 'Unable to set a simple equivalence in unchecked state';
      END IF;
      IF NEW.recursiveequivalenceid IS NOT NULL 
         AND OLD.recursiveequivalenceid != OLD.recursiveequivalenceid THEN
        RAISE EXCEPTION 'Unable to set a recursive equivalence in unchecked state';
      END IF;
      IF NEW.subrecursiveequivalenceid IS NOT NULL 
         AND OLD.subrecursiveequivalenceid != OLD.subrecursiveequivalenceid THEN
        RAISE EXCEPTION 'Unable to set a sub-recursive equivalence in unchecked state';
      END IF;
    END IF;
    RETURN the_row;
  END IF;

  IF is_checked THEN
    RAISE EXCEPTION 'Unable to change tasks in a checked testrun';
  END IF;

  RETURN the_row;
END;$$;


ALTER FUNCTION public.ovt_testrunaction_equivcheck() OWNER TO overtest;

--
-- Name: FUNCTION ovt_testrunaction_equivcheck(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_testrunaction_equivcheck() IS 'Used as a trigger on ovt_testrunaction for INSERT|UPDATE|DELETE. Prevents updates when the testrun is in a checked state. Also prevents moving tasks between versioned actions or testruns';


--
-- Name: ovt_testrunaction_equivcheck_afterupdate(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_testrunaction_equivcheck_afterupdate() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
remove_equiv boolean;
BEGIN
      IF OLD.simpleequivalenceid IS NOT NULL
         AND NEW.simpleequivalenceid IS NULL THEN
        /* Remove the simple equivalence if there is nothing referencing it */
        SELECT count(testrunactionid) = 0 INTO remove_equiv
        FROM ovt_testrunaction
        WHERE simpleequivalenceid=OLD.simpleequivalenceid;
        IF remove_equiv THEN
          DELETE FROM ovt_simpleequivalence
          WHERE simpleequivalenceid=OLD.simpleequivalenceid;
        END IF;
      END IF;
      IF OLD.recursiveequivalenceid IS NOT NULL 
         AND NEW.recursiveequivalenceid IS NULL THEN
        /* Remove the recursive equivalence if there is nothing referencing it */
        SELECT count(testrunactionid) = 0 INTO remove_equiv
        FROM ovt_testrunaction
        WHERE recursiveequivalenceid=OLD.recursiveequivalenceid;
        IF remove_equiv THEN
          DELETE FROM ovt_recursiveequivalence
          WHERE recursiveequivalenceid=OLD.recursiveequivalenceid;
        END IF;
      END IF;
      IF OLD.passed IS NULL and NEW.passed IS NOT NULL 
         AND (SELECT testsuiteid IS NOT NULL
              FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)
              WHERE versionedactionid=OLD.versionedactionid) THEN
        INSERT INTO ovt_history
        (notifytypeid, updateid, fromvalue, tovalue)
        VALUES 
        ((SELECT ovt_notifytype.notifytypeid 
          FROM ovt_notifytype 
          WHERE ovt_notifytype.notifytypename = 'Testsuite Completed'),  
         OLD.testrunactionid,
         ('Not run'),
         ('Complete'));
        INSERT INTO ovt_historypk
        (historyid, notifyentityid, pkid)
        VALUES
        ((SELECT currval('ovt_history_historyid_seq')),
         (SELECT notifyentityid
          FROM ovt_notifyentity
          WHERE notifyentityname='testrunid'),
         NEW.testrunid);
        INSERT INTO ovt_historypk
        (historyid, notifyentityid, pkid)
        VALUES
        ((SELECT currval('ovt_history_historyid_seq')),
         (SELECT notifyentityid
          FROM ovt_notifyentity
          WHERE notifyentityname='testrungroupid'),
         (SELECT testrungroupid
          FROM ovt_testrun
          WHERE testrunid=NEW.testrunid));
        INSERT INTO ovt_historypk
        (historyid, notifyentityid, pkid)
        VALUES
        ((SELECT currval('ovt_history_historyid_seq')),
         (SELECT notifyentityid
          FROM ovt_notifyentity
          WHERE notifyentityname='userid'),
         (SELECT userid
          FROM ovt_testrun
          WHERE testrunid=NEW.testrunid));
        INSERT INTO ovt_historypk
        (historyid, notifyentityid, pkid)
        VALUES
        ((SELECT currval('ovt_history_historyid_seq')),
         (SELECT notifyentityid
          FROM ovt_notifyentity
          WHERE notifyentityname='testsuiteid'),
         (SELECT testsuiteid
          FROM ovt_action INNER JOIN ovt_versionedaction USING (actionid)
          WHERE versionedactionid=NEW.versionedactionid));
      END IF;
  RETURN NEW;
END;$$;


ALTER FUNCTION public.ovt_testrunaction_equivcheck_afterupdate() OWNER TO overtest;

--
-- Name: ovt_testrunattributevalue_equivcheck(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_testrunattributevalue_equivcheck() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
  the_row RECORD;
  is_checked boolean;
BEGIN

  IF TG_OP = 'INSERT' THEN
    the_row := NEW;
  ELSEIF TG_OP = 'UPDATE' THEN
    the_row := NEW;
    IF (OLD.testrunid != NEW.testrunid)
       OR (OLD.attributevalueid != NEW.attributevalueid) THEN
      RAISE EXCEPTION 'testrun requirements can not move between testruns or requirements';
    END IF;
  ELSEIF TG_OP = 'DELETE' THEN
    the_row := OLD;
  END IF;

  SELECT equivcheck INTO is_checked
  FROM ovt_view_testrun_runstatus
  WHERE testrunid = the_row.testrunid;

  IF is_checked THEN
    RAISE EXCEPTION 'Unable to change resource requirements on checked testrun';
  END IF;

  RETURN the_row;
END;$$;


ALTER FUNCTION public.ovt_testrunattributevalue_equivcheck() OWNER TO overtest;

--
-- Name: FUNCTION ovt_testrunattributevalue_equivcheck(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_testrunattributevalue_equivcheck() IS 'Used as a trigger on ovt_testrunattributevalue for INSERT|UPDATE|DELETE. Prevents updates when the testrun is in a checked state. Also prevents moving requirements between testruns or changing the requirement.';


--
-- Name: ovt_unique_claim_check(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_unique_claim_check() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE

id INT;

BEGIN

IF TG_RELNAME='ovt_userclaim' THEN --check that this is only called by the stated table

  IF NEW.returndate IS NOT NULL THEN
    NEW.active = NULL;
  ELSE
    NEW.active = 't';
  END IF;

  RETURN NEW;
ELSE

    RAISE EXCEPTION 'This Trigger Function is for the ovt_userclaim relation';

END IF;

END$$;


ALTER FUNCTION public.ovt_unique_claim_check() OWNER TO overtest;

--
-- Name: FUNCTION ovt_unique_claim_check(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_unique_claim_check() IS 'Ensures that the reasons given for user claims are unique for all active claims for each user.';


--
-- Name: ovt_update_testrun(integer, integer, character varying, integer, integer, timestamp with time zone); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_update_testrun(updatetestrunid integer, ownerid integer, newdescription character varying, newpriority integer, newconcurrency integer, newstarttime timestamp with time zone) RETURNS boolean
    LANGUAGE plpgsql
    AS $$DECLARE

editable boolean = NULL;

currentownerid integer = NULL;

BEGIN

  SELECT ovt_runstatus.iseditable, ovt_testrun.userid INTO editable, currentownerid

          FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)

          WHERE ovt_testrun.testrunid=updatetestrunid;

  IF (NOT FOUND) THEN

    RETURN FALSE;

  END IF;

  IF (currentownerid != ownerid) THEN

    RETURN FALSE;

  END IF;

  IF (editable) THEN

    -- Allow all fields to be edited

    IF (newdescription IS NOT NULL) THEN

      UPDATE ovt_testrun

             SET description=newdescription

             WHERE testrunid=updatetestrunid;

    END IF;

    IF (newstarttime IS NOT NULL) THEN

      UPDATE ovt_testrun

             SET startafter=newstarttime

             WHERE testrunid=updatetestrunid;

    END IF;

  END IF;

  -- Some fields can be changed at any point

  IF (newpriority IS NOT NULL) THEN

    UPDATE ovt_testrun

           SET priority=newpriority

           WHERE testrunid=updatetestrunid;

  END IF;

  IF (newconcurrency IS NOT NULL) THEN

    UPDATE ovt_testrun

           SET concurrency=newconcurrency

           WHERE testrunid=updatetestrunid;

  END IF;

  RETURN TRUE;

END;$$;


ALTER FUNCTION public.ovt_update_testrun(updatetestrunid integer, ownerid integer, newdescription character varying, newpriority integer, newconcurrency integer, newstarttime timestamp with time zone) OWNER TO overtest;

--
-- Name: ovt_update_testrun(integer, integer, character varying, integer, integer, timestamp with time zone, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_update_testrun(updatetestrunid integer, ownerid integer, newdescription character varying, newpriority integer, newconcurrency integer, newstarttime timestamp with time zone, newtestrungroupid integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$DECLARE
editable boolean = NULL;
currentownerid integer = NULL;
status character varying = NULL;
testruncount integer = NULL;
oldtestrungroupid integer = NULL;
BEGIN
  SELECT ovt_runstatus.iseditable, ovt_runstatus.status, ovt_testrun.userid INTO editable, status, currentownerid
          FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)
          WHERE ovt_testrun.testrunid=updatetestrunid;

  IF (NOT FOUND) THEN
    RETURN FALSE;
  END IF;

  IF (currentownerid != ownerid) THEN
    RETURN FALSE;
  END IF;

  IF (status = 'EXTERNAL' or editable) THEN
    -- Allow all fields to be edited
    IF (newdescription IS NOT NULL) THEN
      UPDATE ovt_testrun
             SET description=newdescription
             WHERE testrunid=updatetestrunid;
    END IF;
    IF (newstarttime IS NOT NULL) THEN
      UPDATE ovt_testrun
             SET startafter=newstarttime
             WHERE testrunid=updatetestrunid;
    END IF;
  END IF;

  -- Some fields can be changed at any point
  IF (newpriority IS NOT NULL) THEN
    UPDATE ovt_testrun
           SET priority=newpriority
           WHERE testrunid=updatetestrunid;
  END IF;

  IF (newconcurrency IS NOT NULL) THEN
    UPDATE ovt_testrun
           SET concurrency=newconcurrency
           WHERE testrunid=updatetestrunid;
  END IF;

  IF (status = 'EXTERNAL' AND newtestrungroupid IS NOT NULL) THEN
    SELECT ovt_testrun.testrungroupid INTO oldtestrungroupid
    FROM ovt_testrun
    WHERE ovt_testrun.testrunid=updatetestrunid;

    SELECT count(ovt_testrun.testrunid) INTO testruncount
    FROM ovt_testrun
    WHERE testrungroupid=oldtestrungroupid;

    UPDATE ovt_testrun
           SET testrungroupid=newtestrungroupid
           WHERE testrunid=updatetestrunid;

    IF (testruncount = 1) THEN
      DELETE FROM ovt_testrungroup
      WHERE testrungroupid=oldtestrungroupid;
    END IF;
  END IF;

  RETURN TRUE;
END;$$;


ALTER FUNCTION public.ovt_update_testrun(updatetestrunid integer, ownerid integer, newdescription character varying, newpriority integer, newconcurrency integer, newstarttime timestamp with time zone, newtestrungroupid integer) OWNER TO overtest;

--
-- Name: ovt_update_testrun(integer, integer, character varying, integer, integer, timestamp with time zone, boolean, integer); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_update_testrun(updatetestrunid integer, ownerid integer, newdescription character varying, newpriority integer, newconcurrency integer, newstarttime timestamp with time zone, newautoarchive boolean, newtestrungroupid integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$DECLARE
editable boolean = NULL;
currentownerid integer = NULL;
status character varying = NULL;
testruncount integer = NULL;
oldtestrungroupid integer = NULL;
BEGIN
  SELECT ovt_runstatus.iseditable, ovt_runstatus.status, ovt_testrun.userid INTO editable, status, currentownerid
          FROM ovt_testrun INNER JOIN ovt_runstatus USING (runstatusid)
          WHERE ovt_testrun.testrunid=updatetestrunid;

  IF (NOT FOUND) THEN
    RETURN FALSE;
  END IF;

  IF (currentownerid != ownerid) THEN
    RETURN FALSE;
  END IF;

  IF (status = 'EXTERNAL' or editable) THEN
    -- Allow all fields to be edited
    IF (newdescription IS NOT NULL) THEN
      UPDATE ovt_testrun
             SET description=newdescription
             WHERE testrunid=updatetestrunid;
    END IF;
    IF (newstarttime IS NOT NULL) THEN
      UPDATE ovt_testrun
             SET startafter=newstarttime
             WHERE testrunid=updatetestrunid;
    END IF;
  END IF;

  -- Some fields can be changed at any point
  IF (newpriority IS NOT NULL) THEN
    UPDATE ovt_testrun
           SET priority=newpriority
           WHERE testrunid=updatetestrunid;
  END IF;

  IF (newconcurrency IS NOT NULL) THEN
    UPDATE ovt_testrun
           SET concurrency=newconcurrency
           WHERE testrunid=updatetestrunid;
  END IF;

  IF (newautoarchive IS NOT NULL) THEN
    UPDATE ovt_testrun
           SET autoarchive=newautoarchive
           WHERE testrunid=updatetestrunid;
  END IF;

  IF (status = 'EXTERNAL' AND newtestrungroupid IS NOT NULL) THEN
    SELECT ovt_testrun.testrungroupid INTO oldtestrungroupid
    FROM ovt_testrun
    WHERE ovt_testrun.testrunid=updatetestrunid;

    SELECT count(ovt_testrun.testrunid) INTO testruncount
    FROM ovt_testrun
    WHERE testrungroupid=oldtestrungroupid;

    UPDATE ovt_testrun
           SET testrungroupid=newtestrungroupid
           WHERE testrunid=updatetestrunid;

    IF (testruncount = 1) THEN
      DELETE FROM ovt_testrungroup
      WHERE testrungroupid=oldtestrungroupid;
    END IF;
  END IF;

  RETURN TRUE;
END;$$;


ALTER FUNCTION public.ovt_update_testrun(updatetestrunid integer, ownerid integer, newdescription character varying, newpriority integer, newconcurrency integer, newstarttime timestamp with time zone, newautoarchive boolean, newtestrungroupid integer) OWNER TO overtest;

--
-- Name: ovt_versionedactionattributevalue_equivcheck(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_versionedactionattributevalue_equivcheck() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
  the_row RECORD;
  is_checked boolean;
BEGIN

  IF TG_OP = 'INSERT' THEN
    the_row := NEW;
  ELSEIF TG_OP = 'UPDATE' THEN
    the_row := NEW;
    IF (OLD.versionedactionid != NEW.versionedactionid)
       OR (OLD.attributevalueid!= NEW.attributevalueid) THEN
      RAISE EXCEPTION 'Versioned action resource requiredments cannot be updated';
    END IF;
  ELSEIF TG_OP = 'DELETE' THEN
    the_row := OLD;
  END IF;

  PERFORM *
  FROM ovt_view_versionedaction_usedequivcheck
  WHERE versionedactionid = the_row.versionedactionid
  LIMIT 1;

  IF FOUND THEN
    RAISE EXCEPTION 'Unable to add or remove resource requirements to/from versioned actions, used in a checked testrun';
  END IF;

  RETURN the_row;
END;$$;


ALTER FUNCTION public.ovt_versionedactionattributevalue_equivcheck() OWNER TO overtest;

--
-- Name: FUNCTION ovt_versionedactionattributevalue_equivcheck(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_versionedactionattributevalue_equivcheck() IS 'Used as a trigger on ovt_versionedactionattributevalue for INSERT|UPDATE|DELETE. Prevents updates when the referenced versionedaction is in a testrun that is in a checked state. Also prevents changing existing requirements af ter initial creation.';


--
-- Name: ovt_versionedactionconfigoption_equivcheck(); Type: FUNCTION; Schema: public; Owner: overtest
--

CREATE FUNCTION ovt_versionedactionconfigoption_equivcheck() RETURNS trigger
    LANGUAGE plpgsql
    AS $$DECLARE
  the_row RECORD;
  is_checked boolean;
BEGIN

  IF TG_OP = 'INSERT' THEN
    the_row := NEW;
  ELSEIF TG_OP = 'UPDATE' THEN
    the_row := NEW;
    IF (OLD.versionedactionid != NEW.versionedactionid)
       OR (OLD.configoptionid!= NEW.configoptionid) THEN
      RAISE EXCEPTION 'Versioned action config option links cannot be updated';
    END IF;
  ELSEIF TG_OP = 'DELETE' THEN
    the_row := OLD;
  END IF;

  PERFORM *
  FROM ovt_view_versionedaction_usedequivcheck
  WHERE versionedactionid = the_row.versionedactionid
  LIMIT 1;

  IF FOUND THEN
    PERFORM *
    FROM ovt_configoption INNER JOIN ovt_configoptiongroup USING (configoptiongroupid)
    WHERE NOT ovt_configoptiongroup.automatic
    AND ovt_configoption.affects_equivalence
    AND configoptionid=the_row.configoptionid;

    IF FOUND THEN
      RAISE EXCEPTION 'Unable to add or remove config option links to/from versioned actions, used in a checked testrun';
    END IF;
  END IF;

  RETURN the_row;
END;$$;


ALTER FUNCTION public.ovt_versionedactionconfigoption_equivcheck() OWNER TO overtest;

--
-- Name: FUNCTION ovt_versionedactionconfigoption_equivcheck(); Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON FUNCTION ovt_versionedactionconfigoption_equivcheck() IS 'Used as a trigger on ovt_versionedactionconfigoption for INSERT|UPDATE|DELETE. Prevents updates when the referenced versionedaction is in a testrun that is in a checked state. Also prevents changing existing options after initial creation. Automatic option and those that dont affect equivalence can be changed at any point.';


--
-- Name: ovtversion(character); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion(character) RETURNS ovtversion
    LANGUAGE internal IMMUTABLE STRICT
    AS $$rtrim1$$;


ALTER FUNCTION public.ovtversion(character) OWNER TO mfortune;

--
-- Name: ovtversion_cmp(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_cmp(version1 ovtversion, version2 ovtversion) RETURNS integer
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_cmp';


ALTER FUNCTION public.ovtversion_cmp(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: FUNCTION ovtversion_cmp(version1 ovtversion, version2 ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON FUNCTION ovtversion_cmp(version1 ovtversion, version2 ovtversion) IS 'Compare Overtest versions';


--
-- Name: ovtversion_eq(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_eq(version1 ovtversion, version2 ovtversion) RETURNS boolean
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_eq';


ALTER FUNCTION public.ovtversion_eq(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: FUNCTION ovtversion_eq(version1 ovtversion, version2 ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON FUNCTION ovtversion_eq(version1 ovtversion, version2 ovtversion) IS 'ovtversion equal';


--
-- Name: ovtversion_ge(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_ge(version1 ovtversion, version2 ovtversion) RETURNS boolean
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_ge';


ALTER FUNCTION public.ovtversion_ge(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: FUNCTION ovtversion_ge(version1 ovtversion, version2 ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON FUNCTION ovtversion_ge(version1 ovtversion, version2 ovtversion) IS 'ovtversion greater-than-or-equal';


--
-- Name: ovtversion_gt(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_gt(version1 ovtversion, version2 ovtversion) RETURNS boolean
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_gt';


ALTER FUNCTION public.ovtversion_gt(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: FUNCTION ovtversion_gt(version1 ovtversion, version2 ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON FUNCTION ovtversion_gt(version1 ovtversion, version2 ovtversion) IS 'ovtversion greater-than';


--
-- Name: ovtversion_hash(ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_hash(ovtversion) RETURNS integer
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_hash';


ALTER FUNCTION public.ovtversion_hash(ovtversion) OWNER TO mfortune;

--
-- Name: ovtversion_larger(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_larger(version1 ovtversion, version2 ovtversion) RETURNS ovtversion
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_larger';


ALTER FUNCTION public.ovtversion_larger(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: ovtversion_le(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_le(version1 ovtversion, version2 ovtversion) RETURNS boolean
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_le';


ALTER FUNCTION public.ovtversion_le(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: FUNCTION ovtversion_le(version1 ovtversion, version2 ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON FUNCTION ovtversion_le(version1 ovtversion, version2 ovtversion) IS 'ovtversion less-than-or-equal';


--
-- Name: ovtversion_lt(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_lt(version1 ovtversion, version2 ovtversion) RETURNS boolean
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_lt';


ALTER FUNCTION public.ovtversion_lt(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: FUNCTION ovtversion_lt(version1 ovtversion, version2 ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON FUNCTION ovtversion_lt(version1 ovtversion, version2 ovtversion) IS 'ovtversion less-than';


--
-- Name: ovtversion_ne(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_ne(version1 ovtversion, version2 ovtversion) RETURNS boolean
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_ne';


ALTER FUNCTION public.ovtversion_ne(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: FUNCTION ovtversion_ne(version1 ovtversion, version2 ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON FUNCTION ovtversion_ne(version1 ovtversion, version2 ovtversion) IS 'ovtversion not equal';


--
-- Name: ovtversion_smaller(ovtversion, ovtversion); Type: FUNCTION; Schema: public; Owner: mfortune
--

CREATE FUNCTION ovtversion_smaller(version1 ovtversion, version2 ovtversion) RETURNS ovtversion
    LANGUAGE c IMMUTABLE STRICT
    AS '$libdir/ovtversion', 'ovtversion_smaller';


ALTER FUNCTION public.ovtversion_smaller(version1 ovtversion, version2 ovtversion) OWNER TO mfortune;

--
-- Name: >; Type: OPERATOR; Schema: public; Owner: mfortune
--

CREATE OPERATOR > (
    PROCEDURE = ovtversion_gt,
    LEFTARG = ovtversion,
    RIGHTARG = ovtversion,
    COMMUTATOR = <,
    NEGATOR = >=
);


ALTER OPERATOR public.> (ovtversion, ovtversion) OWNER TO mfortune;

--
-- Name: OPERATOR > (ovtversion, ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON OPERATOR > (ovtversion, ovtversion) IS 'ovtversion greater-than';


--
-- Name: max(ovtversion); Type: AGGREGATE; Schema: public; Owner: mfortune
--

CREATE AGGREGATE max(ovtversion) (
    SFUNC = ovtversion_larger,
    STYPE = ovtversion,
    SORTOP = >
);


ALTER AGGREGATE public.max(ovtversion) OWNER TO mfortune;

--
-- Name: <; Type: OPERATOR; Schema: public; Owner: mfortune
--

CREATE OPERATOR < (
    PROCEDURE = ovtversion_lt,
    LEFTARG = ovtversion,
    RIGHTARG = ovtversion,
    COMMUTATOR = >,
    NEGATOR = >=
);


ALTER OPERATOR public.< (ovtversion, ovtversion) OWNER TO mfortune;

--
-- Name: OPERATOR < (ovtversion, ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON OPERATOR < (ovtversion, ovtversion) IS 'ovtversion less-than';


--
-- Name: min(ovtversion); Type: AGGREGATE; Schema: public; Owner: mfortune
--

CREATE AGGREGATE min(ovtversion) (
    SFUNC = ovtversion_smaller,
    STYPE = ovtversion,
    SORTOP = <
);


ALTER AGGREGATE public.min(ovtversion) OWNER TO mfortune;

--
-- Name: <=; Type: OPERATOR; Schema: public; Owner: mfortune
--

CREATE OPERATOR <= (
    PROCEDURE = ovtversion_le,
    LEFTARG = ovtversion,
    RIGHTARG = ovtversion,
    COMMUTATOR = >=,
    NEGATOR = >
);


ALTER OPERATOR public.<= (ovtversion, ovtversion) OWNER TO mfortune;

--
-- Name: OPERATOR <= (ovtversion, ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON OPERATOR <= (ovtversion, ovtversion) IS 'ovtversion less-than-or-equal';


--
-- Name: <>; Type: OPERATOR; Schema: public; Owner: mfortune
--

CREATE OPERATOR <> (
    PROCEDURE = ovtversion_ne,
    LEFTARG = ovtversion,
    RIGHTARG = ovtversion,
    COMMUTATOR = <>,
    NEGATOR = =
);


ALTER OPERATOR public.<> (ovtversion, ovtversion) OWNER TO mfortune;

--
-- Name: OPERATOR <> (ovtversion, ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON OPERATOR <> (ovtversion, ovtversion) IS 'ovtversion not equal';


--
-- Name: =; Type: OPERATOR; Schema: public; Owner: mfortune
--

CREATE OPERATOR = (
    PROCEDURE = ovtversion_eq,
    LEFTARG = ovtversion,
    RIGHTARG = ovtversion,
    COMMUTATOR = =,
    NEGATOR = <>
);


ALTER OPERATOR public.= (ovtversion, ovtversion) OWNER TO mfortune;

--
-- Name: OPERATOR = (ovtversion, ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON OPERATOR = (ovtversion, ovtversion) IS 'ovtversion equal';


--
-- Name: >=; Type: OPERATOR; Schema: public; Owner: mfortune
--

CREATE OPERATOR >= (
    PROCEDURE = ovtversion_ge,
    LEFTARG = ovtversion,
    RIGHTARG = ovtversion,
    COMMUTATOR = <=,
    NEGATOR = <
);


ALTER OPERATOR public.>= (ovtversion, ovtversion) OWNER TO mfortune;

--
-- Name: OPERATOR >= (ovtversion, ovtversion); Type: COMMENT; Schema: public; Owner: mfortune
--

COMMENT ON OPERATOR >= (ovtversion, ovtversion) IS 'ovtversion greater-than-or-equal';


--
-- Name: ovtversion_ops; Type: OPERATOR CLASS; Schema: public; Owner: mfortune
--

CREATE OPERATOR CLASS ovtversion_ops
    DEFAULT FOR TYPE ovtversion USING btree AS
    OPERATOR 1 <(ovtversion,ovtversion) ,
    OPERATOR 2 <=(ovtversion,ovtversion) ,
    OPERATOR 3 =(ovtversion,ovtversion) ,
    OPERATOR 4 >=(ovtversion,ovtversion) ,
    OPERATOR 5 >(ovtversion,ovtversion) ,
    FUNCTION 1 ovtversion_cmp(ovtversion,ovtversion);


ALTER OPERATOR CLASS public.ovtversion_ops USING btree OWNER TO mfortune;

--
-- Name: ovtversion_ops; Type: OPERATOR CLASS; Schema: public; Owner: mfortune
--

CREATE OPERATOR CLASS ovtversion_ops
    DEFAULT FOR TYPE ovtversion USING hash AS
    OPERATOR 1 =(ovtversion,ovtversion) ,
    FUNCTION 1 ovtversion_hash(ovtversion);


ALTER OPERATOR CLASS public.ovtversion_ops USING hash OWNER TO mfortune;

SET search_path = pg_catalog;

--
-- Name: CAST (character AS public.ovtversion); Type: CAST; Schema: pg_catalog; Owner: 
--

CREATE CAST (character AS public.ovtversion) WITH FUNCTION public.ovtversion(character);


--
-- Name: CAST (public.ovtversion AS character); Type: CAST; Schema: pg_catalog; Owner: 
--

CREATE CAST (public.ovtversion AS character) WITHOUT FUNCTION AS ASSIGNMENT;


--
-- Name: CAST (public.ovtversion AS text); Type: CAST; Schema: pg_catalog; Owner: 
--

CREATE CAST (public.ovtversion AS text) WITHOUT FUNCTION AS IMPLICIT;


--
-- Name: CAST (public.ovtversion AS character varying); Type: CAST; Schema: pg_catalog; Owner: 
--

CREATE CAST (public.ovtversion AS character varying) WITHOUT FUNCTION AS IMPLICIT;


--
-- Name: CAST (text AS public.ovtversion); Type: CAST; Schema: pg_catalog; Owner: 
--

CREATE CAST (text AS public.ovtversion) WITHOUT FUNCTION AS ASSIGNMENT;


--
-- Name: CAST (character varying AS public.ovtversion); Type: CAST; Schema: pg_catalog; Owner: 
--

CREATE CAST (character varying AS public.ovtversion) WITHOUT FUNCTION AS ASSIGNMENT;


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: ovt_action; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_action (
    actionid integer NOT NULL,
    actionname character varying(255) NOT NULL,
    shortname character varying(255),
    actioncategoryid integer NOT NULL,
    testsuiteid integer,
    issecure boolean DEFAULT false NOT NULL,
    lifecyclestateid integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.ovt_action OWNER TO overtest;

--
-- Name: TABLE ovt_action; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_action IS 'A general description of an action to be executed. This is only useful when associated with some version information as versions of actions are expected to change in a variety of ways.';


--
-- Name: COLUMN ovt_action.actioncategoryid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_action.actioncategoryid IS 'Logical grouping for search purposes';


--
-- Name: COLUMN ovt_action.testsuiteid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_action.testsuiteid IS 'The testsuite for tests run by this action';


--
-- Name: COLUMN ovt_action.issecure; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_action.issecure IS 'Set when the action deals with restricted information that must not be copied off the execution host ';


--
-- Name: COLUMN ovt_action.lifecyclestateid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_action.lifecyclestateid IS 'The current state of the action.';


--
-- Name: ovt_action_actionid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_action_actionid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_action_actionid_seq OWNER TO overtest;

--
-- Name: ovt_action_actionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_action_actionid_seq OWNED BY ovt_action.actionid;


--
-- Name: ovt_actioncategory; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_actioncategory (
    actioncategoryid integer NOT NULL,
    actioncategoryname character varying(50) NOT NULL,
    lifecyclestateid integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.ovt_actioncategory OWNER TO overtest;

--
-- Name: TABLE ovt_actioncategory; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_actioncategory IS 'Actions need to be categorised, purely for making searching easier';


--
-- Name: COLUMN ovt_actioncategory.lifecyclestateid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_actioncategory.lifecyclestateid IS 'Represents the current state of a category.';


--
-- Name: ovt_actioncategory_actioncategoryid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_actioncategory_actioncategoryid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_actioncategory_actioncategoryid_seq OWNER TO overtest;

--
-- Name: ovt_actioncategory_actioncategoryid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_actioncategory_actioncategoryid_seq OWNED BY ovt_actioncategory.actioncategoryid;


--
-- Name: ovt_attribute; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_attribute (
    attributeid integer NOT NULL,
    attributename character varying(255) NOT NULL,
    lookup boolean DEFAULT false NOT NULL,
    resourcetypeid integer NOT NULL
);


ALTER TABLE public.ovt_attribute OWNER TO overtest;

--
-- Name: TABLE ovt_attribute; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_attribute IS 'Attributes of resources';


--
-- Name: COLUMN ovt_attribute.lookup; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_attribute.lookup IS 'Whether the attribute has a restricted value list';


--
-- Name: COLUMN ovt_attribute.resourcetypeid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_attribute.resourcetypeid IS 'The group associated with this attribute';


--
-- Name: ovt_attribute_attributeid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_attribute_attributeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_attribute_attributeid_seq OWNER TO overtest;

--
-- Name: ovt_attribute_attributeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_attribute_attributeid_seq OWNED BY ovt_attribute.attributeid;


--
-- Name: ovt_attributevalue; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_attributevalue (
    attributevalueid integer NOT NULL,
    attributeid integer NOT NULL,
    value character varying(255) NOT NULL,
    mustrequest boolean DEFAULT false NOT NULL
);


ALTER TABLE public.ovt_attributevalue OWNER TO overtest;

--
-- Name: TABLE ovt_attributevalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_attributevalue IS 'A restricted set of values for an attribute';


--
-- Name: COLUMN ovt_attributevalue.mustrequest; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_attributevalue.mustrequest IS 'Resources with a mustrequest attribute value will not be allocated unless the value is explicitly requested by a test.';


--
-- Name: ovt_attributevalue_attributevalueid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_attributevalue_attributevalueid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_attributevalue_attributevalueid_seq OWNER TO overtest;

--
-- Name: ovt_attributevalue_attributevalueid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_attributevalue_attributevalueid_seq OWNED BY ovt_attributevalue.attributevalueid;


--
-- Name: ovt_chart; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_chart (
    chartid integer NOT NULL,
    userid integer NOT NULL,
    public boolean DEFAULT false NOT NULL,
    testsuiteid integer NOT NULL,
    search text NOT NULL,
    testrunidentifier text DEFAULT '%[testrunid]%'::text NOT NULL,
    title text NOT NULL,
    charttypeid integer NOT NULL
);


ALTER TABLE public.ovt_chart OWNER TO overtest;

--
-- Name: TABLE ovt_chart; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_chart IS 'Represents charts for testsuite results';


--
-- Name: COLUMN ovt_chart.userid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chart.userid IS 'Owner of the chart';


--
-- Name: COLUMN ovt_chart.public; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chart.public IS 'Whether this chart should be available to all';


--
-- Name: COLUMN ovt_chart.testsuiteid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chart.testsuiteid IS 'The testsuite this chart applies to';


--
-- Name: COLUMN ovt_chart.search; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chart.search IS 'The search query to find results';


--
-- Name: COLUMN ovt_chart.testrunidentifier; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chart.testrunidentifier IS 'The description of each set of results (template)';


--
-- Name: COLUMN ovt_chart.title; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chart.title IS 'The title for a chart';


--
-- Name: COLUMN ovt_chart.charttypeid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chart.charttypeid IS 'The type of chart';


--
-- Name: ovt_chart_chartid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_chart_chartid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_chart_chartid_seq OWNER TO overtest;

--
-- Name: ovt_chart_chartid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_chart_chartid_seq OWNED BY ovt_chart.chartid;


--
-- Name: ovt_chartfield; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_chartfield (
    chartfieldid integer NOT NULL,
    chartid integer NOT NULL,
    resultfieldid integer NOT NULL
);


ALTER TABLE public.ovt_chartfield OWNER TO overtest;

--
-- Name: TABLE ovt_chartfield; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_chartfield IS 'Links a chart to the fields that should be shown';


--
-- Name: COLUMN ovt_chartfield.chartid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chartfield.chartid IS 'The chart';


--
-- Name: COLUMN ovt_chartfield.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_chartfield.resultfieldid IS 'The result field';


--
-- Name: ovt_chartfield_chartfieldid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_chartfield_chartfieldid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_chartfield_chartfieldid_seq OWNER TO overtest;

--
-- Name: ovt_chartfield_chartfieldid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_chartfield_chartfieldid_seq OWNED BY ovt_chartfield.chartfieldid;


--
-- Name: ovt_charttest; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_charttest (
    charttestid integer NOT NULL,
    chartid integer NOT NULL,
    testid integer NOT NULL
);


ALTER TABLE public.ovt_charttest OWNER TO overtest;

--
-- Name: TABLE ovt_charttest; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_charttest IS 'Links a chart to the tests which should be shown';


--
-- Name: COLUMN ovt_charttest.chartid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_charttest.chartid IS 'The chart';


--
-- Name: COLUMN ovt_charttest.testid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_charttest.testid IS 'The test';


--
-- Name: ovt_charttest_charttestid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_charttest_charttestid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_charttest_charttestid_seq OWNER TO overtest;

--
-- Name: ovt_charttest_charttestid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_charttest_charttestid_seq OWNED BY ovt_charttest.charttestid;


--
-- Name: ovt_charttype; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_charttype (
    charttypeid integer NOT NULL,
    charttypename character varying(255) NOT NULL,
    chartmodule character varying(255) NOT NULL,
    numfields integer,
    numtests integer
);


ALTER TABLE public.ovt_charttype OWNER TO overtest;

--
-- Name: TABLE ovt_charttype; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_charttype IS 'Represents a generic chart';


--
-- Name: COLUMN ovt_charttype.charttypename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_charttype.charttypename IS 'Name of the chart';


--
-- Name: COLUMN ovt_charttype.chartmodule; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_charttype.chartmodule IS 'The module used to implement the chart';


--
-- Name: COLUMN ovt_charttype.numfields; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_charttype.numfields IS 'The number of fields supported. If non-zero then at least one must be specified. If null 0 or more are supported';


--
-- Name: COLUMN ovt_charttype.numtests; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_charttype.numtests IS 'The number of tests supported. If non-zero then at least one must be specified. If null 0 or more are supported';


--
-- Name: ovt_charttype_charttypeid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_charttype_charttypeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_charttype_charttypeid_seq OWNER TO overtest;

--
-- Name: ovt_charttype_charttypeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_charttype_charttypeid_seq OWNED BY ovt_charttype.charttypeid;


--
-- Name: ovt_configoption; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_configoption (
    configoptionid integer NOT NULL,
    configoptionname character varying(100) NOT NULL,
    islookup boolean NOT NULL,
    defaultvalue character varying(255),
    configoptiontypeid integer NOT NULL,
    configoptiongroupid integer NOT NULL,
    ordering integer NOT NULL,
    affects_equivalence boolean DEFAULT true NOT NULL
);


ALTER TABLE public.ovt_configoption OWNER TO overtest;

--
-- Name: TABLE ovt_configoption; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_configoption IS 'A configuration option that can be used for multiple versions of actions as well as between different actions.';


--
-- Name: COLUMN ovt_configoption.configoptionname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoption.configoptionname IS 'The name of the configuration option as referred to in scripts';


--
-- Name: COLUMN ovt_configoption.islookup; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoption.islookup IS 'Set when the option has a series of set values';


--
-- Name: COLUMN ovt_configoption.defaultvalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoption.defaultvalue IS 'The standard value (used when not set, unless islookup is set)';


--
-- Name: COLUMN ovt_configoption.configoptiontypeid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoption.configoptiontypeid IS 'The type of option';


--
-- Name: COLUMN ovt_configoption.affects_equivalence; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoption.affects_equivalence IS 'Set when the option affects the outcome of an equivalence';


--
-- Name: ovt_configoption_configoptionid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_configoption_configoptionid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_configoption_configoptionid_seq OWNER TO overtest;

--
-- Name: ovt_configoption_configoptionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_configoption_configoptionid_seq OWNED BY ovt_configoption.configoptionid;


--
-- Name: ovt_configoptiongroup; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_configoptiongroup (
    configoptiongroupid integer NOT NULL,
    configoptiongroupname character varying NOT NULL,
    ordering integer,
    automatic boolean DEFAULT false NOT NULL
);


ALTER TABLE public.ovt_configoptiongroup OWNER TO overtest;

--
-- Name: TABLE ovt_configoptiongroup; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_configoptiongroup IS 'A group of related configuration options';


--
-- Name: ovt_configoptiongroup_configoptiongroupid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_configoptiongroup_configoptiongroupid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_configoptiongroup_configoptiongroupid_seq OWNER TO overtest;

--
-- Name: ovt_configoptiongroup_configoptiongroupid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_configoptiongroup_configoptiongroupid_seq OWNED BY ovt_configoptiongroup.configoptiongroupid;


--
-- Name: ovt_configoptionlookup; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_configoptionlookup (
    configoptionlookupid integer NOT NULL,
    configoptionid integer NOT NULL,
    lookupname character varying(50) NOT NULL,
    lookupvalue character varying(255) NOT NULL,
    defaultlookup boolean DEFAULT false NOT NULL
);


ALTER TABLE public.ovt_configoptionlookup OWNER TO overtest;

--
-- Name: TABLE ovt_configoptionlookup; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_configoptionlookup IS 'Represents a distinct set of values for a given configuration option';


--
-- Name: COLUMN ovt_configoptionlookup.configoptionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoptionlookup.configoptionid IS 'The related configutation option';


--
-- Name: COLUMN ovt_configoptionlookup.lookupname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoptionlookup.lookupname IS 'A descriptive name for this lookup';


--
-- Name: COLUMN ovt_configoptionlookup.lookupvalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoptionlookup.lookupvalue IS 'The value to use when selected. This should not be changed after creation though it will not break equivalences if it is.';


--
-- Name: COLUMN ovt_configoptionlookup.defaultlookup; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoptionlookup.defaultlookup IS 'Set when this option is the default';


--
-- Name: ovt_configoptionlookup_configoptionlookupid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_configoptionlookup_configoptionlookupid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_configoptionlookup_configoptionlookupid_seq OWNER TO overtest;

--
-- Name: ovt_configoptionlookup_configoptionlookupid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_configoptionlookup_configoptionlookupid_seq OWNED BY ovt_configoptionlookup.configoptionlookupid;


--
-- Name: ovt_configoptionlookupattributevalue; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_configoptionlookupattributevalue (
    configoptionlookupattributevalueid integer NOT NULL,
    configoptionlookupid integer NOT NULL,
    attributevalueid integer NOT NULL
);


ALTER TABLE public.ovt_configoptionlookupattributevalue OWNER TO overtest;

--
-- Name: TABLE ovt_configoptionlookupattributevalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_configoptionlookupattributevalue IS 'Links configuration lookup values with additional resource requirements to give dynamic control over resources for a single versionedaction.

Such resource requirements only add to existing requirements on linked versionedactions requiring the same resource type.';


--
-- Name: COLUMN ovt_configoptionlookupattributevalue.configoptionlookupid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoptionlookupattributevalue.configoptionlookupid IS 'The lookup value';


--
-- Name: COLUMN ovt_configoptionlookupattributevalue.attributevalueid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoptionlookupattributevalue.attributevalueid IS 'The resource requirement';


--
-- Name: ovt_configoptionlookupattribu_configoptionlookupattributeva_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_configoptionlookupattribu_configoptionlookupattributeva_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_configoptionlookupattribu_configoptionlookupattributeva_seq OWNER TO overtest;

--
-- Name: ovt_configoptionlookupattribu_configoptionlookupattributeva_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_configoptionlookupattribu_configoptionlookupattributeva_seq OWNED BY ovt_configoptionlookupattributevalue.configoptionlookupattributevalueid;


--
-- Name: ovt_configoptiontype; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_configoptiontype (
    configoptiontypeid integer NOT NULL,
    configoptiontypename character varying(50) NOT NULL
);


ALTER TABLE public.ovt_configoptiontype OWNER TO overtest;

--
-- Name: TABLE ovt_configoptiontype; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_configoptiontype IS 'Configuration options may need to be grouped if an action requires configuration for different aspects';


--
-- Name: COLUMN ovt_configoptiontype.configoptiontypename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configoptiontype.configoptiontypename IS 'A description of a group of related options';


--
-- Name: ovt_configoptiontype_configoptiontypeid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_configoptiontype_configoptiontypeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_configoptiontype_configoptiontypeid_seq OWNER TO overtest;

--
-- Name: ovt_configoptiontype_configoptiontypeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_configoptiontype_configoptiontypeid_seq OWNED BY ovt_configoptiontype.configoptiontypeid;


--
-- Name: ovt_configsetting; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_configsetting (
    configsettingid integer NOT NULL,
    configoptionid integer NOT NULL,
    configoptionlookupid integer,
    configvalue character varying(255),
    testrunid integer NOT NULL,
    CONSTRAINT ovt_configsetting_nonnull CHECK ((((configvalue IS NULL) AND (configoptionlookupid IS NOT NULL)) OR ((configvalue IS NOT NULL) AND (configoptionlookupid IS NULL))))
);


ALTER TABLE public.ovt_configsetting OWNER TO overtest;

--
-- Name: TABLE ovt_configsetting; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_configsetting IS 'Represents the group of configuration settings for a particular run of an action';


--
-- Name: COLUMN ovt_configsetting.configoptionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configsetting.configoptionid IS 'The option being set';


--
-- Name: COLUMN ovt_configsetting.configoptionlookupid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configsetting.configoptionlookupid IS 'The lookup option (for lookup options)';


--
-- Name: COLUMN ovt_configsetting.configvalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configsetting.configvalue IS 'The setting';


--
-- Name: COLUMN ovt_configsetting.testrunid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_configsetting.testrunid IS 'The testrun this setting applies to';


--
-- Name: ovt_configsetting_configsettingid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_configsetting_configsettingid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_configsetting_configsettingid_seq OWNER TO overtest;

--
-- Name: ovt_configsetting_configsettingid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_configsetting_configsettingid_seq OWNED BY ovt_configsetting.configsettingid;


--
-- Name: ovt_dependency; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_dependency (
    dependencyid integer NOT NULL,
    versionedactionid integer NOT NULL,
    versionedactiondep integer NOT NULL,
    dependencygroupid integer,
    versiononly boolean DEFAULT false NOT NULL,
    hostmatch boolean DEFAULT false NOT NULL,
    defaultdep boolean DEFAULT false NOT NULL
);


ALTER TABLE public.ovt_dependency OWNER TO overtest;

--
-- Name: TABLE ovt_dependency; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_dependency IS 'Describes dependency information between versioned actions. Dependencies are allowed to be within a range of versions';


--
-- Name: COLUMN ovt_dependency.versionedactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_dependency.versionedactionid IS 'The versioned action that holds this dependency';


--
-- Name: COLUMN ovt_dependency.versionedactiondep; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_dependency.versionedactiondep IS 'The versioned action that is the minimum version of the dependency';


--
-- Name: COLUMN ovt_dependency.dependencygroupid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_dependency.dependencygroupid IS 'The dependency group for this dependency';


--
-- Name: COLUMN ovt_dependency.versiononly; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_dependency.versiononly IS 'Set when this dependency describes a version realtion only. The related action is not ''run''';


--
-- Name: COLUMN ovt_dependency.hostmatch; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_dependency.hostmatch IS 'Does this dependency require the consumer to run on the same host as the producer';


--
-- Name: ovt_dependency_dependencyid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_dependency_dependencyid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_dependency_dependencyid_seq OWNER TO overtest;

--
-- Name: ovt_dependency_dependencyid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_dependency_dependencyid_seq OWNED BY ovt_dependency.dependencyid;


--
-- Name: ovt_dependencygroup; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_dependencygroup (
    dependencygroupid integer NOT NULL,
    dependencygroupname character varying(50) NOT NULL
);


ALTER TABLE public.ovt_dependencygroup OWNER TO overtest;

--
-- Name: TABLE ovt_dependencygroup; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_dependencygroup IS 'Dependency groups provide a means to have a versionedaction dependent on any one of a group of dependencies. Only one of which has to be fulfilled.';


--
-- Name: COLUMN ovt_dependencygroup.dependencygroupname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_dependencygroup.dependencygroupname IS 'The name for a group of dependencies';


--
-- Name: ovt_dependencygroup_dependencygroupid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_dependencygroup_dependencygroupid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_dependencygroup_dependencygroupid_seq OWNER TO overtest;

--
-- Name: ovt_dependencygroup_dependencygroupid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_dependencygroup_dependencygroupid_seq OWNED BY ovt_dependencygroup.dependencygroupid;


--
-- Name: ovt_goldresult; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_goldresult (
    goldresultid integer NOT NULL,
    actionid integer NOT NULL,
    testrunid integer NOT NULL,
    userid integer NOT NULL,
    goldendate timestamp with time zone DEFAULT now() NOT NULL,
    irrelevant boolean DEFAULT false NOT NULL,
    irrelevantdate timestamp with time zone NOT NULL
);


ALTER TABLE public.ovt_goldresult OWNER TO overtest;

--
-- Name: TABLE ovt_goldresult; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_goldresult IS 'Used to track which testruns have gold results and which action''s results are considered golden';


--
-- Name: COLUMN ovt_goldresult.actionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_goldresult.actionid IS 'The testsuite with golden results';


--
-- Name: COLUMN ovt_goldresult.testrunid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_goldresult.testrunid IS 'The testrun with gold results';


--
-- Name: COLUMN ovt_goldresult.userid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_goldresult.userid IS 'The user who considers these results golden';


--
-- Name: COLUMN ovt_goldresult.goldendate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_goldresult.goldendate IS 'When the gold results were marked';


--
-- Name: COLUMN ovt_goldresult.irrelevant; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_goldresult.irrelevant IS 'Eventually some gold results may not matter';


--
-- Name: COLUMN ovt_goldresult.irrelevantdate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_goldresult.irrelevantdate IS 'When the gold results became irrelevant';


--
-- Name: ovt_goldresult_goldresultid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_goldresult_goldresultid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_goldresult_goldresultid_seq OWNER TO overtest;

--
-- Name: ovt_goldresult_goldresultid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_goldresult_goldresultid_seq OWNED BY ovt_goldresult.goldresultid;


--
-- Name: ovt_history; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_history (
    historyid integer NOT NULL,
    userid integer,
    notifytypeid integer NOT NULL,
    updateid integer,
    fromvalue text,
    tovalue text,
    notificationsent boolean DEFAULT false NOT NULL,
    eventdate timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ovt_history OWNER TO overtest;

--
-- Name: TABLE ovt_history; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_history IS 'A log of all activity in the database.';


--
-- Name: COLUMN ovt_history.userid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_history.userid IS 'The user who made the change';


--
-- Name: COLUMN ovt_history.notifytypeid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_history.notifytypeid IS 'The type of notification';


--
-- Name: COLUMN ovt_history.updateid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_history.updateid IS 'Any useful id relating to the update';


--
-- Name: COLUMN ovt_history.fromvalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_history.fromvalue IS 'The previous state';


--
-- Name: COLUMN ovt_history.tovalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_history.tovalue IS 'The new state';


--
-- Name: COLUMN ovt_history.notificationsent; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_history.notificationsent IS 'True when the information has been sent';


--
-- Name: COLUMN ovt_history.eventdate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_history.eventdate IS 'When did this happen';


--
-- Name: ovt_history_historyid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_history_historyid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_history_historyid_seq OWNER TO overtest;

--
-- Name: ovt_history_historyid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_history_historyid_seq OWNED BY ovt_history.historyid;


--
-- Name: ovt_historypk; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_historypk (
    historypkid integer NOT NULL,
    historyid integer NOT NULL,
    notifyentityid integer NOT NULL,
    pkid integer NOT NULL
);


ALTER TABLE public.ovt_historypk OWNER TO overtest;

--
-- Name: TABLE ovt_historypk; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_historypk IS 'Link history entries to (potentially non-existent) primary keys for various entities. This allows a ''deleted'' message about one entity to still be related to a parent entity even though the only link between them has actually been deleted.';


--
-- Name: COLUMN ovt_historypk.historyid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_historypk.historyid IS 'The history entry this info relates to';


--
-- Name: COLUMN ovt_historypk.notifyentityid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_historypk.notifyentityid IS 'The entity class this info relates to';


--
-- Name: COLUMN ovt_historypk.pkid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_historypk.pkid IS 'An untyped reference to primary keys of various entities. Type is inferred';


--
-- Name: ovt_historypk_historypkid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_historypk_historypkid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_historypk_historypkid_seq OWNER TO overtest;

--
-- Name: ovt_historypk_historypkid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_historypk_historypkid_seq OWNED BY ovt_historypk.historypkid;


--
-- Name: ovt_lifecyclestate; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_lifecyclestate (
    lifecyclestateid integer NOT NULL,
    lifecyclestatename character varying(255) NOT NULL,
    visible boolean DEFAULT true NOT NULL,
    visiblebydefault boolean DEFAULT true NOT NULL,
    valid boolean DEFAULT true NOT NULL
);


ALTER TABLE public.ovt_lifecyclestate OWNER TO overtest;

--
-- Name: TABLE ovt_lifecyclestate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_lifecyclestate IS 'Represents the current state of a category, action or version.';


--
-- Name: COLUMN ovt_lifecyclestate.lifecyclestatename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_lifecyclestate.lifecyclestatename IS 'A human readable name for the state';


--
-- Name: COLUMN ovt_lifecyclestate.visible; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_lifecyclestate.visible IS 'Should the row ever be shown';


--
-- Name: COLUMN ovt_lifecyclestate.visiblebydefault; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_lifecyclestate.visiblebydefault IS 'Should the row be shown as standard';


--
-- Name: COLUMN ovt_lifecyclestate.valid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_lifecyclestate.valid IS 'General state to represent if the relevant row can be used. Exact meaning may vary on a per table basis.';


--
-- Name: ovt_lifecyclestate_lifecyclestateid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_lifecyclestate_lifecyclestateid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_lifecyclestate_lifecyclestateid_seq OWNER TO overtest;

--
-- Name: ovt_lifecyclestate_lifecyclestateid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_lifecyclestate_lifecyclestateid_seq OWNED BY ovt_lifecyclestate.lifecyclestateid;


--
-- Name: ovt_notifyentity; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_notifyentity (
    notifyentityid integer NOT NULL,
    notifyentityname character varying(255) NOT NULL
);


ALTER TABLE public.ovt_notifyentity OWNER TO overtest;

--
-- Name: TABLE ovt_notifyentity; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_notifyentity IS 'Notify types relate to classes of overtest entity. History entries then relate to a specific set of entities.';


--
-- Name: COLUMN ovt_notifyentity.notifyentityname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_notifyentity.notifyentityname IS 'The class of entity';


--
-- Name: ovt_notifyentity_notifyentityid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_notifyentity_notifyentityid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_notifyentity_notifyentityid_seq OWNER TO overtest;

--
-- Name: ovt_notifyentity_notifyentityid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_notifyentity_notifyentityid_seq OWNED BY ovt_notifyentity.notifyentityid;


--
-- Name: ovt_notifymethod; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_notifymethod (
    notifymethodid integer NOT NULL,
    notifymethodname character varying(255) NOT NULL
);


ALTER TABLE public.ovt_notifymethod OWNER TO overtest;

--
-- Name: TABLE ovt_notifymethod; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_notifymethod IS 'The various ways in which a notification can be sent';


--
-- Name: COLUMN ovt_notifymethod.notifymethodname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_notifymethod.notifymethodname IS 'A description of the notification method';


--
-- Name: ovt_notifymethod_notifymethodid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_notifymethod_notifymethodid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_notifymethod_notifymethodid_seq OWNER TO overtest;

--
-- Name: ovt_notifymethod_notifymethodid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_notifymethod_notifymethodid_seq OWNED BY ovt_notifymethod.notifymethodid;


--
-- Name: ovt_notifytype; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_notifytype (
    notifytypeid integer NOT NULL,
    notifytypename character varying(255) NOT NULL,
    emailtemplate text NOT NULL,
    growltemplate text NOT NULL,
    growltitletemplate text NOT NULL
);


ALTER TABLE public.ovt_notifytype OWNER TO overtest;

--
-- Name: TABLE ovt_notifytype; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_notifytype IS 'Notify types describe how a history log entry should be interpreted';


--
-- Name: COLUMN ovt_notifytype.notifytypename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_notifytype.notifytypename IS 'A short description of the notification';


--
-- Name: COLUMN ovt_notifytype.emailtemplate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_notifytype.emailtemplate IS 'A template to describe this type of notification in an email';


--
-- Name: COLUMN ovt_notifytype.growltemplate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_notifytype.growltemplate IS 'A template to describe this type of notification suitabel for a growl message';


--
-- Name: COLUMN ovt_notifytype.growltitletemplate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_notifytype.growltitletemplate IS 'A template for a type of notification suitable for the title of a growl message';


--
-- Name: ovt_notifytype_notifytypeid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_notifytype_notifytypeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_notifytype_notifytypeid_seq OWNER TO overtest;

--
-- Name: ovt_notifytype_notifytypeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_notifytype_notifytypeid_seq OWNED BY ovt_notifytype.notifytypeid;


--
-- Name: ovt_notifytypeentity; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_notifytypeentity (
    notifytypeid integer NOT NULL,
    notifyentityid integer NOT NULL
);


ALTER TABLE public.ovt_notifytypeentity OWNER TO overtest;

--
-- Name: TABLE ovt_notifytypeentity; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_notifytypeentity IS 'Links notify types and entities (many to many)';


--
-- Name: ovt_recursiveequivalence; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_recursiveequivalence (
    recursiveequivalenceid integer NOT NULL,
    recursiveequivalencename character varying(255)
);


ALTER TABLE public.ovt_recursiveequivalence OWNER TO overtest;

--
-- Name: TABLE ovt_recursiveequivalence; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_recursiveequivalence IS 'A small table for referring to recursive equivalences by name and also providing something to lock when generating equivalences';


--
-- Name: COLUMN ovt_recursiveequivalence.recursiveequivalencename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_recursiveequivalence.recursiveequivalencename IS 'A name for referring to the equivalence';


--
-- Name: ovt_recursiveequivalence_recursiveequivalenceid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_recursiveequivalence_recursiveequivalenceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_recursiveequivalence_recursiveequivalenceid_seq OWNER TO overtest;

--
-- Name: ovt_recursiveequivalence_recursiveequivalenceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_recursiveequivalence_recursiveequivalenceid_seq OWNED BY ovt_recursiveequivalence.recursiveequivalenceid;


--
-- Name: ovt_resource; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resource (
    resourceid integer NOT NULL,
    resourcename character varying(50) NOT NULL,
    concurrency integer DEFAULT 1 NOT NULL,
    hostname character varying(255),
    extradata text,
    claimed boolean DEFAULT false NOT NULL,
    not_used integer,
    resourcestatusid integer DEFAULT 3 NOT NULL,
    linkedresourcegroupid integer,
    nouserqueue boolean DEFAULT false NOT NULL,
    baseresourceid integer,
    resourcetypeid integer NOT NULL
);


ALTER TABLE public.ovt_resource OWNER TO overtest;

--
-- Name: TABLE ovt_resource; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resource IS 'A specific resource of a particular type';


--
-- Name: COLUMN ovt_resource.resourcename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.resourcename IS 'The name of the resource';


--
-- Name: COLUMN ovt_resource.concurrency; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.concurrency IS 'How many things can use the resource (only valid for execution hosts currently)';


--
-- Name: COLUMN ovt_resource.extradata; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.extradata IS 'Any extra data the resource needs to store about itself. This may change over time automatically.';


--
-- Name: COLUMN ovt_resource.claimed; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.claimed IS 'If the resource is manually claimed it cannot be used by overtest';


--
-- Name: COLUMN ovt_resource.not_used; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.not_used IS 'n/a';


--
-- Name: COLUMN ovt_resource.resourcestatusid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.resourcestatusid IS 'Resource status 3 is always DISABLED';


--
-- Name: COLUMN ovt_resource.linkedresourcegroupid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.linkedresourcegroupid IS 'If this resource is linked to any others then create a linked resourcegroup for it';


--
-- Name: COLUMN ovt_resource.baseresourceid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.baseresourceid IS 'Link to the parent resource';


--
-- Name: COLUMN ovt_resource.resourcetypeid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resource.resourcetypeid IS 'Type of resource';


--
-- Name: ovt_resource_linkedresourcegroupid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resource_linkedresourcegroupid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resource_linkedresourcegroupid_seq OWNER TO overtest;

--
-- Name: ovt_resource_resourceid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resource_resourceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resource_resourceid_seq OWNER TO overtest;

--
-- Name: ovt_resource_resourceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resource_resourceid_seq OWNED BY ovt_resource.resourceid;


--
-- Name: ovt_resourceattribute; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resourceattribute (
    resourceattributeid integer NOT NULL,
    resourceid integer NOT NULL,
    attributeid integer NOT NULL,
    value character varying(255),
    attributevalueid integer,
    CONSTRAINT ovt_resourceattribute_nullcheck CHECK ((((value IS NULL) AND (attributevalueid IS NOT NULL)) OR ((value IS NOT NULL) AND (attributevalueid IS NULL))))
);


ALTER TABLE public.ovt_resourceattribute OWNER TO overtest;

--
-- Name: TABLE ovt_resourceattribute; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resourceattribute IS 'Attribute information per resource';


--
-- Name: COLUMN ovt_resourceattribute.value; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resourceattribute.value IS 'The attribute value for non lookup attributes';


--
-- Name: COLUMN ovt_resourceattribute.attributevalueid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resourceattribute.attributevalueid IS 'The attribute value for lookup attributes';


--
-- Name: ovt_resourceattribute_resourceattributeid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resourceattribute_resourceattributeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resourceattribute_resourceattributeid_seq OWNER TO overtest;

--
-- Name: ovt_resourceattribute_resourceattributeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resourceattribute_resourceattributeid_seq OWNED BY ovt_resourceattribute.resourceattributeid;


--
-- Name: ovt_resourcelog; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resourcelog (
    resourcelogid integer NOT NULL,
    resourceid integer NOT NULL,
    index integer,
    message text NOT NULL,
    entrydate timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ovt_resourcelog OWNER TO overtest;

--
-- Name: TABLE ovt_resourcelog; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resourcelog IS 'Provides a log for any resource.';


--
-- Name: COLUMN ovt_resourcelog.resourceid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resourcelog.resourceid IS 'The resource relating to the message';


--
-- Name: COLUMN ovt_resourcelog.index; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resourcelog.index IS 'The resource index (when resource can have concurrency)';


--
-- Name: COLUMN ovt_resourcelog.message; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resourcelog.message IS 'Any information';


--
-- Name: ovt_resourcelog_resourcelogid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resourcelog_resourcelogid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resourcelog_resourcelogid_seq OWNER TO overtest;

--
-- Name: ovt_resourcelog_resourcelogid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resourcelog_resourcelogid_seq OWNED BY ovt_resourcelog.resourcelogid;


--
-- Name: ovt_resourcestatus; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resourcestatus (
    resourcestatusid integer NOT NULL,
    status character varying(50) NOT NULL
);


ALTER TABLE public.ovt_resourcestatus OWNER TO overtest;

--
-- Name: TABLE ovt_resourcestatus; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resourcestatus IS 'The various states resources can be in';


--
-- Name: COLUMN ovt_resourcestatus.status; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resourcestatus.status IS 'text description of state';


--
-- Name: ovt_resourcestatus_resourcestatusid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resourcestatus_resourcestatusid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resourcestatus_resourcestatusid_seq OWNER TO overtest;

--
-- Name: ovt_resourcestatus_resourcestatusid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resourcestatus_resourcestatusid_seq OWNED BY ovt_resourcestatus.resourcestatusid;


--
-- Name: ovt_resourcetype; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resourcetype (
    resourcetypeid integer NOT NULL,
    resourcetypename character varying(255)
);


ALTER TABLE public.ovt_resourcetype OWNER TO overtest;

--
-- Name: TABLE ovt_resourcetype; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resourcetype IS 'Logical groupings of resources and attributes. These serve to allow multiple attributes to be considered when selecting resources.';


--
-- Name: ovt_resourcetype_resourcetypeid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resourcetype_resourcetypeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resourcetype_resourcetypeid_seq OWNER TO overtest;

--
-- Name: ovt_resourcetype_resourcetypeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resourcetype_resourcetypeid_seq OWNED BY ovt_resourcetype.resourcetypeid;


--
-- Name: ovt_resultboolean; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resultboolean (
    resultbooleanid integer NOT NULL,
    testrunactionid integer NOT NULL,
    resultfieldid integer NOT NULL,
    resultboolean boolean NOT NULL
);


ALTER TABLE public.ovt_resultboolean OWNER TO overtest;

--
-- Name: TABLE ovt_resultboolean; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resultboolean IS 'A boolean result field for extended result data';


--
-- Name: COLUMN ovt_resultboolean.testrunactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultboolean.testrunactionid IS 'The testrunaction associated with this result';


--
-- Name: COLUMN ovt_resultboolean.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultboolean.resultfieldid IS 'The field this result is for';


--
-- Name: COLUMN ovt_resultboolean.resultboolean; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultboolean.resultboolean IS 'The value';


--
-- Name: ovt_resultboolean_resultbooleanid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resultboolean_resultbooleanid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resultboolean_resultbooleanid_seq OWNER TO overtest;

--
-- Name: ovt_resultboolean_resultbooleanid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resultboolean_resultbooleanid_seq OWNED BY ovt_resultboolean.resultbooleanid;


--
-- Name: ovt_resultfield; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resultfield (
    resultfieldid integer NOT NULL,
    resultfieldname character varying NOT NULL,
    resulttypeid integer NOT NULL,
    ordering integer
);


ALTER TABLE public.ovt_resultfield OWNER TO overtest;

--
-- Name: TABLE ovt_resultfield; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resultfield IS 'Represents any test result that is not simple';


--
-- Name: COLUMN ovt_resultfield.resultfieldname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultfield.resultfieldname IS 'A fieldname for a non simple result';


--
-- Name: COLUMN ovt_resultfield.resulttypeid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultfield.resulttypeid IS 'The type of extended result';


--
-- Name: ovt_resultfield_resultfieldid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resultfield_resultfieldid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resultfield_resultfieldid_seq OWNER TO overtest;

--
-- Name: ovt_resultfield_resultfieldid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resultfield_resultfieldid_seq OWNED BY ovt_resultfield.resultfieldid;


--
-- Name: ovt_resultfloat; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resultfloat (
    resultfloatid integer NOT NULL,
    testrunactionid integer NOT NULL,
    resultfieldid integer NOT NULL,
    resultfloat double precision NOT NULL
);


ALTER TABLE public.ovt_resultfloat OWNER TO overtest;

--
-- Name: TABLE ovt_resultfloat; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resultfloat IS 'An float result field for extended result data';


--
-- Name: COLUMN ovt_resultfloat.testrunactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultfloat.testrunactionid IS 'The test this result is associated with';


--
-- Name: COLUMN ovt_resultfloat.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultfloat.resultfieldid IS 'The field this result is for';


--
-- Name: COLUMN ovt_resultfloat.resultfloat; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultfloat.resultfloat IS 'The value';


--
-- Name: ovt_resultfloat_resultfloatid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resultfloat_resultfloatid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resultfloat_resultfloatid_seq OWNER TO overtest;

--
-- Name: ovt_resultfloat_resultfloatid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resultfloat_resultfloatid_seq OWNED BY ovt_resultfloat.resultfloatid;


--
-- Name: ovt_resultinteger; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resultinteger (
    resultintegerid integer NOT NULL,
    testrunactionid integer NOT NULL,
    resultfieldid integer NOT NULL,
    resultinteger bigint NOT NULL
);


ALTER TABLE public.ovt_resultinteger OWNER TO overtest;

--
-- Name: TABLE ovt_resultinteger; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resultinteger IS 'An integer result field for extended result data';


--
-- Name: COLUMN ovt_resultinteger.testrunactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultinteger.testrunactionid IS 'The testrunaction associated with this result';


--
-- Name: COLUMN ovt_resultinteger.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultinteger.resultfieldid IS 'The field this result is for';


--
-- Name: COLUMN ovt_resultinteger.resultinteger; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultinteger.resultinteger IS 'The value';


--
-- Name: ovt_resultinteger_resultintegerid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resultinteger_resultintegerid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resultinteger_resultintegerid_seq OWNER TO overtest;

--
-- Name: ovt_resultinteger_resultintegerid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resultinteger_resultintegerid_seq OWNED BY ovt_resultinteger.resultintegerid;


--
-- Name: ovt_resultstring; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resultstring (
    resultstringid integer NOT NULL,
    testrunactionid integer NOT NULL,
    resultfieldid integer NOT NULL,
    resultstring text NOT NULL
);


ALTER TABLE public.ovt_resultstring OWNER TO overtest;

--
-- Name: TABLE ovt_resultstring; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resultstring IS 'A string result field for extended result data';


--
-- Name: COLUMN ovt_resultstring.testrunactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultstring.testrunactionid IS 'The test this result is associated with';


--
-- Name: COLUMN ovt_resultstring.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultstring.resultfieldid IS 'The field this result is for';


--
-- Name: COLUMN ovt_resultstring.resultstring; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resultstring.resultstring IS 'The value';


--
-- Name: ovt_resultstring_resultstringid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resultstring_resultstringid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resultstring_resultstringid_seq OWNER TO overtest;

--
-- Name: ovt_resultstring_resultstringid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resultstring_resultstringid_seq OWNED BY ovt_resultstring.resultstringid;


--
-- Name: ovt_resulttype; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_resulttype (
    resulttypeid integer NOT NULL,
    resulttypename character varying(30) NOT NULL
);


ALTER TABLE public.ovt_resulttype OWNER TO overtest;

--
-- Name: TABLE ovt_resulttype; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_resulttype IS 'Various types of extended result data';


--
-- Name: COLUMN ovt_resulttype.resulttypename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_resulttype.resulttypename IS 'Name of result type';


--
-- Name: ovt_resulttype_resulttypeid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_resulttype_resulttypeid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_resulttype_resulttypeid_seq OWNER TO overtest;

--
-- Name: ovt_resulttype_resulttypeid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_resulttype_resulttypeid_seq OWNED BY ovt_resulttype.resulttypeid;


--
-- Name: ovt_runstatus; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_runstatus (
    runstatusid integer NOT NULL,
    status character varying(30) NOT NULL,
    description character varying(50) NOT NULL,
    iseditable boolean DEFAULT false NOT NULL,
    goenabled boolean DEFAULT false NOT NULL,
    pauseenabled boolean DEFAULT false NOT NULL,
    abortenabled boolean DEFAULT false NOT NULL,
    archiveenabled boolean DEFAULT false NOT NULL,
    deleteenabled boolean DEFAULT false NOT NULL,
    checkenabled boolean DEFAULT false NOT NULL,
    externalenabled boolean DEFAULT false NOT NULL,
    equivcheck boolean DEFAULT true NOT NULL,
    isverbose boolean DEFAULT true NOT NULL,
    resultsvalid boolean DEFAULT false NOT NULL,
    CONSTRAINT noarchive CHECK (((NOT archiveenabled) OR (((NOT abortenabled) AND (NOT pauseenabled)) AND (NOT goenabled)))),
    CONSTRAINT nodelete CHECK (((NOT deleteenabled) OR (((NOT abortenabled) AND (NOT pauseenabled)) AND (NOT goenabled))))
);


ALTER TABLE public.ovt_runstatus OWNER TO overtest;

--
-- Name: TABLE ovt_runstatus; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_runstatus IS 'A testrun must go through a series of stages from conception to completion';


--
-- Name: COLUMN ovt_runstatus.status; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.status IS 'A short description of each state a testrun goes through';


--
-- Name: COLUMN ovt_runstatus.goenabled; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.goenabled IS 'Whether the testrun can be started (or continued)';


--
-- Name: COLUMN ovt_runstatus.pauseenabled; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.pauseenabled IS 'Whether the testrun can be paused';


--
-- Name: COLUMN ovt_runstatus.abortenabled; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.abortenabled IS 'Whether the testrun can be aborted';


--
-- Name: COLUMN ovt_runstatus.archiveenabled; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.archiveenabled IS 'Whether the testrun can be archived';


--
-- Name: COLUMN ovt_runstatus.deleteenabled; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.deleteenabled IS 'Whether the testrun can be deleted';


--
-- Name: COLUMN ovt_runstatus.checkenabled; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.checkenabled IS 'Set when the state can move to readytocheck';


--
-- Name: COLUMN ovt_runstatus.equivcheck; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.equivcheck IS 'Set to true when the testrunactions in the testrun are subject to equivalence checking';


--
-- Name: COLUMN ovt_runstatus.isverbose; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.isverbose IS 'Whether this runstate is considered generally irrelevant and transitions to it are recorded as a separate level of logging';


--
-- Name: COLUMN ovt_runstatus.resultsvalid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_runstatus.resultsvalid IS 'Whether the testrun has useful results';


--
-- Name: ovt_runstatus_runstatusid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_runstatus_runstatusid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_runstatus_runstatusid_seq OWNER TO overtest;

--
-- Name: ovt_runstatus_runstatusid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_runstatus_runstatusid_seq OWNED BY ovt_runstatus.runstatusid;


--
-- Name: ovt_simpleequivalence; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_simpleequivalence (
    simpleequivalenceid integer NOT NULL,
    simpleequivalencename character varying(255)
);


ALTER TABLE public.ovt_simpleequivalence OWNER TO overtest;

--
-- Name: TABLE ovt_simpleequivalence; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_simpleequivalence IS 'A small table for referring to simple equivalences by name and also providing something to lock when generating equivalences';


--
-- Name: COLUMN ovt_simpleequivalence.simpleequivalencename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_simpleequivalence.simpleequivalencename IS 'A name for referring to a simple equivalence';


--
-- Name: ovt_simpleequivalence_simpleequivalenceid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_simpleequivalence_simpleequivalenceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_simpleequivalence_simpleequivalenceid_seq OWNER TO overtest;

--
-- Name: ovt_simpleequivalence_simpleequivalenceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_simpleequivalence_simpleequivalenceid_seq OWNED BY ovt_simpleequivalence.simpleequivalenceid;


--
-- Name: ovt_subrecursiveequivalence; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_subrecursiveequivalence (
    subrecursiveequivalenceid integer NOT NULL,
    subrecursiveequivalencename character varying(255)
);


ALTER TABLE public.ovt_subrecursiveequivalence OWNER TO overtest;

--
-- Name: TABLE ovt_subrecursiveequivalence; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_subrecursiveequivalence IS 'Represents an equivalence where all producers of a testrunaction are identical';


--
-- Name: COLUMN ovt_subrecursiveequivalence.subrecursiveequivalencename; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_subrecursiveequivalence.subrecursiveequivalencename IS 'A name for referring to the sub-recursive equivalence';


--
-- Name: ovt_subrecursiveequivalence_subrecursiveequivalenceid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_subrecursiveequivalence_subrecursiveequivalenceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_subrecursiveequivalence_subrecursiveequivalenceid_seq OWNER TO overtest;

--
-- Name: ovt_subrecursiveequivalence_subrecursiveequivalenceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_subrecursiveequivalence_subrecursiveequivalenceid_seq OWNED BY ovt_subrecursiveequivalence.subrecursiveequivalenceid;


--
-- Name: ovt_subscription; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_subscription (
    subscriptionid integer NOT NULL,
    userid integer NOT NULL,
    notifymethodid integer NOT NULL,
    notifytypeid integer NOT NULL
);


ALTER TABLE public.ovt_subscription OWNER TO overtest;

--
-- Name: TABLE ovt_subscription; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_subscription IS '''Catch all'' subscriptions. Holds top level subscription information to allow a user to receive every notification relating to particular entity (resources, testruns, actions etc etc)';


--
-- Name: COLUMN ovt_subscription.userid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_subscription.userid IS 'The user who owns the subscription';


--
-- Name: COLUMN ovt_subscription.notifymethodid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_subscription.notifymethodid IS 'How the user wishes to be notified';


--
-- Name: ovt_subscription_subscriptionid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_subscription_subscriptionid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_subscription_subscriptionid_seq OWNER TO overtest;

--
-- Name: ovt_subscription_subscriptionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_subscription_subscriptionid_seq OWNED BY ovt_subscription.subscriptionid;


--
-- Name: ovt_subscriptionentity; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_subscriptionentity (
    subscriptionentityid integer NOT NULL,
    subscriptionid integer NOT NULL,
    notifyentityid integer NOT NULL,
    pkid integer NOT NULL
);


ALTER TABLE public.ovt_subscriptionentity OWNER TO overtest;

--
-- Name: TABLE ovt_subscriptionentity; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_subscriptionentity IS 'Fine grained subscriptions relate directly to entities';


--
-- Name: COLUMN ovt_subscriptionentity.subscriptionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_subscriptionentity.subscriptionid IS 'The main subscription entry';


--
-- Name: COLUMN ovt_subscriptionentity.notifyentityid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_subscriptionentity.notifyentityid IS 'The entity class for this subscription';


--
-- Name: COLUMN ovt_subscriptionentity.pkid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_subscriptionentity.pkid IS 'An untyped reference to a primary key. Type is inferred from the entity class.';


--
-- Name: ovt_subscriptionentity_subscriptionentityid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_subscriptionentity_subscriptionentityid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_subscriptionentity_subscriptionentityid_seq OWNER TO overtest;

--
-- Name: ovt_subscriptionentity_subscriptionentityid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_subscriptionentity_subscriptionentityid_seq OWNED BY ovt_subscriptionentity.subscriptionentityid;


--
-- Name: ovt_test; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_test (
    testid integer NOT NULL,
    testname character varying(255) NOT NULL,
    testsuiteid integer NOT NULL
);


ALTER TABLE public.ovt_test OWNER TO overtest;

--
-- Name: TABLE ovt_test; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_test IS 'A test is part of a testsuite that is run by an test. Tests are versioned to allow a user to keep track of how a test changes over time if such a thing is required.';


--
-- Name: COLUMN ovt_test.testsuiteid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_test.testsuiteid IS 'Testsuite to group and associate with an test';


--
-- Name: ovt_test_testid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_test_testid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_test_testid_seq OWNER TO overtest;

--
-- Name: ovt_test_testid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_test_testid_seq OWNED BY ovt_test.testid;


--
-- Name: ovt_testresultboolean; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testresultboolean (
    testresultbooleanid integer NOT NULL,
    testruntestid integer NOT NULL,
    resultfieldid integer NOT NULL,
    testresultboolean boolean NOT NULL
);


ALTER TABLE public.ovt_testresultboolean OWNER TO overtest;

--
-- Name: TABLE ovt_testresultboolean; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testresultboolean IS 'An float result field for extended result data';


--
-- Name: COLUMN ovt_testresultboolean.testruntestid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultboolean.testruntestid IS 'The testruntest that the result belongs to';


--
-- Name: COLUMN ovt_testresultboolean.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultboolean.resultfieldid IS 'The field this result is for';


--
-- Name: COLUMN ovt_testresultboolean.testresultboolean; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultboolean.testresultboolean IS 'The value';


--
-- Name: ovt_testresultboolean_testresultbooleanid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testresultboolean_testresultbooleanid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testresultboolean_testresultbooleanid_seq OWNER TO overtest;

--
-- Name: ovt_testresultboolean_testresultbooleanid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testresultboolean_testresultbooleanid_seq OWNED BY ovt_testresultboolean.testresultbooleanid;


--
-- Name: ovt_testresultfloat; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testresultfloat (
    testresultfloatid integer NOT NULL,
    testruntestid integer NOT NULL,
    resultfieldid integer NOT NULL,
    testresultfloat double precision NOT NULL
);


ALTER TABLE public.ovt_testresultfloat OWNER TO overtest;

--
-- Name: TABLE ovt_testresultfloat; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testresultfloat IS 'An float result field for extended result data';


--
-- Name: COLUMN ovt_testresultfloat.testruntestid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultfloat.testruntestid IS 'The testruntest that the result belongs to';


--
-- Name: COLUMN ovt_testresultfloat.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultfloat.resultfieldid IS 'The field this result is for';


--
-- Name: COLUMN ovt_testresultfloat.testresultfloat; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultfloat.testresultfloat IS 'The value';


--
-- Name: ovt_testresultfloat_testresultfloatid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testresultfloat_testresultfloatid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testresultfloat_testresultfloatid_seq OWNER TO overtest;

--
-- Name: ovt_testresultfloat_testresultfloatid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testresultfloat_testresultfloatid_seq OWNED BY ovt_testresultfloat.testresultfloatid;


--
-- Name: ovt_testresultinteger; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testresultinteger (
    testresultintegerid integer NOT NULL,
    testruntestid integer NOT NULL,
    resultfieldid integer NOT NULL,
    testresultinteger bigint NOT NULL
);


ALTER TABLE public.ovt_testresultinteger OWNER TO overtest;

--
-- Name: TABLE ovt_testresultinteger; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testresultinteger IS 'An float result field for extended result data';


--
-- Name: COLUMN ovt_testresultinteger.testruntestid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultinteger.testruntestid IS 'The testruntest that the result belongs to';


--
-- Name: COLUMN ovt_testresultinteger.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultinteger.resultfieldid IS 'The field this result is for';


--
-- Name: COLUMN ovt_testresultinteger.testresultinteger; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultinteger.testresultinteger IS 'The value';


--
-- Name: ovt_testresultinteger_testresultintegerid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testresultinteger_testresultintegerid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testresultinteger_testresultintegerid_seq OWNER TO overtest;

--
-- Name: ovt_testresultinteger_testresultintegerid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testresultinteger_testresultintegerid_seq OWNED BY ovt_testresultinteger.testresultintegerid;


--
-- Name: ovt_testresultstring; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testresultstring (
    testresultstringid integer NOT NULL,
    testruntestid integer NOT NULL,
    resultfieldid integer NOT NULL,
    testresultstring text NOT NULL
);


ALTER TABLE public.ovt_testresultstring OWNER TO overtest;

--
-- Name: TABLE ovt_testresultstring; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testresultstring IS 'An float result field for extended result data';


--
-- Name: COLUMN ovt_testresultstring.testruntestid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultstring.testruntestid IS 'The testruntest that the result belongs to';


--
-- Name: COLUMN ovt_testresultstring.resultfieldid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultstring.resultfieldid IS 'The field this result is for';


--
-- Name: COLUMN ovt_testresultstring.testresultstring; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testresultstring.testresultstring IS 'The value';


--
-- Name: ovt_testresultstring_testresultstringid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testresultstring_testresultstringid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testresultstring_testresultstringid_seq OWNER TO overtest;

--
-- Name: ovt_testresultstring_testresultstringid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testresultstring_testresultstringid_seq OWNED BY ovt_testresultstring.testresultstringid;


--
-- Name: ovt_testrun; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testrun (
    testrunid integer NOT NULL,
    userid integer NOT NULL,
    template boolean DEFAULT false NOT NULL,
    testdate timestamp with time zone,
    priority integer DEFAULT 1000 NOT NULL,
    createddate timestamp with time zone DEFAULT now() NOT NULL,
    startafter timestamp with time zone DEFAULT now() NOT NULL,
    completeddate timestamp with time zone,
    runstatusid integer DEFAULT 1 NOT NULL,
    concurrency integer DEFAULT 1 NOT NULL,
    description text NOT NULL,
    testrungroupid integer,
    autoarchive boolean DEFAULT false NOT NULL
);


ALTER TABLE public.ovt_testrun OWNER TO overtest;

--
-- Name: TABLE ovt_testrun; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testrun IS 'A container for a full test run and all results';


--
-- Name: COLUMN ovt_testrun.userid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrun.userid IS 'The user that owns this testrun';


--
-- Name: COLUMN ovt_testrun.template; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrun.template IS 'Set when a testrun''s action set can be used as a template';


--
-- Name: COLUMN ovt_testrun.testdate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrun.testdate IS 'The date the test was started';


--
-- Name: COLUMN ovt_testrun.priority; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrun.priority IS '1 is the highest priority';


--
-- Name: COLUMN ovt_testrun.startafter; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrun.startafter IS 'When set specifies the testrun should not begin until the given date. When not set the testrun is not enabled.';


--
-- Name: COLUMN ovt_testrun.completeddate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrun.completeddate IS 'The time the testrun completed, aborted or failed';


--
-- Name: COLUMN ovt_testrun.testrungroupid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrun.testrungroupid IS 'The testrun group';


--
-- Name: COLUMN ovt_testrun.autoarchive; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrun.autoarchive IS 'When set causes a testrun to transition from completed to archive automatically';


--
-- Name: ovt_testrun_testrunid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testrun_testrunid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testrun_testrunid_seq OWNER TO overtest;

--
-- Name: ovt_testrun_testrunid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testrun_testrunid_seq OWNED BY ovt_testrun.testrunid;


--
-- Name: ovt_testrunaction; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testrunaction (
    testrunactionid integer NOT NULL,
    testrunid integer NOT NULL,
    versionedactionid integer NOT NULL,
    modified boolean DEFAULT false NOT NULL,
    pid integer,
    providedbytestrunid integer,
    starteddate timestamp with time zone,
    completeddate timestamp with time zone,
    passed boolean,
    archived boolean,
    simpleequivalenceid integer,
    recursiveequivalenceid integer,
    subrecursiveequivalenceid integer
);


ALTER TABLE public.ovt_testrunaction OWNER TO overtest;

--
-- Name: TABLE ovt_testrunaction; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testrunaction IS 'Describes part of a testrun. There will be a testrunaction for every component of every dependency in a test run. Relationships between testrunactions are implicit in the dependencies between versionedactions';


--
-- Name: COLUMN ovt_testrunaction.testrunid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.testrunid IS 'The testrun this action belongs to';


--
-- Name: COLUMN ovt_testrunaction.versionedactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.versionedactionid IS 'The versioned action being linked to a testrun';


--
-- Name: COLUMN ovt_testrunaction.modified; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.modified IS 'Set when the outcome of this test is not guaranteed to be consistent with an identical test. E.g. the sources have been manually altered';


--
-- Name: COLUMN ovt_testrunaction.providedbytestrunid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.providedbytestrunid IS 'When set, indicates that this action does not need to be run, but instead the specified testrun will have run it and the result should be used.';


--
-- Name: COLUMN ovt_testrunaction.starteddate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.starteddate IS 'When set the task is either running or completed';


--
-- Name: COLUMN ovt_testrunaction.completeddate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.completeddate IS 'When set the task is completed';


--
-- Name: COLUMN ovt_testrunaction.passed; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.passed IS 'True indicates success, False indicates failure. Does not indicate test completion.';


--
-- Name: COLUMN ovt_testrunaction.archived; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.archived IS 'Set when the task has been archived, false when being archived';


--
-- Name: COLUMN ovt_testrunaction.simpleequivalenceid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.simpleequivalenceid IS 'Testrunactions with the same simple equivalence have identical properties that relate just to their own versionedactionid';


--
-- Name: COLUMN ovt_testrunaction.recursiveequivalenceid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.recursiveequivalenceid IS 'Testrunactions with the same recursive equivalence have identical properties relating to their own versionedaction and all producer versionedactions recursively to the roots';


--
-- Name: COLUMN ovt_testrunaction.subrecursiveequivalenceid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunaction.subrecursiveequivalenceid IS 'Testrunactions with the same subrecursive equivalence have the same properties for all producer versionedactions recursively to the roots';


--
-- Name: ovt_testrunaction_testrunactionid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testrunaction_testrunactionid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testrunaction_testrunactionid_seq OWNER TO overtest;

--
-- Name: ovt_testrunaction_testrunactionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testrunaction_testrunactionid_seq OWNED BY ovt_testrunaction.testrunactionid;


--
-- Name: ovt_testrunactionresource; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testrunactionresource (
    testrunactionresourceid integer NOT NULL,
    testrunactionid integer NOT NULL,
    resourceid integer NOT NULL,
    held boolean DEFAULT false NOT NULL,
    dead boolean DEFAULT false NOT NULL,
    lastchecked timestamp with time zone,
    CONSTRAINT ovt_testrunactionresource_deadcheck CHECK ((NOT (dead AND held)))
);


ALTER TABLE public.ovt_testrunactionresource OWNER TO overtest;

--
-- Name: TABLE ovt_testrunactionresource; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testrunactionresource IS 'Holds details of previous current and outstanding requests for resources';


--
-- Name: COLUMN ovt_testrunactionresource.testrunactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunactionresource.testrunactionid IS 'The testrunaction making the request';


--
-- Name: COLUMN ovt_testrunactionresource.resourceid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunactionresource.resourceid IS 'The resource being requested';


--
-- Name: COLUMN ovt_testrunactionresource.held; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunactionresource.held IS 'Whether or not the resource is in use or not via this request';


--
-- Name: COLUMN ovt_testrunactionresource.dead; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunactionresource.dead IS 'The request is no longer needed or has been used';


--
-- Name: COLUMN ovt_testrunactionresource.lastchecked; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunactionresource.lastchecked IS 'Used to track when a task with resource requirements was last checked if it was ready';


--
-- Name: ovt_testrunactionresource_testrunactionresourceid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testrunactionresource_testrunactionresourceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testrunactionresource_testrunactionresourceid_seq OWNER TO overtest;

--
-- Name: ovt_testrunactionresource_testrunactionresourceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testrunactionresource_testrunactionresourceid_seq OWNED BY ovt_testrunactionresource.testrunactionresourceid;


--
-- Name: ovt_testrunattributevalue; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testrunattributevalue (
    testrunattributevalueid integer NOT NULL,
    testrunid integer NOT NULL,
    attributevalueid integer NOT NULL
);


ALTER TABLE public.ovt_testrunattributevalue OWNER TO overtest;

--
-- Name: TABLE ovt_testrunattributevalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testrunattributevalue IS 'Test runs can specifically restrict the available attribute values. These restrictions are applied to each testrunaction. They only serve to restrict resources not mandate inclusion of a resource.';


--
-- Name: ovt_testrunattributevalue_testrunattributevalueid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testrunattributevalue_testrunattributevalueid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testrunattributevalue_testrunattributevalueid_seq OWNER TO overtest;

--
-- Name: ovt_testrunattributevalue_testrunattributevalueid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testrunattributevalue_testrunattributevalueid_seq OWNED BY ovt_testrunattributevalue.testrunattributevalueid;


--
-- Name: ovt_testrungroup; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testrungroup (
    testrungroupid integer NOT NULL,
    testrungroupname character varying(255) NOT NULL,
    userid integer NOT NULL,
    createddate timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.ovt_testrungroup OWNER TO overtest;

--
-- Name: TABLE ovt_testrungroup; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testrungroup IS 'Testrun groups allow testruns to share common actions';


--
-- Name: COLUMN ovt_testrungroup.userid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrungroup.userid IS 'Who owns the testrun group';


--
-- Name: COLUMN ovt_testrungroup.createddate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrungroup.createddate IS 'The date the testrun group was created';


--
-- Name: ovt_testrungroup_testrungroupid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testrungroup_testrungroupid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testrungroup_testrungroupid_seq OWNER TO overtest;

--
-- Name: ovt_testrungroup_testrungroupid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testrungroup_testrungroupid_seq OWNED BY ovt_testrungroup.testrungroupid;


--
-- Name: ovt_testrunresource; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testrunresource (
    testrunresourceid integer NOT NULL,
    testrunid integer NOT NULL,
    resourceid integer NOT NULL
);


ALTER TABLE public.ovt_testrunresource OWNER TO overtest;

--
-- Name: TABLE ovt_testrunresource; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testrunresource IS 'Each testrun can be linked to one or more resources';


--
-- Name: COLUMN ovt_testrunresource.testrunid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunresource.testrunid IS 'The testrun instance';


--
-- Name: COLUMN ovt_testrunresource.resourceid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testrunresource.resourceid IS 'The resource to be used';


--
-- Name: ovt_testrunresource_testrunresourceid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testrunresource_testrunresourceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testrunresource_testrunresourceid_seq OWNER TO overtest;

--
-- Name: ovt_testrunresource_testrunresourceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testrunresource_testrunresourceid_seq OWNED BY ovt_testrunresource.testrunresourceid;


--
-- Name: ovt_testruntest; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testruntest (
    testruntestid integer NOT NULL,
    testrunid integer NOT NULL,
    versionedtestid integer NOT NULL,
    providedbytestrunid integer,
    starteddate timestamp with time zone DEFAULT now(),
    completeddate timestamp with time zone,
    passed boolean
);


ALTER TABLE public.ovt_testruntest OWNER TO overtest;

--
-- Name: TABLE ovt_testruntest; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testruntest IS 'Describes the result of a test';


--
-- Name: COLUMN ovt_testruntest.testrunid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testruntest.testrunid IS 'The testrun this test belongs to';


--
-- Name: COLUMN ovt_testruntest.versionedtestid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testruntest.versionedtestid IS 'The versioned test being linked to a testrun';


--
-- Name: COLUMN ovt_testruntest.providedbytestrunid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testruntest.providedbytestrunid IS 'When set, indicates that this test does not need to be run, but instead the specified testrun will have run it and the result should be used.';


--
-- Name: COLUMN ovt_testruntest.starteddate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testruntest.starteddate IS 'The start date of the test';


--
-- Name: COLUMN ovt_testruntest.completeddate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testruntest.completeddate IS 'The completed date of the test';


--
-- Name: COLUMN ovt_testruntest.passed; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_testruntest.passed IS 'True indicates success, False indicates failure';


--
-- Name: ovt_testruntest_testruntestid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testruntest_testruntestid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testruntest_testruntestid_seq OWNER TO overtest;

--
-- Name: ovt_testruntest_testruntestid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testruntest_testruntestid_seq OWNED BY ovt_testruntest.testruntestid;


--
-- Name: ovt_testsuite; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_testsuite (
    testsuiteid integer NOT NULL,
    testsuitename character varying(50) NOT NULL
);


ALTER TABLE public.ovt_testsuite OWNER TO overtest;

--
-- Name: TABLE ovt_testsuite; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_testsuite IS 'Tests are grouped by testsuite and are owned by an test';


--
-- Name: ovt_testsuite_testsuiteid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_testsuite_testsuiteid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_testsuite_testsuiteid_seq OWNER TO overtest;

--
-- Name: ovt_testsuite_testsuiteid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_testsuite_testsuiteid_seq OWNED BY ovt_testsuite.testsuiteid;


--
-- Name: ovt_user; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_user (
    userid integer NOT NULL,
    username character varying(40) NOT NULL,
    fname character varying(40),
    sname character varying(40),
    altnames character varying(255),
    email character varying(255),
    growlhost character varying(255),
    growlpassword character varying(20)
);


ALTER TABLE public.ovt_user OWNER TO overtest;

--
-- Name: TABLE ovt_user; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_user IS 'Details of each overtest user';


--
-- Name: COLUMN ovt_user.username; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_user.username IS 'A short username (unix user ideally)';


--
-- Name: COLUMN ovt_user.fname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_user.fname IS 'First name';


--
-- Name: COLUMN ovt_user.sname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_user.sname IS 'Last name';


--
-- Name: COLUMN ovt_user.altnames; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_user.altnames IS 'A comma separated list of alternative user names';


--
-- Name: COLUMN ovt_user.email; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_user.email IS 'An internal email address';


--
-- Name: COLUMN ovt_user.growlhost; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_user.growlhost IS 'An internal FQDN to send growl notifications to';


--
-- Name: COLUMN ovt_user.growlpassword; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_user.growlpassword IS 'A password for the growl host';


--
-- Name: ovt_user_userid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_user_userid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_user_userid_seq OWNER TO overtest;

--
-- Name: ovt_user_userid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_user_userid_seq OWNED BY ovt_user.userid;


--
-- Name: ovt_userclaim; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_userclaim (
    userclaimid integer NOT NULL,
    userid integer NOT NULL,
    reason text NOT NULL,
    requestdate timestamp with time zone DEFAULT now() NOT NULL,
    grantdate timestamp with time zone,
    returndate timestamp with time zone,
    active boolean DEFAULT true
);


ALTER TABLE public.ovt_userclaim OWNER TO overtest;

--
-- Name: TABLE ovt_userclaim; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_userclaim IS 'Represents a resource claim from a user.';


--
-- Name: COLUMN ovt_userclaim.userid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaim.userid IS 'The user making the claim';


--
-- Name: COLUMN ovt_userclaim.reason; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaim.reason IS 'The reason for this request';


--
-- Name: COLUMN ovt_userclaim.requestdate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaim.requestdate IS 'When the request was made';


--
-- Name: COLUMN ovt_userclaim.grantdate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaim.grantdate IS 'When the request was granted';


--
-- Name: COLUMN ovt_userclaim.returndate; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaim.returndate IS 'When the resources were returned or request cancelled';


--
-- Name: COLUMN ovt_userclaim.active; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaim.active IS 'Set to null when inactive';


--
-- Name: ovt_userclaim_userclaimid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_userclaim_userclaimid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_userclaim_userclaimid_seq OWNER TO overtest;

--
-- Name: ovt_userclaim_userclaimid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_userclaim_userclaimid_seq OWNED BY ovt_userclaim.userclaimid;


--
-- Name: ovt_userclaimattributevalue; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_userclaimattributevalue (
    userclaimattributevalue integer NOT NULL,
    userclaimid integer NOT NULL,
    attributevalueid integer NOT NULL
);


ALTER TABLE public.ovt_userclaimattributevalue OWNER TO overtest;

--
-- Name: TABLE ovt_userclaimattributevalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_userclaimattributevalue IS 'The requested attributes for a resource claim';


--
-- Name: COLUMN ovt_userclaimattributevalue.userclaimid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaimattributevalue.userclaimid IS 'The claim request';


--
-- Name: COLUMN ovt_userclaimattributevalue.attributevalueid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaimattributevalue.attributevalueid IS 'The required attribute';


--
-- Name: ovt_userclaimattributevalue_userclaimattributevalue_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_userclaimattributevalue_userclaimattributevalue_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_userclaimattributevalue_userclaimattributevalue_seq OWNER TO overtest;

--
-- Name: ovt_userclaimattributevalue_userclaimattributevalue_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_userclaimattributevalue_userclaimattributevalue_seq OWNED BY ovt_userclaimattributevalue.userclaimattributevalue;


--
-- Name: ovt_userclaimresource; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_userclaimresource (
    userclaimresourceid integer NOT NULL,
    userclaimid integer NOT NULL,
    resourceid integer NOT NULL,
    held boolean DEFAULT false NOT NULL,
    dead boolean DEFAULT false NOT NULL,
    CONSTRAINT only_live_requests CHECK ((NOT (dead AND held)))
);


ALTER TABLE public.ovt_userclaimresource OWNER TO overtest;

--
-- Name: TABLE ovt_userclaimresource; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_userclaimresource IS 'The resources being claimed';


--
-- Name: COLUMN ovt_userclaimresource.userclaimid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaimresource.userclaimid IS 'The user claim for this resource';


--
-- Name: COLUMN ovt_userclaimresource.resourceid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaimresource.resourceid IS 'The resource being claimed';


--
-- Name: COLUMN ovt_userclaimresource.held; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaimresource.held IS 'Whether or not the resource is in use or not via this request';


--
-- Name: COLUMN ovt_userclaimresource.dead; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_userclaimresource.dead IS 'The request is no longer needed or has been used';


--
-- Name: ovt_userclaimresource_userclaimresourceid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_userclaimresource_userclaimresourceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_userclaimresource_userclaimresourceid_seq OWNER TO overtest;

--
-- Name: ovt_userclaimresource_userclaimresourceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_userclaimresource_userclaimresourceid_seq OWNED BY ovt_userclaimresource.userclaimresourceid;


--
-- Name: ovt_versionedaction; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_versionedaction (
    versionedactionid integer NOT NULL,
    actionid integer NOT NULL,
    versionname ovtversion NOT NULL,
    v1 integer,
    v2 integer,
    v3 integer,
    v4 integer,
    lifecyclestateid integer DEFAULT 1 NOT NULL,
    CONSTRAINT ovt_versionedaction_nonzero_versionname CHECK ((length((versionname)::text) > 0))
);


ALTER TABLE public.ovt_versionedaction OWNER TO overtest;

--
-- Name: TABLE ovt_versionedaction; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_versionedaction IS 'A versionedaction is a full description of a ''task''. All dependencies are described base don version of actions rather than just versions to provide the greatest flexibility.';


--
-- Name: COLUMN ovt_versionedaction.actionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedaction.actionid IS 'The related action';


--
-- Name: COLUMN ovt_versionedaction.versionname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedaction.versionname IS 'The textual part of the version name';


--
-- Name: COLUMN ovt_versionedaction.v1; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedaction.v1 IS 'The most significant version identifier';


--
-- Name: COLUMN ovt_versionedaction.v2; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedaction.v2 IS 'Version identifier';


--
-- Name: COLUMN ovt_versionedaction.v3; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedaction.v3 IS 'Version identifier';


--
-- Name: COLUMN ovt_versionedaction.v4; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedaction.v4 IS 'The least significant version identifier';


--
-- Name: COLUMN ovt_versionedaction.lifecyclestateid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedaction.lifecyclestateid IS 'The current state of the version';


--
-- Name: ovt_versionedaction_versionedactionid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_versionedaction_versionedactionid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_versionedaction_versionedactionid_seq OWNER TO overtest;

--
-- Name: ovt_versionedaction_versionedactionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_versionedaction_versionedactionid_seq OWNED BY ovt_versionedaction.versionedactionid;


--
-- Name: ovt_versionedactionattributevalue; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_versionedactionattributevalue (
    versionedactionattributevalueid integer NOT NULL,
    versionedactionid integer NOT NULL,
    attributevalueid integer NOT NULL
);


ALTER TABLE public.ovt_versionedactionattributevalue OWNER TO overtest;

--
-- Name: TABLE ovt_versionedactionattributevalue; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_versionedactionattributevalue IS 'Actions have resource dependencies which are modelled using specific values of a series of resource attributes';


--
-- Name: ovt_versionedactionattributev_versionedactionattributevalue_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_versionedactionattributev_versionedactionattributevalue_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_versionedactionattributev_versionedactionattributevalue_seq OWNER TO overtest;

--
-- Name: ovt_versionedactionattributev_versionedactionattributevalue_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_versionedactionattributev_versionedactionattributevalue_seq OWNED BY ovt_versionedactionattributevalue.versionedactionattributevalueid;


--
-- Name: ovt_versionedactionconfigoption; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_versionedactionconfigoption (
    versionedactionconfigoptionid integer NOT NULL,
    versionedactionid integer NOT NULL,
    configoptionid integer NOT NULL
);


ALTER TABLE public.ovt_versionedactionconfigoption OWNER TO overtest;

--
-- Name: TABLE ovt_versionedactionconfigoption; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_versionedactionconfigoption IS 'Represents all configuration options for a given version of an action';


--
-- Name: COLUMN ovt_versionedactionconfigoption.versionedactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedactionconfigoption.versionedactionid IS 'The version of an action';


--
-- Name: COLUMN ovt_versionedactionconfigoption.configoptionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedactionconfigoption.configoptionid IS 'The configuration option to link';


--
-- Name: ovt_versionedactionconfigopti_versionedactionconfigoptionid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_versionedactionconfigopti_versionedactionconfigoptionid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_versionedactionconfigopti_versionedactionconfigoptionid_seq OWNER TO overtest;

--
-- Name: ovt_versionedactionconfigopti_versionedactionconfigoptionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_versionedactionconfigopti_versionedactionconfigoptionid_seq OWNED BY ovt_versionedactionconfigoption.versionedactionconfigoptionid;


--
-- Name: ovt_versionedactionconfigoptionlookup; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_versionedactionconfigoptionlookup (
    versionedactionconfigoptionlookupid integer NOT NULL,
    versionedactionid integer NOT NULL,
    configoptionlookupid integer NOT NULL
);


ALTER TABLE public.ovt_versionedactionconfigoptionlookup OWNER TO overtest;

--
-- Name: TABLE ovt_versionedactionconfigoptionlookup; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_versionedactionconfigoptionlookup IS 'Represents which lookup values are permitted for each versionedaction. ';


--
-- Name: COLUMN ovt_versionedactionconfigoptionlookup.versionedactionid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedactionconfigoptionlookup.versionedactionid IS 'The associated versionedaction';


--
-- Name: COLUMN ovt_versionedactionconfigoptionlookup.configoptionlookupid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedactionconfigoptionlookup.configoptionlookupid IS 'The lookup value';


--
-- Name: ovt_versionedactionconfigopti_versionedactionconfigoptionlo_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_versionedactionconfigopti_versionedactionconfigoptionlo_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_versionedactionconfigopti_versionedactionconfigoptionlo_seq OWNER TO overtest;

--
-- Name: ovt_versionedactionconfigopti_versionedactionconfigoptionlo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_versionedactionconfigopti_versionedactionconfigoptionlo_seq OWNED BY ovt_versionedactionconfigoptionlookup.versionedactionconfigoptionlookupid;


--
-- Name: ovt_versionedtest; Type: TABLE; Schema: public; Owner: overtest; Tablespace: 
--

CREATE TABLE ovt_versionedtest (
    versionedtestid integer NOT NULL,
    testid integer NOT NULL,
    versionname ovtversion NOT NULL,
    CONSTRAINT ovt_versionedtest_nonzero_versionname CHECK ((length((versionname)::text) > 0))
);


ALTER TABLE public.ovt_versionedtest OWNER TO overtest;

--
-- Name: TABLE ovt_versionedtest; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON TABLE ovt_versionedtest IS 'A versioned test is used to describe how a test has changed over time';


--
-- Name: COLUMN ovt_versionedtest.testid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedtest.testid IS 'The related test';


--
-- Name: COLUMN ovt_versionedtest.versionname; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON COLUMN ovt_versionedtest.versionname IS 'The textual part of the version name';


--
-- Name: ovt_versionedtest_versionedtestid_seq; Type: SEQUENCE; Schema: public; Owner: overtest
--

CREATE SEQUENCE ovt_versionedtest_versionedtestid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ovt_versionedtest_versionedtestid_seq OWNER TO overtest;

--
-- Name: ovt_versionedtest_versionedtestid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: overtest
--

ALTER SEQUENCE ovt_versionedtest_versionedtestid_seq OWNED BY ovt_versionedtest.versionedtestid;


--
-- Name: ovt_view_configoptionlookup_usedequivcheck; Type: VIEW; Schema: public; Owner: overtest
--

CREATE VIEW ovt_view_configoptionlookup_usedequivcheck AS
    SELECT ovt_runstatus.equivcheck, ovt_configsetting.configoptionlookupid FROM ((ovt_configsetting JOIN ovt_testrun USING (testrunid)) JOIN ovt_runstatus USING (runstatusid)) WHERE ovt_runstatus.equivcheck;


ALTER TABLE public.ovt_view_configoptionlookup_usedequivcheck OWNER TO overtest;

--
-- Name: VIEW ovt_view_configoptionlookup_usedequivcheck; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON VIEW ovt_view_configoptionlookup_usedequivcheck IS 'Determine if a configoptionlookup is used in a checked testrun';


--
-- Name: ovt_view_describe_testrungroupid; Type: VIEW; Schema: public; Owner: overtest
--

CREATE VIEW ovt_view_describe_testrungroupid AS
    SELECT ovt_testrungroup.testrungroupname AS description, ovt_testrungroup.testrungroupid AS pkid FROM ovt_testrungroup;


ALTER TABLE public.ovt_view_describe_testrungroupid OWNER TO overtest;

--
-- Name: VIEW ovt_view_describe_testrungroupid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON VIEW ovt_view_describe_testrungroupid IS 'Describe a testrungroup';


--
-- Name: ovt_view_describe_testrunid; Type: VIEW; Schema: public; Owner: overtest
--

CREATE VIEW ovt_view_describe_testrunid AS
    SELECT ovt_testrun.description, ovt_testrun.testrunid AS pkid FROM ovt_testrun;


ALTER TABLE public.ovt_view_describe_testrunid OWNER TO overtest;

--
-- Name: VIEW ovt_view_describe_testrunid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON VIEW ovt_view_describe_testrunid IS 'Describe a testrun';


--
-- Name: ovt_view_describe_testsuiteid; Type: VIEW; Schema: public; Owner: overtest
--

CREATE VIEW ovt_view_describe_testsuiteid AS
    SELECT ovt_testsuite.testsuitename AS description, ovt_testsuite.testsuiteid AS pkid FROM ovt_testsuite;


ALTER TABLE public.ovt_view_describe_testsuiteid OWNER TO overtest;

--
-- Name: VIEW ovt_view_describe_testsuiteid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON VIEW ovt_view_describe_testsuiteid IS 'Fetch the testsuite names';


--
-- Name: ovt_view_describe_userid; Type: VIEW; Schema: public; Owner: overtest
--

CREATE VIEW ovt_view_describe_userid AS
    SELECT (((ovt_user.fname)::text || ' '::text) || (ovt_user.sname)::text) AS description, ovt_user.userid AS pkid FROM ovt_user;


ALTER TABLE public.ovt_view_describe_userid OWNER TO overtest;

--
-- Name: VIEW ovt_view_describe_userid; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON VIEW ovt_view_describe_userid IS 'Describe a user';


--
-- Name: ovt_view_testrun_runstatus; Type: VIEW; Schema: public; Owner: overtest
--

CREATE VIEW ovt_view_testrun_runstatus AS
    SELECT ovt_testrun.testrunid, ovt_runstatus.runstatusid, ovt_runstatus.status, ovt_runstatus.description, ovt_runstatus.iseditable, ovt_runstatus.goenabled, ovt_runstatus.pauseenabled, ovt_runstatus.abortenabled, ovt_runstatus.archiveenabled, ovt_runstatus.deleteenabled, ovt_runstatus.checkenabled, ovt_runstatus.externalenabled, ovt_runstatus.equivcheck FROM (ovt_testrun JOIN ovt_runstatus USING (runstatusid));


ALTER TABLE public.ovt_view_testrun_runstatus OWNER TO overtest;

--
-- Name: ovt_view_testrunactionconfig; Type: VIEW; Schema: public; Owner: overtest
--

CREATE VIEW ovt_view_testrunactionconfig AS
    SELECT ovt_configoption.configoptionname, CASE WHEN ovt_configoption.islookup THEN ovt_configoptionlookup.lookupname WHEN (ovt_configsetting.configvalue IS NULL) THEN ovt_configoption.defaultvalue ELSE ovt_configsetting.configvalue END AS value, ovt_testrunaction.testrunactionid, ovt_configoptiongroup.automatic FROM (((((ovt_configoption JOIN ovt_configoptiongroup USING (configoptiongroupid)) JOIN ovt_versionedactionconfigoption USING (configoptionid)) JOIN ovt_testrunaction USING (versionedactionid)) LEFT JOIN ovt_configsetting ON (((ovt_configsetting.configoptionid = ovt_configoption.configoptionid) AND (ovt_configsetting.testrunid = ovt_testrunaction.testrunid)))) LEFT JOIN ovt_configoptionlookup ON ((((ovt_configsetting.configoptionlookupid IS NOT NULL) AND (ovt_configsetting.configoptionlookupid = ovt_configoptionlookup.configoptionlookupid)) OR (((ovt_configsetting.configoptionlookupid IS NULL) AND (ovt_configoptionlookup.configoptionid = ovt_configoption.configoptionid)) AND ovt_configoptionlookup.defaultlookup))));


ALTER TABLE public.ovt_view_testrunactionconfig OWNER TO overtest;

--
-- Name: VIEW ovt_view_testrunactionconfig; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON VIEW ovt_view_testrunactionconfig IS 'Extract the config data for a given testrunaction.';


--
-- Name: ovt_view_versionedaction_usedequivcheck; Type: VIEW; Schema: public; Owner: overtest
--

CREATE VIEW ovt_view_versionedaction_usedequivcheck AS
    SELECT ovt_runstatus.equivcheck, ovt_testrunaction.versionedactionid, ovt_testrun.testrunid FROM ((ovt_testrunaction JOIN ovt_testrun USING (testrunid)) JOIN ovt_runstatus USING (runstatusid)) WHERE ovt_runstatus.equivcheck;


ALTER TABLE public.ovt_view_versionedaction_usedequivcheck OWNER TO overtest;

--
-- Name: VIEW ovt_view_versionedaction_usedequivcheck; Type: COMMENT; Schema: public; Owner: overtest
--

COMMENT ON VIEW ovt_view_versionedaction_usedequivcheck IS 'Determine if a versionedaction is used in a checked testrun';


--
-- Name: actionid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_action ALTER COLUMN actionid SET DEFAULT nextval('ovt_action_actionid_seq'::regclass);


--
-- Name: actioncategoryid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_actioncategory ALTER COLUMN actioncategoryid SET DEFAULT nextval('ovt_actioncategory_actioncategoryid_seq'::regclass);


--
-- Name: attributeid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_attribute ALTER COLUMN attributeid SET DEFAULT nextval('ovt_attribute_attributeid_seq'::regclass);


--
-- Name: attributevalueid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_attributevalue ALTER COLUMN attributevalueid SET DEFAULT nextval('ovt_attributevalue_attributevalueid_seq'::regclass);


--
-- Name: chartid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_chart ALTER COLUMN chartid SET DEFAULT nextval('ovt_chart_chartid_seq'::regclass);


--
-- Name: chartfieldid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_chartfield ALTER COLUMN chartfieldid SET DEFAULT nextval('ovt_chartfield_chartfieldid_seq'::regclass);


--
-- Name: charttestid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_charttest ALTER COLUMN charttestid SET DEFAULT nextval('ovt_charttest_charttestid_seq'::regclass);


--
-- Name: charttypeid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_charttype ALTER COLUMN charttypeid SET DEFAULT nextval('ovt_charttype_charttypeid_seq'::regclass);


--
-- Name: configoptionid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoption ALTER COLUMN configoptionid SET DEFAULT nextval('ovt_configoption_configoptionid_seq'::regclass);


--
-- Name: configoptiongroupid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoptiongroup ALTER COLUMN configoptiongroupid SET DEFAULT nextval('ovt_configoptiongroup_configoptiongroupid_seq'::regclass);


--
-- Name: configoptionlookupid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoptionlookup ALTER COLUMN configoptionlookupid SET DEFAULT nextval('ovt_configoptionlookup_configoptionlookupid_seq'::regclass);


--
-- Name: configoptionlookupattributevalueid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoptionlookupattributevalue ALTER COLUMN configoptionlookupattributevalueid SET DEFAULT nextval('ovt_configoptionlookupattribu_configoptionlookupattributeva_seq'::regclass);


--
-- Name: configoptiontypeid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoptiontype ALTER COLUMN configoptiontypeid SET DEFAULT nextval('ovt_configoptiontype_configoptiontypeid_seq'::regclass);


--
-- Name: configsettingid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configsetting ALTER COLUMN configsettingid SET DEFAULT nextval('ovt_configsetting_configsettingid_seq'::regclass);


--
-- Name: dependencyid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_dependency ALTER COLUMN dependencyid SET DEFAULT nextval('ovt_dependency_dependencyid_seq'::regclass);


--
-- Name: dependencygroupid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_dependencygroup ALTER COLUMN dependencygroupid SET DEFAULT nextval('ovt_dependencygroup_dependencygroupid_seq'::regclass);


--
-- Name: goldresultid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_goldresult ALTER COLUMN goldresultid SET DEFAULT nextval('ovt_goldresult_goldresultid_seq'::regclass);


--
-- Name: historyid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_history ALTER COLUMN historyid SET DEFAULT nextval('ovt_history_historyid_seq'::regclass);


--
-- Name: historypkid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_historypk ALTER COLUMN historypkid SET DEFAULT nextval('ovt_historypk_historypkid_seq'::regclass);


--
-- Name: lifecyclestateid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_lifecyclestate ALTER COLUMN lifecyclestateid SET DEFAULT nextval('ovt_lifecyclestate_lifecyclestateid_seq'::regclass);


--
-- Name: notifyentityid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_notifyentity ALTER COLUMN notifyentityid SET DEFAULT nextval('ovt_notifyentity_notifyentityid_seq'::regclass);


--
-- Name: notifymethodid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_notifymethod ALTER COLUMN notifymethodid SET DEFAULT nextval('ovt_notifymethod_notifymethodid_seq'::regclass);


--
-- Name: notifytypeid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_notifytype ALTER COLUMN notifytypeid SET DEFAULT nextval('ovt_notifytype_notifytypeid_seq'::regclass);


--
-- Name: recursiveequivalenceid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_recursiveequivalence ALTER COLUMN recursiveequivalenceid SET DEFAULT nextval('ovt_recursiveequivalence_recursiveequivalenceid_seq'::regclass);


--
-- Name: resourceid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resource ALTER COLUMN resourceid SET DEFAULT nextval('ovt_resource_resourceid_seq'::regclass);


--
-- Name: resourceattributeid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resourceattribute ALTER COLUMN resourceattributeid SET DEFAULT nextval('ovt_resourceattribute_resourceattributeid_seq'::regclass);


--
-- Name: resourcelogid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resourcelog ALTER COLUMN resourcelogid SET DEFAULT nextval('ovt_resourcelog_resourcelogid_seq'::regclass);


--
-- Name: resourcestatusid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resourcestatus ALTER COLUMN resourcestatusid SET DEFAULT nextval('ovt_resourcestatus_resourcestatusid_seq'::regclass);


--
-- Name: resourcetypeid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resourcetype ALTER COLUMN resourcetypeid SET DEFAULT nextval('ovt_resourcetype_resourcetypeid_seq'::regclass);


--
-- Name: resultbooleanid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultboolean ALTER COLUMN resultbooleanid SET DEFAULT nextval('ovt_resultboolean_resultbooleanid_seq'::regclass);


--
-- Name: resultfieldid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultfield ALTER COLUMN resultfieldid SET DEFAULT nextval('ovt_resultfield_resultfieldid_seq'::regclass);


--
-- Name: resultfloatid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultfloat ALTER COLUMN resultfloatid SET DEFAULT nextval('ovt_resultfloat_resultfloatid_seq'::regclass);


--
-- Name: resultintegerid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultinteger ALTER COLUMN resultintegerid SET DEFAULT nextval('ovt_resultinteger_resultintegerid_seq'::regclass);


--
-- Name: resultstringid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultstring ALTER COLUMN resultstringid SET DEFAULT nextval('ovt_resultstring_resultstringid_seq'::regclass);


--
-- Name: resulttypeid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resulttype ALTER COLUMN resulttypeid SET DEFAULT nextval('ovt_resulttype_resulttypeid_seq'::regclass);


--
-- Name: runstatusid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_runstatus ALTER COLUMN runstatusid SET DEFAULT nextval('ovt_runstatus_runstatusid_seq'::regclass);


--
-- Name: simpleequivalenceid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_simpleequivalence ALTER COLUMN simpleequivalenceid SET DEFAULT nextval('ovt_simpleequivalence_simpleequivalenceid_seq'::regclass);


--
-- Name: subrecursiveequivalenceid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_subrecursiveequivalence ALTER COLUMN subrecursiveequivalenceid SET DEFAULT nextval('ovt_subrecursiveequivalence_subrecursiveequivalenceid_seq'::regclass);


--
-- Name: subscriptionid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_subscription ALTER COLUMN subscriptionid SET DEFAULT nextval('ovt_subscription_subscriptionid_seq'::regclass);


--
-- Name: subscriptionentityid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_subscriptionentity ALTER COLUMN subscriptionentityid SET DEFAULT nextval('ovt_subscriptionentity_subscriptionentityid_seq'::regclass);


--
-- Name: testid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_test ALTER COLUMN testid SET DEFAULT nextval('ovt_test_testid_seq'::regclass);


--
-- Name: testresultbooleanid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultboolean ALTER COLUMN testresultbooleanid SET DEFAULT nextval('ovt_testresultboolean_testresultbooleanid_seq'::regclass);


--
-- Name: testresultfloatid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultfloat ALTER COLUMN testresultfloatid SET DEFAULT nextval('ovt_testresultfloat_testresultfloatid_seq'::regclass);


--
-- Name: testresultintegerid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultinteger ALTER COLUMN testresultintegerid SET DEFAULT nextval('ovt_testresultinteger_testresultintegerid_seq'::regclass);


--
-- Name: testresultstringid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultstring ALTER COLUMN testresultstringid SET DEFAULT nextval('ovt_testresultstring_testresultstringid_seq'::regclass);


--
-- Name: testrunid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrun ALTER COLUMN testrunid SET DEFAULT nextval('ovt_testrun_testrunid_seq'::regclass);


--
-- Name: testrunactionid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunaction ALTER COLUMN testrunactionid SET DEFAULT nextval('ovt_testrunaction_testrunactionid_seq'::regclass);


--
-- Name: testrunactionresourceid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunactionresource ALTER COLUMN testrunactionresourceid SET DEFAULT nextval('ovt_testrunactionresource_testrunactionresourceid_seq'::regclass);


--
-- Name: testrunattributevalueid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunattributevalue ALTER COLUMN testrunattributevalueid SET DEFAULT nextval('ovt_testrunattributevalue_testrunattributevalueid_seq'::regclass);


--
-- Name: testrungroupid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrungroup ALTER COLUMN testrungroupid SET DEFAULT nextval('ovt_testrungroup_testrungroupid_seq'::regclass);


--
-- Name: testrunresourceid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunresource ALTER COLUMN testrunresourceid SET DEFAULT nextval('ovt_testrunresource_testrunresourceid_seq'::regclass);


--
-- Name: testruntestid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testruntest ALTER COLUMN testruntestid SET DEFAULT nextval('ovt_testruntest_testruntestid_seq'::regclass);


--
-- Name: testsuiteid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testsuite ALTER COLUMN testsuiteid SET DEFAULT nextval('ovt_testsuite_testsuiteid_seq'::regclass);


--
-- Name: userid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_user ALTER COLUMN userid SET DEFAULT nextval('ovt_user_userid_seq'::regclass);


--
-- Name: userclaimid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_userclaim ALTER COLUMN userclaimid SET DEFAULT nextval('ovt_userclaim_userclaimid_seq'::regclass);


--
-- Name: userclaimattributevalue; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_userclaimattributevalue ALTER COLUMN userclaimattributevalue SET DEFAULT nextval('ovt_userclaimattributevalue_userclaimattributevalue_seq'::regclass);


--
-- Name: userclaimresourceid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_userclaimresource ALTER COLUMN userclaimresourceid SET DEFAULT nextval('ovt_userclaimresource_userclaimresourceid_seq'::regclass);


--
-- Name: versionedactionid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedaction ALTER COLUMN versionedactionid SET DEFAULT nextval('ovt_versionedaction_versionedactionid_seq'::regclass);


--
-- Name: versionedactionattributevalueid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionattributevalue ALTER COLUMN versionedactionattributevalueid SET DEFAULT nextval('ovt_versionedactionattributev_versionedactionattributevalue_seq'::regclass);


--
-- Name: versionedactionconfigoptionid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionconfigoption ALTER COLUMN versionedactionconfigoptionid SET DEFAULT nextval('ovt_versionedactionconfigopti_versionedactionconfigoptionid_seq'::regclass);


--
-- Name: versionedactionconfigoptionlookupid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionconfigoptionlookup ALTER COLUMN versionedactionconfigoptionlookupid SET DEFAULT nextval('ovt_versionedactionconfigopti_versionedactionconfigoptionlo_seq'::regclass);


--
-- Name: versionedtestid; Type: DEFAULT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedtest ALTER COLUMN versionedtestid SET DEFAULT nextval('ovt_versionedtest_versionedtestid_seq'::regclass);


--
-- Name: ovt_action_actionname_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_action
    ADD CONSTRAINT ovt_action_actionname_key UNIQUE (actionname, actioncategoryid);


--
-- Name: ovt_action_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_action
    ADD CONSTRAINT ovt_action_pkey PRIMARY KEY (actionid);


--
-- Name: ovt_action_testsuiteid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_action
    ADD CONSTRAINT ovt_action_testsuiteid_key UNIQUE (testsuiteid);


--
-- Name: ovt_actioncategory_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_actioncategory
    ADD CONSTRAINT ovt_actioncategory_pkey PRIMARY KEY (actioncategoryid);


--
-- Name: ovt_attribute_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_attribute
    ADD CONSTRAINT ovt_attribute_pkey PRIMARY KEY (attributeid);


--
-- Name: ovt_attributevalue_attributeid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_attributevalue
    ADD CONSTRAINT ovt_attributevalue_attributeid_key UNIQUE (attributeid, value);


--
-- Name: ovt_attributevalue_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_attributevalue
    ADD CONSTRAINT ovt_attributevalue_pkey PRIMARY KEY (attributevalueid);


--
-- Name: ovt_chart_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_chart
    ADD CONSTRAINT ovt_chart_pkey PRIMARY KEY (chartid);


--
-- Name: ovt_chartfield_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_chartfield
    ADD CONSTRAINT ovt_chartfield_pkey PRIMARY KEY (chartfieldid);


--
-- Name: ovt_charttest_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_charttest
    ADD CONSTRAINT ovt_charttest_pkey PRIMARY KEY (charttestid);


--
-- Name: ovt_charttype_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_charttype
    ADD CONSTRAINT ovt_charttype_pkey PRIMARY KEY (charttypeid);


--
-- Name: ovt_configoption_configoptionname_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configoption
    ADD CONSTRAINT ovt_configoption_configoptionname_key UNIQUE (configoptionname, configoptiongroupid);


--
-- Name: ovt_configoption_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configoption
    ADD CONSTRAINT ovt_configoption_pkey PRIMARY KEY (configoptionid);


--
-- Name: ovt_configoptiongroup_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configoptiongroup
    ADD CONSTRAINT ovt_configoptiongroup_pkey PRIMARY KEY (configoptiongroupid);


--
-- Name: ovt_configoptionlookup_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configoptionlookup
    ADD CONSTRAINT ovt_configoptionlookup_pkey PRIMARY KEY (configoptionlookupid);


--
-- Name: ovt_configoptionlookupattributevalue_configoptionlookupid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configoptionlookupattributevalue
    ADD CONSTRAINT ovt_configoptionlookupattributevalue_configoptionlookupid_key UNIQUE (configoptionlookupid, attributevalueid);


--
-- Name: ovt_configoptionlookupattributevalue_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configoptionlookupattributevalue
    ADD CONSTRAINT ovt_configoptionlookupattributevalue_pkey PRIMARY KEY (configoptionlookupattributevalueid);


--
-- Name: ovt_configoptiontype_configoptiontypename_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configoptiontype
    ADD CONSTRAINT ovt_configoptiontype_configoptiontypename_key UNIQUE (configoptiontypename);


--
-- Name: ovt_configoptiontype_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configoptiontype
    ADD CONSTRAINT ovt_configoptiontype_pkey PRIMARY KEY (configoptiontypeid);


--
-- Name: ovt_configsetting_configoptionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configsetting
    ADD CONSTRAINT ovt_configsetting_configoptionid_key UNIQUE (configoptionid, testrunid);


--
-- Name: ovt_configsetting_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_configsetting
    ADD CONSTRAINT ovt_configsetting_pkey PRIMARY KEY (configsettingid);


--
-- Name: ovt_dependency_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_dependency
    ADD CONSTRAINT ovt_dependency_pkey PRIMARY KEY (dependencyid);


--
-- Name: ovt_dependency_versionedactionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_dependency
    ADD CONSTRAINT ovt_dependency_versionedactionid_key UNIQUE (versionedactionid, versionedactiondep);


--
-- Name: ovt_dependencygroup_dependencygroupname_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_dependencygroup
    ADD CONSTRAINT ovt_dependencygroup_dependencygroupname_key UNIQUE (dependencygroupname);


--
-- Name: ovt_dependencygroup_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_dependencygroup
    ADD CONSTRAINT ovt_dependencygroup_pkey PRIMARY KEY (dependencygroupid);


--
-- Name: ovt_goldresult_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_goldresult
    ADD CONSTRAINT ovt_goldresult_pkey PRIMARY KEY (goldresultid);


--
-- Name: ovt_history_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_history
    ADD CONSTRAINT ovt_history_pkey PRIMARY KEY (historyid);


--
-- Name: ovt_historypk_historyid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_historypk
    ADD CONSTRAINT ovt_historypk_historyid_key UNIQUE (historyid, notifyentityid, pkid);


--
-- Name: ovt_historypk_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_historypk
    ADD CONSTRAINT ovt_historypk_pkey PRIMARY KEY (historypkid);


--
-- Name: ovt_lifecyclestate_lifecyclestatename_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_lifecyclestate
    ADD CONSTRAINT ovt_lifecyclestate_lifecyclestatename_key UNIQUE (lifecyclestatename);


--
-- Name: ovt_lifecyclestate_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_lifecyclestate
    ADD CONSTRAINT ovt_lifecyclestate_pkey PRIMARY KEY (lifecyclestateid);


--
-- Name: ovt_notifyentity_notifyentityname_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_notifyentity
    ADD CONSTRAINT ovt_notifyentity_notifyentityname_key UNIQUE (notifyentityname);


--
-- Name: ovt_notifyentity_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_notifyentity
    ADD CONSTRAINT ovt_notifyentity_pkey PRIMARY KEY (notifyentityid);


--
-- Name: ovt_notifymethod_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_notifymethod
    ADD CONSTRAINT ovt_notifymethod_pkey PRIMARY KEY (notifymethodid);


--
-- Name: ovt_notifytype_notifytypename_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_notifytype
    ADD CONSTRAINT ovt_notifytype_notifytypename_key UNIQUE (notifytypename);


--
-- Name: ovt_notifytype_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_notifytype
    ADD CONSTRAINT ovt_notifytype_pkey PRIMARY KEY (notifytypeid);


--
-- Name: ovt_notifytypeentity_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_notifytypeentity
    ADD CONSTRAINT ovt_notifytypeentity_pkey PRIMARY KEY (notifytypeid, notifyentityid);


--
-- Name: ovt_recursiveequivalence_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_recursiveequivalence
    ADD CONSTRAINT ovt_recursiveequivalence_pkey PRIMARY KEY (recursiveequivalenceid);


--
-- Name: ovt_resource_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resource
    ADD CONSTRAINT ovt_resource_pkey PRIMARY KEY (resourceid);


--
-- Name: ovt_resourceattribute_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resourceattribute
    ADD CONSTRAINT ovt_resourceattribute_pkey PRIMARY KEY (resourceattributeid);


--
-- Name: ovt_resourcelog_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resourcelog
    ADD CONSTRAINT ovt_resourcelog_pkey PRIMARY KEY (resourcelogid);


--
-- Name: ovt_resourcestatus_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resourcestatus
    ADD CONSTRAINT ovt_resourcestatus_pkey PRIMARY KEY (resourcestatusid);


--
-- Name: ovt_resourcestatus_status_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resourcestatus
    ADD CONSTRAINT ovt_resourcestatus_status_key UNIQUE (status);


--
-- Name: ovt_resourcetype_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resourcetype
    ADD CONSTRAINT ovt_resourcetype_pkey PRIMARY KEY (resourcetypeid);


--
-- Name: ovt_resourcetype_resourcetypename_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resourcetype
    ADD CONSTRAINT ovt_resourcetype_resourcetypename_key UNIQUE (resourcetypename);


--
-- Name: ovt_resultboolean_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultboolean
    ADD CONSTRAINT ovt_resultboolean_pkey PRIMARY KEY (resultbooleanid);


--
-- Name: ovt_resultboolean_testrunactionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultboolean
    ADD CONSTRAINT ovt_resultboolean_testrunactionid_key UNIQUE (testrunactionid, resultfieldid);

ALTER TABLE ovt_resultboolean CLUSTER ON ovt_resultboolean_testrunactionid_key;


--
-- Name: ovt_resultfield_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultfield
    ADD CONSTRAINT ovt_resultfield_pkey PRIMARY KEY (resultfieldid);


--
-- Name: ovt_resultfloat_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultfloat
    ADD CONSTRAINT ovt_resultfloat_pkey PRIMARY KEY (resultfloatid);


--
-- Name: ovt_resultfloat_testrunactionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultfloat
    ADD CONSTRAINT ovt_resultfloat_testrunactionid_key UNIQUE (testrunactionid, resultfieldid);

ALTER TABLE ovt_resultfloat CLUSTER ON ovt_resultfloat_testrunactionid_key;


--
-- Name: ovt_resultinteger_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultinteger
    ADD CONSTRAINT ovt_resultinteger_pkey PRIMARY KEY (resultintegerid);


--
-- Name: ovt_resultinteger_testrunactionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultinteger
    ADD CONSTRAINT ovt_resultinteger_testrunactionid_key UNIQUE (testrunactionid, resultfieldid);

ALTER TABLE ovt_resultinteger CLUSTER ON ovt_resultinteger_testrunactionid_key;


--
-- Name: ovt_resultstring_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultstring
    ADD CONSTRAINT ovt_resultstring_pkey PRIMARY KEY (resultstringid);


--
-- Name: ovt_resultstring_testrunactionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resultstring
    ADD CONSTRAINT ovt_resultstring_testrunactionid_key UNIQUE (testrunactionid, resultfieldid);

ALTER TABLE ovt_resultstring CLUSTER ON ovt_resultstring_testrunactionid_key;


--
-- Name: ovt_resulttype_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_resulttype
    ADD CONSTRAINT ovt_resulttype_pkey PRIMARY KEY (resulttypeid);


--
-- Name: ovt_runstatus_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_runstatus
    ADD CONSTRAINT ovt_runstatus_pkey PRIMARY KEY (runstatusid);


--
-- Name: ovt_runstatus_status_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_runstatus
    ADD CONSTRAINT ovt_runstatus_status_key UNIQUE (status);


--
-- Name: ovt_simpleequivalence_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_simpleequivalence
    ADD CONSTRAINT ovt_simpleequivalence_pkey PRIMARY KEY (simpleequivalenceid);


--
-- Name: ovt_subrecursiveequivalence_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_subrecursiveequivalence
    ADD CONSTRAINT ovt_subrecursiveequivalence_pkey PRIMARY KEY (subrecursiveequivalenceid);


--
-- Name: ovt_subrecursiveequivalence_subrecursiveequivalencename_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_subrecursiveequivalence
    ADD CONSTRAINT ovt_subrecursiveequivalence_subrecursiveequivalencename_key UNIQUE (subrecursiveequivalencename);


--
-- Name: ovt_subscription_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_subscription
    ADD CONSTRAINT ovt_subscription_pkey PRIMARY KEY (subscriptionid);


--
-- Name: ovt_subscriptionentity_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_subscriptionentity
    ADD CONSTRAINT ovt_subscriptionentity_pkey PRIMARY KEY (subscriptionentityid);


--
-- Name: ovt_subscriptionentity_subscriptionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_subscriptionentity
    ADD CONSTRAINT ovt_subscriptionentity_subscriptionid_key UNIQUE (subscriptionid, notifyentityid, pkid);


--
-- Name: ovt_test_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_test
    ADD CONSTRAINT ovt_test_pkey PRIMARY KEY (testid);


--
-- Name: ovt_test_testname_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_test
    ADD CONSTRAINT ovt_test_testname_key UNIQUE (testname, testsuiteid);


--
-- Name: ovt_testresultboolean_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testresultboolean
    ADD CONSTRAINT ovt_testresultboolean_pkey PRIMARY KEY (testresultbooleanid);


--
-- Name: ovt_testresultboolean_testruntestid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testresultboolean
    ADD CONSTRAINT ovt_testresultboolean_testruntestid_key UNIQUE (testruntestid, resultfieldid);

ALTER TABLE ovt_testresultboolean CLUSTER ON ovt_testresultboolean_testruntestid_key;


--
-- Name: ovt_testresultfloat_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testresultfloat
    ADD CONSTRAINT ovt_testresultfloat_pkey PRIMARY KEY (testresultfloatid);


--
-- Name: ovt_testresultfloat_testruntestid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testresultfloat
    ADD CONSTRAINT ovt_testresultfloat_testruntestid_key UNIQUE (testruntestid, resultfieldid);

ALTER TABLE ovt_testresultfloat CLUSTER ON ovt_testresultfloat_testruntestid_key;


--
-- Name: ovt_testresultinteger_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testresultinteger
    ADD CONSTRAINT ovt_testresultinteger_pkey PRIMARY KEY (testresultintegerid);


--
-- Name: ovt_testresultinteger_testruntestid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testresultinteger
    ADD CONSTRAINT ovt_testresultinteger_testruntestid_key UNIQUE (testruntestid, resultfieldid);

ALTER TABLE ovt_testresultinteger CLUSTER ON ovt_testresultinteger_testruntestid_key;


--
-- Name: ovt_testresultstring_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testresultstring
    ADD CONSTRAINT ovt_testresultstring_pkey PRIMARY KEY (testresultstringid);


--
-- Name: ovt_testresultstring_testruntestid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testresultstring
    ADD CONSTRAINT ovt_testresultstring_testruntestid_key UNIQUE (testruntestid, resultfieldid);

ALTER TABLE ovt_testresultstring CLUSTER ON ovt_testresultstring_testruntestid_key;


--
-- Name: ovt_testrun_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrun
    ADD CONSTRAINT ovt_testrun_pkey PRIMARY KEY (testrunid);


--
-- Name: ovt_testrun_testrungroupid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrun
    ADD CONSTRAINT ovt_testrun_testrungroupid_key UNIQUE (testrungroupid, description);


--
-- Name: ovt_testrunaction_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrunaction
    ADD CONSTRAINT ovt_testrunaction_pkey PRIMARY KEY (testrunactionid);


--
-- Name: ovt_testrunaction_testrunid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrunaction
    ADD CONSTRAINT ovt_testrunaction_testrunid_key UNIQUE (testrunid, versionedactionid);


--
-- Name: ovt_testrunactionresource_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrunactionresource
    ADD CONSTRAINT ovt_testrunactionresource_pkey PRIMARY KEY (testrunactionresourceid);


--
-- Name: ovt_testrunactionresource_resourceid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrunactionresource
    ADD CONSTRAINT ovt_testrunactionresource_resourceid_key UNIQUE (resourceid, testrunactionid);


--
-- Name: ovt_testrunattributevalue_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrunattributevalue
    ADD CONSTRAINT ovt_testrunattributevalue_pkey PRIMARY KEY (testrunattributevalueid);


--
-- Name: ovt_testrunattributevalue_testrunid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrunattributevalue
    ADD CONSTRAINT ovt_testrunattributevalue_testrunid_key UNIQUE (testrunid, attributevalueid);


--
-- Name: ovt_testrungroup_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrungroup
    ADD CONSTRAINT ovt_testrungroup_pkey PRIMARY KEY (testrungroupid);


--
-- Name: ovt_testrungroup_testrungroupname_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrungroup
    ADD CONSTRAINT ovt_testrungroup_testrungroupname_key UNIQUE (testrungroupname, userid);


--
-- Name: ovt_testrunresource_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrunresource
    ADD CONSTRAINT ovt_testrunresource_pkey PRIMARY KEY (testrunresourceid);


--
-- Name: ovt_testrunresource_testrunid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testrunresource
    ADD CONSTRAINT ovt_testrunresource_testrunid_key UNIQUE (testrunid, resourceid);


--
-- Name: ovt_testruntest_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testruntest
    ADD CONSTRAINT ovt_testruntest_pkey PRIMARY KEY (testruntestid);


--
-- Name: ovt_testruntest_testrunid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testruntest
    ADD CONSTRAINT ovt_testruntest_testrunid_key UNIQUE (testrunid, versionedtestid);


--
-- Name: ovt_testsuite_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_testsuite
    ADD CONSTRAINT ovt_testsuite_pkey PRIMARY KEY (testsuiteid);


--
-- Name: ovt_user_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_user
    ADD CONSTRAINT ovt_user_pkey PRIMARY KEY (userid);


--
-- Name: ovt_user_username_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_user
    ADD CONSTRAINT ovt_user_username_key UNIQUE (username);


--
-- Name: ovt_userclaim_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_userclaim
    ADD CONSTRAINT ovt_userclaim_pkey PRIMARY KEY (userclaimid);


--
-- Name: ovt_userclaim_unique_reasons; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_userclaim
    ADD CONSTRAINT ovt_userclaim_unique_reasons UNIQUE (userid, reason, active);


--
-- Name: ovt_userclaimattributevalue_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_userclaimattributevalue
    ADD CONSTRAINT ovt_userclaimattributevalue_pkey PRIMARY KEY (userclaimattributevalue);


--
-- Name: ovt_userclaimattributevalue_userclaimid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_userclaimattributevalue
    ADD CONSTRAINT ovt_userclaimattributevalue_userclaimid_key UNIQUE (userclaimid, attributevalueid);


--
-- Name: ovt_userclaimresource_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_userclaimresource
    ADD CONSTRAINT ovt_userclaimresource_pkey PRIMARY KEY (userclaimresourceid);


--
-- Name: ovt_versionedaction_actionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedaction
    ADD CONSTRAINT ovt_versionedaction_actionid_key UNIQUE (actionid, versionname);


--
-- Name: ovt_versionedaction_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedaction
    ADD CONSTRAINT ovt_versionedaction_pkey PRIMARY KEY (versionedactionid);


--
-- Name: ovt_versionedactionattributevalue_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedactionattributevalue
    ADD CONSTRAINT ovt_versionedactionattributevalue_pkey PRIMARY KEY (versionedactionattributevalueid);


--
-- Name: ovt_versionedactionattributevalue_versionedactionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedactionattributevalue
    ADD CONSTRAINT ovt_versionedactionattributevalue_versionedactionid_key UNIQUE (versionedactionid, attributevalueid);


--
-- Name: ovt_versionedactionconfigoption_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedactionconfigoption
    ADD CONSTRAINT ovt_versionedactionconfigoption_pkey PRIMARY KEY (versionedactionconfigoptionid);


--
-- Name: ovt_versionedactionconfigoption_versionedactionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedactionconfigoption
    ADD CONSTRAINT ovt_versionedactionconfigoption_versionedactionid_key UNIQUE (versionedactionid, configoptionid);


--
-- Name: ovt_versionedactionconfigoptionlookup_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedactionconfigoptionlookup
    ADD CONSTRAINT ovt_versionedactionconfigoptionlookup_pkey PRIMARY KEY (versionedactionconfigoptionlookupid);


--
-- Name: ovt_versionedactionconfigoptionlookup_versionedactionid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedactionconfigoptionlookup
    ADD CONSTRAINT ovt_versionedactionconfigoptionlookup_versionedactionid_key UNIQUE (versionedactionid, configoptionlookupid);


--
-- Name: ovt_versionedtest_pkey; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedtest
    ADD CONSTRAINT ovt_versionedtest_pkey PRIMARY KEY (versionedtestid);


--
-- Name: ovt_versionedtest_testid_key; Type: CONSTRAINT; Schema: public; Owner: overtest; Tablespace: 
--

ALTER TABLE ONLY ovt_versionedtest
    ADD CONSTRAINT ovt_versionedtest_testid_key UNIQUE (testid, versionname);


--
-- Name: ovt_action_category_actionid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_action_category_actionid_index ON ovt_action USING btree (actionid, actioncategoryid);

ALTER TABLE ovt_action CLUSTER ON ovt_action_category_actionid_index;


--
-- Name: ovt_action_category_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_action_category_index ON ovt_action USING btree (actioncategoryid);


--
-- Name: ovt_attribute_resourcetype_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_attribute_resourcetype_index ON ovt_attribute USING btree (resourcetypeid);

ALTER TABLE ovt_attribute CLUSTER ON ovt_attribute_resourcetype_index;


--
-- Name: ovt_configsetting_equivalence_helper; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_configsetting_equivalence_helper ON ovt_configsetting USING btree (testrunid);


--
-- Name: ovt_dependency_mindepversionedaction_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_dependency_mindepversionedaction_index ON ovt_dependency USING btree (versionedactiondep);


--
-- Name: ovt_dependency_versionedactionid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_dependency_versionedactionid_index ON ovt_dependency USING btree (versionedactionid);


--
-- Name: ovt_resultboolean_testrunaction_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_resultboolean_testrunaction_index ON ovt_resultboolean USING btree (testrunactionid);


--
-- Name: ovt_resultfield_resultfieldname_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_resultfield_resultfieldname_index ON ovt_resultfield USING btree (resultfieldname);


--
-- Name: ovt_resultfloat_testrunaction_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_resultfloat_testrunaction_index ON ovt_resultfloat USING btree (testrunactionid);


--
-- Name: ovt_resultinteger_testrunaction_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_resultinteger_testrunaction_index ON ovt_resultinteger USING btree (testrunactionid);


--
-- Name: ovt_resultstring_testrunaction_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_resultstring_testrunaction_index ON ovt_resultstring USING btree (testrunactionid);


--
-- Name: ovt_test_testsuite_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_test_testsuite_index ON ovt_test USING btree (testsuiteid);


--
-- Name: ovt_test_testsuite_testid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_test_testsuite_testid_index ON ovt_test USING btree (testid, testsuiteid);

ALTER TABLE ovt_test CLUSTER ON ovt_test_testsuite_testid_index;


--
-- Name: ovt_testresultboolean_testruntest_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testresultboolean_testruntest_index ON ovt_testresultboolean USING btree (testruntestid);


--
-- Name: ovt_testresultfloat_testruntest_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testresultfloat_testruntest_index ON ovt_testresultfloat USING btree (testruntestid);


--
-- Name: ovt_testresultinteger_testruntest_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testresultinteger_testruntest_index ON ovt_testresultinteger USING btree (testruntestid);


--
-- Name: ovt_testresultstring_testruntest_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testresultstring_testruntest_index ON ovt_testresultstring USING btree (testruntestid);


--
-- Name: ovt_testrun_createddate_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrun_createddate_index ON ovt_testrun USING btree (createddate);


--
-- Name: ovt_testrun_priority_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrun_priority_index ON ovt_testrun USING btree (priority);


--
-- Name: ovt_testrun_userid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrun_userid_index ON ovt_testrun USING btree (userid);


--
-- Name: ovt_testrunaction_providedby_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunaction_providedby_index ON ovt_testrunaction USING btree (providedbytestrunid);


--
-- Name: ovt_testrunaction_recursiveequivalenceid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunaction_recursiveequivalenceid_index ON ovt_testrunaction USING btree (recursiveequivalenceid);


--
-- Name: ovt_testrunaction_simple_testrunid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunaction_simple_testrunid_index ON ovt_testrunaction USING btree (simpleequivalenceid, testrunid);

ALTER TABLE ovt_testrunaction CLUSTER ON ovt_testrunaction_simple_testrunid_index;


--
-- Name: ovt_testrunaction_simpleequivalenceid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunaction_simpleequivalenceid_index ON ovt_testrunaction USING btree (simpleequivalenceid);


--
-- Name: ovt_testrunaction_subrec_testrunid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunaction_subrec_testrunid_index ON ovt_testrunaction USING btree (subrecursiveequivalenceid, testrunid);


--
-- Name: ovt_testrunaction_subrecursiveequivalenceid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunaction_subrecursiveequivalenceid_index ON ovt_testrunaction USING btree (subrecursiveequivalenceid);


--
-- Name: ovt_testrunaction_testrunid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunaction_testrunid_index ON ovt_testrunaction USING btree (testrunid);


--
-- Name: ovt_testrunaction_versionedactionid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunaction_versionedactionid_index ON ovt_testrunaction USING btree (versionedactionid);


--
-- Name: ovt_testrunattibutevalue_attributevalue_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testrunattibutevalue_attributevalue_index ON ovt_testrunattributevalue USING btree (attributevalueid);


--
-- Name: ovt_testruntest_providedby_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testruntest_providedby_index ON ovt_testruntest USING btree (providedbytestrunid);


--
-- Name: ovt_testruntest_testrunid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testruntest_testrunid_index ON ovt_testruntest USING btree (testrunid);


--
-- Name: ovt_testruntest_versionedtestid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_testruntest_versionedtestid_index ON ovt_testruntest USING btree (versionedtestid);


--
-- Name: ovt_versionedaction_actionid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_versionedaction_actionid_index ON ovt_versionedaction USING btree (actionid);

ALTER TABLE ovt_versionedaction CLUSTER ON ovt_versionedaction_actionid_index;


--
-- Name: ovt_versionedaction_versionname_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_versionedaction_versionname_index ON ovt_versionedaction USING btree (versionname);


--
-- Name: ovt_versionedtest_testid_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_versionedtest_testid_index ON ovt_versionedtest USING btree (testid);

ALTER TABLE ovt_versionedtest CLUSTER ON ovt_versionedtest_testid_index;


--
-- Name: ovt_versionedtest_versionname_index; Type: INDEX; Schema: public; Owner: overtest; Tablespace: 
--

CREATE INDEX ovt_versionedtest_versionname_index ON ovt_versionedtest USING btree (versionname);


--
-- Name: ovt_attributevalue_alter_equivcheck; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_attributevalue_alter_equivcheck
    BEFORE INSERT OR DELETE OR UPDATE ON ovt_testrunattributevalue
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_testrunattributevalue_equivcheck();


--
-- Name: ovt_configoption_alter_equivcheck; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_configoption_alter_equivcheck
    BEFORE UPDATE ON ovt_configoption
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_configoption_equivcheck();


--
-- Name: ovt_configoptionlookupattributevalue_alter_equivcheck; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_configoptionlookupattributevalue_alter_equivcheck
    BEFORE INSERT OR DELETE OR UPDATE ON ovt_configoptionlookupattributevalue
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_configoptionlookupattributevalue_alter_equivcheck();


--
-- Name: ovt_configsetting_alter_equivcheck; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_configsetting_alter_equivcheck
    BEFORE INSERT OR DELETE OR UPDATE ON ovt_configsetting
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_configsetting_equivcheck();


--
-- Name: ovt_dependency_alter_equivcheck; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_dependency_alter_equivcheck
    BEFORE INSERT OR DELETE OR UPDATE ON ovt_dependency
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_dependency_equivcheck();


--
-- Name: ovt_resource_resourcename_change; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_resource_resourcename_change
    BEFORE INSERT OR UPDATE ON ovt_resource
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_resource_resourcename_check();


--
-- Name: ovt_testrun_equivalence; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_testrun_equivalence
    AFTER UPDATE ON ovt_testrun
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_testrun_performequivalance();


--
-- Name: ovt_testrunaction_alter_equivcheck; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_testrunaction_alter_equivcheck
    BEFORE INSERT OR DELETE OR UPDATE ON ovt_testrunaction
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_testrunaction_equivcheck();


--
-- Name: ovt_testrunaction_alter_equivcheck_afterupdate; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_testrunaction_alter_equivcheck_afterupdate
    AFTER UPDATE ON ovt_testrunaction
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_testrunaction_equivcheck_afterupdate();


--
-- Name: ovt_userclaim_unique_claim_check; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_userclaim_unique_claim_check
    BEFORE INSERT OR UPDATE ON ovt_userclaim
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_unique_claim_check();


--
-- Name: ovt_versionedactionattributevalue_alter_equivcheck; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_versionedactionattributevalue_alter_equivcheck
    BEFORE INSERT OR DELETE OR UPDATE ON ovt_versionedactionattributevalue
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_versionedactionattributevalue_equivcheck();


--
-- Name: ovt_versionedactionconfigoption_alter_equivcheck; Type: TRIGGER; Schema: public; Owner: overtest
--

CREATE TRIGGER ovt_versionedactionconfigoption_alter_equivcheck
    BEFORE INSERT OR DELETE OR UPDATE ON ovt_versionedactionconfigoption
    FOR EACH ROW
    EXECUTE PROCEDURE ovt_versionedactionconfigoption_equivcheck();


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrun
    ADD CONSTRAINT "$1" FOREIGN KEY (userid) REFERENCES ovt_user(userid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedaction
    ADD CONSTRAINT "$1" FOREIGN KEY (actionid) REFERENCES ovt_action(actionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_dependency
    ADD CONSTRAINT "$1" FOREIGN KEY (versionedactionid) REFERENCES ovt_versionedaction(versionedactionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunaction
    ADD CONSTRAINT "$1" FOREIGN KEY (testrunid) REFERENCES ovt_testrun(testrunid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoptionlookup
    ADD CONSTRAINT "$1" FOREIGN KEY (configoptionid) REFERENCES ovt_configoption(configoptionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configsetting
    ADD CONSTRAINT "$1" FOREIGN KEY (configoptionid) REFERENCES ovt_configoption(configoptionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoption
    ADD CONSTRAINT "$1" FOREIGN KEY (configoptiontypeid) REFERENCES ovt_configoptiontype(configoptiontypeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedtest
    ADD CONSTRAINT "$1" FOREIGN KEY (testid) REFERENCES ovt_test(testid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $1; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testruntest
    ADD CONSTRAINT "$1" FOREIGN KEY (testrunid) REFERENCES ovt_testrun(testrunid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $2; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configsetting
    ADD CONSTRAINT "$2" FOREIGN KEY (configoptionlookupid) REFERENCES ovt_configoptionlookup(configoptionlookupid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: $4; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_dependency
    ADD CONSTRAINT "$4" FOREIGN KEY (dependencygroupid) REFERENCES ovt_dependencygroup(dependencygroupid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_action_actioncategoryid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_action
    ADD CONSTRAINT ovt_action_actioncategoryid_fkey FOREIGN KEY (actioncategoryid) REFERENCES ovt_actioncategory(actioncategoryid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_action_lifecyclestateid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_action
    ADD CONSTRAINT ovt_action_lifecyclestateid_fkey FOREIGN KEY (lifecyclestateid) REFERENCES ovt_lifecyclestate(lifecyclestateid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_action_testsuiteid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_action
    ADD CONSTRAINT ovt_action_testsuiteid_fkey FOREIGN KEY (testsuiteid) REFERENCES ovt_testsuite(testsuiteid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_actioncategory_lifecyclestateid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_actioncategory
    ADD CONSTRAINT ovt_actioncategory_lifecyclestateid_fkey FOREIGN KEY (lifecyclestateid) REFERENCES ovt_lifecyclestate(lifecyclestateid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_attribute_resourcetypeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_attribute
    ADD CONSTRAINT ovt_attribute_resourcetypeid_fkey FOREIGN KEY (resourcetypeid) REFERENCES ovt_resourcetype(resourcetypeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_attributevalue_attributeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_attributevalue
    ADD CONSTRAINT ovt_attributevalue_attributeid_fkey FOREIGN KEY (attributeid) REFERENCES ovt_attribute(attributeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_chart_charttypeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_chart
    ADD CONSTRAINT ovt_chart_charttypeid_fkey FOREIGN KEY (charttypeid) REFERENCES ovt_charttype(charttypeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_chart_testsuiteid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_chart
    ADD CONSTRAINT ovt_chart_testsuiteid_fkey FOREIGN KEY (testsuiteid) REFERENCES ovt_testsuite(testsuiteid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_chart_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_chart
    ADD CONSTRAINT ovt_chart_userid_fkey FOREIGN KEY (userid) REFERENCES ovt_user(userid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_chartfield_chartid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_chartfield
    ADD CONSTRAINT ovt_chartfield_chartid_fkey FOREIGN KEY (chartid) REFERENCES ovt_chart(chartid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_chartfield_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_chartfield
    ADD CONSTRAINT ovt_chartfield_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_charttest_chartid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_charttest
    ADD CONSTRAINT ovt_charttest_chartid_fkey FOREIGN KEY (chartid) REFERENCES ovt_chart(chartid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_charttest_testid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_charttest
    ADD CONSTRAINT ovt_charttest_testid_fkey FOREIGN KEY (testid) REFERENCES ovt_test(testid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_configoption_configoptiongroupid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoption
    ADD CONSTRAINT ovt_configoption_configoptiongroupid_fkey FOREIGN KEY (configoptiongroupid) REFERENCES ovt_configoptiongroup(configoptiongroupid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_configoptionlookupattributevalue_attributevalueid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoptionlookupattributevalue
    ADD CONSTRAINT ovt_configoptionlookupattributevalue_attributevalueid_fkey FOREIGN KEY (attributevalueid) REFERENCES ovt_attributevalue(attributevalueid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_configoptionlookupattributevalue_configoptionlookupid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configoptionlookupattributevalue
    ADD CONSTRAINT ovt_configoptionlookupattributevalue_configoptionlookupid_fkey FOREIGN KEY (configoptionlookupid) REFERENCES ovt_configoptionlookup(configoptionlookupid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_configsetting_testrunid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_configsetting
    ADD CONSTRAINT ovt_configsetting_testrunid_fkey FOREIGN KEY (testrunid) REFERENCES ovt_testrun(testrunid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_dependency_versionedactiondep_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_dependency
    ADD CONSTRAINT ovt_dependency_versionedactiondep_fkey FOREIGN KEY (versionedactiondep) REFERENCES ovt_versionedaction(versionedactionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_goldresult_actionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_goldresult
    ADD CONSTRAINT ovt_goldresult_actionid_fkey FOREIGN KEY (actionid) REFERENCES ovt_action(actionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_goldresult_testrunid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_goldresult
    ADD CONSTRAINT ovt_goldresult_testrunid_fkey FOREIGN KEY (testrunid) REFERENCES ovt_testrun(testrunid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_goldresult_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_goldresult
    ADD CONSTRAINT ovt_goldresult_userid_fkey FOREIGN KEY (userid) REFERENCES ovt_user(userid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_history_notifytypeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_history
    ADD CONSTRAINT ovt_history_notifytypeid_fkey FOREIGN KEY (notifytypeid) REFERENCES ovt_notifytype(notifytypeid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_history_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_history
    ADD CONSTRAINT ovt_history_userid_fkey FOREIGN KEY (userid) REFERENCES ovt_user(userid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_historypk_historyid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_historypk
    ADD CONSTRAINT ovt_historypk_historyid_fkey FOREIGN KEY (historyid) REFERENCES ovt_history(historyid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_historypk_notifyentityid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_historypk
    ADD CONSTRAINT ovt_historypk_notifyentityid_fkey FOREIGN KEY (notifyentityid) REFERENCES ovt_notifyentity(notifyentityid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_notifytypeentity_notifyentityid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_notifytypeentity
    ADD CONSTRAINT ovt_notifytypeentity_notifyentityid_fkey FOREIGN KEY (notifyentityid) REFERENCES ovt_notifyentity(notifyentityid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_notifytypeentity_notifytypeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_notifytypeentity
    ADD CONSTRAINT ovt_notifytypeentity_notifytypeid_fkey FOREIGN KEY (notifytypeid) REFERENCES ovt_notifytype(notifytypeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_resource_baseresourceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resource
    ADD CONSTRAINT ovt_resource_baseresourceid_fkey FOREIGN KEY (baseresourceid) REFERENCES ovt_resource(resourceid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_resource_resourcestatusid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resource
    ADD CONSTRAINT ovt_resource_resourcestatusid_fkey FOREIGN KEY (resourcestatusid) REFERENCES ovt_resourcestatus(resourcestatusid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_resource_resourcetypeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resource
    ADD CONSTRAINT ovt_resource_resourcetypeid_fkey FOREIGN KEY (resourcetypeid) REFERENCES ovt_resourcetype(resourcetypeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_resourceattribute_attributeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resourceattribute
    ADD CONSTRAINT ovt_resourceattribute_attributeid_fkey FOREIGN KEY (attributeid) REFERENCES ovt_attribute(attributeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_resourceattribute_attributevalueid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resourceattribute
    ADD CONSTRAINT ovt_resourceattribute_attributevalueid_fkey FOREIGN KEY (attributevalueid) REFERENCES ovt_attributevalue(attributevalueid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_resourceattribute_resourceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resourceattribute
    ADD CONSTRAINT ovt_resourceattribute_resourceid_fkey FOREIGN KEY (resourceid) REFERENCES ovt_resource(resourceid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_resourcelog_resourceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resourcelog
    ADD CONSTRAINT ovt_resourcelog_resourceid_fkey FOREIGN KEY (resourceid) REFERENCES ovt_resource(resourceid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_resultboolean_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultboolean
    ADD CONSTRAINT ovt_resultboolean_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_resultboolean_testrunactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultboolean
    ADD CONSTRAINT ovt_resultboolean_testrunactionid_fkey FOREIGN KEY (testrunactionid) REFERENCES ovt_testrunaction(testrunactionid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_resultfield_resulttypeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultfield
    ADD CONSTRAINT ovt_resultfield_resulttypeid_fkey FOREIGN KEY (resulttypeid) REFERENCES ovt_resulttype(resulttypeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_resultfloat_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultfloat
    ADD CONSTRAINT ovt_resultfloat_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_resultfloat_testrunactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultfloat
    ADD CONSTRAINT ovt_resultfloat_testrunactionid_fkey FOREIGN KEY (testrunactionid) REFERENCES ovt_testrunaction(testrunactionid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_resultinteger_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultinteger
    ADD CONSTRAINT ovt_resultinteger_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_resultinteger_testrunactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultinteger
    ADD CONSTRAINT ovt_resultinteger_testrunactionid_fkey FOREIGN KEY (testrunactionid) REFERENCES ovt_testrunaction(testrunactionid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_resultstring_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultstring
    ADD CONSTRAINT ovt_resultstring_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_resultstring_testrunactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_resultstring
    ADD CONSTRAINT ovt_resultstring_testrunactionid_fkey FOREIGN KEY (testrunactionid) REFERENCES ovt_testrunaction(testrunactionid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_subscription_notifymethodid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_subscription
    ADD CONSTRAINT ovt_subscription_notifymethodid_fkey FOREIGN KEY (notifymethodid) REFERENCES ovt_notifymethod(notifymethodid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_subscription_notifytypeid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_subscription
    ADD CONSTRAINT ovt_subscription_notifytypeid_fkey FOREIGN KEY (notifytypeid) REFERENCES ovt_notifytype(notifytypeid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_subscription_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_subscription
    ADD CONSTRAINT ovt_subscription_userid_fkey FOREIGN KEY (userid) REFERENCES ovt_user(userid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_subscriptionentity_notifyentityid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_subscriptionentity
    ADD CONSTRAINT ovt_subscriptionentity_notifyentityid_fkey FOREIGN KEY (notifyentityid) REFERENCES ovt_notifyentity(notifyentityid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_subscriptionentity_subscriptionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_subscriptionentity
    ADD CONSTRAINT ovt_subscriptionentity_subscriptionid_fkey FOREIGN KEY (subscriptionid) REFERENCES ovt_subscription(subscriptionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_test_testsuiteid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_test
    ADD CONSTRAINT ovt_test_testsuiteid_fkey FOREIGN KEY (testsuiteid) REFERENCES ovt_testsuite(testsuiteid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_testresultboolean_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultboolean
    ADD CONSTRAINT ovt_testresultboolean_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testresultboolean_testruntestid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultboolean
    ADD CONSTRAINT ovt_testresultboolean_testruntestid_fkey FOREIGN KEY (testruntestid) REFERENCES ovt_testruntest(testruntestid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testresultfloat_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultfloat
    ADD CONSTRAINT ovt_testresultfloat_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testresultfloat_testruntestid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultfloat
    ADD CONSTRAINT ovt_testresultfloat_testruntestid_fkey FOREIGN KEY (testruntestid) REFERENCES ovt_testruntest(testruntestid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testresultinteger_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultinteger
    ADD CONSTRAINT ovt_testresultinteger_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testresultinteger_testruntestid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultinteger
    ADD CONSTRAINT ovt_testresultinteger_testruntestid_fkey FOREIGN KEY (testruntestid) REFERENCES ovt_testruntest(testruntestid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testresultstring_resultfieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultstring
    ADD CONSTRAINT ovt_testresultstring_resultfieldid_fkey FOREIGN KEY (resultfieldid) REFERENCES ovt_resultfield(resultfieldid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testresultstring_testruntestid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testresultstring
    ADD CONSTRAINT ovt_testresultstring_testruntestid_fkey FOREIGN KEY (testruntestid) REFERENCES ovt_testruntest(testruntestid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testrun_runstatusid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrun
    ADD CONSTRAINT ovt_testrun_runstatusid_fkey FOREIGN KEY (runstatusid) REFERENCES ovt_runstatus(runstatusid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_testrun_testrungroupid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrun
    ADD CONSTRAINT ovt_testrun_testrungroupid_fkey FOREIGN KEY (testrungroupid) REFERENCES ovt_testrungroup(testrungroupid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_testrunaction_providedbytestrunid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunaction
    ADD CONSTRAINT ovt_testrunaction_providedbytestrunid_fkey FOREIGN KEY (providedbytestrunid) REFERENCES ovt_testrun(testrunid) ON UPDATE RESTRICT ON DELETE SET NULL;


--
-- Name: ovt_testrunaction_recursiveequivalenceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunaction
    ADD CONSTRAINT ovt_testrunaction_recursiveequivalenceid_fkey FOREIGN KEY (recursiveequivalenceid) REFERENCES ovt_recursiveequivalence(recursiveequivalenceid) ON UPDATE RESTRICT ON DELETE SET NULL;


--
-- Name: ovt_testrunaction_simpleequivalenceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunaction
    ADD CONSTRAINT ovt_testrunaction_simpleequivalenceid_fkey FOREIGN KEY (simpleequivalenceid) REFERENCES ovt_simpleequivalence(simpleequivalenceid) ON UPDATE RESTRICT ON DELETE SET NULL;


--
-- Name: ovt_testrunaction_subrecursiveequivalenceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunaction
    ADD CONSTRAINT ovt_testrunaction_subrecursiveequivalenceid_fkey FOREIGN KEY (subrecursiveequivalenceid) REFERENCES ovt_subrecursiveequivalence(subrecursiveequivalenceid) ON UPDATE RESTRICT ON DELETE SET NULL;


--
-- Name: ovt_testrunaction_versionedactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunaction
    ADD CONSTRAINT ovt_testrunaction_versionedactionid_fkey FOREIGN KEY (versionedactionid) REFERENCES ovt_versionedaction(versionedactionid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testrunactionresource_resourceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunactionresource
    ADD CONSTRAINT ovt_testrunactionresource_resourceid_fkey FOREIGN KEY (resourceid) REFERENCES ovt_resource(resourceid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_testrunactionresource_testrunactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunactionresource
    ADD CONSTRAINT ovt_testrunactionresource_testrunactionid_fkey FOREIGN KEY (testrunactionid) REFERENCES ovt_testrunaction(testrunactionid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_testrunattributevalue_attributevalueid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunattributevalue
    ADD CONSTRAINT ovt_testrunattributevalue_attributevalueid_fkey FOREIGN KEY (attributevalueid) REFERENCES ovt_attributevalue(attributevalueid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_testrunattributevalue_testrunid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunattributevalue
    ADD CONSTRAINT ovt_testrunattributevalue_testrunid_fkey FOREIGN KEY (testrunid) REFERENCES ovt_testrun(testrunid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_testrungroup_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrungroup
    ADD CONSTRAINT ovt_testrungroup_userid_fkey FOREIGN KEY (userid) REFERENCES ovt_user(userid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_testrunresource_resourceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunresource
    ADD CONSTRAINT ovt_testrunresource_resourceid_fkey FOREIGN KEY (resourceid) REFERENCES ovt_resource(resourceid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_testrunresource_testrunid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testrunresource
    ADD CONSTRAINT ovt_testrunresource_testrunid_fkey FOREIGN KEY (testrunid) REFERENCES ovt_testrun(testrunid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_testruntest_providedbytestrunid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testruntest
    ADD CONSTRAINT ovt_testruntest_providedbytestrunid_fkey FOREIGN KEY (providedbytestrunid) REFERENCES ovt_testrun(testrunid) ON UPDATE RESTRICT ON DELETE SET NULL;


--
-- Name: ovt_testruntest_versionedtestid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_testruntest
    ADD CONSTRAINT ovt_testruntest_versionedtestid_fkey FOREIGN KEY (versionedtestid) REFERENCES ovt_versionedtest(versionedtestid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ovt_userclaim_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_userclaim
    ADD CONSTRAINT ovt_userclaim_userid_fkey FOREIGN KEY (userid) REFERENCES ovt_user(userid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_userclaimattributevalue_attributevalueid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_userclaimattributevalue
    ADD CONSTRAINT ovt_userclaimattributevalue_attributevalueid_fkey FOREIGN KEY (attributevalueid) REFERENCES ovt_attributevalue(attributevalueid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_userclaimattributevalue_userclaimid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_userclaimattributevalue
    ADD CONSTRAINT ovt_userclaimattributevalue_userclaimid_fkey FOREIGN KEY (userclaimid) REFERENCES ovt_userclaim(userclaimid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_userclaimresource_resourceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_userclaimresource
    ADD CONSTRAINT ovt_userclaimresource_resourceid_fkey FOREIGN KEY (resourceid) REFERENCES ovt_resource(resourceid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_userclaimresource_userclaimid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_userclaimresource
    ADD CONSTRAINT ovt_userclaimresource_userclaimid_fkey FOREIGN KEY (userclaimid) REFERENCES ovt_userclaim(userclaimid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_versionedaction_lifecyclestateid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedaction
    ADD CONSTRAINT ovt_versionedaction_lifecyclestateid_fkey FOREIGN KEY (lifecyclestateid) REFERENCES ovt_lifecyclestate(lifecyclestateid) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- Name: ovt_versionedactionattributevalue_attributevalueid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionattributevalue
    ADD CONSTRAINT ovt_versionedactionattributevalue_attributevalueid_fkey FOREIGN KEY (attributevalueid) REFERENCES ovt_attributevalue(attributevalueid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_versionedactionattributevalue_versionedactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionattributevalue
    ADD CONSTRAINT ovt_versionedactionattributevalue_versionedactionid_fkey FOREIGN KEY (versionedactionid) REFERENCES ovt_versionedaction(versionedactionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_versionedactionconfigoption_configoptionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionconfigoption
    ADD CONSTRAINT ovt_versionedactionconfigoption_configoptionid_fkey FOREIGN KEY (configoptionid) REFERENCES ovt_configoption(configoptionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_versionedactionconfigoption_versionedactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionconfigoption
    ADD CONSTRAINT ovt_versionedactionconfigoption_versionedactionid_fkey FOREIGN KEY (versionedactionid) REFERENCES ovt_versionedaction(versionedactionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_versionedactionconfigoptionlookup_configoptionlookupid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionconfigoptionlookup
    ADD CONSTRAINT ovt_versionedactionconfigoptionlookup_configoptionlookupid_fkey FOREIGN KEY (configoptionlookupid) REFERENCES ovt_configoptionlookup(configoptionlookupid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: ovt_versionedactionconfigoptionlookup_versionedactionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: overtest
--

ALTER TABLE ONLY ovt_versionedactionconfigoptionlookup
    ADD CONSTRAINT ovt_versionedactionconfigoptionlookup_versionedactionid_fkey FOREIGN KEY (versionedactionid) REFERENCES ovt_versionedaction(versionedactionid) ON UPDATE RESTRICT ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO overtest;
GRANT ALL ON SCHEMA public TO mfortune WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

