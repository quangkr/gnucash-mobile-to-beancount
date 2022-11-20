#!/usr/bin/env bash

DIR=$(dirname $(realpath "${0}"))
$DIR/convert.py && fava "${DIR}/output.beancount"
