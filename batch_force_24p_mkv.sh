#!/bin/bash
# Copyleft Efenstor
# Revision 2025-11-18

# User defines
src_ext="mp4"
dst_ext="mkv"

# Help
if [ $# -lt 2 ]; then
  echo
  echo "Batch-force video frame rate to 23.976 using mkvmerge without re-encoding"
  echo
  echo "Usage: batch_force_24p_mkv.sh <src_dir> <dst_dir> [src_ext]"
  echo "Note: existing files in dst_dir will be skipped, not overwritten"
  echo
  exit
fi

# Optional params
if [ "$3" ]; then
  src_ext="$3"
fi

# Do processing
src_dir="$1"
dst_dir="$2"
files=$(find "$src_dir" -maxdepth 1 -type f -iname "*.$src_ext" | sort -n)
while [ -n "$files" ]
do
  i=$(echo "$files" | head -n 1)
  files=$(echo "$files" | tail -n +2)

  # Prepare some vars
  filename=$(basename "$i")
  filename_out="$dst_dir/${filename%.*}.$dst_ext"

  # Process only if the output file does not exists
  if [ ! -e "$filename_out" ]; then
    mkvmerge -o "$filename_out" --default-duration 0:23.976023976p --fix-bitstream-timing-information 0:1 "$i"
    if [ $? -ne 0 ]; then
      exit $?
    fi
  else
    echo "\"$filename_out\" already exists, skipping..."
  fi

done
