#!/usr/bin/env bash

DIR=$(dirname $(realpath "${0}"))
INPUT_DIR='../gnucash'
INPUT_FILE=$(realpath $(ls "${INPUT_DIR}"/*.csv -At | head -n1))

$DIR/convert.py "${INPUT_FILE}" && fava output.beancount
