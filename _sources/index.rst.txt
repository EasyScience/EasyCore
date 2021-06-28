.. image:: https://raw.githubusercontent.com/easyScience/easyCore/master/resources/images/ec_logo.svg
   :target: https://github.com/easyscience/easycore

``easyCore`` is the foundation of the easyScience universe, providing the building blocks for libraries and applications which aim to make scientific data simulation and analysis easier.

=========================================
Welcome to easyCore's documentation!
=========================================

The code of the project is on Github: `easyCore <https://github.com/easyScience/easyCore>`_

Features of easyCore
=========================

Free and open-source
Anyone is free to use easyCore and the source code is openly shared on GitHub.

* *Cross-platform* - easyCore is written in Python and available for all platforms.

* *Various techniques* - easyCore has been used to build various libraries such as easyDiffraction and easyReflectometry.

* *Advanced built-in features* - easyCore provides features such as model minimization, automatic script generation, undo/redo, and more.


Projects using easyCore
============================

easyCore is currently being used in the following projects:

* `easyDiffraction <https://easydiffraction.org>`_ - Scientific software for modelling and analysis of neutron diffraction data.

* `easyReflectometry <https://easyreflectometry.org>`_ - Scientific software for modelling and analysis of neutron reflectometry data.


Installation
============

Install via ``pip``
-------------------

You can do a direct install via pip by using:

.. code-block:: bash

    $ pip install easyScienceCore

Install as an easyCore developer
-------------------------------------

You can get the latest development source from our `Github repository
<https://github.com/github.com/easyScience/easyCore>`_.:

.. code-block:: console

    $ git clone https://github.com/easyScience/easyCore
    $ cd easyCore

And install via pip:

.. code-block:: console

    $ pip install -r requirements.txt
    $ pip install -e .

Or Poetry

.. code-block:: console

    $ git clone https://github.com/easyScience/easyCore
    $ cd easyCore
    $ poetry install

.. installation-end-content

Documentation
------------------------------------------

.. toctree::
   :caption: Getting Started
   :maxdepth: 3

   getting-started/overview
   getting-started/installation
   getting-started/quick-start
   getting-started/faq


.. toctree::
   :caption: Base Classes
   :maxdepth: 3

   reference/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`