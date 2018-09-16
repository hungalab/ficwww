#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

import os
import socket
import time
import json

# import RPi module
import RPi.GPIO as gpio

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

#------------------------------------------------------------------------------
# Board GPIO aliases
# Board GPIO pin number <--> FPGA signal
#------------------------------------------------------------------------------
pin = {
        'RP_INIT' : 4,   # FPGA reset
        'RP_RDWR' : 27,  # for FPGA conf
        'RP_PROG' : 5,   # for FPGA conf
        'RP_DONE' : 6,   # for FPGA conf
        'RP_CCLK' : 7,   # for FPGA conf

        'RP_CD0' : 8,    # for FPGA conf
        'RP_CD1' : 9,    # for FPGA conf
        'RP_CD2' : 10,   # for FPGA conf
        'RP_CD3' : 11,   # for FPGA conf

        'RP_CD4' : 12,   # for FPGA I/O
        'RP_CD5' : 13,   # for FPGA I/O
        'RP_CD6' : 14,   # for FPGA I/O
        'RP_CD7' : 15,   # for FPGA I/O
        'RP_CD8' : 16,   # for FPGA I/O
        'RP_CD9' : 17,   # for FPGA I/O
        'RP_CD10' : 18,  # for FPGA I/O
        'RP_CD11' : 19,  # for FPGA I/O
        'RP_CD12' : 20,  # for FPGA I/O
        'RP_CD13' : 21,  # for FPGA I/O
        'RP_CD14' : 22,  # for FPGA I/O
        'RP_CD15' : 23,  # for FPGA I/O

        'RP_PWOK' : 24,  # must be set as input
        'RP_G_CKSEL' : 25, # must be set as input
        'RP_CSI' : 26,
}

#------------------------------------------------------------------------------

LOCKFILE = '/tmp/ficweb.lock'
FPGA_STAT_FILE = 'tmp/ficweb.stat'
FPGA_STARTUP_BITSTREAM = "ring.bin"
BUFSIZE = 4096
#------------------------------------------------------------------------------
#def lockfile():
#    while os.path.exists(LOCKFILE):
#        time.sleep(1)
#
#    f = open(LOCKFILE, 'w')
#    f.close()
#
#def unlockfile():
#    os.remove(LOCKFILE)
#------------------------------------------------------------------------------
#def fic_gpio_setup():
#    gpio.setmode(gpio.BCM) # GPIO number assignment mode
#
#    # PIN init
#
#    # initial PIN mode setup
#    for pn, pi in pin.items():
#        if pn == 'RP_PWOK' or  pn == 'RP_INIT' or \
#                pn == 'RP_DONE' or pn == 'RP_G_CKSEL':
#            gpio.setup(pi, gpio.IN)
#
#        else:
#            gpio.setup(pi, gpio.OUT)    # default OUT
#            gpio.output(pi, gpio.LOW)   # default LOW
#
#    # test
#    # print("TEST: PW_OK STAT:", gpio.input(pin['RP_PWOK']))
#
#
#------------------------------------------------------------------------------
# Obtain board status
#------------------------------------------------------------------------------
#def get_board_stat():
#        stat = {}
#        try:
#            lockfile()
#
#            fic_gpio_setup() # Init pins
#
#            stat['PW_OK'] = gpio.input(pin['RP_PWOK'])   # Power is okey
#            stat['DONE'] = gpio.input(pin['RP_DONE'])    # FPGA is run state
#
#            print('DEBUG', stat['DONE'])
#
#            gpio.cleanup()
#
#            unlockfile()
#            return stat
#
#        except Exception as e:
#            print("DEBUG: except", e)
#
#        unlockfile()
#        return None
#------------------------------------------------------------------------------
def open_socket():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 4000))
    return client

#------------------------------------------------------------------------------
def get_board_stat():
    client = open_socket()
    
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'
    
    client.send(b'STAT')
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    #print(resp[0])
    
    client.close()
    
    return json.loads(resp[0])

#------------------------------------------------------------------------------
def init_fpga():
    client = open_socket()

    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'

    client.send(b'INIT')

    client.close()

#------------------------------------------------------------------------------
def set_fpga_bitstream(fs, mode):
    buf = fs.read() # read into buffer at all

    client = open_socket()
    
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'
    
    # selectmap x16
    if mode == 'fpga_prog16':
        client.send('PROG {0:d}'.format(len(buf)).encode())
        
    # selectmap x16 + pr
    if mode == 'fpga_prog16_pr':
        client.send('PROGPR {0:d}'.format(len(buf)).encode())
        
    # selectmap x8
    if mode == 'fpga_prog8':
        client.send('PROG8 {0:d}'.format(len(buf)).encode())
        
    # selectmap x8 + pr
    if mode == 'fpga_prog8_pr':
        client.send('PROG8PR {0:d}'.format(len(buf)).encode())

    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'
    
    client.sendall(buf)
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'
    
    client.close()

    return 'success'

#------------------------------------------------------------------------------
def fpga_startup():
    client = open_socket()
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'

    print("INFO: Startup FPGA configuration with", FPGA_STARTUP_BITSTREAM)

    with open(FPGA_STARTUP_BITSTREAM, 'rb') as fd:
        buf = fd.read()

        tx_left = len(buf)
        client.send('PROG {0:d}'.format(tx_left).encode()) # PROG <len>
        resp = client.recv(BUFSIZE)
        if resp == 'ERROR\r\n':
            exit(1)

        # send configurtaion bitstream
        while tx_left > 0:
            tx = client.send(buf)
            tx_left -= tx
            
        resp = client.recv(BUFSIZE)
        if resp == 'ERROR\r\n':
            exit(1)

    client.close()

    print("INFO: Startup FPGA configuration done")

#------------------------------------------------------------------------------
def write_reg(addr, value):
    client = open_socket()
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'

    client.send('WRITE {0:d} {1:d}'.format(addr, value)) # WRITE xxxx xxxx
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'

    client.close()
    print("INFO: write reg at {0:02x} = {1:02x} done".format(addr, value))

    return 'success'

def read_reg(addr):
    client = open_socket()
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')
    if resp[0] != 'OK': return '{}'

    print('DEBUG', addr)
    client.send('READ {0:d}'.format(addr).encode()) # READ xxxx
    resp = client.recv(BUFSIZE).decode('ascii').split('\r\n')

    client.close()
    print("INFO: Read reg at {0:d} = {1:s} done".format(addr, resp[0]))

    return 'success'

#------------------------------------------------------------------------------
# Docroot
#------------------------------------------------------------------------------
@app.route('/')
def docroot():
    host = socket.gethostname()
    title = "FiC node:({0:s})".format(host)
    return render_template('index.html', title=title, host=host)

#------------------------------------------------------------------------------
@app.route('/api/<key>', methods=['POST','GET'])
def api_post(key):
    if request.method == 'POST':
        # FPGA configuration
        if key == 'fpga_prog16' or key == 'fpga_prog16_pr' or \
                key == 'fpga_prog8' or key == 'fpga_prog8_pr':

            filebuf = request.files.get('bitstream')
            if filebuf is None:
                return jsonify('File is not found!')

            fs = filebuf.stream
            return jsonify(set_fpga_bitstream(fs, key))

        # FPGA operations
        if key == 'fpga':
            if request.json['query'] == 'reset':
                print("reset")
                init_fpga()
                return jsonify(ret='success')

            if request.json['query'] == 'startup':
                fpga_startup()
                return jsonify(ret='success')

        # WRITE reg
        if key == 'reg':
            if request.json['query'] == 'write':
                print('reg write')
                addr = int(request.json['addr'])
                value = int(request.json['value'])
                return jsonify(write_reg(addr, value))

            if request.json['query'] == 'read':
                addr = int(request.json['addr'])
                return jsonify(read_reg(addr))


        return jsonify(resp='invalid')

    elif request.method == 'GET':
        if key == 'status':
            return jsonify(get_board_stat())

        else:
            return jsonify('invalid')

#------------------------------------------------------------------------------
if __name__ == "__main__":
#    fpga_startup()
    app.run(debug=True, use_reloader=False, host='0.0.0.0')

