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
import gc
import tracemalloc
import gzip

import subprocess
from subprocess import Popen

from flask import Flask, render_template, jsonify, request, abort, g
#from flask_restful import Resource, Api, reqparse

app = Flask(__name__)

# ------------------------------------------------------------------------------
# Note:
# FIX190316: ifbit maybe 4bit fixed. nobody use 8bit interface
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
ENABLE_RUNCMD_API      = True                       # If enable RUNCMD_API

MINIMUM_UPDATE_SEC     = 20                         # minimum status update period

RUNCMD_DEFAULT_TIMEOUT = 20
MAX_B64_CONFIG_SIZE = int(128*1024*1024*1.5)        # Limit maximum FPGA configuration file 128MB
TZ = datetime.timezone(datetime.timedelta(hours=+9), 'JST')  # Timezone

# ------------------------------------------------------------------------------
# Settings for XVCD
# ------------------------------------------------------------------------------
XVCD_START_CMD         = '/opt/xvcd/bin/xvcd -V 0x0403 -P 0x6014'
XVCD_STOP_CMD          = 'killall xvcd'
XVCD_CHECK_CMD         = 'pgrep xvcd'
XVCD_CHECK_CABLE_CMD   = 'lsusb -d 0403:6014'

# ------------------------------------------------------------------------------
# Status table
# ------------------------------------------------------------------------------
ST = {
    "last_update": 0,                           # last update ts
    "last_status": False,                       # last update status
    "config": {                                 # ficwww config
        "auto_reflesh": False,                  # Auto reflesh mode
        "use_gpio": True,                       # use GPIO
    },
    "fpga": {
        "mode": "",                            # configured mode
        "bitname": "unknown",                  # configure bitfile name
        "bitsize":  0,                         # configuration bitstream size
        "conftime": "----/--/-- --:--:--",     # configure time
        "txtime"  : 0,                         # configuration transfer time
        "progtime": 0,                         # FPGA programing time
        "memo": "",                            # memo
        "done": 0,                             # configure done via ficwww
    },
    "switch": {
        "ports": 4,
        "slots": 1,
        "outputs": 1,
        "table" : {
            "output0": {
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
    },
    "hls": {
        "status": "stop",
    },
    "board": {                                  # Board part is updated by get_status()
        "power":   0,                           # Board power ok signal
        "done":    0,                           # Board done signal
        "dipsw":   0,                           # DipSW status
        "led":     0,                           # LED register status
        "link":    0,                           # Aurora linkup signal
        "channel": 0x0000,                      # Channel register status
        "id":      -1,
        "pcr": {                                # Packet counter status
            "in0": -1, "in1": -1, "in2": -1, "in3": -1,
            "out0": -1, "out1": -1, "out2": -1, "out3": -1
            },
        "timer0":   0,
        "timer1":   0,
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
            print("DEBUG: gpio_open() failed", self.fd_lock)
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
# Before request (mostly for time mesurement purpose)
# ------------------------------------------------------------------------------
@app.before_request
def before_request():
    g.start = time.time()

# ------------------------------------------------------------------------------
# RESTful APIs
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# /fpga 
# ------------------------------------------------------------------------------
@app.route('/fpga_prog_status', methods=['GET'])
def rest_fpga_prog_status():
    ps_val = Fic.prog_status()

    prog_stat = {}

    # FPGA prog status
    if ps_val[0] == 0:
        prog_stat['stat'] = 'INIT'

    elif ps_val[0] == 1:
        prog_stat['stat'] = 'PROG'

    elif ps_val[0] == 2:
        prog_stat['stat'] = 'DONE'

    elif ps_val[0] == 3:
        prog_stat['stat'] = 'FAIL'

    # Smap mode
    if ps_val[1] == 0:
        prog_stat['smap_mode'] = 'INIT'

    elif ps_val[1] == 16:
        prog_stat['smap_mode'] = 'SM16'

    elif ps_val[0] == 2:
        prog_stat['stat'] = 'DONE'

    elif ps_val[0] == 3:
        prog_stat['stat'] = 'FAIL'

    # Smap mode
    prog_stat['smap_mode'] = ps_val[1]

    # Prog mode
    if ps_val[2] == 0:
        prog_stat['smap_mode'] = 'NORM'

    elif ps_val[2] == 1:
        prog_stat['smap_mode'] = 'PR'

    # Prog start time (Unix epoch)
    prog_stat['prog_st_time'] = ps_val[3]
    prog_stat['prog_ed_time'] = ps_val[4]


    # Program size (Configuration size)
    prog_stat['prog_size'] = ps_val[5]

    # Transfered size (Progress)
    prog_stat['tx_size'] = ps_val[6]

    print(prog_stat)
    return jsonify({"return": "success", "status": prog_stat})

# ------------------------------------------------------------------------------
@app.route('/fpga', methods=['POST'])
def rest_fpga_post():
    #s1 = tracemalloc.take_snapshot()       # Memory leak check

    # Check json
    if not request.is_json:
        abort(400)

    json = request.json

    try:
        ST['fpga']['mode'] = json['mode']
        ST['fpga']['bitname'] = json['bitname']
        bitstream = json['bitstream']
        ST['fpga']['txtime'] = time.time() - g.start   # Configuration transfer time (request time)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"return": "failed"})

    # Check progmode
    if ("sm16", "sm16pr", "sm8", "sm8pr").count(ST['fpga']['mode']) == 0:
        return jsonify({"return": "failed"})

    # Decode bitstream
    try:
        if len(bitstream) > MAX_B64_CONFIG_SIZE:
            # b64 string is too large
            raise ValueError

        bs = base64.b64decode(bitstream)
        print("DEBUG: Recived bytes: ", len(bs))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"return": "failed"})

    # Check compress mode is on
    if 'compress' in json and json['compress'] == True:
        bs = gzip.decompress(bs)

    print("DEBUG: Program FPGA...")
    try:
        with Opengpio():
            ST['fpga']['done'] = 0

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
            ST['fpga']['conftime'] = datetime.datetime.now(TZ)
            ST['fpga']['memo'] = json['memo']
            ST['fpga']['done'] = 1

            ps_val = Fic.prog_status()
            ST['fpga']['progtime'] = (ps_val[4] - ps_val[3]) / 1000000  # div by CLOCKS_PER_SEC
            ST['fpga']['bitsize']  = ps_val[5]

    except Exception as e:
        traceback.print_exc()
        return jsonify({"return": "failed"})

    #s2 = tracemalloc.take_snapshot()           # Memory leak check
    #diff = s2.compare_to(s1, 'lineno')
    #for s in diff[:10]:
    #    print(s)

    return jsonify({"return": "success"})

# ------------------------------------------------------------------------------
@app.route('/fpga', methods=['GET'])
def rest_fpga_get():
    return jsonify({"return": "success", "status": ST["fpga"]})

# ------------------------------------------------------------------------------
@app.route('/fpga', methods=['DELETE'])
def rest_fpga_delete():
    try:
#        if os.path.exists(u'/tmp/gpio.lock'):
#            os.remove(u'/tmp/gpio.lock');   # Reset overrides GPIO lock

        with Opengpio():
            Fic.prog_init()

    except:
        traceback.print_exc()
        return jsonify({"return": "failed"})

    ST['fpga']['bitname'] = ''
    ST['fpga']['conftime'] = ''
    ST['fpga']['done'] = 0 
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
    n_outputs = 0
    tbl_tmp = []

    try:
        n_ports   = int(json['ports'])
        n_slots   = int(json['slots'])
        n_outputs = int(json['outputs'])
        _table    = json['table']

        # Parse table
        for on in range(n_outputs):
            nout_key = 'output{0:d}'.format(on)
            if nout_key not in _table:
                raise KeyError('output {0:s} is not found'.format(nout_key))

            for pn in range(n_ports):
                pout_key = 'port{0:d}'.format(pn)
                if pout_key not in _table[nout_key]:
                    raise KeyError('port {0:s} is not found'.format(pout_key))

                addr_hi = pn 
                for sout in range(n_slots):
                    sout_key = 'slot{0:d}'.format(sout)
                    if sout_key not in _table[nout_key][pout_key]:
                        raise KeyError('slot {0:s} is not found'.format(sout_key))

                    addr_lo = sout
                    addr = (addr_hi << 8 | addr_lo)
                    tbl_tmp.append((addr, _table[nout_key][pout_key][sout_key]))    # Set to internal table

        # Set onmemory internal table (for reference cache)
        ST['switch']['ports']   = n_ports
        ST['switch']['slots']   = n_slots
        ST['switch']['outputs'] = n_outputs
        ST['switch']['table']   = tbl_tmp

    except Exception as e:
        traceback.print_exc()
        return jsonify({"return": "failed"})

    # Configure switch
    try:
        with Opengpio():
            Fic.write(0xfff8, n_slots << 1);    # Set maximum number of slots
            for t in tbl_tmp:
                addr, sv = t
                print('DEBUG:', addr, sv)
                Fic.write(addr, sv)

    except:  # Except while GPIO open
        traceback.print_exc()
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

    #if ST['board']['done'] == False:
    #    return jsonify({"return": "failed", "error": "FPGA is not configured"})

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

            return jsonify({"return": "success", "data": list(hls_data)})

        elif hls_cmd == 'send':
            if ST['hls']['status'] == 'stop':
                return jsonify({"return": "failed", "error": "HLS is not running yet"})

            hls_data = json['data']
            with Opengpio():
                Fic.hls_send(bytes(hls_data))

        else:
            return jsonify({"return": "failed", "error": "Unknown command"})

    except Exception:
        traceback.print_exc()
        return jsonify({"return": "failed"})

    return jsonify({"return": "success"})

#-------------------------------------------------------------------------------
# /status
#-------------------------------------------------------------------------------
@app.route('/status', methods=['GET'])
def rest_status_get():

    # Status update condition
    update_period = time.time() - ST['last_update']

    # If fpga not configured via ficwww and update_period is less than MIN_UPDATE_SEC * 3 -> return cache
    if (ST['last_status'] == False or ST['fpga']['done'] == 0) and update_period <= (MINIMUM_UPDATE_SEC * 3):
        return jsonify({"return": "success", "status": ST, "source": "cache"})     # Return cached status

    # If fpga configured via ficwww and update_period is less than MIN_UPDATE_SEC -> return cache
    # If last_status was true and update_period is less than MIN_UPDATE_SEC -> return cache
    if (ST['last_status'] == True or ST['fpga']['done'] == 1) and update_period <= MINIMUM_UPDATE_SEC:
        return jsonify({"return": "success", "status": ST, "source": "cache"})     # Return cached status

    try:
        with Opengpio():
            ST['board']['power'] = Fic.get_power()
            if ST['board']['power'] == 1:       # if board power is on
                ST['board']['done'] = Fic.get_done()

#                if ST['config']['use_gpio'] and ST['board']['done'] == 1:    # FPGA is configured
                if ST['config']['use_gpio']:
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

                    # ---- Timer -----
                    base_addr = 0xff80
                    ST['board']['timer0'] = (
                            Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                            Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    base_addr = 0xff84
                    ST['board']['timer1'] = (
                            Fic.read(base_addr+3) << 24 | Fic.read(base_addr+2) << 16 | 
                            Fic.read(base_addr+1) << 8 | Fic.read(base_addr))

                    ST['last_status'] = True
 
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

                    ST['board']['timer0'] = 0
                    ST['board']['timer1'] = 0

    except:
        # If can not read out from the board, reset values.

        ST['board']['led'] = 0
        ST['board']['dipsw'] = 0
        ST['board']['link'] = 0
        ST['board']['id'] = -1
        ST['board']['channel'] = 0x10000

        # ---- Packet counter ----
        ST['board']['pcr']['in0']  = -1
        ST['board']['pcr']['in1']  = -1
        ST['board']['pcr']['in2']  = -1
        ST['board']['pcr']['in3']  = -1
        ST['board']['pcr']['out0'] = -1
        ST['board']['pcr']['out1'] = -1
        ST['board']['pcr']['out2'] = -1
        ST['board']['pcr']['out3'] = -1

        ST['board']['timer0'] = 0
        ST['board']['timer1'] = 0

        traceback.print_exc()
        gc.collect()

        ST['last_update'] = time.time()
        ST['last_status'] = False

        #return jsonify({"return": "failed", "status": ST})
        return jsonify({"return": "success", "status": ST, "source": "cache"})     # Return cached status

    ST['last_update'] = time.time()

    gc.collect()
    return jsonify({"return": "success", "status": ST, "source": "realtime"})

# ------------------------------------------------------------------------------
# /regwrite
# ------------------------------------------------------------------------------
@app.route('/regwrite', methods=['POST'])
def rest_regwrite():
    # Check json
    if not request.is_json:
        abort(400)

    #if ST['board']['done'] == False:
    #    return jsonify({"return": "failed", "error": "FPGA is not configured"})

    json = request.json
    try:
        addr = json['address']
        data = json['data']

        with Opengpio():
            Fic.write(addr, data)

    except:
        traceback.print_exc()
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

    #if ST['board']['done'] == 0:
    #    return jsonify({"return": "failed", "error": "FPGA is not configured"})

    data = None
    json = request.json
    try:
        addr = json['address']

        with Opengpio():
            data = Fic.read(addr)

    except:
        traceback.print_exc()
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
        traceback.print_exc()
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
        traceback.print_exc()
        return jsonify({"return": "failed"})

    return jsonify({"return": "success"})

#-------------------------------------------------------------------------------
# /xvcd status check
#-------------------------------------------------------------------------------
@app.route('/xvcd', methods=['GET'])
def rest_xvcd_check():

    ret = {
        "return": "success",
        "reason": ""
    }

    # Get timeout from json. Default value is 5 sec
    timeout = RUNCMD_DEFAULT_TIMEOUT

    try:
        # Check cable
        proc = Popen(XVCD_CHECK_CABLE_CMD, shell=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid)
        sout, serr = proc.communicate(timeout=timeout)

        if sout.decode() == "":
            return jsonify({"return": "failed",
                            "error_code": "cable_not_found",
                            "error": "Cable not found"})

        # Check xvcd daemon
        proc = Popen(XVCD_CHECK_CMD, shell=True, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid)
        sout, serr = proc.communicate(timeout=timeout)

        if sout.decode() == "":
            return jsonify({"return": "failed",
                            "error_code": "xvcd_not_running",
                            "error": "xvcd not running"})

    except subprocess.TimeoutExpired as e:
        #proc.terminate()    # Terminate timeout process tree
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

        return jsonify({"return": "failed", 
                        "error": "called process timeout happened (force KILLED)"})

    except subprocess.CalledProcessError as e:
        return jsonify({"return": "failed", 
                        "error": "called process returned non zero"})

    except Exception:
        traceback.print_exc()
        return jsonify({"return": "failed", 
                        "error": "something nasty happened:\n{0:s}".format(traceback.format_exc())})


    return jsonify({"return": "success",
                    "error": ""})

#-------------------------------------------------------------------------------
# /xvcd start stop
#-------------------------------------------------------------------------------
@app.route('/xvcd', methods=['POST'])
def rest_xvcd_start_stop():
    # Check json
    if not request.is_json:
        abort(400)

    json = request.json
    try:
        # Get cmd from json
        cmd = json['command']

        # Get timeout from json. Default value is 5 sec
        timeout = RUNCMD_DEFAULT_TIMEOUT

        # Start xvcd
        if cmd == "start":
            proc = Popen(XVCD_START_CMD, shell=True, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        preexec_fn=os.setsid)

        if cmd == "stop":
            proc = Popen(XVCD_STOP_CMD, shell=True, stdout=subprocess.PIPE,
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
        traceback.print_exc()
        return jsonify({"return": "failed", 
                        "stdout": "", 
                        "stderr": "", 
                        "error": "Something nasty happened:\n{0:s}".format(traceback.format_exc())
                        })

    return jsonify({"return": "success",
                    "error": ""})

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', nargs='?', type=int, default=5000, help='port number (default: 5000)')
    args = parser.parse_args()

    tracemalloc.start() # Memory trace

    #    fpga_startup()
    app.run(debug=True, use_reloader=True, host='0.0.0.0', port=args.port)
