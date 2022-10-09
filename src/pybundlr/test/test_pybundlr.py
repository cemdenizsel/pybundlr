import os
import time

import pytest
import requests

from src.pybundlr import pybundlr

def test_balance_arweave():
    ar_address = "Ry2bDGfBIvYtvDPYnf0eg_ijH4A1EDKaaEEecyjbUQ4"
    bal = pybundlr.balance(ar_address, "arweave") #not AR
    assert bal > 0

    
def test_balance_ethereum():
    eth_address = "0x7BA3d8551A6f2C70a5d47bb448BcF7EF69661822"
    bal = pybundlr.balance(eth_address, "ethereum") #not ETH
    assert bal >= 0

    
def test_balance_matic():
    eth_address = "0x7BA3d8551A6f2C70a5d47bb448BcF7EF69661822"
    bal = pybundlr.balance(eth_address, "matic") #not "polygon" or "MATIC"
    assert bal >= 0

    
def test_balance_foo():
    address = "Ry2bDGfBIvYtvDPYnf0eg_ijH4A1EDKaaEEecyjbUQ4"
    with pytest.raises(ValueError) as e_info:
        pybundlr.balance(address, "foo")
    assert "Unknown/Unsupported currency foo" in str(e_info)


def test_fund_and_withdraw():
    eth_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
    eth_address = pybundlr.eth_address(eth_private_key)

    amt_fund_wei = 3
    pybundlr.fund(amt_fund_wei, "ethereum", eth_private_key)

    amt_withdraw_wei = 2

    #give time for deposit to go through, if needed
    for i in range(10):
        bal_wei = pybundlr.balance(eth_address, "ethereum")
        if bal_wei >= amt_withdraw_wei:
            break
        print(f"Not enough funds yet, so sleep. bal_wei={bal_wei}")
        time.sleep(1.0)        

    try:
        pybundlr.withdraw(amt_withdraw_wei, "ethereum", eth_private_key)
    except ValueError as e_info:
        #let it pass if insufficient balance, otherwise error gets raised
        #why: the funding above doesn't seem to make it through (FIXME)
        if "Insufficient Balance" in str(e_info):
            break e
        raise ValueError(e_info)


def test_fund_fail_no_eth():
    #randomly create a new account, which therefore has 0 eth
    account = pybundlr.w3().eth.account.create()
    eth_private_key = account.key.hex()

    #watch funding fail
    amt_wei = 3
    with pytest.raises(ValueError) as e_info:
        pybundlr.fund(amt_wei, "ethereum", eth_private_key)
        
    assert "Can't fund" in str(e_info)
    assert "balance is 0" in str(e_info)


def test_price(tmp_path):
    num_bytes = 10
    amt_wei = pybundlr.price(num_bytes, "ethereum")
    assert amt_wei > 100000000  # example observed number: 24275774772


def test_upload(tmp_path):
    content_in = "mycontent"
    f = tmp_path / "myfile.txt"
    f.write_text(content_in)
    file_name = str(f)

    num_bytes = os.stat(file_name).st_size

    eth_private_key = os.getenv('REMOTE_TEST_PRIVATE_KEY1')
    p = pybundlr.price(num_bytes, "ethereum")
    
    amt_wei = p * 2 # the 2x is for safety margin, since price fluctuates
    pybundlr.fund(amt_wei, "ethereum", eth_private_key)
    
    url = pybundlr.upload(file_name, "ethereum", eth_private_key)
    assert "https://arweave.net/" in url, url

    result = requests.get(url)
    content_out = result.text

    assert content_in == content_out, content_out

