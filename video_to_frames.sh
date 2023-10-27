#!/bin/sh
# Copyleft 2020-2023 Efenstor

# Internal defines
RED="\033[0;31m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
NC="\033[0m"

# Show help
if [ $# -lt 3 ]; then
  printf "\n${YELLOW}Convert video file to frame image files using ffmpeg
${GREEN}(copyleft) Efenstor${NC}\n
Usage: video_to_frames.sh <src_file> <images_dir> <images_ext> [segment_start]
       [segment_end]\n
Parameters:
  src_file       source video file
  images_dir     directory with frame image files
  images_ext     image file extension (e.g. png)
  segment_start  start time of the video segment to extract
  segment_end    end time of the video segment to extract

Time should be specified in the FFMPEG format [HH:]MM:SS[.m...]
Examples:
  55 = 55 sec
  0.2 = 0.2 seconds
  200ms = 200 milliseconds
  200000us = 200000 microseconds
  12:03:45 = 12 hours, 03 minutes and 45 seconds
  23.189 = 23.189 seconds
\n"
  exit
fi

# Check the source file
src_file="$1"
dst_dir="$2"
dst_ext="$3"

# Prepare the destination dir
if [ ! -e "$dst_dir" ] || [ ! -d "$dst_dir" ]; then
  mkdir "$dst_dir"
elif [ $(find "frames2" -maxdepth 1 -type d -empty | wc -l) > /dev/null -eq 0 ]; then
  read -p "The destination directory is not empty. Should it be purged? (y/N)" ans
  if [ "$ans" = "y" ]; then
    # This may look stupid but it allows to delete
    # unlimited number of files while $dst_dir/* cannot
    rm -Rf "$dst_dir"
    mkdir "$dst_dir"
  fi
fi

# Seek position
if [ $# -gt 3 ]; then
  ss="-ss $4"
fi
# To position
if [ $# -gt 4 ]; then
  to="-to $5"
fi

# Do the job
ffmpeg -loglevel info -i "$src_file" $ss $to "$dst_dir/%08d.$dst_ext"

