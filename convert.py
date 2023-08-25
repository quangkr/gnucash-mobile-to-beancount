#!/usr/bin/env python3

from pathlib import Path
from itertools import chain


def main():
    script_path = Path(__file__).absolute().parent
    template_path = script_path.joinpath('template.beancount')
    output_path = script_path.joinpath('output.beancount')

    files = chain(script_path.parent.glob('gnucash/*'), script_path.glob('gnucash/*'))
    filtered_files = filter(lambda f: f.suffix in { '.csv', '.gnca', '.gnucash' }, files)
    input_path = max(filtered_files, key=lambda f: f.stat().st_mtime)
    with input_path.open(mode='r', encoding='utf-8', newline='') as in_f, template_path.open(mode='r', encoding='utf-8') as tem_f, output_path.open(mode='w', encoding='utf-8') as out_f:
        # copy template over to the output
        out_f.writelines(tem_f)
        # read input CSV, then transform the data
        # and write directly to the output
        if input_path.suffix in { '.csv' }:
            for l in transform_csv(in_f):
                out_f.write(l)
        elif input_path.suffix in { '.gnca', '.gnucash' }:
            for l in transform_xml(in_f):
                out_f.write(l)

    # start fava
    start_fava(output_path)


def start_fava(path):
    try:
        from setproctitle import setproctitle
        from fava.application import create_app
        setproctitle('gnucashfava')
        app = create_app([path])
        app.run('localhost', 5000)
    except ModuleNotFoundError:
        print('Unable to import module fava and/or setproctitle')
        print('Will not start fava instance')


def transform_csv(input_file):
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
            yield '{} * "{}"\n'.format(row['Date'], row['Description'])
            currency = row['Commodity/Currency'].split(':')[-1]
        # gnucash desktop use parentheses for negative number
        account = row['Full Account Name'].replace(' ', '-').replace(',', '')
        amount = row[header_amount].replace('(', '-').replace(')', '')
        yield '  {}        {} {}\n'.format(account, amount, currency)


def transform_xml(input_file):
    import xml.etree.ElementTree as ET
    events = ET.iterparse(input_file, events=('start', 'end', 'start-ns', 'end-ns'))

    # build namespace map, then grab the root element
    nsmap = {}
    actmap = {}
    root = None
    while True:
        event, elem = next(events)
        ns, url = elem
        nsmap[ns] = url
        if event == 'start':
            root = elem
            break

    for event, elem in events:
        if event == 'end':

            # build account tree
            if elem.tag == ET.QName(nsmap['gnc'], 'account'):
                if elem.find(ET.QName(nsmap['act'], 'type').text).text == 'ROOT':
                    actid = elem.find(ET.QName(nsmap['act'], 'id').text).text
                    name = elem.find(ET.QName(nsmap['act'], 'name').text).text
                    actmap[actid] = { 'id': actid, 'name': name, 'parent': None }
                else:
                    actid = elem.find(ET.QName(nsmap['act'], 'id').text).text
                    name = elem.find(ET.QName(nsmap['act'], 'name').text).text
                    parent = elem.find(ET.QName(nsmap['act'], 'parent').text).text
                    if (actmap[parent]['parent']):
                        name = actmap[parent]['name'] + ':' + name
                    actmap[actid] = { 'id': actid, 'name': name, 'parent': parent }

            # parse transactions
            elif elem.tag == ET.QName(nsmap['gnc'], 'transaction'):
                date = elem.find(ET.QName(nsmap['trn'], 'date-posted').text).find(ET.QName(nsmap['ts'], 'date').text).text.split(' ')[0]
                currency = elem.find(ET.QName(nsmap['trn'], 'currency').text).find(ET.QName(nsmap['cmdty'], 'id').text).text
                description = elem.find(ET.QName(nsmap['trn'], 'description').text).text
                yield '{} * "{}"\n'.format(date, description)
                for s in elem.iter(ET.QName(nsmap['trn'], 'split').text):
                    account = actmap[s.find(ET.QName(nsmap['split'], 'account').text).text]['name'].replace(' ', '-').replace(',', '')
                    amount = s.find(ET.QName(nsmap['split'], 'quantity').text).text
                    yield '  {}        {} {}\n'.format(account, amount, currency)

            root.clear()  # Free up memory by clearing the root element.



# Unused for now
def strip_accents(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


if __name__ == "__main__":
    main()
