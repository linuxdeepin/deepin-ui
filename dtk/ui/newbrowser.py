#!/usr/bin/env python

import webkit
class WebView(webkit.WebView):
    def __init__(self, cookie="cookie"):
        import ctypes
        webkit.WebView.__init__(self)
        ctypes.CDLL('./libaddjar.1.0.1').add_jar(cookie)
