# RaceGOW6 Track2 (BetaFPV / Sabj) – unofficial Velocidrone track

Source video: https://youtu.be/PqOFU-AwNvU ("RaceGOW6 Track2 sponsored by BetaFPV and designed by Sabj", IGOW channel).

The video description says the track will be an **official Velocidrone track called "RaceGOW6 Track2"**.
As of 2026-10-09 it was not yet in Velocidrone's official catalogue (only "RaceGOW6 Track1" was),
so this file is a fan rebuild made from the video. When the official track appears in the game, use that instead.

## Files
- `RaceGOW6 Track2 fan build.trk` – the track file (Sports Hall scenery)
- `RaceGOW6 Track2 fan build.json` – the decrypted gate/barrier list, for editing
- `preview.png` – top and side view of the layout
- `build_track2.py` + `vdcrypt.py` – generator (edit the layout, re-run, re-import)

## Import into Velocidrone
1. Copy `RaceGOW6 Track2 fan build.trk` into your **Documents** folder (Windows) or **Home** folder (macOS/Linux).
2. In Velocidrone: main menu → **Track Editor** → **Import Track** (button at the bottom) → press **Import** next to the track.
3. Select Sports Hall scenery, track "RaceGOW6 Track2 fan build", Micro / whoop class.

## What is modelled
Physical track from the video parts list (24" PVC sections):
- Start/Finish gate (3 sections, 2 elbows, 1 tee, 1 5-way)
- Spacer (1 section) on the floor between the gate and the tower
- Lower cube (7 sections, 5 tees, 2 4-ways, 1 5-way) – four uprights plus a three-sided mid square
- Upper cube and flag (9 sections, 4 4-ways) – stacked on the lower cube, flag pole on one top corner

Sim scale follows IGOW's official RaceGOW6 Track1: one 24" section = 0.88 m (gates at 44 %).
PVC tubes are thin cube barriers, race gates are Default Neon Squares (green start, blue, purple),
repeat/odd-angle passes are invisible checkpoints, exactly as IGOW builds their official files.

## Lap order (assumed – see note)
0. Start/finish gate (green)
1. Lower cube, enter through the side nearest the gate (blue)
2. Lower cube, exit the far side (invisible)
3. Climbing 180: back in through the far side of the upper cube (purple)
4. Pop out through the top square (invisible, horizontal)
5. Round the flag pole on the gate side (invisible), then dive and come back through the start gate

**Note:** the flythrough could only be read from YouTube's 2-second storyboard frames (the video stream itself
was not downloadable from this machine), so the exact gate order of the real track is inferred, not confirmed.
If the official flythrough differs, edit the `gate(...)` lines in `build_track2.py` (centre, fly direction, order)
and re-run `python3 build_track2.py`.
