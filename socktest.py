#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
import os
import socket
import time
import base64

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

BUFSIZE = 4*1024
#------------------------------------------------------------------------------
def test_stat(client):
    client.send(b'STAT')
    b = client.recv(BUFSIZE)
    print(b)

def test_prog(client):
    with open('ring_4bit.bin', 'rb') as fd:
        buf = fd.read()
        #client.send('PROG {0:d}'.format(len(buf)).encode()) # PROG <len>
        client.send('PROG8 {0:d}'.format(len(buf)).encode()) # PROG <len>
        resp = client.recv(BUFSIZE)
        if resp == 'ERROR\r\n':
            exit(1)

        client.sendall(buf) # send configurtaion bitstream
        print(client.recv(BUFSIZE)) # wait OK

def test_read(client):
    client.send(b'WRITE ffff cb')
    resp = client.recv(BUFSIZE)
    if resp == 'ERROR\r\n':
            exit(1)

    client.send(b'READ ffff')
    resp = client.recv(BUFSIZE)
    print(resp)

#------------------------------------------------------------------------------
if __name__ == '__main__':
       client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # IP socket is using for debug purpose it would be change unix sock
       #client = socket.socket(socket.UNIX, socket.SOCK_STREAM)   # IP socket is using for debug purpose it would be change unix sock

       client.connect(('127.0.0.1', 4000))

       b = client.recv(BUFSIZE)
       if b != b'OK\r\n': exit(1)
       print(b)

       #test_stat(client)
       test_prog(client)
       #test_stat(client)
       #test_write(client)

       test_read(client)

       #client.send('PROG {0:d}'.format(len(buf)).encode())
       #resp = client.recv(4096)
       #if resp == 'ERROR\r\n':
       #    exit(1)
       #client.sendall(buf)
       #print(client.recv(4096))

#       client.send(b'WRITE fffb 0f')
#       b = client.recv(BUFSIZE)
#       if b != b'OK\r\n': exit(1)
#       print(b)
#
#       client.send(b'READ fffb')
#       b = client.recv(BUFSIZE)
#       print(b)

#       client.close()

