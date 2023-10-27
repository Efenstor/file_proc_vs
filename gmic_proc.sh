#!/bin/sh
# (copyleft) Efenstor, 2023

gmic_commands="banding_denoise_v2 50,0,20,30,0,0,0,133.257,16.7024"

fps=23.976
ffmpeg_options="-c:v libx264 -crf 16 -pix_fmt yuv420p"
threads=8
in_dir="gmic_input_frames"
out_dir="gmic_output_frames"
gmic=gmic

# ctrlc
ctrlc() {
  echo "Abort"
  abort=true
}

# Help
if [ $# -lt 2 ]; then
  echo "Usage: gmic_proc.sh <input_video_file> <output_video_file>"
  exit
fi

# Extract video to images
if [ ! -d "$in_dir" ]; then
  mkdir "$in_dir"
else
  read -p "Input frames dir already exists. Skip extracting? Y/n " ans
  if [ "$ans" = "n" ]; then
    echo "Purging the input dir..."
    rm -r "$in_dir"
    mkdir "$in_dir"
  else
    skip_extract=true
  fi
fi
if [ ! $skip_extract ]; then
  echo "Extracting frames..."
  ffmpeg -i "$1" "$in_dir/%08d.png"
  if [ $? -ne 0 ]; then
    exit
  fi
fi

# Purge the output dir
if [ ! -d "$out_dir" ]; then
  mkdir "$out_dir"
else
  read -p "Output frames dir already exists. Purge it? Y/n " ans
  if [ "$ans" != "n" ]; then
    echo "Purging the output dir..."
    rm -r "$out_dir"
    mkdir "$out_dir"
  fi
fi

# Main multi-threaded processing
echo "Processing..."
trap "ctrlc" INT
files=$(find "$in_dir" -maxdepth 1 -type f -iname "*.png" | sort -n -f)
while [ -n "$files" ]; do
  # Get free thread count
  thr_working=$(pgrep -x $gmic | wc -l)
  if [ $abort ] && [ ! $thr_working ]; then break; fi
  thr_free=$(expr $threads - $thr_working)
  # Run new threads
  while [ $thr_free -gt 0 ] && [ -n "$files" ]; do
    f=$(echo "$files" | head -n 1)
    of="$out_dir"/$(basename "$f")
    if [ -f "$of" ]; then
      echo "Output file $of already exists. Skipping..."
      files=$(echo "$files" | tail -n +2)
      continue
    fi
    $gmic "$f" $gmic_commands -o "$of" &
    if [ $? -ne 0 ]; then
      exit
    fi
    thr_free=$(expr $thr_free - 1)
    files=$(echo "$files" | tail -n +2)
  done
  if [ $abort ]; then break; fi
done
trap - INT
# Wait for all threads to finish
while pgrep -x $gmic > /dev/null; do true; done

# Encode
echo "Encoding frames to video..."
ffmpeg -y -framerate $fps -i "$out_dir/%08d.png" $ffmpeg_options "$2"

