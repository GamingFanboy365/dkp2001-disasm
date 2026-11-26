PREFIX  ?= arm-none-eabi-
AS      := $(PREFIX)as
LD      := $(PREFIX)ld
OBJCOPY := $(PREFIX)objcopy

BUILD   ?= build
ASFLAGS := -mcpu=arm7tdmi -mthumb-interwork -I . -I $(BUILD)
ASM     := $(shell find asm data -name '*.s' -o -name '*.S' 2>/dev/null)
ASSETS  := $(shell find assets -type f 2>/dev/null)
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

.PHONY: all compare clean shifted

ifeq ($(wildcard assets)$(filter clean,$(MAKECMDGOALS)),)
$(error assets/ is missing. Extract it from your own copy of the game: python3 tools/dkp_split.py path/to/Diddy_Kong_Pilot_2001.elf --assets-only)
endif

all: $(BUILD)/dkp.gba

compare: build/dkp.gba
	@sha1sum -c dkp.sha1

shifted:
	@$(MAKE) --no-print-directory BUILD=build_shift_c$(SHIFT_CODE)_d$(SHIFT_DATA) build_shift_c$(SHIFT_CODE)_d$(SHIFT_DATA)/dkp.gba

$(BUILD)/assets.stamp: $(CONV) tools/gfx.py
	@mkdir -p $(BUILD)
	python3 tools/gfx.py build $(BUILD) $(if $(filter tools/gfx.py,$?),$(CONV),$(filter-out tools/gfx.py,$?))
	@touch $@

$(BUILD)/rom.o: rom.s $(ASM) $(ASSETS) $(BUILD)/assets.stamp
	@mkdir -p $(BUILD)
	$(AS) $(ASFLAGS) -o $@ $<

$(BUILD)/dkp.elf: $(BUILD)/rom.o ld_script.ld
	$(LD) -T ld_script.ld -o $@ $<

$(BUILD)/dkp.gba: $(BUILD)/dkp.elf
	$(OBJCOPY) -O binary $< $@

clean:
	rm -rf build build_shift_*
