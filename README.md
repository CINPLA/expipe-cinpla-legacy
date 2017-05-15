# expipe-dev

## Installation without browsers
```
cd utils/expipe-environment && conda env create -n expipe && cd ../..
source activate expipe
python setup.py develop/install
```
## Installation with browsers
```
cd utils/expipe-environment && conda env create -n expipe && cd ../..
source activate expipe
python setup.py develop/install --extra browser
```
## Installation without browsers and with phy
```
cd utils/phy-environment && conda env create -n phy && cd ../..
source activate phy
python setup.py develop/install --extra phy
```
## Uninstall everything
```
python setup.py uninstall
source deactivate phy/expipe
conda env remove -n expipe/phy
```
