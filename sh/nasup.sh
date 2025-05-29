#!/bin/bash

dir="/home/ryu/code/oneKey/et/"
url='http://nas.nebulaol.com:88/?launchApp=SYNO.SDS.Drive.Application#file_id=877012051539574605'
thunar "${dir}" &
#firefox --new-window "http://nas.nebulaol.com:88/?launchApp=SYNO.SDS.Drive.Application"
firefox --new-window $url
