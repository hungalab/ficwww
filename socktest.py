#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
import os
import socket
import time
import base64
import requests
import json

# import RPi module
#import RPi.GPIO as gpio

#import http.server
#import socketserver
#import serial
#
#import sys, traceback
#import math
#import struct
#import argparse
#import copy
#import re

BASE_URI = 'http://172.20.2.101:5000'
#BASE_URI = 'http://172.20.2.101/index.fcgi'

#------------------------------------------------------------------------------
def test_fpga():
    print("DEBUG: test_fpga")
    url = BASE_URI + '/fpga'
    f = open('ring_8bit.bin', 'rb')
    b64 = base64.b64encode(f.read())
    f.close()

    j = json.dumps({
        "mode": "sm16",
        "bitname": "ring.bin",
        "bitstream": b64.decode(encoding='utf-8')
    })

    resp = requests.post(url, j, headers={'Content-Type': 'application/json'})
    print(resp.json())

#------------------------------------------------------------------------------
def test_status():
    print("DEBUG: test_status")

    url = BASE_URI + '/fpga'
    resp = requests.get(url, headers={'Content-Type': 'application/json'})
    print(resp.json())

    url = BASE_URI + '/status'
    resp = requests.get(url, headers={'Content-Type': 'application/json'})
    print(resp.json())

#------------------------------------------------------------------------------
def test_switch():
    print("DEBUG: test_switch")

    url = BASE_URI + '/switch'
    j = json.dumps({
        "ports": "4",
        "slots": "4",
        "outputs" : {
            "o0": {
                's0': 0,
                's1': 0,
                's2': 0,
                's3': 0,
            },
            "o1": {
                's0': 0,
                's1': 0,
                's2': 0,
                's3': 0,
            },
            "o2": {
                's0': 0,
                's1': 0,
                's2': 0,
                's3': 0,
            },
            "o3": {
                's0': 0,
                's1': 0,
                's2': 0,
                's3': 0,
            },
        },
    })

    resp = requests.post(url, j, headers={'Content-Type': 'application/json'})
    print(resp.json())

#------------------------------------------------------------------------------
def test_hls():
    print("DEBUG: test_hls")
    url = BASE_URI + '/hls'

    j = json.dumps({
        "type": "command",
        "command": "reset",
    })

    resp = requests.post(url, j, headers={'Content-Type': 'application/json'})
    print(resp.json())

    j = json.dumps({
        "type": "command",
        "command": "start",
    })

    resp = requests.post(url, j, headers={'Content-Type': 'application/json'})
    print(resp.json())

    #j = json.dumps({
    #    "type": "data",
    #    "data": [0xa, 0xb, 0xc, 0xd, 0x0, 0x1, 0x2, 0x3],
    #})

    #resp = requests.post(url, j, headers={'Content-Type': 'application/json'})
    #print(resp.json())

#------------------------------------------------------------------------------
if __name__ == '__main__':
    test_fpga()
    test_status()

#    test_switch()
#    test_hls()
