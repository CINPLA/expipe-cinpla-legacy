# This repository is deprecated, use expipe-cinpla-requirements to aid installation

## Scope
This is a development repository for all expipe related projects. It serves to simplify installation and development that goes across multiple projects.

## Development
If you develop across multiple projects you may fork this repository and send pull requests. However, **YOU** are then responsible to push these updates to respective subrepo projects. This can sometimes be a complicated endeavour if there are updates in progress on these projects.

## Issues
Issues are not included in this repository, if you have problems please open an issue in the respective project where it belongs. This is to keep a repository-relevant issue tracking history.

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
