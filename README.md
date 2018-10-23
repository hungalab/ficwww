
# ficwww

## fic board www GUI interface
* Using python flask + JINJA2 web flamework
* FPGA communication with ficlib2
* Provides RESTful interface

---
## Table of contents

<!-- TOC -->

- [ficwww](#ficwww)
    - [fic board www GUI interface](#fic-board-www-gui-interface)
    - [Table of contents](#table-of-contents)
    - [Instrallation](#instrallation)
        - [Required packages](#required-packages)
        - [Easy Run and Debug](#easy-run-and-debug)
        - [Deployment](#deployment)
        - [GUI interface (AS IS)](#gui-interface-as-is)
- [API Reference](#api-reference)
    - [RESTful API](#restful-api)
        - [/fpga](#fpga)
            - [POST METHOD](#post-method)
            - [GET METHOD](#get-method)
            - [DELETE METHOD](#delete-method)
        - [/switch](#switch)
            - [POST METHOD](#post-method-1)
        - [/hls](#hls)
            - [POST METHOD](#post-method-2)
            - [GET METHOD](#get-method-1)
        - [/status](#status)
            - [GET METHOD](#get-method-2)
        - [/register](#register)
            - [PUT METHOD](#put-method)
            - [GET METHOD](#get-method-3)

<!-- /TOC -->

---

## Instrallation

### Required packages
Following packages are required.

* lighttpd
* python3
* python3-flask

In addition, pyficlib2.so is also required.

### Easy Run and Debug
Just run ficwww.py like following:

    nyacom@fic02:/home/nyacom/project/ficwww$ ./ficwww.py
    * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
    * Restarting with stat
    * Debugger is active!
    * Debugger pin code: 197-084-620

As default behavior, built-in httpd is awaiting port 5000.
So you can access http://localhost:5000 by web browser.

socktest.py is a test script for RESTful API


### Deployment
For deployment, use lighttpd with fcgi plugin. (Please refer official flask deployment manual)

index.fcgi is an example entry point .fcgi script for ficwww.py

### GUI interface (AS IS)
This part is still very undergo. (I need certain time to finish this part...)

I would be welcoming your contribution on this part :) 

---

# API Reference

## RESTful API

----

### /fpga
Configure FPGA (Perform FPGA programming)

#### POST METHOD
Perform FPGA configuration

- JSON format
    - mode : FPGA configuration mode (select map x16 or x8 and partial reconfiguration)
    - bitname : name of bitstream file e.g. ring.bin
    - bitstream : BASE64 encoded FPGA bitstream file

    ```
    {
      'mode': '<sm16 | sm8 | sm16pr | sm8pr>'
      'bitname'   : '<name>'
      'bitstream' : '<base64 encoded FPGA bitfile>'
    }
    ```

- Return
  - return: success or failed

  ```
  {
    'return': 'success' | 'failed'
  }
  ```

#### GET METHOD
Get FPGA configuration status

- Return
  - done : Indicating current FPGA status. If the value true, FPGA is configured and running.
  - bitname : Configured bitname in last time
  - conftime : A timestamp of last FPGA configuration
  ```
  {
    'done'    : 'true' | 'false'
    'bitname' : '<current bitstream name>'
    'conftime' : '<date string>'
  }
  ```

#### DELETE METHOD
Initilize FPGA configuration

- Return
  - return : success or failed
  ```
  {
    'return': 'success' | 'failed'
  }
  ```

----

### /switch
Configuring switch table

#### POST METHOD

- JSON format
  ```
  {
    'ports' : '<number of out ports Pn>',
    'slots' : '<number of slots Sn>',
    'output' : {
      'output0': {
        'slot0': '0',
        ...
        'slotSn': '<input port number>',
      },
      ...
      'outputPn': {
        ...,
      },
    },
  }
  ```

- Return
    - return : success or failed
    ```
    {
      'error' : '<error message if present>',
      'return': 'success' | 'failed',
    }
    ```

----

### /hls
Control HLS module

#### POST METHOD
Send command or data to HLS module

- JSON format 
    ```
    {
      'type'   : '<command | data>',
      'command': '<reset | start>',
      'data' : [0x80, 0x80, 0x80,...,],
    }
    ```

- Return 
    ```
    {
      'error' : '<error message if present>',
      'return': '<success | failed>',
    }
    ```

#### GET METHOD
Receive data from HLS module

Note: you need start HLS module before this.

- JSON format
    ```
    {
      'count' : '<number of elements to read>
    }
    ```

- Return 
  ```
  {
    'data'  : [0x00, 0x00, 0x00 ... 0x00]
    'error' : '<error message if present>'
    'return': 'success' | 'failed'
  }
  ```

----

### /status
#### GET METHOD
receive current FiC board status

- Return
    ```
    {
      'dipsw'   : '<current value'
      'led'     : '<current value>'
      'link'    : '<current value>'
      'pwrok'   : '<current value>'
      'done'    : 'true' | 'false'
      'bitname' : '<current bitstream name>'
      'conftime' : '<date string>'
    }
    ```

----

### /register
direct R/W to/from FiC register

#### PUT METHOD
Write to FiC register

- JSON Format
    ```
    {
      'address'   : '<target address>'
      'data'      : '<data in hex>'
    }
    ```

- Return 
    ```
    {
      'error' : '<error message if present>'
      'return': 'success' | 'failed'
    }
    ```

#### GET METHOD
Read to FiC register

- JSON Format
    ```
    {
      'address'   : '<target address>'
    }
    ```

- Return 
    ```
    {
      'data'  : '<read data value>'
      'error' : '<error message if present>'
      'return': 'success' | 'failed'
    }
