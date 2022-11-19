#!/usr/bin/env python3

import sys
import csv
import unicodedata


# Unused for now
def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


with open(sys.argv[1], mode='r', newline='') as in_f, open('template.beancount', mode='r') as tem_f, open('output.beancount', mode='w') as out_f:
    # copy template over to the output
    out_f.writelines(tem_f)

    # read input CSV, then transform the data and write directly to the output
    reader = csv.DictReader(in_f)
    currency = ''
    for row in reader:
        if row['Date']:
            out_f.write('{} * "{}"\n'.format(row['Date'], row['Description']))
            currency = row['Commodity/Currency'].split(':')[-1]

        account = row['Full Account Name'].replace(' ', '-').replace(',', '')
        out_f.write('  {}        {} {}\n'.format(
            account, row['Amount Num'], currency))
