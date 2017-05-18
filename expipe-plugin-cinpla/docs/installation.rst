.. _installation_page:

============
Installation
============

We recommend installing the expipe dev package found at https://github.com/CINPLA/expipe-dev::

  $ git clone https://github.com/CINPLA/expipe-dev.git

Due to dependency issues we have to make two separate environments, one for
phy and one for expipe with browsers. These environments will hopefully
be possible to merge in the near future.

In short, install an expipe environment with browsers, and a phy environment
for spikesoting:

.. code-block:: bash

  cd expipe-dev
  conda env create -f expipe-environment.yml
  activate expipe
  python setup.py develop --extra browser
  conda env create -f phy-environment.yml
  activate phy
  python setup.py develop --extra phy

Following the instructions you should be be able to::

  expipe --help

Configuring expipe
------------------

Now that you have the enviroments installed you need to configure expipe. In
``expipe-plugin-cinpla/utils`` you will find example configuration files.
Start by copying all files to ``c:/users/uiousername/.config/expipe``.
Open ``config.yaml`` which looks like:

.. code-block:: yaml

  data_path: c:/users/uiousername/expipe_temp_storage
  processing:
    data_path: /home/user/expipe_temp_storage
    username: <processing server username>
    hostname: user@ipaddress
  norstore:
    data_path: /norstore_osl/projects/NS9048K/server
    username: <norstore username>
    hostname: login.norstore.uio.no
  firebase:
    email: your@email.com
    password: yourpassword
    config:
      apiKey: AIzaSyAjGqZwiCKS2333m820e9UdZ7jbnkfEpjw
      authDomain: expipe-26506.firebaseapp.com
      databaseURL: https://expipe-26506.firebaseio.com
      storageBucket: expipe-26506.appspot.com

Here we have defined two servers, one for `norstore` and one for a `processing`
server e.g. your office computer; see [usage](address to usage).
Note that you can add arbitrary names for servers.
