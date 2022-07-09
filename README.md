# FINCEN 114 FBAR with GnuCash

A simple Python script based on [Piecash](https://github.com/sdementen/piecash).

## Preparation

1. Download ``gnucash-fincen114``.
2. Start up virtual environment

Something like::

    pipenv install --requirements ./requirements.txt

3. If you are not using SQLite as file format, save as your GnuCash database in SQLite format.

Currently, no option for changing database typ

## Configurations

It is necessary to configure things manually inside the Python file at this stage.

- ``GNUCASH_DB_FILE`` is the SQLite file name of your GnuCash database.
- ``BANK_ACCOUNTS`` is the GUID of the bank accounts to use. 
- ``THIS_YEAR`` is this calendar year. The report will be performed automatically from last year's Jan 1 to last year's Dec 31. So change THIS_YEAR one year greate to whatever year you need to get FBAR values for.

