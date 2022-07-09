# FINCEN 114 FBAR with GnuCash

A simple Python script based on [Piecash](https://github.com/sdementen/piecash) in order to calculate high balances of accounts, with the primary intent of filing the FINCEN 114 - FBAR report.

## Preparation

1. Download ``gnucash-fincen114``.
2. Start up virtual environment

Something like::

    pipenv install --requirements ./requirements.txt

3. If you are not using SQLite as file format, save as your GnuCash database in SQLite format.

Currently, no option for changing database type. In order to change, you need to play with the script.

## Configurations

1. In GnuCash, tag each account you would like included in the FBAR report with the word ``#fbar``. It doesn't matter where you put it, as long as it is in the description somewhere.
2. Not required: Get the Exchange rate as of December 31 of the year you are interested in. Needed to convert into USD, which is required for FBAR filing.
3. Pick the year. If you do not pick one, last calendar year will be used.

Then run::

    python3 ./fincen114.py myportfolio.gnucash --conversion <conversion_rate>



## Contributing

- Look at issues in the [Issues section of the GitHub repo](https://github.com/zgypa/gnucash_fincen114/issues).
- Make all pull requests off of the ``develop`` branch.
- Please commit pull request for changes.
