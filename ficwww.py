#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
import pyficlib2 as Fic
import os
import signal
import socket
import time
import datetime
import json
import base64
import sys
import argparse
import traceback

import subprocess
from subprocess import Popen

from flask import Flask, render_template, jsonify, request, abort
#from flask_restful import Resource, Api, reqparse

app = Flask(__name__)

# ------------------------------------------------------------------------------
# Note:
# FIX190316: ifbit maybe 4bit fixed. nobody use 8bit interface
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
ENABLE_RUNCMD_API = True                        # If enable RUNCMD_API
MINIMUM_UPDATE_SEC = 10                         # minimum status update period
RUNCMD_DEFAULT_TIMEOUT = 5

# ------------------------------------------------------------------------------
# Status table
# ------------------------------------------------------------------------------
ST = {
    "last_update": 0,                          # last update ts
    "config": {                                 # ficwww config
        "auto_reflesh": False,                  # Auto reflesh mode
        "use_gpio": True,                       # use GPIO
    },
    "fpga": {
        "mode": "",                            # configured mode
        "bitname": "unknown",                  # configure bitfile name
        "conftime": "----/--/-- --:--:--",     # configure time
        "memo": "",                            # memo
        "done": False,                         # configure done via ficwww
    },
    "switch": {
        "ports": 4,
        "slots": 1,
        "outputs": {
            "port0": {
                "slot0": 0,
            },
            "port1": {
                "slot0": 0,
            },
            "port2": {
                "slot0": 0,
            },
            "port3": {
                "slot0": 0,
            }
        },
    },
    "hls": {
        "status": "stop",
    },
    "board": {                                  # Board part is updated by get_status()
        "power":   False,                       # Board power ok signal
        "done":    False,                       # Board done signal
        "dipsw":   0,                           # DipSW status
        "led":     0,                           # LED register status
        "link":    0,                           # Aurora linkup signal
        "channel": 0x0000,                      # Channel register status
        "id":      -1,
        "pcr": {                                # Packet counter status
            "in0": -1, "in1": -1, "in2": -1, "in3": -1,
            "out0": -1, "out1": -1, "out2": -1, "out3": -1
        }
    },
}

# ------------------------------------------------------------------------------
# Note: pyficlib2 is not manage any state
# so this library is for only handle open/close 
# ------------------------------------------------------------------------------
class Opengpio:
    def __init__(self):
        self.fd_lock = 0

    def __enter__(self):
        try:
            self.fd_lock = Fic.gpio_open()
            #print("DEBUG: gpio_open()", self.fd_lock)

        except:
            raise IOError
            
        return self

    def __exit__(self, type, value, traceback):
        try:
            Fic.gpio_close(self.fd_lock)
            #print("DEBUG: gpio_close()", self.fd_lock)

        except:
            print("DEBUG: gpio_close() failed")
            raise IOError

        return False    # Should not supress exception propergation

# ------------------------------------------------------------------------------
# Docroot
# ------------------------------------------------------------------------------
@app.route('/')
def docroot():
    host = socket.gethostname()
    title = "FiC node:({0:s})".format(host)
    return render_template('index.html', title=title, host=host)

# ------------------------------------------------------------------------------
# RESTful APIs
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# /fpga 
# ------------------------------------------------------------------------------
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
        return jsonify({"return": "failed"})

    # Check progmode
    if ("sm16", "sm16pr", "sm8", "sm8pr").count(ST['fpga']['mode']) == 0:
        return jsonify({"return": "failed"})

    # Decode bitstream
    try:
        bs = base64.b64decode(bitstream)
        print("DEBUG: Recived bytes: ", len(bs))

    except Exception as e:
        print(e)
        return jsonify({"return": "failed"})

    print("DEBUG: Program FPGA...")
    try:
        with Opengpio():
            ST['fpga']['done'] = False

            if ST['fpga']['mode'] == 'sm16':
                Fic.prog_sm16(data=bs, progmode=0)
                # ST['fpga']['ifbit'] = 8    # FIX190316

            elif ST['fpga']['mode'] == 'sm16pr':
                Fic.prog_sm16(data=bs, progmode=1)
                # ST['fpga']['ifbit'] = 8    # FIX190316

            elif ST['fpga']['mode'] == 'sm8':
                Fic.prog_sm8(data=bs, progmode=0)
                # ST['fpga']['ifbit'] = 4    # FIX190316

            elif ST['fpga']['mode'] == 'sm8pr':
                Fic.prog_sm8(data=bs, progmode=1)
                # ST['fpga']['ifbit'] = 4    # FIX190316

            # Set status
            ST['fpga']['conftime'] = datetime.datetime.now()
            ST['fpga']['done'] = Fic.get_done()
            ST['fpga']['memo'] = json['memo']

    except Exception as e:
        return jsonify({"return": "failed"})

    return jsonify({"return": "success"})

# ------------------------------------------------------------------------------
@app.route('/fpga', methods=['GET'])
def rest_fpga_get():
    return jsonify({"return": "success", "status": ST["fpga"]})

# ------------------------------------------------------------------------------
@app.route('/fpga', methods=['DELETE'])
def rest_fpga_delete():
    try:
        with Opengpio():
            Fic.prog_init()

    except:
        return jsonify({"return": "failed"})

    ST['fpga']['bitname'] = ''
    ST['fpga']['conftime'] = ''
    ST['fpga']['done'] = False
    ST['fpga']['memo'] = ''

    return jsonify({"return": "success"})

# ------------------------------------------------------------------------------
# /switch
# ------------------------------------------------------------------------------
@app.route('/switch', methods=['POST'])
def rest_switch_post():
    # Check json
    if not request.is_json:
        abort(400)

    json = request.json

    n_ports = 0
    n_slots = 0
    table = []

    try:
        n_ports = int(json['ports'])
        n_slots = int(json['slots'])
        _table = json['outputs']

        # Parse table
        for nout in range(n_ports):
            nout_key = 'port{0:d}'.format(nout)
            if nout_key not in _table:
                raise KeyError('port {0:s} is not found'.format(nout_key))

            addr_hi = nout
            for sout in range(n_slots):
                sout_key = 'slot{0:d}'.format(sout)
                if sout_key not in _table[nout_key]:
                    raise KeyError('slot {0:s} is not found'.format(sout_key))

                addr_lo = sout
                addr = (addr_hi << 8 | addr_lo)
                table.append((addr, _table[nout_key][sout_key]))

        # Set fcgi internal table
        ST['switch']['ports'] = n_ports
        ST['switch']['slots'] = n_slots
        ST['switch']['outputs'] = _table

    except Exception as e:
        print(e)
        return jsonify({"return": "failed"})

    # Configure switch
    try:
        with Opengpio():
            for t in table:
                addr, sv = t
                Fic.read(addr, sv)

    except:  # Except while GPIO open
        return jsonify({"return": "failed"})

    return jsonify({"return": "success"})

# ------------------------------------------------------------------------------
@app.route('/switch', methods=['GET'])
def rest_switch_get():
    return jsonify({"return": "success", "status": ST["switch"]})

# ------------------------------------------------------------------------------
# /hls
# ------------------------------------------------------------------------------
@app.route('/hls', methods=['POST'])
def rest_hls_post():
    # Check json
    if not request.is_json:
        abort(400)

    if ST['board']['done'] == False:
        return jsonify({"return": "failed", "error": "FPGA is not configured"})

    json = request.json
    try:
        hls_cmd = json['command']
        if hls_cmd == 'start':
            with Opengpio():
                Fic.hls_start()
                ST['hls']['status'] = 'start'

        elif hls_cmd == 'reset':
            with Opengpio():
                Fic.hls_reset()
                ST['hls']['status'] = 'stop'

        elif hls_cmd == 'receive':
            if ST['hls']['status'] == 'stop':
                return jsonify({"return": "failed", "error": "HLS is not running yet"})

            hls_data_count = json['count']
            with Opengpio():
                hls_data = Fic.hls_receive(hls_data_count)  # Todo: is any 8bit I/F?

            return jsonify({"return": "success", "data": hls_data})

        elif hls_cmd == 'send':
            if ST['hls']['status'] == 'stop':
                return jsonify({"return": "failed", "error": "HLS is not running yet"})

            hls_data = json['data']
            with Opengpio():
                Fic.hls_send(bytes(hls_data))

        else:
            return jsonify({"return": "failed", "error": "Unknown command"})

    except Exception:
        return jsonify({"return": "failed"})

    return jsonify({"return": "success"})

#-------------------------------------------------------------------------------
# /status
#-------------------------------------------------------------------------------
@app.route('/status', methods=['GET'])
def rest_status_get():
    if (time.time() - ST['last_update']) <= MINIMUM_UPDATE_SEC:
        return jsonify({"return": "success", "status": ST})
    
    try:
        with Opengpio():
            ST['board']['power'] = Fic.get_power()
            if ST['board']['power'] == 1:       # if board power is on
                ST['board']['done'] = Fic.get_done()

                if ST['config']['use_gpio'] and ST['board']['done'] == 1:    # FPGA is configured
                    ST['board']['led']     = Fic.read(0xfffb)  # read LED status
                    ST['board']['dipsw']   = Fic.read(0xfffc)  # read DIPSW status
                    ST['board']['link']    = Fic.read(0xfffd)  # read Link status
                    ST['board']['id']      = Fic.read(0xfffc)  # read board ID
                    ST['board']['channel'] = (Fic.read(0xfff9) << 8 | Fic.read(0xfffa))  # Channel linkup

                    # ---- Packet counter ----
                    base_addr = 0xff00
                    ST['board']['pcr']['in0'] = (
                        Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                        Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    base_addr = 0xff04
                    ST['board']['pcr']['in1'] = (
                        Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                        Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    base_addr = 0xff08
                    ST['board']['pcr']['in2'] = (
                        Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                        Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    base_addr = 0xff0c
                    ST['board']['pcr']['in3'] = (
                        Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                        Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    base_addr = 0xff10
                    ST['board']['pcr']['out0'] = (
                        Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                        Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    base_addr = 0xff14
                    ST['board']['pcr']['out1'] = (
                        Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                        Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    base_addr = 0xff18
                    ST['board']['pcr']['out2'] = (
                        Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                        Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    base_addr = 0xff1c
                    ST['board']['pcr']['out3'] = (
                        Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                        Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                else:
                    # If can not read out from the board, reset values.

                    ST['board']['led'] = 0
                    ST['board']['dipsw'] = 0
                    ST['board']['link'] = 0
                    ST['board']['id'] = -1
                    ST['board']['channel'] = 0x10000

                    # ---- Packet counter ----
                    ST['board']['pcr']['in0'] = -1
                    ST['board']['pcr']['in1'] = -1
                    ST['board']['pcr']['in2'] = -1
                    ST['board']['pcr']['in3'] = -1
                    ST['board']['pcr']['out0'] = -1
                    ST['board']['pcr']['out1'] = -1
                    ST['board']['pcr']['out2'] = -1
                    ST['board']['pcr']['out3'] = -1

    except:
        return jsonify({"return": "failed", "status": ST})

    ST['last_update'] = time.time()
    return jsonify({"return": "success", "status": ST})

# ------------------------------------------------------------------------------
# /regwrite
# ------------------------------------------------------------------------------
@app.route('/regwrite', methods=['POST'])
def rest_regwrite():
    # Check json
    if not request.is_json:
        abort(400)

    if ST['board']['done'] == False:
        return jsonify({"return": "failed", "error": "FPGA is not configured"})

    json = request.json
    try:
        addr = json['address']
        data = json['data']

        with Opengpio():
            Fic.write(addr, data)

    except:
        return jsonify({"return": "failed"})

    return jsonify({"return": "success"})

# ------------------------------------------------------------------------------
# /regread
# ------------------------------------------------------------------------------
@app.route('/regread', methods=['POST'])
def rest_regread():
    # Check json
    if not request.is_json:
        abort(400)

    if ST['board']['done'] == False:
        return jsonify({"return": "failed", "error": "FPGA is not configured"})

    data = None
    json = request.json
    try:
        addr = json['address']

        with Opengpio():
            data = Fic.read(addr)

    except:
        return jsonify({"return": "failed"})

    return jsonify({"return": "success", "data": data})

#-------------------------------------------------------------------------------
# /runcmd
#-------------------------------------------------------------------------------
@app.route('/runcmd', methods=['POST'])
def rest_runcmd():
    # Check json
    if not request.is_json:
        abort(400)

    if ENABLE_RUNCMD_API == False:
        return jsonify({"return": "failed", 
                        "stdout": "", 
                        "stderr": "", 
                        "error": "This feature is disabled"})

    json = request.json
    try:
        # Get cmd from json
        cmd = json['command']

        # Get timeout from json. Default value is 5 sec
        timeout = RUNCMD_DEFAULT_TIMEOUT
        if 'timeout' in json.keys():
            timeout = json['timeout']

        proc = Popen(cmd, shell=True, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,
                     preexec_fn=os.setsid)
        sout, serr = proc.communicate(timeout=timeout)

    except subprocess.TimeoutExpired as e:
        #proc.terminate()    # Terminate timeout process tree
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        return jsonify({"return": "failed", 
                        "stdout": e.stdout, 
                        "stderr": e.stderr, 
                        "error": "Called process timeout happened (Force KILLED)"})

    except subprocess.CalledProcessError as e:
        return jsonify({"return": "failed", 
                        "stdout": e.stdout, 
                        "stderr": e.stderr, 
                        "error": "Called process returned non zero"})

    except Exception:
        return jsonify({"return": "failed", 
                        "stdout": "", 
                        "stderr": "", 
                        "error": "Something nasty happened:\n{0:s}".format(traceback.format_exc())
                        })


    return jsonify({"return": "success",
                    "stdout": sout,
                    "stderr": serr,
                    "error": ""})

#-------------------------------------------------------------------------------
# ficwww configure API
# /config
#-------------------------------------------------------------------------------
@app.route('/config', methods=['POST'])
def rest_conf():
    # Check json
    if not request.is_json:
        abort(400)

    json = request.json
    try:
        for k, v in json.items():
            if k in ST['config']:
                ST['config'][k] = v

    except Exception as e:
        print(e)
        return jsonify({"return": "failed"})

    return jsonify({"return": "success"})

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', nargs='?', type=int, default=5000, help='port number (default: 5000)')
    args = parser.parse_args()

    #    fpga_startup()
    app.run(debug=True, use_reloader=True, host='0.0.0.0', port=args.port)
