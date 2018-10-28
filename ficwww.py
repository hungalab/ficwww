#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
import os
import socket
import time, datetime
import json
import base64

from flask import Flask, render_template, jsonify, request, abort
#from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
#api = Api(app)

# pyficlib2
import pyficlib2 as Fic 

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
# Status table
#------------------------------------------------------------------------------
ST = {
    "fpga" : {
        "mode" : "",        # configured mode
        "bitname" : "unknown",     # configure bitfile name
        "conftime" : "----/--/-- --:--:--",    # configure time
        "ifbit" : 8,        # Interface bit width
        "done": False,     # configure done
    },
    "switch" : {
        "ports" : 4,
        "slots" : 1,
        "outputs" : {
            "port0" : {
                "slot0" : 0,
            },
            "port1" : {
                "slot0" : 0,
            },
            "port2" : {
                "slot0" : 0,
            },
            "port3" : {
                "slot0" : 0,
            }
        },
    },
    "hls" : {
        "status" : "stop",
    },
    "board" : {
        "dipsw" : 0,
        "led" : 0,
        "link" : 0,
        "power" : False,
        "done" : False,
    },
}

#------------------------------------------------------------------------------
# Docroot
#------------------------------------------------------------------------------
@app.route('/')
def docroot():
    host = socket.gethostname()
    title = "FiC node:({0:s})".format(host)
    return render_template('index.html', title=title, host=host)

#------------------------------------------------------------------------------
# RESTful APIs
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# API for FPGA
#------------------------------------------------------------------------------

# POST
@app.route('/fpga', methods=['POST'])
def rest_fpga_post():
    # Check json 
    if not request.is_json:
        abort(400)

    json = request.json

    try:
        ST['fpga']['mode'] = json['mode']
        ST['fpga']['bitname'] = json['bitname']
        bitstream = json['bitstream']

    except Exception as e:
        print(e)
        return jsonify({"return" : "failed"})


    # Check progmode
    if ("sm16", "sm16pr", "sm8", "sm8pr").count(ST['fpga']['mode']) == 0:
        return jsonify({"return" : "failed"})

    # Decode bitstream
    try:
        bs = base64.b64decode(bitstream)
        print("DEBUG: Recived bytes: ", len(bs))

    except Exception as e:
        print(e)
        return jsonify({"return" : "failed"})

    print("DEBUG: Program FPGA...")
    try:
        # Program FPGA
        Fic.gpio_open()

        ST['fpga']['done'] = False

        if ST['fpga']['mode'] == 'sm16':
            Fic.prog_sm16(data=bs, progmode=0)
            ST['fpga']['ifbit'] = 8

        elif ST['fpga']['mode'] == 'sm16pr':
            Fic.prog_sm16(data=bs, progmode=1)
            ST['fpga']['ifbit'] = 8

        elif ST['fpga']['mode'] == 'sm8':
            Fic.prog_sm8(data=bs, progmode=0)
            ST['fpga']['ifbit'] = 4

        elif ST['fpga']['mode'] == 'sm8pr':
            Fic.prog_sm8(data=bs, progmode=1)
            ST['fpga']['ifbit'] = 4

        # Set status
        ST['fpga']['conftime'] = datetime.datetime.now()
        ST['fpga']['done'] = Fic.get_done()
        Fic.gpio_close()

    except:
        Fic.gpio_close()
        return jsonify({"return" : "failed"})

    return jsonify({"return" : "success"})

# GET FPGA STATUS
@app.route('/fpga', methods=['GET'])
def rest_fpga_get():
    return jsonify({"return" : "success", "status" : ST["fpga"]})

# Reset FPGA
@app.route('/fpga', methods=['DELETE'])
def rest_fpga_delete():
    try:
        Fic.gpio_open()
        Fic.prog_init()
        Fic.gpio_close()

    except:
        Fic.gpio_close()
        return jsonify({"return" : "failed"})

    ST['fpga']['bitname'] = ''
    ST['fpga']['conftime'] = ''
    ST['fpga']['done'] = False

    return jsonify({"return" : "success"})

#------------------------------------------------------------------------------
# API for SWITCH
#------------------------------------------------------------------------------

# POST Switch
@app.route('/switch', methods=['POST'])
def rest_switch_post():
    # Check json 
    if not request.is_json:
        abort(400)

    json = request.json
    try:
        ST['switch']['ports'] = json['ports']
        ST['switch']['slots'] = json['slots']
        ST['switch']['outputs'] = json['outputs']

    except Exception as e:
        print(e)
        return jsonify({"return" : "failed"})

    # Configure switch
    try: 
        Fic.gpio_open()
        for on, (ok, ov) in enumerate(ST['switch']['outputs'].items()):
            addr_hi = on
            for sn, (sk, sv) in enumerate(ov.items()):
                addr_lo = sn
                addr = (addr_hi << 8 | addr_lo)

                if (ST['fpga']['ifbit'] == 8):
                    # Use 8bit mode I/F
                    #Fic.wb8(addr, sv.to_bytes(1, 'big'))
                    Fic.wb8(addr, sv)

                elif (ST['fpga']['ifbit'] == 4):
                    # Use 4bit mode I/F
                    #Fic.wb4(addr, sv.to_bytes(1, 'big'))
                    Fic.wb4(addr, sv)

        Fic.gpio_close()

    except:
        Fic.gpio_close()
        return jsonify({"return" : "failed"})

    return jsonify({"return" : "success"})

# GET Switch
@app.route('/switch', methods=['GET'])
def rest_switch_get():
    return jsonify({"return" : "success", "status" : ST["switch"]})

#------------------------------------------------------------------------------
# API for HLS
#------------------------------------------------------------------------------
@app.route('/hls', methods=['POST'])
def rest_hls_post():
    # Check json 
    if not request.is_json:
        abort(400)

    if ST['fpga']['done'] == False:
        return jsonify({"return" : "failed", "error" : "FPGA is not configured"})

    json = request.json
    try:
        hls_type = json['type']
        if hls_type == 'command':
            hls_cmd = json['command']

            Fic.gpio_open()

            if hls_cmd == 'start':
                if ST['fpga']['ifbit'] == 8:
                    Fic.hls_start8()

                if ST['fpga']['ifbit'] == 4:
                    Fic.hls_start4()

                ST['hls']['status'] = 'start'

            elif hls_cmd == 'reset':
                if ST['fpga']['ifbit'] == 8:
                    Fic.hls_reset8()

                if ST['fpga']['ifbit'] == 4:
                    Fic.hls_reset4()

                ST['hls']['status'] = 'stop'

            Fic.gpio_close()

        elif hls_type == 'data':
            if ST['hls']['status'] == 'stop':
                return jsonify({"return" : "failed", "error" : "HLS is not running yet"})

            hls_data = json['data']
            Fic.gpio_open()
            Fic.hls_send4(bytes(hls_data))  # Todo: is any 8bit I/F?
            Fic.gpio_close()

    except Exception as e:
        print(e)
        Fic.gpio_close()
        return jsonify({"return" : "failed"})

    return jsonify({"return" : "success"})

#------------------------------------------------------------------------------
# API for status
#------------------------------------------------------------------------------
@app.route('/status', methods=['GET'])
def rest_status_get():
    try:
        Fic.gpio_open()

        if ST['fpga']['ifbit'] == 8:
            ST['board']['led'] = Fic.rb8(0xfffb)    # read LED status
            ST['board']['dipsw'] = Fic.rb8(0xfffc)  # read DIPSW status
            ST['board']['link'] = Fic.rb8(0xfffd)   # read Link status

        if ST['fpga']['ifbit'] == 4:
            ST['board']['led'] = Fic.rb4(0xfffb)    # read LED status
            ST['board']['dipsw'] = Fic.rb4(0xfffc)  # read DIPSW status
            ST['board']['link'] = Fic.rb4(0xfffd)   # read Link status
        
        ST['board']['done'] = Fic.get_done()
        ST['board']['power'] = Fic.get_power()

        Fic.gpio_close()

    except:
        Fic.gpio_close()
        return jsonify({"return" : "failed", "status" : ST})

    return jsonify({"return" : "success", "status" : ST})

#------------------------------------------------------------------------------
# API for reg
#------------------------------------------------------------------------------
@app.route('/regwrite', methods=['POST'])
def rest_regwrite():
    # Check json 
    if not request.is_json:
        abort(400)

    if ST['fpga']['done'] == False:
        return jsonify({"return" : "failed", "error" : "FPGA is not configured"})

    json = request.json
    try:
        addr = json['address']
        data = json['data']

        Fic.gpio_open()

        if ST['fpga']['ifbit'] == 8:
            Fic.wb8(addr, data)

        if ST['fpga']['ifbit'] == 4:
            Fic.wb4(addr, data)

        Fic.gpio_close()

    except Exception as e:
        print(e)
        Fic.gpio_close()
        return jsonify({"return" : "failed"})

    return jsonify({"return" : "success"})

@app.route('/regread', methods=['POST'])
def rest_regread():
    # Check json 
    if not request.is_json:
        abort(400)

    if ST['fpga']['done'] == False:
        return jsonify({"return" : "failed", "error" : "FPGA is not configured"})

    data = None
    json = request.json
    try:
        addr = json['address']
        Fic.gpio_open()

        if ST['fpga']['ifbit'] == 8:
            data = Fic.rb8(addr)

        if ST['fpga']['ifbit'] == 4:
            data = Fic.rb4(addr)

        Fic.gpio_close()

    except Exception as e:
        print(e)
        Fic.gpio_close()
        return jsonify({"return" : "failed"})

    return jsonify({"return" : "success", "data" : data})

#------------------------------------------------------------------------------
if __name__ == "__main__":
#    fpga_startup()
    app.run(debug=True, use_reloader=True, host='0.0.0.0')
