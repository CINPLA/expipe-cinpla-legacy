# expipe-dev

## Installation without browsers
```
conda env create -f expipe-environment.yml
source activate expipe
python setup.py develop|install
```
## Installation with browsers
```
conda env create -f expipe-environment.yml
source activate expipe
python setup.py develop|install --extra browser
```
## Installation without browsers and with phy
```
conda env create -f phy-environment.yml
source activate phy
python setup.py develop|install --extra phy
```
## Uninstall everything
```
python setup.py uninstall
source deactivate phy|expipe
conda env remove -n phy|expipe
```
