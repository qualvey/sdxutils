#!/bin/bash

dir="/home/ryu/code/oneKey"
etdir="${dir}/et"
url='http://nas.nebulaol.com:88/?launchApp=SYNO.SDS.Drive.Application#file_id=877012051539574605'
dt=$(date -d "yesterday" +"%m%d")
source "$dir/venv/bin/activate"
python "$dir/main.py"
etfile="${dt}日报表/2025年日报表.xlsx"

et "$dir/et/${etfile}" &
thunar "$etdir" &
firefox --new-window $url &
dufs "$etdir"
