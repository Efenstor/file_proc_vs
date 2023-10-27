file_proc_vs
============

**file_proc_vs.sh**

A Linux shell script (should be Bourne-shell-compatible) for processing video with sound using [VapourSynth](https://www.vapoursynth.com). Supports preview using mpv, can skip a number of seconds from the start, etc. Does not use VapourSynth's internal sound support (was made before that), so sound is always encoded/previewed as is.

If the script fails with something like *"Permission denied ... Failed to recognize file format"*, uncomment and edit the *vspath* variable at the beginning of the script to point to the location of *vapoursynth.so*.

**batch_proc_vs.sh**

A script for batch processing of many files. Executes *file_proc_vs.sh* for each file in a specified dir.

**functions.py**

A set of useful processing functions.

**example.py**

A sample script (used for restoration of some VHS-quality DVD).

***Requirements:***

- VapourSynth R60 or later
- ffmpeg (for encoding/audio extraction)
- mpv (for preview)
- (optional) many different plugins for functions.py

