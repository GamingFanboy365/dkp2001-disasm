/* romtest + execution coverage: ORs executed instruction addresses (ROM and
 * IWRAM code) into the bitmap file $COVER (1 bit per halfword). */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern void (*armTraceExec)(uint32_t pc, int thumb);
#define ROM_HW (0x01000000 / 2)
#define IW_HW (0x8000 / 2)
static uint8_t bits[(ROM_HW + IW_HW) / 8];
static void ex(uint32_t pc, int thumb) {
	(void) thumb;
	uint32_t i;
	if (pc >= 0x08000000 && pc < 0x09000000) i = (pc - 0x08000000) / 2;
	else if (pc >= 0x03000000 && pc < 0x03008000) i = ROM_HW + (pc - 0x03000000) / 2;
	else return;
	bits[i >> 3] |= 1 << (i & 7);
}
#define main romtest_main
#include "romtest.c"  /* build: see README.md (needs mgba-trace-hooks.patch) */
#undef main
int main(int argc, char** argv) {
	const char* path = getenv("COVER");
	FILE* f = fopen(path, "rb");
	if (f) { fread(bits, 1, sizeof(bits), f); fclose(f); }
	armTraceExec = ex;
	int r = romtest_main(argc, argv);
	f = fopen(path, "wb"); fwrite(bits, 1, sizeof(bits), f); fclose(f);
	return r;
}
