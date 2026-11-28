/* romtest: run a GBA ROM headlessly in mGBA with scripted input and report
 * a hash of the screen at fixed frames. Two ROMs that behave identically give
 * identical hash lists, which is how relocated / patched builds are checked
 * against the original.
 *
 *   romtest ROM FRAMES EVERY [--ppm PREFIX] [FRAME:KEY[:HOLD] ...]
 *
 * KEY is one of A B SELECT START RIGHT LEFT UP DOWN R L. HOLD defaults to 6
 * frames. With --ppm, each checkpoint is also written to PREFIX_<frame>.ppm.
 * With RAM_OUT=path in the environment, EWRAM (256 KiB) then IWRAM (32 KiB)
 * (and with RAM_VIDEO set, then palette RAM, VRAM and OAM; with RAM_SRAM, then the
 * first 64 KB of save RAM)
 * are written there after the last frame. With AUDIO_OUT=path.wav the sound
 * output is recorded (from frame AUDIO_FROM, default 1) as a stereo WAV.
 * POKE="FRAME:ADDR=VALUE,FRAME:ADDR|VALUE,..." writes (=) or ORs (|) a 32-bit
 * word into memory just before that frame runs (hex ADDR and VALUE), e.g. to
 * hand the player's plane to the computer (sys_flags |= 0x40).
 * Build: see tools/romtest/README.md.
 */
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba-util/audio-buffer.h>
#include <mgba-util/image.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

struct press { unsigned frame, hold; int key; };

/* Count stores to ROM (the game writing to data the linker put in ROM).
 * With PROBLEMS=1 in the environment, also collect every error/warning mGBA
 * reports (bad memory accesses, undefined instructions, ...) with the PC that
 * caused it, and print them de-duplicated at the end. */
static unsigned rom_stores;
static struct mCore* g_core;
static int collect_problems;
#define MAX_PROBLEMS 512
static struct { char msg[96]; uint32_t pc; unsigned count, first_frame; } problems[MAX_PROBLEMS];
static int nproblems;
static unsigned cur_frame;
static void quiet_log(struct mLogger* logger, int category, enum mLogLevel level, const char* format, va_list args) {
	(void) logger; (void) category;
	if (strstr(format, "Unimplemented memory Store")) {
		++rom_stores;
	}
	if (!collect_problems || !(level & (mLOG_FATAL | mLOG_ERROR | mLOG_WARN | mLOG_GAME_ERROR | mLOG_STUB))) {
		return;
	}
	char msg[96];
	vsnprintf(msg, sizeof(msg), format, args);
	uint32_t pc = 0;
	if (g_core) {
		int32_t v = 0;
		if (g_core->readRegister(g_core, "pc", &v)) {
			pc = (uint32_t) v;
		}
	}
	for (int i = 0; i < nproblems; ++i) {
		if (problems[i].pc == pc && !strcmp(problems[i].msg, msg)) {
			++problems[i].count;
			return;
		}
	}
	if (nproblems < MAX_PROBLEMS) {
		strcpy(problems[nproblems].msg, msg);
		problems[nproblems].pc = pc;
		problems[nproblems].count = 1;
		problems[nproblems].first_frame = cur_frame;
		++nproblems;
	}
}
static struct mLogger quiet = { .log = quiet_log };

static int key_bit(const char* name) {
	static const char* names[] = { "A", "B", "SELECT", "START", "RIGHT", "LEFT", "UP", "DOWN", "R", "L" };
	for (int i = 0; i < 10; ++i) {
		if (!strcmp(name, names[i])) {
			return i;
		}
	}
	return -1;
}

int main(int argc, char** argv) {
	if (argc < 4) {
		fprintf(stderr, "usage: %s ROM FRAMES EVERY [--ppm PREFIX] [FRAME:KEY[:HOLD] ...]\n", argv[0]);
		return 2;
	}
	const char* rom = argv[1];
	unsigned frames = strtoul(argv[2], NULL, 0);
	unsigned every = strtoul(argv[3], NULL, 0);
	const char* ppm = NULL;
	static struct press presses[4096];
	static struct { unsigned frame; uint32_t addr, value; char op; } pokes[64];
	int npoke = 0;
	const char* poke_env = getenv("POKE");
	while (poke_env && *poke_env && npoke < 64) {
		unsigned f; unsigned a, v; char op; int used = 0;
		if (sscanf(poke_env, "%u:%x%c%x%n", &f, &a, &op, &v, &used) < 4 || (op != '=' && op != '|')) {
			fprintf(stderr, "bad POKE '%s'\n", poke_env);
			return 2;
		}
		pokes[npoke].frame = f; pokes[npoke].addr = a; pokes[npoke].value = v; pokes[npoke].op = op; ++npoke;
		poke_env += used;
		if (*poke_env == ',') ++poke_env;
	}
	int npress = 0;
	for (int i = 4; i < argc; ++i) {
		if (!strcmp(argv[i], "--ppm") && i + 1 < argc) {
			ppm = argv[++i];
			continue;
		}
		char key[16] = { 0 };
		unsigned f = 0, hold = 6;
		if (sscanf(argv[i], "%u:%15[A-Z]:%u", &f, key, &hold) < 2 || key_bit(key) < 0 || npress == (int) (sizeof(presses) / sizeof(presses[0]))) {
			fprintf(stderr, "bad press '%s'\n", argv[i]);
			return 2;
		}
		presses[npress++] = (struct press) { f, hold, key_bit(key) };
	}

	mLogSetDefaultLogger(&quiet);
	collect_problems = getenv("PROBLEMS") != NULL;
	struct mCore* core = mCoreFind(rom);
	g_core = core;
	if (!core || !core->init(core)) {
		fprintf(stderr, "cannot open %s\n", rom);
		return 1;
	}
	mCoreInitConfig(core, NULL);
	unsigned w, h;
	core->baseVideoSize(core, &w, &h);
	mColor* buf = calloc(w * h, BYTES_PER_PIXEL);
	core->setVideoBuffer(core, buf, w);
	core->setAudioBufferSize(core, 2048);
	if (!mCoreLoadFile(core, rom)) {
		fprintf(stderr, "cannot load %s\n", rom);
		return 1;
	}
	core->reset(core);

	FILE* wav = NULL;
	unsigned audio_from = getenv("AUDIO_FROM") ? strtoul(getenv("AUDIO_FROM"), NULL, 0) : 1;
	uint32_t wav_bytes = 0;
	if (getenv("AUDIO_OUT")) {
		wav = fopen(getenv("AUDIO_OUT"), "wb");
		if (wav) {
			static const char hdr[44] = { 0 };
			fwrite(hdr, 1, 44, wav); /* filled in at the end */
		}
	}

	for (unsigned frame = 1; frame <= frames; ++frame) {
		uint32_t keys = 0;
		for (int i = 0; i < npress; ++i) {
			if (frame >= presses[i].frame && frame < presses[i].frame + presses[i].hold) {
				keys |= 1u << presses[i].key;
			}
		}
		core->setKeys(core, keys);
		cur_frame = frame;
		for (int i = 0; i < npoke; ++i) {
			if (pokes[i].frame == frame) {
				uint32_t v = pokes[i].value;
				if (pokes[i].op == '|') {
					v |= core->busRead32(core, pokes[i].addr);
				}
				core->busWrite32(core, pokes[i].addr, v);
			}
		}
		core->runFrame(core);
		if (wav) {
			struct mAudioBuffer* ab = core->getAudioBuffer(core);
			int16_t samples[2 * 2048];
			size_t n;
			while ((n = mAudioBufferRead(ab, samples, 2048)) > 0) {
				if (frame >= audio_from) {
					fwrite(samples, 4, n, wav);
					wav_bytes += n * 4;
				}
			}
		}
		if (every && frame % every == 0) {
			uint64_t hash = 1469598103934665603ull;
			for (unsigned p = 0; p < w * h; ++p) {
				uint32_t c = (uint32_t) buf[p] & 0xFFFFFF;
				hash = (hash ^ c) * 1099511628211ull;
			}
			printf("%6u %016llx\n", frame, (unsigned long long) hash);
			if (ppm) {
				char path[512];
				snprintf(path, sizeof(path), "%s_%06u.ppm", ppm, frame);
				FILE* f = fopen(path, "wb");
				if (f) {
					fprintf(f, "P6\n%u %u\n255\n", w, h);
					for (unsigned p = 0; p < w * h; ++p) {
						uint32_t c = (uint32_t) buf[p];
						unsigned char rgb[3] = { c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF };
						fwrite(rgb, 1, 3, f);
					}
					fclose(f);
				}
			}
		}
	}
	if (wav) {
		uint32_t rate = core->audioSampleRate(core);
		uint8_t h[44];
		memcpy(h, "RIFF", 4);
		uint32_t v = 36 + wav_bytes; memcpy(h + 4, &v, 4);
		memcpy(h + 8, "WAVEfmt ", 8);
		v = 16; memcpy(h + 16, &v, 4);
		uint16_t w = 1; memcpy(h + 20, &w, 2);
		w = 2; memcpy(h + 22, &w, 2);
		memcpy(h + 24, &rate, 4);
		v = rate * 4; memcpy(h + 28, &v, 4);
		w = 4; memcpy(h + 32, &w, 2);
		w = 16; memcpy(h + 34, &w, 2);
		memcpy(h + 36, "data", 4);
		memcpy(h + 40, &wav_bytes, 4);
		fseek(wav, 0, SEEK_SET);
		fwrite(h, 1, 44, wav);
		fclose(wav);
	}
	printf("stores-to-rom %u\n", rom_stores);
	for (int i = 0; i < nproblems; ++i) {
		printf("problem pc=%08x frame=%u count=%u %s\n", problems[i].pc, problems[i].first_frame, problems[i].count, problems[i].msg);
	}
	const char* ram_out = getenv("RAM_OUT");
	if (ram_out) { /* EWRAM then IWRAM, as seen by the CPU */
		FILE* f = fopen(ram_out, "wb");
		if (f) {
			for (uint32_t a = 0x02000000; a < 0x02040000; a += 4) { uint32_t v = core->busRead32(core, a); fwrite(&v, 4, 1, f); }
			for (uint32_t a = 0x03000000; a < 0x03008000; a += 4) { uint32_t v = core->busRead32(core, a); fwrite(&v, 4, 1, f); }
			if (getenv("RAM_VIDEO")) { /* then palette, VRAM and OAM */
				for (uint32_t a = 0x05000000; a < 0x05000400; a += 4) { uint32_t v = core->busRead32(core, a); fwrite(&v, 4, 1, f); }
				for (uint32_t a = 0x06000000; a < 0x06018000; a += 4) { uint32_t v = core->busRead32(core, a); fwrite(&v, 4, 1, f); }
				for (uint32_t a = 0x07000000; a < 0x07000400; a += 4) { uint32_t v = core->busRead32(core, a); fwrite(&v, 4, 1, f); }
			}
			if (getenv("RAM_SRAM")) { /* then the first 64 KB of save RAM, a byte at a time */
				for (uint32_t a = 0x0e000000; a < 0x0e010000; a++) { uint8_t v = core->busRead8(core, a); fwrite(&v, 1, 1, f); }
			}
			fclose(f);
		}
	}
	core->deinit(core);
	free(buf);
	return 0;
}
