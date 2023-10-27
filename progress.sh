#!/bin/sh
# by Efenstor, 2022-2023

DELLINE="\r\033[0K"

if [ $# -lt 2 ]; then
  printf "\n${YELLOW}Display progress when processing files by another process
${GREEN}(copyleft) Efenstor${NC}\n
Usage: progress.sh <src_dir> <dst_dir>\n
Parameters:
  src_dir  directory containing source files
  dst_dir  directory where processed files are being placed
\n"
  exit
fi

ftotal=$(($(ls "$1" | wc -l)*2))
fdone=0
while [ $fdone -lt $ftotal ]
do
  fdone=$(ls "$2" | wc -l)
  pdone=$(($fdone*100/$ftotal))
  echo -n "Done: $pdone% ($fdone/$ftotal)"
  sleep 1
  echo -n $DELLINE
done

