# A few Django apps

## About

This app was made for educational purposes:

- Reports: create messages of various types, comment and change the status
- Homeoffice, track the absence of colleagues
- Time-sheet (not finished), takes data from Homeoffice
- Resource planning: plan assemblers and cars, based on Homeoffice info

## Installation

1. Make sure you have python3 installed.
1. Create python venv [as usial](https://docs.python.org/3/library/venv.html).
2. Activate venv: `. venv/bin/activate`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Launch the app: `python manage.py runserver`.
3. Login to `http://127.0.0.1:8000/reg/` with login `kostya` and password `L7tHNEi0%sjO`.

A small SQLite demo-DB is included, enjoy! In case you start with an empty DB, you'll need migrations and also you'll need to [setup admin account for Django](https://docs.djangoproject.com/en/5.1/intro/tutorial02/#creating-an-admin-user).

The buttons on the top allow to switch between the apps.

## Background

You can read the background story and find all my contacts [here](https://en.kovchinnikov.info/2024-11-newideas.html).
