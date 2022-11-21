#!/usr/bin/env python3

import csv
import unicodedata
from pathlib import Path


def main():
    script_path = Path(__file__).absolute().parent
    input_path = sorted(script_path.parent.joinpath(
        'gnucash').iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)[0]
    template_path = script_path.joinpath('template.beancount')
    output_path = script_path.joinpath('output.beancount')
    with input_path.open(mode='r', newline='') as in_f, template_path.open(mode='r') as tem_f, output_path.open(mode='w') as out_f:
        # copy template over to the output
        out_f.writelines(tem_f)
        # read input CSV, then transform the data
        # and write directly to the output
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
    reader = csv.DictReader(input_file)
    currency = ''
    for row in reader:
        if row['Date']:
            output_file.write(
                '{} * "{}"\n'.format(row['Date'], row['Description']))
            currency = row['Commodity/Currency'].split(':')[-1]

        account = row['Full Account Name'].replace(' ', '-').replace(',', '')
        amount = row['Amount Num']
        output_file.write('  {}        {} {}\n'.format(
            account, amount, currency))


# Unused for now
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


if __name__ == "__main__":
    main()
