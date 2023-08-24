#!/usr/bin/env python3

from pathlib import Path
from itertools import chain


def main():
    script_path = Path(__file__).absolute().parent
    template_path = script_path.joinpath('template.beancount')
    output_path = script_path.joinpath('output.beancount')

    extensions = { '.csv', '.gnca', '.gnucash' }
    files = chain(script_path.parent.glob('gnucash/*'), script_path.glob('gnucash/*'))
    filtered_files = filter(lambda f: f.suffix in extensions, files)
    input_path = max(filtered_files, key=lambda f: f.stat().st_mtime)
    with input_path.open(mode='r', newline='') as in_f, template_path.open(mode='r') as tem_f, output_path.open(mode='w') as out_f:
        # copy template over to the output
        out_f.writelines(tem_f)
        # read input CSV, then transform the data
        # and write directly to the output
        if input_path.suffix in { '.csv' }:
            transform_csv(in_f, out_f)
    # start fava
    start_fava(output_path)


def start_fava(path):
    try:
        from setproctitle import setproctitle
        from fava.application import app
        setproctitle('gnucashfava')
        app.config['BEANCOUNT_FILES'] = [path]
        app.run('localhost', 5000)
    except ModuleNotFoundError:
        print('Unable to import module fava and/or setproctitle')
        print('Will not start fava instance')


def transform_csv(input_file, output_file):
    import csv
    reader = csv.DictReader(input_file)
    currency = ''
    transaction_id = ''
    # gnucash desktop has different header name
    header_amount = 'Amount Num'
    if (header_amount not in reader.fieldnames):
        header_amount = 'Amount Num.'
    for row in reader:
        if (row['Transaction ID'] and row['Transaction ID'] != transaction_id):
            transaction_id = row['Transaction ID']
            output_file.write('{} * "{}"\n'.format(row['Date'], row['Description']))
            currency = row['Commodity/Currency'].split(':')[-1]
        # gnucash desktop use parentheses for negative number
        account = row['Full Account Name'].replace(' ', '-').replace(',', '')
        amount = row[header_amount].replace('(', '-').replace(')', '')
        output_file.write('  {}        {} {}\n'.format(account, amount, currency))


# Unused for now
def strip_accents(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


if __name__ == "__main__":
    main()
