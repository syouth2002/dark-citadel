# DARK CITADEL

**English** | [日本語](README.ja.md)

**An original first-person maze shooter for the NEC PC-6001mkII**

![Real play in PC6001VW](docs/images/walk.gif)

*Real play in PC6001VW (cut from a recording, at actual speed)*

With only a lantern to light the way, climb the 13 floors of a citadel sunk in darkness, from the bottom to the top, in first person.
Walls and enemies are drawn in 3D by raycasting, and the enemies groan and scream through the machine's speech synthesis chip (uPD7752).
The name, logo, maps, characters, colours, sound effects, enemy voices and music were all made new for this project.

Written in Z80 assembly. Runs in the PC6001VW emulator, or on real hardware from a cassette WAV.

| | |
|---|---|
| ![Combat](docs/images/combat.png) | ![Newer foes](docs/images/foes.png) |
| Eight kinds of enemies; tougher ones join on higher floors | A bloater, a lamp turret and a bat (floor 10) |
| ![Exploring and the auto map](docs/images/explore.png) | ![The warden](docs/images/warden.png) |
| The light reaches 5 cells deep; the walls it touches appear on the map | On the top floor the warden (boss) guards the exit |
| ![Floor cleared](docs/images/tally.png) | ![Ending](docs/images/ending.png) |
| The tally for a cleared floor, and the password for the next | The ending: dawn breaks over the citadel |

## Features

- Double-buffered raycasting on the PC-6001mkII (mode 5, 160x200 dots, 16 colours)
- 13 floors of 24x24 cells, locked doors, an automatic map
- Two weapons (gun and axe), eight kinds of enemies (boss included); health, ammo, keys and lantern oil to pick up
- Three difficulty levels (EASY / NORMAL / HARD): harder levels bring more enemies, more damage and fewer supplies
- Enemy voices on the speech chip; sound effects and five tunes on the PSG
- Passwords to resume from a later floor; a hidden debug mode
- A title logo and an ending (a dawn scene and a tally)

## Download

Get these files from [Releases](../../releases).

| File | Contents |
|---|---|
| `fps.cas` | Cassette image for emulators (about 19.1 KB) |
| `fps.wav` | Audio for real hardware (about 3 min 24 s, 48 kHz, 8-bit, mono) |
| `vtest.cas` | Speech-chip check (keys 1-9, 0, A, B play the enemy voices; P plays an effect and a voice together) |

## How to play (PC6001VW)

1. Set the machine to PC-6001mkII and load `fps.cas` with LOAD-TAPE
2. On the start-up screen choose `5` (N60m BASIC), and answer `1` to `How Many Pages?`
3. Type `CLOAD`; when `Ok` appears, type `RUN`
4. On the title screen choose the difficulty with left/right, then press SPACE

![Title screen](docs/images/title.png)

### On real hardware

1. Play `fps.wav` on a PC with its audio output connected to the PC-6001mkII's CMT input (data recorder socket)
   (or record it to a cassette tape and play that in a data recorder)
2. Start in mode 5, type `CLOAD`, then start the WAV
3. When `Ok` appears, type `RUN`

- Without a remote-control connection, the WAV keeps playing after the BASIC part has loaded.
  There is a 2-second leader tone after the BASIC part; if that is not enough, pause the playback at `Ok`, type `RUN`, then resume.
- Use a fairly high output volume.
- **The WAV has not been tried on real hardware yet.** Reading the waveform back gives the original data exactly, but some equipment may need the volume or polarity adjusted.
- The enemy voices were designed with a reproduction of the speech chip like PC6001VW's, so they may sound different on real hardware.

## Controls

| Key | Action |
|---|---|
| Left / Right | Turn |
| Up / Down | Move forward / back |
| SPACE | Fire (a click when out of ammo) / swing the axe |
| SHIFT | Switch weapons (gun / axe) |
| STOP | Pause (press again to resume) |
| P (title screen) | Enter a password |

A joystick works too.

## Rules

- Touch the glowing wall (the exit) somewhere on each floor to clear it. Leave the 13th floor (the top) to reach the ending.
- Doors open when you walk into them. Orange and violet doors stay shut until you have the key of the same colour; the key is always in a room before its door.
- Higher floors have more enemies, and tougher ones among them. No enemy attacks through walls or closed doors.

| Enemy | From | Health (hits) | Behaviour |
|---|---|---|---|
| Wanderer | Floor 1 | 3 | Walks up and claws (8 damage) |
| Sentinel | Floor 1 | 4 | Keeps its distance and fires bolts of light (5 damage) |
| Bat | Floor 3 | 1 | Faster than a stalker; flies in wide swings from side to side, changing sides at unpredictable moments. Bites (4 damage) |
| Brute | Floor 4 | 8 | Slow but tough; winds up and strikes hard (20 damage) |
| Bloater | Floor 5 | 6 | Once it notices you, it rolls at you quickly; within a cell it swells and soon bursts: 25 damage within 1.5 cells, if you are in its sight. Shot down, it bursts where it is. The burst hurts other enemies too (3 damage), and bloaters nearby burst in turn |
| Stalker | Floor 7 | 2 | Very fast, zigzags from side to side, hard to aim at. Quick claws (5 damage) |
| Lamp turret | Floor 9 | 10 | Does not move. Notices you whenever it can see you within 8 cells, even from the darkness beyond your lantern, and starts firing at once; then a bolt about every 1.5 s (8 damage) |
| Warden (boss) | Floor 13 only | 30 | Guards the exit room; half as big again as the others. Strikes up close (15 damage), throws bolts from afar (10 damage) |

- The exit on floor 13 stays shut until the warden falls. Once the warden stirs, its health gauge (a red bar in a grey frame) appears on the message line.
  Floor 13 has its own tune, which changes to the battle tune only while you are within the warden's reach (anywhere it can see you).
- There are two weapons; the one in hand is shown as WEAPON (GUN / AXE) on the second line.
  - Gun: uses a round, reaches far (1 damage).
  - Axe: uses no rounds and reaches only about 1.2 cells, but deals 2 damage a swing.
  - Firing the last round switches to the axe.
- Pickups: health (not picked up at full health), ammo (12 rounds each, up to 99), keys, lantern oil (one on each floor from floor 3: for about a minute the light reaches 7 cells, and OIL shows on the second line).
- The lantern: its light reaches only 5 cells deep; beyond is darkness. Enemies in the dark can't be seen or shot.
- The map (bottom right): only walls and doors your lantern has lit are drawn. North is up, you (the white dot) stay in the middle, and the map moves.
- When your health reaches 0, choose CONTINUE (restart the floor at full health) or TITLE.
  On CONTINUE, your rounds are made up to the difficulty's amount (see the Difficulty table) if you have fewer.
- The lines under the view:
  - 1st: HEALTH, AMMO, KILLS (defeated / enemies on the floor)
  - 2nd: WEAPON, KEY (keys held)
  - 3rd: messages (pickups, doors that need a key, the warden's gauge and so on)
  - 4th: DARK CITADEL, FLOOR, the difficulty
  - 5th: a reminder of the controls
  - When hurt, the health figure turns red and the edge of the view on the side of the attack lights up. An enemy hit by a round or the axe flashes for a moment.
- Records: on clearing a floor, its kills, items and time; at the ending, the total time, total kills, deaths and the best time (for each difficulty).

## Difficulty

Choose with left/right on the title screen (EASY → NORMAL → HARD → EASY; NORMAL at power-on). The chosen difficulty is shown in red after the floor number during play.

| | EASY | NORMAL | HARD |
|---|---|---|---|
| Enemies | each floor's base number | 1.5x | 2x (still one warden) |
| Damage taken | as is | 1.5x | 2x |
| Rounds at the start | 50 | 30 | 0 (start with the axe) |
| Health items | all | half | half |
| Ammo items | all | half | half (6 rounds each) |
| Rounds made up on CONTINUE | up to 30 + 3 x (floor - 1) | up to 20 + 2 x (floor - 1) | none |

- The extra enemies come in the same mix of kinds as the floor's own, placed outside the start room (placed at build time: always the same).
- "Half" the items means every second one is left out.
- A best time is kept for each difficulty; the title screen shows the chosen difficulty's.
- Passwords carry the difficulty too.

## Passwords

- When you clear a floor, the tally shows a password (5 characters) for the next floor. It carries your health, rounds and difficulty.
- On the title screen, press `P` and type the 5 characters to start from that floor.
- Games started from a password don't set best times.

## Ending

Defeat the warden on floor 13 and leave by the exit: dawn breaks over the citadel, a few words follow, and then the tally. Press SPACE to skip through.

## Debug mode (for testing)

On the title screen, enter Up Up Down Down Left Right Left Right to open the debug menu. Choose an item with up/down and change it with left/right.

| Item | Contents |
|---|---|
| FLOOR | Starting floor (1-13) |
| SOUND | Sound test: 1-7 effects, 8-27 enemy voices, 28-32 tunes. SPACE plays |
| INVINCIBLE | Invincible (the hurt sound and red figure still show, but health doesn't drop) |
| START | Start from the chosen floor with 99 rounds |
| EXIT | Back to the title |

Games played in debug mode don't set best times.

## Building

You need Python 3, the assembler `zxbasm` from [ZX Basic](https://github.com/boriel-basic/zxbasic) (`pip install zxbasic`), and Pillow (`pip install pillow`).
The tests also use the Z80 emulator package (`pip install z80`).

```bash
python tools/fps_gen.py
python tools/build_fps.py
python tools/cas2wav.py fps.cas fps.wav
```

- `fps_gen.py`: generates the tables, pictures, logo, maps and variable layout (`src/fps_*.inc`, and an overview of the floors in `build/floors_preview.png`).
- `build_fps.py`: assembles and compresses the data kept in low RAM (`src/fps_ram.asm`), and makes `fps.cas` and `vtest.cas` with the program.
- `cas2wav.py`: turns a `.cas` into a `.wav` for real hardware.

## Tests

`tools/harness.py` is a headless model of the Z80 and the parts of the PC-6001mkII the game uses (the mode 5 screen, the timer and key interrupts, the PSG, the speech chip).
The tests run the game on it and check its memory and screen (`python tools/<name>.py`, after building).

| Test | Checks |
|---|---|
| `fps_mech_test` | Doors, keys, items, exits, every floor in turn, timing |
| `fps_map_test` | The map and automapping |
| `fps_ray_test` | Every column's ray against an exact calculation |
| `fps_los_test` | No attacks through walls or doors |
| `fps_enemy_test` | Each kind's first floor, health, damage, speed, movement, voices |
| `fps_foes_test` | Bat, bloater, lamp turret (first floors, swelling and bursting, bursting when shot, hurting others and chain bursts, fire from the dark, the bat's speed and swing) |
| `fps_boss_test` | The warden: placement, the barred exit, waking, attacks, gauge, music switching, defeat |
| `fps_axe_test` | The axe: switching, reach, damage, automatic switch when out of ammo |
| `fps_items_test` | Lantern oil, hit flash, the hurt-direction marker, pause |
| `fps_death_test` | CONTINUE / TITLE when slain, rounds made up |
| `fps_password_test` | Passwords shown, typed, mistyped (with the difficulty) |
| `fps_diff_test` | Choosing the difficulty; enemies, damage, rounds at start and on CONTINUE, items, best times by difficulty |
| `fps_ending_test` | The ending |
| `fps_debug_test` | Hidden command, floor select, sound test, invincibility, EXIT |
| `fps_sfx_test` / `fps_voice_test` | Effect channels and latency, music, data sent to the speech chip |
| `fps_tables_test` | Tables made at start-up |
| `fps_still_test` | Partial redraws while standing still match full redraws byte for byte |
| `fps_ab_test` | Two builds played the same way give the same screens frame by frame (for optimisations) |
| `fps_test` / `fps_prof` | Speed, and where the time goes |
| `fps_shots` | Makes this README's screenshots (`docs/images`, except the animated GIF) |

## Technical notes

- Screen: mode 5 (160x200 dots, 16 colours), double-buffered at 8000h / C000h. The view is 32 columns x 4 dots x 112 rows.
  Plane 1 of the view is constant for a floor, so only plane 0 is drawn; ceiling and floor are repainted only where the wall's top and bottom moved.
- Loader: a BASIC program pokes a small machine-code stub that loads the game at 4000h with the BASIC ROM's tape routines, then maps RAM over the ROM and starts it.
- Interrupts: IM2. A 2 ms timer interrupt paces the frames, steps the sound effects and music, and feeds the speech chip. At most 25 frames a second.
- Raycasting: the DDA runs in registers; multiplication uses quarter-square tables and wall heights come from tables - no division. Rays stop at a depth of 5 cells.
- Floors: 24x24 cells, made at build time by `tools/fps_levels.py` by splitting into rooms (7-18 rooms a floor, joined by doors as a tree), with fixed random seeds so every build is the same.
- Enemy voices: the speech chip's external parameter mode, a 7-byte frame every 10 ms. The voices are made in `tools/voices.py` and can be previewed with `tools/d7752sim.py`.
- Music: `tools/music.py`. Notes and volume steps advance every 16 ms.
- Title logo: the citadel's towers in silhouette against the night sky, with the name in front. Drawn dot by dot in `tools/fps_logo.py`, compressed with LZ one plane at a time into the program (about 1.1 KB), and unpacked straight onto the screen each time the title is drawn.
- Saving space:
  - Data used only at start-up (the low-RAM data, the packed pictures, seeds for tables) sits at the end of the program and may run past 7FFFh (over the loader's BASIC area). It is unpacked before the screens are cleared, so only what is used during play has to fit in 4000h-7FFFh.
  - The trigonometric tables are kept for a quarter turn; wall-height and other tables are made at start-up.
  - Character pictures are packed 4 bits a dot, LZ-compressed and unpacked at start-up.
  - Maps are kept as wall runs plus locked-door and exit cells (`tools/fps_mapcode.py`; about 1.4 KB for 13 floors). They can be read as they are, so they stay in the program.
  - Weapon pictures, the extra enemies of the harder difficulties, the voices and the music are assembled apart for low RAM, LZ-compressed (`tools/lz.py`) and unpacked at start-up.
- Speed (about half the time a frame took before these):
  - While standing still, the view isn't worked out again; only columns that enemies or the weapon were drawn over are redrawn.
  - Each column remembers the shade of its wall on each page; if it is the same, only the rows the wall grew by are drawn.
  - Multiplications by small high bytes become additions, and the busiest ones are written out in place.
  - Wall seams are decided by comparing values from the ray against a table by angle, with no multiplication.
  - Enemies behind you or beyond the light get only their depth worked out.
  - The map is redrawn using tables that give the screen bytes for two cells' colours directly.
- Sources:
  - `src/fps.asm`: the drawing engine, input, the speech chip
  - `src/fps_game.asm`: enemies, firing, doors, items, floors, the map, the screens, sound effects, music
  - `src/fps_ram.asm`: the low-RAM data (takes in the generated files)
  - `src/vtest.asm`: the speech-chip check build
  - `tools/fps_logo.py`: the title logo (`python tools/fps_logo.py` writes `build/logo.png` to look at)

## License

[MIT License](LICENSE)
