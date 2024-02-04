file_proc_vs
============

**file_proc_vs.sh**

A Linux shell script (should be Bourne-shell-compatible) for processing video with sound using [VapourSynth](https://www.vapoursynth.com). Supports preview using mpv, can skip a number of seconds from the start, etc. Does not use VapourSynth's internal sound support (was made before that), so sound is always encoded/previewed as is.

To set the ffmpeg encoding parameters edit the *ffmpeg_options_v* (video) and *ffmpeg_options_a* (audio) variables at the beginning of the script.

If the script fails with something like *"Permission denied ... Failed to recognize file format"*, uncomment and edit the *vspath* variable at the beginning of the script to point to the location of *vapoursynth.so*.

If you're encoding video from a DVD source it is highly recommended to use the '-l' option to avoid audio delay issues.

**batch_proc_vs.sh**

A script for batch processing of many files. Executes *file_proc_vs.sh* for each file in a specified dir.

**video_to_frames.sh**

A script for converting a video file to image files of separate frames using ffmpeg. Start and end time can be specified.

**frames_to_video.sh**

A script for converting separate frames from image files back to video file, also using ffmpeg.

**gmic_proc.sh**

A script for multi-threaded (actually multi-process) processing of video using [G'MIC](https://gmic.eu). It's a bit simplistic, so the options are set by editing vars inside the script. It extracts video frames into frame files, then processes and encodes them back into video, so in its current form it's a bit redundant considering the existence of the *video_to_frames.sh* and *frames_to_video.sh* scripts.

**progress.sh**

A script to display progress when processing files by another script (or any process) by comparing the number of files in the source dir to the destination. Useful in conjunction with *gmic_proc.sh*.

**functions.py**

A set of useful processing functions.

**example.py**

A sample script (used for restoration of some VHS-quality DVD).

***Requirements:***

- VapourSynth R60 or later
- ffmpeg (for encoding/audio extraction)
- mpv (for preview)
- (optional) many different plugins for functions.py

