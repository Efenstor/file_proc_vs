#!/bin/sh
# Copyleft 2020-2023 Efenstor

ffmpeg_options_out="-c:v h264 -crf 15 -an"
src_format="%08d"

# Internal defines
RED="\033[0;31m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
NC="\033[0m"

# Show help
if [ $# -lt 4 ]; then
  printf "\n${YELLOW}Convert frame image files to a video file using ffmpeg
${GREEN}(copyleft) Efenstor${NC}\n
Usage: frames_to_video.sh <images_dir> <images_ext> <dst_file> <fps>
Parameters:
  images_dir  directory with frame image files
  images_ext  image file extension (e.g. png)
  dst_file    destination video file
  fps         destination frame rate (e.g. 23.976)
\n"
  exit
fi

# Check the source dir
src_dir="$1"
src_ext="$2"
dst_file="$3"
dst_fps=$4

# Do the job
ffmpeg -loglevel info -i "$src_dir/$src_format.$src_ext" $ffmpeg_options_out -vf fps=$dst_fps $dst_file

