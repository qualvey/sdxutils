#!/bin/bash

nasup() {
  dir="/home/ryu/code/oneKey/et/"
  url="http://nas.nebulaol.com:88/?launchApp=SYNO.SDS.Drive.Application#file_id=887980386458581107"
  thunar "${dir}" &
  ~/.local/bin/chromium-smart --new-window $url &
  dufs $dir
}

set -e
dir="/home/ryu/code/oneKey"
source "$dir/venv/bin/activate"

if [ "$1" = "today" ]; then
  source "$dir/venv/bin/activate"
  python "$dir/ota.py"
  exit 0
fi

dt=$(date -d "yesterday" +"%m%d")
etfile="${dt}日报表/2025年日报表.xlsx"

python "$dir/main.py"
#et "$dir/et/${etfile}" &
libreoffice "$dir/et/${etfile}" &
nasup
