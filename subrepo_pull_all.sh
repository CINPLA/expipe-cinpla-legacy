#!/bin/bash
for D in python-neo \
         elephant \
         exdir \
         expipe \
         expipe-browser \
         expipe-cli \
         exdir-cli \
         expipe-plugin-cinpla \
         exdir-browser \
         expipe-io-neuro \
         exana \
         phy \
         phy-contrib \
         pyxona; do
    if [ -d "$D" ]; then
        git subrepo pull "$D"
    fi
done
