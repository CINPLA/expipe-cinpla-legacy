#!/bin/bash
for D in python-neo \
         exdir \
         expipe \
         expipe-browser \
         expipe-cli \
         exdir-cli \
         expipe-plugin-cinpla \
         exdir-browser \
         expipe-io-neuro \
         exana \
         phy-contrib \
         pyxona; do
    if [ -d "$D" ]; then
        cd "$D"
        git subrepo push "$D"
    fi
done
