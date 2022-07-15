# Application

This repository contains the web publication application of the corpus of manuscript sales catalogues.

## Getting started :

* First, download this repository. Using command lines, clone the repository with :
```bash
git clone https://github.com/katabase/Application.git
cd Application
```
* Then, create a virtual environment and activate it :
```bash
python3 -m venv my_env
source my_env/bin/activate
```
* Now, you have to install dependencies :
```bash
pip install -r requirements.txt
```
* You can finally launch the application :
```bash
python3 run.py
```

## Workflow

<img src="images/workflow.png" alt="Katabase workflow diagram" title="Katabase Workflow" width="70%" height="50%"/>

## Website updates and description of the git branches

The structure of the git repository is as follows:
- [`main`](https://github.com/katabase/Application) for the current, stable version of the 
  Katabase app
- [`dev`](https://github.com/katabase/Application/tree/dev) for the unstable version of the
  app, in developpment and not running online.
- [`versionX.X.X`](https://github.com/katabase/Application/tree/version1.0.0) are archive
  repositories to document the former versions of the Katabase app. There should be as many
  of these branches as there are new versions of the website, and their `X.X.X` code should
  follow the release numbers.

New additions to the website should be done on `dev` and tested before being moved to `main`.
The version of the website visible on `main` should be the same as the version of the website
online (unless, for reasons out of our control, we can't publish a new version of the website
online, but a new version is ready and won't be changed again). Before merging a new version
of the website from `dev` to `main`, the `main` branch should be moved the `versionX.X.X`.
A new release should then be created for the updated version of the website.

## Credits

The application was designed by Alexandre Bartz and Paul Kervegan with the help of Simon Gabay, Matthias Gille Levenson and Ljudmila Petkovic.

## Cite this repository

## Licence
This work is licensed under [GNU GPL-3.0](./LICENSE).
