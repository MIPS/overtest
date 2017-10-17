--- Overtest version type and operators                      -*- sql -*-
---
--- Copyright © 20012 Matthew Fortune <matthew.fortune@imgtec.com>
--- Copyright © 2008 Roger Leigh <rleigh@debian.org>
---
--- This program is free software: you can redistribute it and/or modify
--- it under the terms of the GNU General Public License as published by
--- the Free Software Foundation, either version 2 of the License, or
--- (at your option) any later version.
---
--- This program is distributed in the hope that it will be useful, but
--- WITHOUT ANY WARRANTY; without even the implied warranty of
--- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
--- General Public License for more details.
---
--- You should have received a copy of the GNU General Public License
--- along with this program.  If not, see
--- <http://www.gnu.org/licenses/>.

CREATE TYPE ovtversion;

CREATE OR REPLACE FUNCTION ovtversionin(cstring)
  RETURNS ovtversion
  AS 'textin'
  LANGUAGE 'internal'
  IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION ovtversionout(ovtversion)
  RETURNS cstring
  AS 'textout'
  LANGUAGE 'internal'
  IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION ovtversionrecv(internal)
  RETURNS ovtversion
  AS 'textrecv'
  LANGUAGE 'internal'
  STABLE STRICT;

CREATE OR REPLACE FUNCTION ovtversionsend(ovtversion)
  RETURNS bytea
  AS 'textsend'
  LANGUAGE 'internal'
  STABLE STRICT;

CREATE TYPE ovtversion (
    LIKE           = text,
    INPUT          = ovtversionin,
    OUTPUT         = ovtversionout,
    RECEIVE        = ovtversionrecv,
    SEND           = ovtversionsend,
    -- make it a non-preferred member of string type category
    CATEGORY       = 'S',
    PREFERRED      = false
);

COMMENT ON TYPE ovtversion IS 'Overtest version number';

CREATE OR REPLACE FUNCTION ovtversion(bpchar)
  RETURNS ovtversion
  AS 'rtrim1'
  LANGUAGE 'internal'
  IMMUTABLE STRICT;

CREATE CAST (ovtversion AS text)    WITHOUT FUNCTION AS IMPLICIT;
CREATE CAST (ovtversion AS varchar) WITHOUT FUNCTION AS IMPLICIT;
CREATE CAST (ovtversion AS bpchar)  WITHOUT FUNCTION AS ASSIGNMENT;
CREATE CAST (text AS ovtversion)    WITHOUT FUNCTION AS ASSIGNMENT;
CREATE CAST (varchar AS ovtversion) WITHOUT FUNCTION AS ASSIGNMENT;
CREATE CAST (bpchar AS ovtversion)  WITH FUNCTION ovtversion(bpchar);

CREATE OR REPLACE FUNCTION ovtversion_cmp (version1 ovtversion,
       	  	  	   		   version2 ovtversion)
  RETURNS integer AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;
COMMENT ON FUNCTION ovtversion_cmp (ovtversion, ovtversion)
  IS 'Compare Overtest versions';

CREATE OR REPLACE FUNCTION ovtversion_eq (version1 ovtversion,
       	  	  	   		  version2 ovtversion)
  RETURNS boolean AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;
COMMENT ON FUNCTION ovtversion_eq (ovtversion, ovtversion)
  IS 'ovtversion equal';

CREATE OR REPLACE FUNCTION ovtversion_ne (version1 ovtversion,
       	  	  	   		  version2 ovtversion)
  RETURNS boolean AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;
COMMENT ON FUNCTION ovtversion_ne (ovtversion, ovtversion)
  IS 'ovtversion not equal';

CREATE OR REPLACE FUNCTION ovtversion_lt (version1 ovtversion,
       	  	  	   		  version2 ovtversion)
  RETURNS boolean AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;
COMMENT ON FUNCTION ovtversion_lt (ovtversion, ovtversion)
  IS 'ovtversion less-than';

CREATE OR REPLACE FUNCTION ovtversion_gt (version1 ovtversion,
       	  	  	   		  version2 ovtversion)
  RETURNS boolean AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;
COMMENT ON FUNCTION ovtversion_gt (ovtversion, ovtversion)
  IS 'ovtversion greater-than';

CREATE OR REPLACE FUNCTION ovtversion_le (version1 ovtversion,
       	  	  	   		  version2 ovtversion)
  RETURNS boolean AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;
COMMENT ON FUNCTION ovtversion_le (ovtversion, ovtversion)
  IS 'ovtversion less-than-or-equal';

CREATE OR REPLACE FUNCTION ovtversion_ge (version1 ovtversion,
       	  	  	   		  version2 ovtversion)
  RETURNS boolean AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;
COMMENT ON FUNCTION ovtversion_ge (ovtversion, ovtversion)
  IS 'ovtversion greater-than-or-equal';

CREATE OPERATOR = (
  PROCEDURE = ovtversion_eq,
  LEFTARG = ovtversion,
  RIGHTARG = ovtversion,
  COMMUTATOR = =,
  NEGATOR = !=
);
COMMENT ON OPERATOR = (ovtversion, ovtversion)
  IS 'ovtversion equal';

CREATE OPERATOR != (
  PROCEDURE = ovtversion_ne,
  LEFTARG = ovtversion,
  RIGHTARG = ovtversion,
  COMMUTATOR = !=,
  NEGATOR = =
);
COMMENT ON OPERATOR != (ovtversion, ovtversion)
  IS 'ovtversion not equal';

CREATE OPERATOR < (
  PROCEDURE = ovtversion_lt,
  LEFTARG = ovtversion,
  RIGHTARG = ovtversion,
  COMMUTATOR = >,
  NEGATOR = >=
);
COMMENT ON OPERATOR < (ovtversion, ovtversion)
  IS 'ovtversion less-than';

CREATE OPERATOR > (
  PROCEDURE = ovtversion_gt,
  LEFTARG = ovtversion,
  RIGHTARG = ovtversion,
  COMMUTATOR = <,
  NEGATOR = >=
);
COMMENT ON OPERATOR > (ovtversion, ovtversion)
  IS 'ovtversion greater-than';

CREATE OPERATOR <= (
  PROCEDURE = ovtversion_le,
  LEFTARG = ovtversion,
  RIGHTARG = ovtversion,
  COMMUTATOR = >=,
  NEGATOR = >
);
COMMENT ON OPERATOR <= (ovtversion, ovtversion)
  IS 'ovtversion less-than-or-equal';

CREATE OPERATOR >= (
  PROCEDURE = ovtversion_ge,
  LEFTARG = ovtversion,
  RIGHTARG = ovtversion,
  COMMUTATOR = <=,
  NEGATOR = <
);
COMMENT ON OPERATOR >= (ovtversion, ovtversion)
  IS 'ovtversion greater-than-or-equal';

CREATE OPERATOR CLASS ovtversion_ops
DEFAULT FOR TYPE ovtversion USING btree AS
  OPERATOR 1 <  (ovtversion, ovtversion),
  OPERATOR 2 <= (ovtversion, ovtversion),
  OPERATOR 3 =  (ovtversion, ovtversion),
  OPERATOR 4 >= (ovtversion, ovtversion),
  OPERATOR 5 >  (ovtversion, ovtversion),
  FUNCTION 1 ovtversion_cmp(ovtversion, ovtversion);

CREATE OR REPLACE FUNCTION ovtversion_hash(ovtversion)
  RETURNS int4
  AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;

CREATE OPERATOR CLASS ovtversion_ops
DEFAULT FOR TYPE ovtversion USING hash AS
  OPERATOR 1 = (ovtversion, ovtversion),
  FUNCTION 1 ovtversion_hash(ovtversion);

CREATE OR REPLACE FUNCTION ovtversion_smaller(version1 ovtversion,
					      version2 ovtversion)
  RETURNS ovtversion
  AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;

CREATE OR REPLACE FUNCTION ovtversion_larger(version1 ovtversion,
					     version2 ovtversion)
  RETURNS ovtversion
  AS '$libdir/ovtversion'
  LANGUAGE 'C'
  IMMUTABLE STRICT;

CREATE AGGREGATE min(ovtversion)  (
  SFUNC = ovtversion_smaller,
  STYPE = ovtversion,
  SORTOP = <
);

CREATE AGGREGATE max(ovtversion)  (
  SFUNC = ovtversion_larger,
  STYPE = ovtversion,
  SORTOP = >
);

