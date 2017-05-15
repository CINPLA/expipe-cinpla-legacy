#!/bin/bash
for D in neo \
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
         expipe-dev \
         pyxona; do
    pip uninstall "$D" -y
done
