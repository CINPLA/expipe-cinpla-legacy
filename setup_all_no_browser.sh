for D in python-neo elephant exdir expipe expipe-browser expipe-cli exdir-cli expipe-plugin-cinpla exdir-browser expipe-io-neuro exana pyxona; do
    if [ -d "$D" ]; then
        cd "$D"
        python setup.py develop
        cd ..
    fi
done
