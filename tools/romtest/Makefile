# Build romtest against a static libmgba. See README.md in this directory.
MGBA_SRC   ?= ../mgba
MGBA_BUILD ?= $(MGBA_SRC)/build
# Use exactly the defines libmgba was compiled with: they change struct layouts.
DEFS := $(shell grep -m1 -A3 'build CMakeFiles/mgba.dir/src/core/core.c.o' $(MGBA_BUILD)/build.ninja | sed -n 's/.*DEFINES = //p')

romtest: romtest.c $(MGBA_BUILD)/libmgba.a
	$(CC) -O2 $(DEFS) -I$(MGBA_SRC)/include -I$(MGBA_BUILD)/include -o $@ $< \
		$(MGBA_BUILD)/libmgba.a -lm -lpthread $(shell pkg-config --libs freetype2 2>/dev/null)

clean:
	rm -f romtest
