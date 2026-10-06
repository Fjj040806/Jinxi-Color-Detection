# Reference case handling

Place locally licensed positive-reference images in this folder only while
retraining. Do not commit or redistribute source photographs unless their
permissions allow it.

For each image, record at minimum:

- exact place and camera position;
- capture date and time;
- weather and lighting;
- device, exposure, and white-balance information where available;
- photographer or source;
- usage and redistribution permission;
- who selected it as a positive case and why;
- community disagreement or alternative interpretations.

Prototype 0.3 contains only derived mosaics, palettes, hashes, and model
statistics from the current 13 examples. It does not contain the raw files.

On 2026-10-06, the original three sources were supplied again along with ten
additional townscape images. All 13 were jointly processed with SLIC (220
requested segments), CIELAB region statistics, equal image weights, 28 color
prototypes, and leave-one-image-out calibration. Reference weight remains 35%.
No source location, capture date, or image-license metadata was inferred.
Only derived low-resolution mosaics, palettes, hashes and statistics are
committed. Source filenames are recorded in reference_model.json.
