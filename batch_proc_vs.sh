#!/bin/sh
# (copyleft) Efenstor 2015-2023
# Revision 2023-10-27

file_proc_script="file_proc_vs.sh"

# Check for the file proc script
SDIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
if [ ! -e "$SDIR/$file_proc_script" ]; then
  echo "Cannot find the \"$file_proc_script\" script file! It is required." >&2
  exit
fi

# Internal defines
RED="\033[0;31m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
NC="\033[0m"

# Parse the named parameters
optstr="?he:d:a:pnl"
while getopts $optstr opt; do
  case "$opt" in
    e) file_proc_params="$file_proc_params -e $OPTARG"
       ;;
    d) file_proc_params="$file_proc_params -d $OPTARG"
       ;;
    a) file_proc_params="$file_proc_params -a $OPTARG"
       ;;
    n) file_proc_params="$file_proc_params -n"
       ;;
    l) file_proc_params="$file_proc_params -l"
       ;;
    :) echo "Missing argument for -$OPTARG" >&2
       exit 1
       ;;
  esac
done

# Parse the unnamed parameters
shift $((OPTIND - 1))

# Show help
if [ $# -lt 4 ]; then
  printf "
${YELLOW}Batch convert files using VapourSynth
${GREEN}(copyleft) Efenstor${NC}\n
Usage: batch_proc_vs [options] <src_dir> <src_ext> <dst_dir> <proc.py>
Parameters:
  src_dir  source directory containing files to process and encode
  src_ext  extension of the source files (without dot, e.g. mp4)
  dst_dir  directory where the output files are to be placed, if it does not
           exist it will be created
  proc.py  VapourSynth script to be used for processing

For description of the options see $file_proc_script.
\n"
  exit
fi

# Do processing
src_dir="$1"
src_ext="$2"
dst_dir="$3"
script="$4"

files=$(find "$src_dir" -maxdepth 1 -type f -iname "*.$src_ext" | sort -n)
IFS=$'\n'
for i in $files; do
  # Process
  if [ $file_proc_params ]; then
    "$SDIR/$file_proc_script" "$file_proc_params" "$i" "$dst_dir" "$script"
  else
    "$SDIR/$file_proc_script" "$i" "$dst_dir" "$script"
  fi
  # Cancelled
  if [ $file_proc_vs_exit ]; then exit $?; fi
done

