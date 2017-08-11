#!/bin/bash

NAMEONE=$1
NAMETWO=$2

WINNER=$((RANDOM %2))

if [ $WINNER -eq 0 ]; then
    echo $NAMEONE
else
    echo $NAMETWO
fi
