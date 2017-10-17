/*
 * ovtversion: PostgreSQL functions for ovtversion type
 * Copyright © 20012  Matthew Fortune <matthew.fortune@imgtec.com>
 * Copyright © 2009,2011  Roger Leigh <rleigh@debian.org>
 * schroot is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * schroot is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see
 * <http://www.gnu.org/licenses/>.
 *
 *********************************************************************/


#include <postgres.h>
#include <fmgr.h>
#include <access/hash.h>
#include <utils/builtins.h>
#include <stdlib.h>

#ifdef PG_MODULE_MAGIC
  PG_MODULE_MAGIC;
#endif

  int32 ovtversioncmp (text *, text *);
  extern Datum ovtversion_cmp (PG_FUNCTION_ARGS);
  extern Datum ovtversion_hash (PG_FUNCTION_ARGS);
  extern Datum ovtversion_eq (PG_FUNCTION_ARGS);
  extern Datum ovtversion_ne (PG_FUNCTION_ARGS);
  extern Datum ovtversion_gt (PG_FUNCTION_ARGS);
  extern Datum ovtversion_ge (PG_FUNCTION_ARGS);
  extern Datum ovtversion_lt (PG_FUNCTION_ARGS);
  extern Datum ovtversion_le (PG_FUNCTION_ARGS);
  extern Datum ovtversion_smaller (PG_FUNCTION_ARGS);
  extern Datum ovtversion_larger (PG_FUNCTION_ARGS);

  int32
  ovtversioncmp (text *left,
		 text *right)
  {
    int32 result;
    char *lstr, *rstr;
    char *lstr_buf = NULL, *rstr_buf = NULL;
    char *lstr_tok, *rstr_tok;

    lstr = text_to_cstring(left);
    rstr = text_to_cstring(right);

    lstr_tok = strtok_r (lstr, ".", &lstr_buf);
    rstr_tok = strtok_r (rstr, ".", &rstr_buf);

    while (lstr_tok != NULL
           && rstr_tok != NULL)
    {
      result = strcmp (lstr_tok, rstr_tok);

      if (result != 0)
      {
        long int lint, rint;
        char *lint_end, *rint_end;
      
        lint = strtol (lstr_tok, &lint_end, 10);
        rint = strtol (rstr_tok, &rint_end, 10);
      
        if (lint_end != lstr_tok && rint_end != rstr_tok)
        {
          /* Both are numbers (may be more characters) */
          if (lint == rint)
          {
            /* Need to consider remaining characters */
            result = strcmp (lint_end, rint_end);
          }
          else
          {
            result = (lint < rint) ? -1 : 1;
          }
        }
        else if (lint_end != lstr_tok)
        {
          /* The left side is a number, therefore smaller */
          result = -1;
        }
        else if (rint_end != rstr_tok)
        {
          /* The right side is a number, therefore bigger */
          result = 1;
        }

        if (result != 0)
        {
          break;
        }
      }

      lstr_tok = strtok_r (NULL, ".", &lstr_buf);
      rstr_tok = strtok_r (NULL, ".", &rstr_buf);
    }

    if (lstr_tok == NULL && rstr_tok != NULL)
    {
      result = -1;
    }
    else if (lstr_tok != NULL && rstr_tok == NULL)
    {
      result = 1;
    }

    pfree (lstr);
    pfree (rstr);

    return (result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_cmp);

  Datum
  ovtversion_cmp(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    int32 result;

    result = ovtversioncmp(left, right);

    PG_FREE_IF_COPY(left, 0);
    PG_FREE_IF_COPY(right, 1);

    PG_RETURN_INT32(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_hash);

  Datum
  ovtversion_hash(PG_FUNCTION_ARGS)
  {
    text *txt = PG_GETARG_TEXT_PP(0);
    char *str;
    Datum result;

    str = text_to_cstring(txt);

    result = hash_any((unsigned char *) str, strlen(str));
    pfree(str);

    PG_FREE_IF_COPY(txt, 0);

    PG_RETURN_DATUM(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_eq);

  Datum
  ovtversion_eq(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    bool  result;

    result = ovtversioncmp(left, right) == 0;

    PG_FREE_IF_COPY(left, 0);
    PG_FREE_IF_COPY(right, 1);

    PG_RETURN_BOOL(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_ne);

  Datum
  ovtversion_ne(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    bool  result;

    result = ovtversioncmp(left, right) != 0;

    PG_FREE_IF_COPY(left, 0);
    PG_FREE_IF_COPY(right, 1);

    PG_RETURN_BOOL(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_lt);

  Datum
  ovtversion_lt(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    bool  result;

    result = ovtversioncmp(left, right) < 0;

    PG_FREE_IF_COPY(left, 0);
    PG_FREE_IF_COPY(right, 1);

    PG_RETURN_BOOL(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_le);

  Datum
  ovtversion_le(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    bool  result;

    result = ovtversioncmp(left, right) <= 0;

    PG_FREE_IF_COPY(left, 0);
    PG_FREE_IF_COPY(right, 1);

    PG_RETURN_BOOL(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_gt);

  Datum
  ovtversion_gt(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    bool  result;

    result = ovtversioncmp(left, right) > 0;

    PG_FREE_IF_COPY(left, 0);
    PG_FREE_IF_COPY(right, 1);

    PG_RETURN_BOOL(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_ge);

  Datum
  ovtversion_ge(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    bool  result;

    result = ovtversioncmp(left, right) >= 0;

    PG_FREE_IF_COPY(left, 0);
    PG_FREE_IF_COPY(right, 1);

    PG_RETURN_BOOL(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_smaller);

  Datum
  ovtversion_smaller(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    text *result;

    result = ovtversioncmp(left, right) < 0 ? left : right;

    PG_RETURN_TEXT_P(result);
  }

  PG_FUNCTION_INFO_V1(ovtversion_larger);

  Datum
  ovtversion_larger(PG_FUNCTION_ARGS)
  {
    text *left  = PG_GETARG_TEXT_PP(0);
    text *right = PG_GETARG_TEXT_PP(1);
    text *result;

    result = ovtversioncmp(left, right) > 0 ? left : right;

    PG_RETURN_TEXT_P(result);
  }
