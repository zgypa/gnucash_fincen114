#!/usr/bin/env python

import sys
import argparse
from datetime import datetime, date, timedelta
import locale
from decimal import Decimal

import piecash
import prettytable

VERSION = "0.1.0"

locale.setlocale(locale.LC_ALL, '')
GNUCASH_DB_FILE = "master_folio/masterfolio.gnucash"

# The name of the account parent of the accounts to traverse. Must be the exact
# bank account name.
PARENT_OF_BANK_ACCOUNTS = ""
LAST_YEAR = datetime.now().year

aggregate_high_balance_usd = 0
book = None
args = None

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n+1)


def get_high_balance(account):
    """Get the highest balance for a given account in a given year.

    Uses piecash.Account.get_balance(at_date=). This method is about 5x slower than ``get_high_balance1()``, because the get_balance functions recalculates the entire balance for each run. But it is slightly more accurate, because it does not take into account in-accurate daily oscillations. 

    The resolution of transactions is 1 day. Any movement within that day is therefore random and should not be taken into account.

    Parameters
    ----------
    :param account: The account to be analyzed
    :type account: :class:`piecash.Account`

    :param year: The year to process.
    :type year: int

    :return: A tuple of maximum balance and maximum data
    :rtype: tuple
    """
    year = args.year
    high_balance = 0
    high_balance_day = date(year, 1, 1)
    print(f'Processing {account.name} {account.type}: ', end='')
    for sp in account.splits:
        day = sp.transaction.post_date
        balance = account.get_balance(at_date=day)
        # print(f'{day} {locale.currency(sp.value, symbol=False)}\t{locale.currency(balance, symbol=False)}')
        if day > date(year-1, 12, 31) and day < date(year+1, 1, 1):
            if balance > high_balance:
                high_balance = balance
                high_balance_day = day
    print(high_balance)
    return high_balance, high_balance_day


def get_high_balance1(account):
    """Get the highest balance for a given account in a given year.

    Using the underlying SQLAlchemy session has been used, because the
    get_balance() function only provides a total balance for a given day,
    while what we need here is the maximum balance the account touched. We
    therefore need to watch the balance transaction by transaction.
    I eventually also tried getting the splits from the piecash library, and
    summing up the way that get_balance() does, but this fails to work,
    because the splits come in unsorted, and there is no clean and easy way to
    sort them by their transaction's posted date. Using SQLAlchemy provides a
    quick and clean solution where we can sort by date very quickly

    .. warning::
        Great thought, however i don't think this is the best approach to go.
        See notes in ``get_high_balance()`` above. The point is that the imported
        transaction's precision/resolution is only one day. So i must consider
        anything that happens within one day as atomic, and any intra-day
        balances as non-sensical, because we have no way of knowing what the
        actual balance was on the bank account at a specific time of the day.

        I left this function here just for example purposes on how to use
        SQLAlchemy.

    Parameters
    ----------
    :param account: The account to be analyzed
    :type account: :class:`piecash.Account`

    :param year: The year to process.
    :type year: int

    :return: A tuple of maximum balance and maximum data
    :rtype: tuple
    """
    year = args.year
    high_balance = 0
    high_balance_day = date(year, 1, 1)
    balance = 0
    print(f'Processing {account.name}: ', end='')
    session = book.session
    for sp in session.query(piecash.Split).\
            filter(piecash.Split.account_guid == account.guid).\
            join(piecash.Transaction).\
            order_by(piecash.Transaction.post_date):
        balance += sp.quantity
        day = sp.transaction.post_date
        # print(f'{day} {locale.currency(sp.value, symbol=False)}\t{locale.currency(balance, symbol=False)}')
        if day > date(year-1, 12, 31) and day < date(year+1, 1, 1):
            if balance > high_balance:
                high_balance = balance
                high_balance_day = day

    print(high_balance)
    return high_balance, high_balance_day


def add_table_row(account):
    global aggregate_high_balance_usd
    high_balance, high_balance_day = get_high_balance(account=account)
    if args.conversion is None:
        high_balance_usd = "N/A"
    else:
        high_balance_usd = high_balance / Decimal(args.conversion)
        aggregate_high_balance_usd += high_balance_usd
        high_balance_usd = locale.currency(high_balance_usd, grouping=True)
    if high_balance > 0:
        fincen_table.add_row([
            account.name,
            locale.currency(high_balance, grouping=True, symbol=False),
            account.commodity.mnemonic,
            high_balance_usd,
            high_balance_day
        ])


def fincen114(sysargs):
    """Calculate maximum amount of EUR accounts for FINCEN114 FBAR reporting.

    """
    global fincen_table, book, args
    args = sysargs

    book = piecash.open_book(args.dbfile, readonly=True, open_if_lock=True)

    accounts = [account for account in book.accounts if (
        "#fbar" in account.description)]
    fincen_table = prettytable.PrettyTable()
    fincen_table.field_names = ["Account", "Max Balance", "CUR", "USD", "Date"]
    fincen_table.align["Account"] = "l"
    fincen_table.align["Max Balance"] = "r"
    fincen_table.align["CUR"] = "l"
    fincen_table.align["USD"] = "r"
    for account in accounts:
        add_table_row(account)

    if args.conversion is None or aggregate_high_balance_usd > 10000:
        print(fincen_table)
    else:
        # Only required to file FBAR if aggregate of all high balances is over $10k.
        print(
            f"Maximum aggregate high balance is only {locale.currency(aggregate_high_balance_usd, grouping=True)} which is less than $10k. No need to file FBAR for year {args.year}")


def main():
    fincen114()


def cmdline_args():
    # Make parser object
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)

    p.add_argument("dbfile",
                   help="GnuCash DB SQLite file")
    p.add_argument("-y", "--year", type=int, default=LAST_YEAR,
                   help="Year to calculate")
    p.add_argument("-c", "--conversion", type=float,
                   help="Price of 1USD in foreign currency.")
    p.add_argument("--version", action="version",
                   version=f"gnucash-fincen114 v{VERSION}")
    p.add_argument("-v","--verbose", action="store_true", help="Print Exceptions.")
    return(p.parse_args())


# Try running with these args
#
# "Hello" 123 --enable
if __name__ == '__main__':

    if sys.version_info < (3, 5, 0):
        sys.stderr.write("You need python 3.5 or later to run this script\n")
        sys.exit(1)

    try:
        args = cmdline_args()
        fincen114(args)
    except Exception as e:
        print(e + 'Try $python ./fincen114.py "file.gnucash" ')
