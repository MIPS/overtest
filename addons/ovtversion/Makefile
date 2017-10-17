MODULES = ovtversion
EXTENSION = ovtversion
DATA = ovtversion--1.0.sql ovtversion.sql uninstall_ovtversion.sql
#REGRESS = ovtversion

PG_CONFIG = pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)

ovtversion.so: ovtversion.o
	$(CC) $(LDFLAGS) -shared -o $@ $^

ovtversion.o: ovtversion.c
	$(COMPILE.c) $(CFLAGS_SL) $(OUTPUT_OPTION) $<

