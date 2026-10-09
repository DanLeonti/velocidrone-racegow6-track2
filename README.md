# RaceGOW6 Track2 (BetaFPV / Sabj) – unofficial Velocidrone track

Source video: https://youtu.be/PqOFU-AwNvU ("RaceGOW6 Track2 sponsored by BetaFPV and designed by Sabj", IGOW channel).
Layout data: GeddyV's RaceGOW 6 track visualizer, https://racegow.geddyv.lt/track-visualizer/
(its `track-2.json`, kept in `source/`), which has the PVC pipes, the 14 gates in lap order and the flight path.

The video description says the track will be an **official Velocidrone track called "RaceGOW6 Track2"**.
As of 2026-10-09 it was not yet in Velocidrone's official catalogue, so this is a fan build.
When the official track appears in the game, prefer that one.

## Files
- `RaceGOW6 Track2 fan build.trk` – the track file (Sports Hall scenery)
- `RaceGOW6 Track2 fan build.json` – the decrypted gate/barrier list
- `preview.png` – top and side view with the lap path
- `build_track2.py` + `vdcrypt.py` – generator (reads `source/racegow6-track-2.visualizer.json`, writes the .trk)
- `source/` – the visualizer layouts for Track 1 and Track 2

## Import into Velocidrone
1. Copy `RaceGOW6 Track2 fan build.trk` into your **Documents** folder (Windows) or **Home** folder (macOS/Linux).
2. In Velocidrone: main menu → **Track Editor** → **Import Track** (button at the bottom) → press **Import** next to the track.
3. Select Sports Hall scenery, track "RaceGOW6 Track2 fan build", Micro / whoop class.

## What is modelled
All 20 PVC tubes from the visualizer (24" sections): start/finish gate, floor spacer, lower cube with a
three-sided mid square, upper cube, and the flag pole on the far top corner. Scale follows IGOW's official
RaceGOW6 Track1 file: one section = 0.88 m (gates at 44 %). Tubes are thin cube barriers. Only the start gate (green) and the four entry faces (blue) are visible
neon squares; exit faces, repeat passes and air checkpoints are invisible checkpoints. Gate directions were taken from the visualizer's flight
path and checked against its lap animation.

## Lap (14 passes, in order)
0. Start/finish gate (green)
1. Round the right side to the back, into the lower cube through the back face
2. Out the lower cube's front face (invisible)
3. Climbing left turn, into the upper cube through the left face
4. Out the upper cube's right face (invisible)
5. Up and round behind the flag pole (air checkpoint)
6. Over the back-left corner, dive into the top square
7. Out the upper cube's back face (invisible)
8. Descend round the left, into the lower cube through the left face
9. Out the lower cube's back face
10. Climb, into the upper cube through the back face
11. Out the upper cube's front face (invisible)
12. Round the left side (air checkpoint)
13. Behind the tower past the flag's base (air checkpoint), round the right and back to the start gate

To change anything, edit `source/racegow6-track-2.visualizer.json` (or the colour map / scale in
`build_track2.py`) and re-run `python3 build_track2.py`.
