#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flup.server.fcgi import WSGIServer
from ficwww import app

if __name__ == '__main__':
    WSGIServer(app).run()
    