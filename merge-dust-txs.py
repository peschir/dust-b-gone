#!/usr/bin/python

# Distributed under the MIT/X11 software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from __future__ import absolute_import, division, print_function, unicode_literals

# Script to merge the dust transactions.

import argparse
import random
import sys

import bitcoin
import bitcoin.rpc

from bitcoin.core import COIN, x, b2x, b2lx, str_money_value, CTxIn, CTxOut, CTransaction
from bitcoin.core.script import CScript, OP_RETURN

parser = argparse.ArgumentParser(description='Merge dust txouts')
parser.add_argument('--testnet', action='store_true',
        help='Use testnet rather than mainnet')

args = parser.parse_args()
if args.testnet:
    bitcoin.SelectParams('testnet')

proxy = bitcoin.rpc.Proxy()

txins = []
prevouts = set()
sum_value_in = 0
line = -1
for l in sys.stdin.readlines():
    line += 1

    l = l.strip()

    try:
        tx = CTransaction.deserialize(x(l))
    except Exception:
        continue


    for txin in tx.vin:
        try:
            txout_info = proxy.gettxout(txin.prevout)
        except IndexError:
            print('Already spent! line %d, txid %s %d' % \
                    (line, b2lx(txin.prevout.hash), txin.prevout.n),
                    file=sys.stderr)
            continue

        print('line %d: %s %d: %s' % \
                (line, b2lx(txin.prevout.hash), txin.prevout.n,
                    str_money_value(txout_info['txout'].nValue)),
                file=sys.stderr)

        sum_value_in += txout_info['txout'].nValue

        if txin.prevout not in prevouts:
            prevouts.add(txin.prevout)
            txins.append(txin)
        else:
            print('Dup! line %d, txid %s %d' % \
                    (line, b2lx(txin.prevout.hash), txin.prevout.n),
                    file=sys.stderr)

random.shuffle(txins)
tx = CTransaction(txins, [CTxOut(0, CScript([OP_RETURN]))])

print(b2x(tx.serialize()))

print('Total: %s  Size: %d' % (str_money_value(sum_value_in), len(tx.serialize())), file=sys.stderr)
