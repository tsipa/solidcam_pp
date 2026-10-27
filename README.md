# solidcam_pp

Contains a Sinumerik 828D post for a Chinese no-name VMC540. Rotary has not been tested yet.
Also includes a Mach3 post forked from teodoryantcheff/SolidCam-Mach3-Post.

This comes with absolutely no warranty.

Offline Python postprocessor tests: see [pp_tests/README.md](pp_tests/README.md).
Run `python -m unittest discover -s tests -v` (post) and
`python -m unittest discover -s tests_engine -v` (test engine) from this directory.
