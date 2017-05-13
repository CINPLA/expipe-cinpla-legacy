# Exdir CLI #

Simple command line interface for browsing exdir folders.

## Installation ##

Exdir CLI is distributed as an Anaconda package.

[Download Anaconda](http://continuum.io/downloads)

```bash
$ conda install exdir-cli -c defaults -c cinpla -c conda-forge
```

You may replace `-c cinpla` with `-c cinpla/label/dev` to get the latest
unstable version from the dev branch.

## Usage ##

```bash
$ ls
test.exdir
$ exdir list test.exdir
group1
group2
dataset
$ cd test.exdir
$ exdir list
group1
group2
dataset
$ exdir show dataset
nums
Type: Dataset
Name: /dataset
Shape: (23632,)
Data:
[0 0 0 ..., 6 6 6]
```

## Documentation ##

Use `exdir --help` to list available commands.
More documentation will be added at a later point in time.
