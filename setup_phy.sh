#!/bin/bash
for D in python-neo \
         elephant \
         exdir \
         expipe \
         expipe-cli \
         exdir-cli \
         expipe-plugin-cinpla \
         expipe-io-neuro \
         exana \
         phy \
         phy-contrib \
         pyxona; do
    if [ -d "$D" ]; then
        cd "$D"
        python setup.py $1
        cd ..
    fi
done
