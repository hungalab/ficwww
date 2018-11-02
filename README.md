
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
        - [/regread](#regread)
            - [POST METHOD](#post-method-3)
        - [/regwrite](#regwrite)
            - [POST METHOD](#post-method-4)

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
For deployment, use lighttpd with fcgi plugin. 
(Please refer official flask deployment manual too)

index.fcgi is an example entry point .fcgi script for ficwww.py

#### On Raspbian
ficwww is totally depends on libfic2 (ficlib2) to control FPGA.

so you need build libfic2 1st and create pyficlib2.so symlink on ficwww directory.

do following commands on root

    sudo apt install lighttpd
    cd /var/www
    git clone http://github.com/hungalab/ficwww
    cd ficwww
    git clone http://github.com/hungalab/libfic2
    cd libfic2
    make
    cd ../
    ln -s libfic2/pyficlib2.so .

Install FSGI server for python

    root@fic08:# sudo pip3 install flup-py3
    Collecting flup-py3
      Downloading https://files.pythonhosted.org/packages/d9/95/fc6abf5c8830d97a0493d272d85d3ea63e502772d5de439904435d71d63d/flup_py3-1.0.3-py3-none-any.whl (74kB)
        100% |████████████████████████████████| 81kB 1.3MB/s
    Installing collected packages: flup-py3
    Successfully installed flup-py3-1.0.3


modify /etc/lighttpd/lighttpd.conf like below

    server.modules = (
            "mod_access",
            "mod_alias",
            "mod_compress",
            "mod_redirect",
            "mod_accesslog",
    )

    server.document-root        = "/var/www/ficwww"
    server.upload-dirs          = ( "/var/cache/lighttpd/uploads" )
    server.errorlog             = "/var/log/lighttpd/error.log"
    server.pid-file             = "/var/run/lighttpd.pid"
    server.username             = "www-data"
    server.groupname            = "www-data"
    server.port                 = 80

    index-file.names            = ( "index.php", "index.html", "index.lighttpd.html", "index.fcgi" )
    url.access-deny             = ( "~", ".inc" )
    static-file.exclude-extensions = ( ".php", ".pl", ".fcgi" )

    compress.cache-dir          = "/var/cache/lighttpd/compress/"
    compress.filetype           = ( "application/javascript", "text/css", "text/html", "text/plain" )

    # default listening port for IPv6 falls back to the IPv4 port
    include_shell "/usr/share/lighttpd/use-ipv6.pl " + server.port
    include_shell "/usr/share/lighttpd/create-mime.assign.pl"
    include_shell "/usr/share/lighttpd/include-conf-enabled.pl"

then enable modules on /etc/lighttpd/conf-enabled
(create symlinks from conf-available)

    drwxr-xr-x 2 root root 4096 Oct 30 00:12 .
    drwxr-xr-x 4 root root 4096 Oct 30 00:09 ..
    lrwxrwxrwx 1 root root   35 Oct 30 00:12 10-accesslog.conf -> ../conf-available/10-accesslog.conf
    lrwxrwxrwx 1 root root   33 Oct 30 00:11 10-fastcgi.conf -> ../conf-available/10-fastcgi.conf
    lrwxrwxrwx 1 root root   42 Sep  8  2017 90-javascript-alias.conf -> ../conf-available/90-javascript-ali

modify 10-fastcgi.conf like below

    # /usr/share/doc/lighttpd/fastcgi.txt.gz
    # http://redmine.lighttpd.net/projects/lighttpd/wiki/Docs:ConfigurationOptions#mod_fastcgi-fastcgi

    server.modules += ( "mod_fastcgi" )

    # ficwww FCGI setting
    fastcgi.server = (
    ".fcgi" => (
        (
        "socket" => "/tmp/index-fcgi.sock",
        "bin-path" => "/var/www/ficwww/index.fcgi",
        "check-local" => "disable",
        "max-procs" => 1
        )
    )
    )

    fastcgi.debug = 1

    alias.url = (
    "/static/" => "/var/www/ficwww/static/"
    )

    url.rewrite-once = (
    "^(/static($|/.*))$" => "$1",
    "^(/.*)$" => "/index.fcgi$1",
    )

then restart lighttpd and test via web browser.

Note: An example configuration for lighttpd is also attached to example/lighttpd/


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

_Note: Return format is out-of-dated. please reference actual code_

- Return
    ```
    {
      'dipsw'   : '<current value>'
      'led'     : '<current value>'
      'link'    : '<current value>'
      'pwrok'   : '<current value>'
      'done'    : 'true' | 'false'
      'bitname' : '<current bitstream name>'
      'conftime' : '<date string>'
    }
    ```

----

### /regread
direct register read of FiC FPGA
#### POST METHOD
Read from FiC register

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

----

### /regwrite
direct register write of FiC FPGA

#### POST METHOD
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