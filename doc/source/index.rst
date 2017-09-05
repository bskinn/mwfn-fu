.. mwfn-fu documentation master file, created by
    sphinx-quickstart on Wed Aug 30 00:56:28 2017.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.

Welcome to mwfn-fu's documentation!
===================================

``mwfn-fu`` is intended to provide two-fold assistance when working
with `Multiwfn <http://sobereva.com/multiwfn/>`__, "A Multifunctional
Wavefunction Analyzer."  Interaction with Multiwfn is primarily conducted
through a command-line interface, and many of the generated results
are reported only as text printed to ``stdout``.  The goals of this
package are

 1. Enabling automatic execution and operation of Multiwfn, as in a
    scripting context.

 2. Implementing a command-line 'wrapper' around Multiwfn that permits
    more convenient extraction of its computational outputs into a
    numerically manipulable form.

``mwfn-fu`` is in a preliminary stage of development, and so far only
a basic driver class for Multiwfn has been implemented, which provides
an initial implementation of #1 above.

Contents
--------

.. toctree::
    :maxdepth: 2

    Usage Instructions <usage>
    API <api>



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

