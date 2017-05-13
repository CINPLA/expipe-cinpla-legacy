for D in python-neo exdir expipe expipe-browser expipe-cli exdir-cli expipe-plugin-cinpla exdir-browser expipe-io-neuro exana pyxona phy-contrib; do
    if [ -d "$D" ]; then
        git subrepo push "$D"
    fi
done
