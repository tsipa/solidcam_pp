# solidcam_pp

Contains a Sinumerik 828D post for a Chinese no-name VMC540. Rotary has not been tested yet.
Also includes a Mach3 post forked from teodoryantcheff/SolidCam-Mach3-Post.

This comes with absolutely no warranty.

## Offline tests

Offline Python postprocessor tests (Python 3.10+, standard library only, no SolidCAM
needed): see [pp_tests/README.md](pp_tests/README.md). Run them from this directory.

Linux / macOS:

```sh
python3 -m unittest discover -s tests -v          # the post
python3 -m unittest discover -s tests_engine -v   # the GPPL test engine
```

Windows (PowerShell or cmd):

```powershell
py -m unittest discover -s tests -v
py -m unittest discover -s tests_engine -v
```

(`python -m unittest ...` works on either system when `python` is a Python 3.10+
interpreter.) The post tests run on the GPPL engine in `pp_tests/gppl`;
`GPPL_ENGINE=legacy` runs them on the original engine. Suspected postprocessor
defects are reported as skipped "known defect ... reproduced" tests and listed, with
the defects already fixed, in [tests/PP_FINDINGS.md](tests/PP_FINDINGS.md); set
`PP_STRICT_KNOWN_DEFECTS=1` to run the open ones as failures.
