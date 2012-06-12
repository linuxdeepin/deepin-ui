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

from dbus.mainloop.glib import DBusGMainLoop
import dbus
import dbus.service

class UniqueService(dbus.service.Object):
    def __init__(self, bus_name, app_dbus_name, app_object_name, unique_callback=None):
        # Init.
        dbus.service.Object.__init__(self, bus_name, app_object_name)
        self.unique_callback = unique_callback

        # Define DBus method.
        def unique(self):
            if self.unique_callback:
                self.unique_callback()

        # Below code export dbus method dyanmically.
        # Don't use @dbus.service.method !
        setattr(UniqueService, 'unique', dbus.service.method(app_dbus_name)(unique))

def is_exists(app_dbus_name, app_object_name):
    '''Is application exists.'''
    DBusGMainLoop(set_as_default=True) # WARING: only use once in one process
        
    # Init dbus.
    bus = dbus.SessionBus()
    if bus.request_name(app_dbus_name) != dbus.bus.REQUEST_NAME_REPLY_PRIMARY_OWNER:
        method = bus.get_object(app_dbus_name, app_object_name).get_dbus_method("unique")
        method()
        
        return True
    else:
        return False
