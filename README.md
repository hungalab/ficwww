
# ficwww

## fic board www GUI interface
* Using python flask + JINJA2 web flamework
* FPGA communication with ficlib2
* Providing RESTful interface

---

## Instrallation

### Required packages
* lighttpd
* git
* python3
* python3-flask

---

## RESTful API

### /fpga
Configure FPGA (Perform FPGA programming)

#### PUT METHOD
Perform FPGA configuration

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

##### Return

- return : success or failed

```
{
  'return': 'success' | 'failed'
}
```

#### GET METHOD
Get FPGA configuration status

##### Rertun
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

##### Return
- return : success or failed
```
{
  'return': 'success' | 'failed'
}
```


### /switch
Configuring switch table

#### PUT METHOD

```
{
  'ports' : '<number of out ports Pn>'
  'slots' : '<number of slots Sn>'

  'output0': {
    'slot0': '0'
    ...
    'slotSn': '<input port number>'
  }
  ...
  'outputPn': {
    ...
  }

}
```

##### Return
- return : success or failed
```
{
  'error' : '<error message if present>'
  'return': 'success' | 'failed'
}
```

### /hls
Control HLS module

#### PUT METHOD
- send to HLS module

##### Input
```
{
  'type'   : '<command | data>'
  'command': '<reset | start>'
  'data' : [0x80, 0x80, 0x80,...,]
}
```

##### Return 
```
{
  'error' : '<error message if present>'
  'return': '<success | failed>'
}
```

#### GET METHOD
- receive from HLS module

```
{
  'count' : '<number of elements to read>
}
```

##### Return 
```
{
  'data'  : [0x00, 0x00, 0x00 ... 0x00]
  'error' : '<error message if present>'
  'return': 'success' | 'failed'
}
```

### /status
#### GET METHOD
- receive current FiC board status

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

### register
- direct R/W to/from FiC register

#### PUT METHOD
- Write to FiC register
```
{
  'address'   : '<target address>'
  'data'      : '<data in hex>'
}
```

##### Return 
```
{
  'error' : '<error message if present>'
  'return': 'success' | 'failed'
}
```

#### GET METHOD
- Read to FiC register
```
{
  'address'   : '<target address>'
}
```

##### Return 
```
{
  'data'  : '<read data value>'
  'error' : '<error message if present>'
  'return': 'success' | 'failed'
}
