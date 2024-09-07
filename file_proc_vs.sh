#!/bin/sh
# (copyleft) Efenstor 2015-2024
# Revision 2024-09-08

# Examples:
# ffmpeg_options_v="-c:v libx264 -crf 16 -preset fast -tune film"
# ffmpeg_options_v="-c:v ffvhuff -vf pp=subfilters=l5/lowpass5"
# ffmpeg_options_v="-c:v mjpeg -q:v 2 -vf colormatrix=bt709:bt601"
# ffmpeg_options_a="-c:a copy"
# ffmpeg_options_a="-c:a pcm_s16le"
# ffmpeg_options_a="-c:a ogg -q:a 3.0"

# User defines
ffmpeg_options_v="-c:v libx264 -crf 18 -tune film"
ffmpeg_options_a="-c:a aac -b:a 256k"
dst_ext_default="mkv"
threads=8
thread_queue_size=64
vspath=/usr/local/lib/python3.11/site-packages

# Internal defines
export file_proc_vs_exit=
RED="\033[0;31m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
NC="\033[0m"

# Parse the named parameters
optstr="?he:d:a:pxnlf"
audio_track=0
audio_delay=0
while getopts $optstr opt; do
  case "$opt" in
    e) dst_ext=$OPTARG
       echo "Destination extension: $dst_ext"
       ;;
    d) audio_delay=$(awk "BEGIN {print ($OPTARG)/1000}")
       echo "Audio delay: $audio_delay sec"
       ;;
    a) audio_track=$OPTARG
       echo "Audio track: $audio_track"
       ;;
    p) mpv=true
       echo "Preview instead of encoding"
       ;;
    x) pause=true
       echo "Start preview in the paused state"
       ;;
    n) no_audio=true
       echo "Without audio"
       ;;
    l) audio_delay_auto=true
       echo "Detect audio delay from source"
       ;;
    f) fast_time=true
       echo "Using fast and crude time to frame number conversion"
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
Usage: file_proc_vs [options] <src_file> <dst> <proc.py> [start_time]
       [start_frame] [end_frame]
Options:
  -e dst_ext   destination file extension, defines container format; if it is
               specified then <dst> will always be treated as a directory name
  -p           preview the output using mpv instead of doing conversion
  -x           start preview in the paused state
  -n           do not process audio
  -d ms        audio delay in milliseconds
  -l           get audio delay from source file (-d delay will be added to it)
  -a num       audio track to use
  -f           use fast and crude time to frame number conversion (seconds*fps)
Parameters:
  <src_file>    source file to process and encode or preview
  <dst>         file or directory where the output file is to be placed;
                if <dst> has no extension then it is assumed than it is a
                directory, if it does not exist it will be created; extracted
                audio file is placed next to the output file; existing files are
                overwritten silentily
  <proc.py>     VapourSynth script to be used for processing
  [start_time]  start time in seconds
  [start_frame] specify start frame directly to accelerate start (start_time
                should also be specified if audio is used)
  [end_frame]   end frame

${CYAN}Note: dst_dir must be specified even if you're just previewing the output,
      because it's the directory where audio is pre-extracted and used with.${NC}
\n"
  exit
fi

# Determine if dst is a file or a dir
if [ ! "$dst_ext" ]; then
  # Extension not specified directly with an -e parameter
  ext="${2##*.}"
  if [ "$ext" = "$2" ]; then ext= ; fi
  echo "ext: $ext"
  if [ $(echo "$2" | sed "s/.*\/$//g") ] && [ "$ext" ]; then
    # dst not ending with a / and has some extension
    dst="$2"
    dst_dir=$(dirname "$2")
    dst_ext="$ext"
  else
    dst_ext=$dst_ext_default
    echo "Destination extension: $dst_ext"
  fi
fi

# Prepare some vars
src_file="$1"
if [ ! "$dst_dir" ]; then
  echo "Destination dir: \"$dst\""
  dst_dir="$2"
fi
script="$3"
if [ "$4" ]; then
  video_start_time=$4
else
  video_start_time=0
fi
if [ "$5" ]; then
  start_frame=$5
fi
if [ "$6" ]; then
  end_frame=$6
fi
echo "Video start time: $video_start_time sec"
if [ $audio_delay_auto ]; then
  video_delay_base=$(ffprobe -show_entries stream -select_streams v:0 -i "$src_file" 2>&1 | sed -n "s/start_time=//p")
  echo "Video delay in the input file: $video_delay_base sec"
  audio_delay_base=$(ffprobe -show_entries stream -select_streams a:0 -i "$src_file" 2>&1 | sed -n "s/start_time=//p")
  echo "Audio delay in the input file: $audio_delay_base sec"
  audio_start_time=$(awk "BEGIN {print ($video_start_time)-($audio_delay_base)+($video_delay_base)+($audio_delay)}")
else
  audio_start_time=$(awk "BEGIN {print ($video_start_time)+($audio_delay)}")
fi
echo "Audio start time: $audio_start_time sec"
src=$(basename "$src_file")
audio="$dst_dir/$src".wav
if [ ! "$dst" ]; then
  dst="$dst_dir/${src%.*}.$dst_ext"
  echo "Destination file: \"$dst\""
fi

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
echo "Start time: $video_start_time sec"
if [ ! $start_frame ]; then
  if [ ! $fast_time ]; then
    # Precise calculation
    echo "Detecting the start frame for the given start time"
    start_frame=$(ffmpeg -hide_banner -i "$src_file" \
      -t $video_start_time -codec:v yuv4 -codec:a copy -f null /dev/null 2>&1 | \
      sed -n "s/.*frame= *\([[:digit:]]*\).*/\1/p" | tail -n 1)
  else
    # Fast calculation
    fps=$(ffprobe -show_entries stream -select_streams v:0 -i "$src_file" 2>&1 | \
      sed -n "s/avg_frame_rate=//p")
    start_frame=$(awk "BEGIN {print int(($video_start_time)*($fps))}")
  fi
fi
echo "Start frame: $start_frame"
if [ $end_frame ]; then
  echo "End frame: $end_frame"
fi
echo

# Process video (and mux with audio)
if [ ! $mpv ]; then
  # Remove the file if already exists
  if [ -e "$dst" ] && [ -f "$dst" ]; then
    rm "$dst"
  fi
  # Encode
  echo "Encoding..."
  if [ ! $no_audio ]; then
    env ${vspath:+PYTHONPATH="$vspath":}"$PWD" vspipe -a filename="$src_file" \
      -c y4m "$script" -p -r $threads -s $start_frame \
      ${end_frame:+-e $end_frame} - | \
      ffmpeg -thread_queue_size $thread_queue_size -i pipe: \
      -ss $audio_start_time -i "$audio" -map 0:v:0 -map 1:a:0 \
      $ffmpeg_options_v $ffmpeg_options_a "$dst"
  else
    env ${vspath:+PYTHONPATH="$vspath":}"$PWD" vspipe -a filename="$src_file" \
      -c y4m "$script" -p -r $threads -s $start_frame \
      ${end_frame:+-e $end_frame} - | \
      ffmpeg -thread_queue_size $thread_queue_size -i pipe: \
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
      -c y4m "$script" -p -r $threads -s $start_frame \
      ${end_frame:+-e $end_frame} - | \
      mpv --audio-file="$audio" \
      	--audio-delay=$(awk "BEGIN {print -($audio_start_time)}") \
      	${pause:+--pause} --fs -
  else
    # Without audio
    env ${vspath:+PYTHONPATH="$vspath":}"$PWD" vspipe -a filename="$src_file" \
      -c y4m "$script" -p -r $threads -s $start_frame \
      ${end_frame:+-e $end_frame} - | \
      mpv ${pause:+--pause} --fs -
  fi
  # Cancelled
  if [ $? -ne 0 ]; then export file_proc_vs_exit=1; exit 1; fi
fi

