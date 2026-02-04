Ideally we have to come to a compromise where for space:
* exposing the functionality in C.
* propogating it up to a Python interface.

and for features:
* gettng easy access to the registers so anything can be done.
* exposing useful interfaces for general use.

Finding the right balance is a challenge...

Proposal:
1. Expose the registers so a sophisticated user can manipulate all possibilities with care.
2. Expose a useful basic interface subset in C and expose as Python class.

Its possible we want to add safety into 1 so that (say) changing a timing mode bit deactivates the clock and bricks the device - is made more difficult.

##Plan: