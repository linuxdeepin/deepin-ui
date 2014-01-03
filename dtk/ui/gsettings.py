#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

try:
    import deepin_gsettings
    DESKTOP_SETTINGS_CONF = "org.gnome.desktop.interface"
    DESKTOP_SETTINGS = deepin_gsettings.new(DESKTOP_SETTINGS_CONF)
except ImportError:
    print "----------Please Install Deepin GSettings Python Binding----------"
    print "sudo apt-get install python-deepin-gsettings"
    print "------------------------------------------------------------------"

DEFAULT_CURSOR_BLINK_TIME = 600  # microsecond

