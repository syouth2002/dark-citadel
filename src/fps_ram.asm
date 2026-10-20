; ============================================================================
;  DARK CITADEL - data kept in low RAM: weapons, voices, music.
;  Assembled on its own at RAM_DATA (the org in fps_ram.inc: just after the
;  sprites); tools/build_fps.py compresses it into src/fps_blob.inc and unlz
;  (fps.asm) unpacks it at start-up.
; ============================================================================
#include "fps_ram.inc"
#include "fps_voice.inc"
#include "fps_music.inc"
ram_end:
