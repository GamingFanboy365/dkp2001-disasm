PREFIX  ?= arm-none-eabi-
AS      := $(PREFIX)as
LD      := $(PREFIX)ld
OBJCOPY := $(PREFIX)objcopy

BUILD   ?= build
ASFLAGS := -mcpu=arm7tdmi -mthumb-interwork -I . -I $(BUILD)
ASM     := $(shell find asm data updates -name '*.s' -o -name '*.S' 2>/dev/null)
ASSETS  := $(shell find assets -type f 2>/dev/null)
# Our own binary data for the updates build (pictures etc.), .incbin'd from updates/
UPDATES_BIN := $(shell find updates -name '*.bin' 2>/dev/null)
# Editable assets (PNG/PAL/WAV) are converted to the .bin files the source
# .incbin's, under $(BUILD)/assets/; as finds them through -I $(BUILD).
CONV    := $(filter %.png %.pal %.wav,$(ASSETS))

# Relocation test: insert padding before .text (moves all ROM code and data)
# or before .rodata (moves data only), e.g. make shifted SHIFT_CODE=0x1000
ifdef SHIFT_CODE
ASFLAGS += --defsym SHIFT_CODE=$(SHIFT_CODE)
endif
ifdef SHIFT_DATA
ASFLAGS += --defsym SHIFT_DATA=$(SHIFT_DATA)
endif
# Bug fixes are in the source behind ".ifdef FIXES"; see FIXES.md.
ifdef UPDATES
ASFLAGS += --defsym UPDATES=1
endif
ifdef FIXES
ASFLAGS += --defsym FIXES=1
endif

.PHONY: all compare clean shifted fixed updated patch

ifeq ($(wildcard assets)$(filter clean,$(MAKECMDGOALS)),)
$(error assets/ is missing. Extract it from your own copy of the game: python3 tools/dkp_split.py path/to/Diddy_Kong_Pilot_2001.elf --assets-only)
endif

all: $(BUILD)/dkp.gba

compare: build/dkp.gba
	@sha1sum -c dkp.sha1

# Two patched ROMs, and an IPS patch from the original to each:
#   fixed:   bug fixes and restored content (FIXES)
#   updated: the same plus new design, such as the dogfight (FIXES and UPDATES)
fixed:
	@$(MAKE) --no-print-directory BUILD=build_fixed FIXES=1 build_fixed/dkp.gba

updated:
	@$(MAKE) --no-print-directory BUILD=build_updated FIXES=1 UPDATES=1 build_updated/dkp.gba

patch: build/dkp.gba fixed updated
	python3 tools/make_ips.py create build/dkp.gba build_fixed/dkp.gba build_fixed/dkp2001_fixes.ips
	python3 tools/make_ips.py create build/dkp.gba build_updated/dkp.gba build_updated/dkp2001_updates.ips
	@mkdir -p patches
	cp build_fixed/dkp2001_fixes.ips patches/dkp2001_fixes.ips
	cp build_updated/dkp2001_updates.ips patches/dkp2001_updates.ips
	@sha1sum build_fixed/dkp.gba | sed 's|build_fixed/dkp.gba|dkp2001_fixed.gba|' > patches/dkp2001_fixed.sha1
	@sha1sum build_updated/dkp.gba | sed 's|build_updated/dkp.gba|dkp2001_updated.gba|' > patches/dkp2001_updated.sha1

shifted:
	@$(MAKE) --no-print-directory BUILD=build_shift_c$(SHIFT_CODE)_d$(SHIFT_DATA) build_shift_c$(SHIFT_CODE)_d$(SHIFT_DATA)/dkp.gba

$(BUILD)/assets.stamp: $(CONV) tools/gfx.py
	@mkdir -p $(BUILD)
	python3 tools/gfx.py build $(BUILD) $(if $(filter tools/gfx.py,$?),$(CONV),$(filter-out tools/gfx.py,$?))
	@touch $@

$(BUILD)/rom.o: rom.s $(ASM) $(ASSETS) $(UPDATES_BIN) $(BUILD)/assets.stamp
	@mkdir -p $(BUILD)
	$(AS) $(ASFLAGS) -o $@ $<

$(BUILD)/dkp.elf: $(BUILD)/rom.o ld_script.ld
	$(LD) -T ld_script.ld -o $@ $<

$(BUILD)/dkp.gba: $(BUILD)/dkp.elf
	$(OBJCOPY) -O binary $< $@

clean:
	rm -rf build build_shift_* build_fixed build_updated build_fx_* build_up_*
