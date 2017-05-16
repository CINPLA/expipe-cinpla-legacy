Welcome to expipe-plugin CINPLA's documentation!
================================================

Expipe is a python module for neuroscientific data analysis.

.. toctree::
   :maxdepth: 2
   :hidden:

   installation
   developers_guide
   authors

.. testsetup:

   import expipe
   expipe.ensure_testing()

Working with Axona
------------------

Open Anaconda 3 prompt

``FILNAVN`` er "axona navn" e.g. 22031701
``DATO`` 220317
``SESSION`` 01
``ROTTE`` er rottenavnet e.g. 1704
``ACTION-ID`` er ``ROTTE-FILNAVN``::

  activate phy

To get an overview of available commands::
  expipe
For help på en spesifikk kommando::
  expipe register-axona --help

To overwrite existing data use ``--overwrite``::

  expipe register-axona `z:\USER\DATA\ROTTE\FILNAVN.set`

Now modules are loaded to the firebase server and depth registration
is promted to the user.

**Spikesorting**::

  $ expipe spikesort ROTTE-DATO-SESSION
  $ phy neo-gui c:\temp\ROTTE-DATO-SESSION\main.exdir --channel-group 0

Save with ctrl-s

**Plotting og analysis**
*Plotting with notebook*::

  $ expipe generate-notebook ROTTE-DATO-SESSION --run

``kernel -> restart and run all``

*Make png figurer*::

  $ expipe analyse ROTTE-DATO-SESSION --spatial

If you only want to look at a particular channel group::

  $ expipe analyse ROTTE-DATO-SESSION --channel-group 0

*Register cells and transfer data to norstore*::

  $ expipe register-units ROTTE-DATO-SESSION

  $ expipe transfer ROTTE-DATO-SESSION --from-temp

Gå inn til `SERVER/PROJECT/ROTTE-FILNAVN/main.exdir/analysis` to check out
results

*Example tags:*
Bare dritt: no
Good shit: yes
Vet ikke: maybe
Head direction: HD
Grid cell: GC
Place cell: PC
Spatial cell: SC
Boarder cell: BC

*Adjustment*::

  $ expipe adjust ROTTE --user Aurora --date dd.mm.yyyy:HH:MM/now --left um --right um


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
