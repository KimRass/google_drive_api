#!/bin/bash

drive_id=$1
path=$2

mkdir -p $path

./down_gdrive.py \
	-p $path \
	--drive_id $drive_id \
	--download
# 	--extentions ADD EXTENTIONS IF YOU WANT TO DOWNLOAD ONLY SPECIFIC FILES
