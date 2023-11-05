#!/bin/sh
# (copyleft) Efenstor 2015-2023
# Revision 2023-10-27

# Examples:
# ffmpeg_options_v="-c:v libx264 -crf 16 -preset fast -tune film"
# ffmpeg_options_v="-c:v ffvhuff -vf pp=subfilters=l5/lowpass5"
# ffmpeg_options_v="-c:v mjpeg -q:v 2 -vf colormatrix=bt709:bt601"
# ffmpeg_options_a="-c:a copy"
# ffmpeg_options_a="-c:a pcm_s16le"
# ffmpeg_options_a="-c:a ogg -q:a 3.0"

# User defines
ffmpeg_options_v="-c:v libx264 -crf 20 -tune film"
ffmpeg_options_a="-c:a aac -b:a 256k"
dst_ext_default="mkv"
threads=4
vspath=/usr/local/lib/python3.11/site-packages

# Internal defines
export file_proc_vs_exit=
RED="\033[0;31m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
NC="\033[0m"

# Parse the named parameters
optstr="?he:d:a:pnl"
audio_track=0
audio_delay=0
while getopts $optstr opt; do
  case "$opt" in
    e) dst_ext=$OPTARG
       echo "Destination extension: $dst_ext"
       ;;
    d) audio_delay=$(awk "BEGIN {print $OPTARG/1000}")
       echo "Audio delay: $audio_delay sec"
       ;;
    a) audio_track=$OPTARG
       echo "Audio track: $audio_track"
       ;;
    p) mpv=true
       echo "Preview instead of encoding"
       ;;
    n) no_audio=true
       echo "Without audio"
       ;;
    l) audio_delay_auto=true
       echo "Detect audio delay from source"
       ;;
    :) echo "Missing argument for -$OPTARG" >&2
       exit 1
       ;;
  esac
done

# Parse the unnamed parameters
shift $((OPTIND - 1))

# Show help
if [ $# -lt 3 ]; then
  printf "
${YELLOW}Convert a file using VapourSynth
${GREEN}(copyleft) Efenstor${NC}\n
Usage: file_proc_vs [options] <src_file> <dst_dir> <proc.py> [start_time]
Options:
  -e dst_ext  the destination file extension, e.g. mp4, mkv, etc.
  -p          preview the output using mpv instead of doing conversion
  -n          do not process audio
  -d ms       audio delay in milliseconds
  -l          get audio delay from source file (-d delay will be added to it)
  -a num      audio track to use
Parameters:
  src_file    source file to process and encode or preview
  dst_dir     directory where the output file is to be placed, if it does not
              exist it will be created
  proc.py     VapourSynth script to be used for processing
  start_time  start time in seconds

${CYAN}Note: dst_dir must be specified even if you're just previewing the output,
      because it's the directory where audio is pre-extracted and used with.${NC}
\n"
  exit
fi

# Default extension
if [ ! "$dst_ext" ]; then
  echo "Using the default extension \"$dst_ext_default\""
  dst_ext=$dst_ext_default
fi

# Prepare some vars
src_file="$1"
dst_dir="$2"
script="$3"
if [ "$4" ]; then
  video_start_time=$4
else
  video_start_time=0
fi
echo "Video start time: $video_start_time sec"
if [ $audio_delay_auto ]; then
  audio_delay_base=$(ffprobe -show_entries stream -select_streams a:0 -i "ruscico/VTS_03_1.VOB" 2>&1 | sed -n "s/start_time=//p")
  echo "Audio delay in the input file: $audio_delay_base sec"
  audio_start_time=$(awk "BEGIN {print $video_start_time-$audio_delay_base+$audio_delay}")
else
  audio_start_time=$(awk "BEGIN {print $video_start_time+$audio_delay}")
fi
echo "Audio start time: $audio_start_time sec"
src=$(basename "$src_file")
audio=$dst_dir/${src%.*}.wav
dst=$dst_dir/${src%.*}.$dst_ext

# Create the output directory
if [ ! -e "$dst_dir" ] || [ ! -d "$dst_dir" ]; then
  echo "Output directory does not exist. Creating..."
  mkdir "$dst_dir"
fi

# Extract audio (only if not already exists; useful for cancelled sessions)
if [ ! $no_audio ]; then
  if [ ! -e "$audio" ]; then
    echo "Extracting audio..."
    if [ $audio_track ]; then
      ffmpeg -i "$src_file" -vn -acodec copy -map 0:a:$audio_track "$audio"
    else
      ffmpeg -i "$src_file" -vn -acodec copy "$audio"
    fi
    # Cancelled
    if [ $? -ne 0 ]; then export file_proc_vs_exit=1; exit 1; fi
  else
    printf "\n${YELLOW}WARNING: Not extracting audio as the temporary audio file already exists!
Double-check if it contains the audio you wanted!${NC}\n"
  fi
fi

# Find the start frame for the given start time
echo "Detecting the start frame for the given start time"
start_frame=$(ffmpeg -hide_banner -i "$src_file" \
  -t $video_start_time -codec:v yuv4 -codec:a copy -f null /dev/null 2>&1 | \
  sed -n "s/.*frame= *\([[:digit:]]*\).*/\1/p" | tail -n 1)
echo "Start time: $video_start_time sec"
echo "Start frame: $start_frame"
echo

# Process video (and mux with audio)
if [ ! $mpv ]; then
  # Remove the file if already exists
  if [ -e "$dst" ]; then
    rm "$dst"
  fi
  # Encode
  echo "Encoding..."
  if [ ! $no_audio ]; then
    env ${vspath:+PYTHONPATH="$vspath":}"$PWD" vspipe -a filename="$src_file" \
      -c y4m "$script" -p -r $threads -s $start_frame - | ffmpeg -i pipe: \
      -ss $audio_start_time -i "$audio" -map 0:v:0 -map 1:a:0 \
      $ffmpeg_options_v $ffmpeg_options_a "$dst"
  else
    env ${vspath:+PYTHONPATH="$vspath":}"$PWD" vspipe -a filename="$src_file" \
      -c y4m "$script" -p -r $threads -s $start_frame - | ffmpeg -i pipe: \
      $ffmpeg_options_v -c:a none "$dst"
  fi
  # Cancelled
  if [ $? -ne 0 ]; then export file_proc_vs_exit=1; exit 1; fi
  # Remove the temporary files
  if [ ! $no_audio ]; then
    rm "$audio"
  fi
else
  # Preview
  echo "Preview..."
  if [ ! $no_audio ]; then
    # With audio
    env ${vspath:+PYTHONPATH="$vspath":}"$PWD" vspipe -a filename="$src_file" \
      -c y4m "$script" -p -r $threads -s $start_frame - | \
      mpv --audio-file="$audio" --audio-delay=-$audio_start_time --fs -
  else
    # Without audio
    env ${vspath:+PYTHONPATH="$vspath":}"$PWD" vspipe -a filename="$src_file" \
      -c y4m "$script" -p -r $threads -s $start_frame - | \
      mpv --fs -
  fi
  # Cancelled
  if [ $? -ne 0 ]; then export file_proc_vs_exit=1; exit 1; fi
fi

