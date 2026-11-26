/* Diddy Kong Pilot (2001) layout.
 *
 * Sections flow one after another, so an unmodified build lands exactly on the
 * original addresses, and code or data that grows simply pushes what follows.
 * .text32 runs from IWRAM (0x03000000) but is stored in ROM right after .boot;
 * AgbMain copies it using __text32_lma.
 */
OUTPUT_ARCH(arm)
ENTRY(_start)
SECTIONS
{
    .boot 0x08000000 : { *(.boot) }

    __text32_lma = ALIGN(4);
    .text32 0x03000000 : AT(__text32_lma) { *(.text32) }
    __text32_lma_end = __text32_lma + SIZEOF(.text32);

    .bss32 ALIGN(ADDR(.text32) + SIZEOF(.text32), 4) (NOLOAD) : { *(.bss32) }

    .text ALIGN(__text32_lma_end, 4) : AT(ALIGN(__text32_lma_end, 4)) { *(.text) }
    .rodata ALIGN(16) : { *(.rodata) }
    .data ALIGN(4) : { *(.data) }
    .fixes ALIGN(4) : { *(.fixes) }   /* bug-fix build only: new code at the end of the ROM */

    .bss 0x02000000 (NOLOAD) : { *(.bss) }

    /DISCARD/ : { *(.ARM.attributes) }
}
