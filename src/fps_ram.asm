; ============================================================================
;  DARK CITADEL - data kept in low RAM: weapons, floors, voices, music.
;  Assembled on its own at RAM_DATA; tools/build_fps.py compresses it into
;  src/fps_blob.inc and unlz (fps.asm) unpacks it at start-up.
; ============================================================================
        org 27E0h
#include "fps_ram.inc"
#include "fps_voice.inc"
#include "fps_music.inc"
ram_end:
