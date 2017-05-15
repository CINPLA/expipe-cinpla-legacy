#!/bin/bash
for D in neo \
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
         expipe-dev \
         pyxona; do
    pip uninstall "$D" -y
done
