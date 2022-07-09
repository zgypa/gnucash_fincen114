#!/usr/bin/env python

from datetime import datetime, date, timedelta
import locale
import piecash
import prettytable

locale.setlocale(locale.LC_ALL, '')
GNUCASH_DB_FILE = "master_folio/masterfolio.gnucash"

# The GUID for "40 Bank Accounts EUR"
BANK_ACCOUNTS_EUR = "81545e89426f7f9122e86340a2528a8d"

THIS_YEAR = datetime.now().date().year
LAST_YEAR = THIS_YEAR - 1


def opening_balance(account):
    return account.get_balance(at_date=date(LAST_YEAR, 1, 1))


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n+1)


def get_max_balance(account, year=LAST_YEAR):
    """Get the highest balance for a given account in a given year.

    Uses piecash.Account.get_balance(at_date=). This method is about 5x slower than ``get_max_balance1()``, because the get_balance functions recalculates the entire balance for each run. But it is slightly more accurate, because it does not take into account in-accurate daily oscillations. 

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
    max_balance = 0
    max_balance_day = date(LAST_YEAR, 1, 1)
    print(f'Processing {account.name} {account.type}: ', end='')
    for sp in account.splits:
        day = sp.transaction.post_date
        balance = account.get_balance(at_date=day)
        # print(f'{day} {locale.currency(sp.value, symbol=False)}\t{locale.currency(balance, symbol=False)}')
        if day > date(year-1, 12, 31) and day < date(year+1, 1, 1):
            if balance > max_balance:
                max_balance = balance
                max_balance_day = day
    print(max_balance)
    return max_balance, max_balance_day


def get_max_balance1(account, year=LAST_YEAR):
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
        See notes in ``get_max_balance()`` above. The point is that the imported
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
    max_balance = 0
    max_balance_day = date(LAST_YEAR, 1, 1)
    balance = 0
    print(f'Processing {account.name}: ', end='')
    for sp in session.query(piecash.Split).\
            filter(piecash.Split.account_guid == account.guid).\
            join(piecash.Transaction).\
            order_by(piecash.Transaction.post_date):
        balance += sp.quantity
        day = sp.transaction.post_date
        # print(f'{day} {locale.currency(sp.value, symbol=False)}\t{locale.currency(balance, symbol=False)}')
        if day > date(year-1, 12, 31) and day < date(year+1, 1, 1):
            if balance > max_balance:
                max_balance = balance
                max_balance_day = day

    print(max_balance)
    return max_balance, max_balance_day


def fincen_subaccounts(accounts):
    for acc in accounts.children:
        if acc.type == 'BANK' and acc.placeholder == 0:
            max_balance, max_balance_day = get_max_balance(account=acc)
            if max_balance > 0:
                fincen_table.add_row([
                    acc.name,
                    locale.currency(max_balance, grouping=True, symbol=False),
                    acc.commodity.mnemonic,
                    max_balance_day
                ])
        else:
            fincen_subaccounts(acc)


def fincen114():
    """Calculate maximum amount of EUR accounts for FINCEN114 FBAR reporting.

    """
    global fincen_table
    book = piecash.open_book(GNUCASH_DB_FILE, readonly=True, open_if_lock=True)
    session = book.session

    eur_accounts = book.accounts(guid=BANK_ACCOUNTS_EUR)
    fincen_table = prettytable.PrettyTable()
    fincen_table.field_names = ["Account", "Max Balance", "CUR", "Date"]
    fincen_table.align["Account"] = "l"
    fincen_table.align["Max Balance"] = "r"
    fincen_table.align["CUR"] = "l"
    fincen_subaccounts(eur_accounts)

    print(fincen_table)

def main():
    fincen114()

if __name__ == "__main__":
    main()