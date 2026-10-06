# Reference case handling

Place positive-reference images in this folder only while retraining. Public
copies belong in `static/reference-originals/` only when permission allows
project use and display.

For each image, record at minimum:

- exact place and camera position;
- capture date and time;
- weather and lighting;
- device, exposure, and white-balance information where available;
- photographer or source;
- usage and redistribution permission;
- who selected it as a positive case and why;
- community disagreement or alternative interpretations.

Prototype 0.5 contains the permitted, watermark-free originals together with
derived mosaics, palettes, hashes, and model statistics for 13 examples.

On 2026-10-06, the original three sources were supplied again along with ten
additional townscape images. All 13 were jointly processed with SLIC (220
requested segments), CIELAB region statistics, equal image weights, 28 color
prototypes, and leave-one-image-out calibration. Reference weight remains 35%.
The user confirmed permission to use and display these images in the project.
No source location, capture date, creator credit, or specific license terms
were inferred. Those fields remain required documentation rather than guessed
metadata.
