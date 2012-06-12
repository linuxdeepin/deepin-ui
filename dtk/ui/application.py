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

from mplayer_window import MplayerWindow
from threads import post_gui
from titlebar import Titlebar
from window import Window
from utils import container_remove_all, place_center
import gtk
from skin import SkinWindow
from skin_config import skin_config

class Application(object):
    '''Application.'''

    def __init__(self, app_support_colormap=True):
        '''Init application.'''
        # Init.
        self.app_support_colormap = app_support_colormap
        self.close_callback = self.close_window

        # Start application.
        self.init()

    def init(self):
        '''Init.'''
        # Init gdk threads, the integrant method for multi-thread GUI application.
        gtk.gdk.threads_init()

        # Init status.
        self.menu_button_callback = None

        # Init window.
        if self.app_support_colormap:
            self.window = Window(True)
        else:
            self.window = MplayerWindow(True)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.connect("destroy", self.destroy)
        
        # Init main box.
        self.main_box = self.window.window_frame

        # Add titlebar box.
        self.titlebar = None
        self.titlebar_box = gtk.HBox()
        self.main_box.pack_start(self.titlebar_box, False)

    def add_titlebar(self,
                     button_mask=["theme", "menu", "max", "min", "close"],
                     icon_dpixbuf=None, app_name=None, title=None, add_separator=False):
        '''Add titlebar.'''
        # Init titlebar.
        self.titlebar = Titlebar(button_mask, icon_dpixbuf, app_name, title, add_separator)
        if "theme" in button_mask:
            self.titlebar.theme_button.connect("clicked", self.theme_callback)
        if "menu" in button_mask:
            self.titlebar.menu_button.connect("clicked", self.menu_callback)
        if "min" in button_mask:
            self.titlebar.min_button.connect("clicked", lambda w: self.window.min_window())
        if "max" in button_mask:
            self.titlebar.max_button.connect("clicked", lambda w: self.window.toggle_max_window())
        if "close" in button_mask:
            self.titlebar.close_button.connect("clicked", self.close_callback)
        self.window.add_toggle_event(self.titlebar.drag_box)
        self.window.add_move_event(self.titlebar.drag_box)

        # Show titlebar.
        self.show_titlebar()

    def close_window(self, widget):
        '''Close window.'''
        self.window.close_window()

    def show_titlebar(self):
        '''Show titlebar.'''
        if self.titlebar_box.get_children() == [] and self.titlebar != None:
            self.titlebar_box.add(self.titlebar)

    def hide_titlebar(self):
        '''Hide titlebar.'''
        container_remove_all(self.titlebar_box)

    @post_gui
    def raise_to_top(self):
        '''Raise to top.'''
        self.window.present()

    def set_title(self, title):
        '''Set application title.'''
        self.window.set_title(title)

    def set_default_size(self, default_width, default_height):
        '''Set application default size.'''
        self.window.set_default_size(default_width, default_height)
        self.window.set_geometry_hints(
            None,
            default_width,       # minimum width
            default_height       # minimum height
            -1, -1, -1, -1, -1, -1, -1, -1
            )
        
        # Pass application size to skin config.
        skin_config.set_application_window_size(default_width, default_height)

    def set_icon(self, icon_dpixbuf):
        '''Set icon.'''
        gtk.window_set_default_icon(icon_dpixbuf.get_pixbuf())

    def destroy(self, widget, data=None):
        '''Destroy main window.'''
        gtk.main_quit()

    def run(self):
        '''Run.'''
        # Show window.
        self.window.show_window()

        # Run main loop.
        gtk.main()

    def set_skin_preview(self, preview_pixbuf):
        '''Set skin preview pixbuf.'''
        self.skin_preview_pixbuf = preview_pixbuf
        
    def theme_callback(self, widget):
        '''Theme button callback.'''
        skin_window = SkinWindow(self.skin_preview_pixbuf)
        skin_window.show_all()
        place_center(self.window, skin_window)

        return False

    def menu_callback(self, widget):
        '''Menu button callback.'''
        if self.menu_button_callback:
            self.menu_button_callback(widget)

        return False

    def set_menu_callback(self, callback):
        '''Set menu callback.'''
        self.menu_button_callback = callback
