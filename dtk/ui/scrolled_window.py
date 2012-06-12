#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Xia Bin
# 
# Author:     Xia Bin <xiabin@linuxdeepin.com>
# Maintainer: Xia Bin <xiabin@linuxdeepin.com>
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

import gobject
import gtk
from gtk import gdk
from utils import remove_callback_id, color_hex_to_cairo
from theme import ui_theme

# the p_range is the virtual width/height, it's value is smaller than
# the allocation.width/height when scrollbar's width/height smaller than
# the minmum scrollbar length.
# p_range =  allocation.width/height - (min_bar_len - *bar_len*)
#       the *bar_len* =  (adj.page_size / adj.upper) * allocation.width/height
# by this processing, 0~(adj.upper-adj.page_size) will be mapped to 0~p_range.
def value2pos(value, p_range, upper):
    '''compute the scrollbar position by the adjustment value'''
    if upper == 0: return 0
    return p_range * float(value) / upper

def pos2value(pos, p_range, upper):
    '''compute the adjustment value by the scrollbar position'''
    if p_range == 0 : return 0
    return pos * upper / p_range

class ScrolledWindow(gtk.Bin):
    '''Scrolled window.'''

    def __init__(self):
        '''Init scrolled window.'''
        gtk.Bin.__init__(self)
        self.bar_min_length = 50  #scrollbar smallest height

        self.bar_small_width = 7
        self.bar_width = 14  #normal scrollbar width
        self.bar_background = ui_theme.get_color("scrolledbar")

        class Record():
            def __init__(self):
                self.bar_len = 0  #scrollbar length
                self.last_pos = 0 #last mouse motion pointer's position (x or y)

                #last mouse motion timestamp, if user moved the window
                #then the last_pos is likely become invalid so we need "last_time"
                #to deal with this situation.
                self.last_time = 0
                self.virtual_len = 0  #the virtual window height or width length
                self.bar_pos = 0 #the scrollbar topcorner/leftcorner position
                self.is_inside = False # is pointer in the scrollbar region?
                self.in_motion = False # is user is draging scrollbar?
                self.value_change_id = None

        self._horizaontal = Record()
        self._vertical = Record()

        self.set_can_focus(True)
        self.vallocation = gdk.Rectangle()
        self.hallocation = gdk.Rectangle()
        self.set_vadjustment(gtk.Adjustment())
        self.set_hadjustment(gtk.Adjustment())
        #self.set_app_paintable(True)
        self.set_has_window(False)




    def do_expose_event(self, e):
        if e.window == self.vwindow:
            self.draw_vbar()
            return True
        elif e.window == self.hwindow:
            self.draw_hbar()
            return True
        else:
            return False

    def draw_vbar(self):
        #img = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        cr = self.vwindow.cairo_create()
        cr.set_source_rgb(*color_hex_to_cairo(self.bar_background.get_color()))
        cr.rectangle(0, 0, self.vallocation.width, self.vallocation.height)
        cr.fill()

    def draw_hbar(self):
        cr = self.hwindow.cairo_create()
        cr.set_source_rgb(*color_hex_to_cairo(self.bar_background.get_color()))
        cr.rectangle(0, 0, self.hallocation.width, self.hallocation.height)
        cr.fill()

    def do_button_release_event(self, e):
        if e.window == self.hwindow:
            self._horizaontal.in_motion = False
            if not self._horizaontal.is_inside:
                self.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
            return True
        elif e.window == self.vwindow:
            self._vertical.in_motion = False
            if not self._vertical.is_inside:
                self.make_bar_smaller(gtk.ORIENTATION_VERTICAL)
            return True
        else:
            return False


    def make_bar_smaller(self, orientation):
        (right_space, top_bootm_space) = (2, 3)
        if orientation == gtk.ORIENTATION_HORIZONTAL:
            region = gdk.region_rectangle(gdk.Rectangle(0, 0, int(self._horizaontal.bar_len), self.bar_small_width))

            if self.hallocation.x == 0:
                self.hwindow.shape_combine_region(region, top_bootm_space, self.bar_width - self.bar_small_width -right_space)
            else:
                self.hwindow.shape_combine_region(region, -top_bootm_space, self.bar_width - self.bar_small_width -right_space)
        elif orientation == gtk.ORIENTATION_VERTICAL:
            region = gdk.region_rectangle(gdk.Rectangle(0, 0, self.bar_small_width-2, int(self._vertical.bar_len)))

            if self.vallocation.y == 0:
                self.vwindow.shape_combine_region(region, self.bar_width-self.bar_small_width, 3)
            else:
                self.vwindow.shape_combine_region(region, self.bar_width-self.bar_small_width, -3)
        else:
            raise "make_bar_smaller's orientation must be gtk.ORIENTATION_VERTICAL or gtk.ORIENTATION_HORIZONTAL"

        return False

    def make_bar_bigger(self, orientation):
        (right_space, top_bootm_space) = (2, 3)

        if orientation == gtk.ORIENTATION_HORIZONTAL:
            region = gdk.region_rectangle(gdk.Rectangle(0, 0, int(self._horizaontal.bar_len), self.bar_width))

            if self.hallocation.x == 0:
                self.hwindow.shape_combine_region(region, top_bootm_space, -right_space)
            else:
                self.hwindow.shape_combine_region(region, -top_bootm_space, -right_space)
        elif orientation == gtk.ORIENTATION_VERTICAL:
            region = gdk.region_rectangle(gdk.Rectangle(0, 0, self.bar_width, int(self._vertical.bar_len)))

            if self.vallocation.y == 0:
                self.vwindow.shape_combine_region(region, -right_space, top_bootm_space)
            else:
                self.vwindow.shape_combine_region(region, -right_space, -top_bootm_space)
        else:
            raise "make_bar_bigger's orientation must be gtk.ORIENTATION_VERTICAL or gtk.ORIENTATION_HORIZONTAL"

    def do_scroll_event(self, e):
        value = self.vadjustment.value
        step = self.vadjustment.step_increment
        page_size = self.vadjustment.page_size
        upper = self.vadjustment.upper

        #TODO: need handle other scrolltype? I can only capture below two scrolltype at the moment
        if e.direction == gdk.SCROLL_DOWN:
            self.vadjustment.set_value(min(upper-page_size-1, value+step))
            return True
        elif e.direction == gdk.SCROLL_UP:
            self.vadjustment.set_value(max(0, value-step))
            return True
        else:
            return False

    def do_leave_notify_event(self, e):
        if e.window == self.hwindow :
            self._horizaontal.is_inside = False
            #if e.y < 0 and not self._horizaontal.in_motion:
            if not self._horizaontal.in_motion:
                self.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
            return True
        elif e.window == self.vwindow:
            self._vertical.is_inside = False
            if not self._vertical.in_motion:
            #if e.x < 0 and not self._vertical.in_motion:
                self.make_bar_smaller(gtk.ORIENTATION_VERTICAL)
            return True
        else:
            return False

    def do_enter_notify_event(self, e):
        if e.window == self.hwindow:
            self.make_bar_bigger(gtk.ORIENTATION_HORIZONTAL)
            self._horizaontal.is_inside = True
            return True
        elif e.window == self.vwindow:
            self.make_bar_bigger(gtk.ORIENTATION_VERTICAL)
            self._vertical.is_inside = True
            return True
        else:
            return False

    def do_motion_notify_event(self, e):
        if not (e.window == self.hwindow or e.window == self.vwindow): return False

        if e.window == self.hwindow and e.state == gtk.gdk.BUTTON1_MASK:
            self.make_bar_bigger(gtk.ORIENTATION_HORIZONTAL)
            if self._horizaontal.last_time == 0:
                self._horizaontal.last_time = e.time
            elif e.time - self._horizaontal.last_time > 1000:
                self._horizaontal.last_time = 0
                self._horizaontal.last_pos = 0

            if self._horizaontal.last_pos == 0 or self._horizaontal.last_time == 0:
                self._horizaontal.last_pos  = e.x_root
                return True
            deltaX = e.x_root - self._horizaontal.last_pos
            upper = self.hadjustment.upper

            #the pos maybe beyond the effective range, but we will immediately corrected
            #it's value.
            #the "invariant" is  the "value" always in the effective range.
            value = pos2value(self._horizaontal.bar_pos+deltaX, self._horizaontal.virtual_len, upper)
            value = max(0, min(value, self.hadjustment.upper-self.hadjustment.page_size))
            self.hadjustment.set_value(value)

            self._horizaontal.last_pos = e.x_root
            self._horizaontal.last_time = e.time
            self._horizaontal.in_motion = True
            return True

        elif e.window == self.vwindow and e.state == gtk.gdk.BUTTON1_MASK:
            self.make_bar_bigger(gtk.ORIENTATION_VERTICAL)
            if self._vertical.last_time == 0:
                self._vertical.last_time = e.time
            elif e.time - self._vertical.last_time > 1000:
                self._vertical.last_time = 0
                self._vertical.last_pos = 0

            if self._vertical.last_pos == 0 or self._vertical.last_time == 0:
                self._vertical.last_pos  = e.y_root
                return True

            upper = self.vadjustment.upper
            deltaY = e.y_root - self._vertical.last_pos

            value = pos2value(self._vertical.bar_pos+deltaY, self._vertical.virtual_len, upper)
            value = max(0, min(value, self.vadjustment.upper-self.vadjustment.page_size))
            self.vadjustment.set_value(value)

            self._vertical.last_pos = e.y_root
            self._vertical.last_time = e.time
            self._vertical.in_motion = True
            return True

    def calc_vbar_length(self):
        self._vertical.virtual_len = self.allocation.height
        if self.vadjustment.upper <= 1:
            self._vertical.bar_len = 0
            return

        ratio = float(self.vadjustment.page_size) / (self.vadjustment.upper-self.vadjustment.lower)

        assert(self.vadjustment.upper >= self.vadjustment.page_size)
        if ratio == 1:
            self._vertical.bar_len = 0
        else:
            bar_len = self._vertical.virtual_len * ratio
            if bar_len < self.bar_min_length:
                self._vertical.virtual_len -= (self.bar_min_length - bar_len)
            self._vertical.bar_len = max(bar_len, self.bar_min_length)

    def calc_vbar_allocation(self):
        self.vallocation = gdk.Rectangle(
                self.allocation.width - self.bar_width, int(self._vertical.bar_pos),
                self.bar_width, int(self._vertical.bar_len))

    def calc_hbar_length(self):
        self._horizaontal.virtual_len = self.allocation.width
        if self.hadjustment.upper <= 1:
            self._horizaontal.bar_len = 0
            return


        ratio = float(self.hadjustment.page_size) / (self.hadjustment.upper-self.hadjustment.lower)
        assert(self.hadjustment.lower == 0)

        assert(self.hadjustment.upper >= self.hadjustment.page_size)
        if ratio == 1:
            self._horizaontal.bar_len = 0
        else:
            bar_len = self._horizaontal.virtual_len * ratio
            if bar_len < self.bar_min_length:
                self._horizaontal.virtual_len -= (self.bar_min_length - bar_len)
            self._horizaontal.bar_len = max(bar_len, self.bar_min_length)

    def calc_hbar_allocation(self):
        #assert 0 <= int(self.hpos) <= self.allocation.width - self.hbar_length,\
        #        "self.hpos %f   self.allocation.width %f self.hbar_lengh %f" % (self.hpos, self.allocation.width,
        #                self.hbar_length)
        self.hallocation = gdk.Rectangle(
                int(self._horizaontal.bar_pos), self.allocation.height - self.bar_width,
                int(self._horizaontal.bar_len), self.bar_width)

    def vadjustment_changed(self, adj):
        if self.get_realized():
            assert(self.vadjustment.value <= self.vadjustment.upper-self.vadjustment.page_size)
            upper = self.vadjustment.upper
            self._vertical.bar_pos = value2pos(adj.value, self._vertical.virtual_len, upper)
            self.calc_vbar_allocation()
            self.vwindow.move_resize(*self.vallocation)
            self.queue_draw()

    def hadjustment_changed(self, adj):
        if self.get_realized():
            assert(self.hadjustment.value <= self.hadjustment.upper-self.hadjustment.page_size)
            upper = self.hadjustment.upper
            self._horizaontal.bar_pos = value2pos(adj.value, self._horizaontal.virtual_len, upper)
            self.calc_hbar_allocation()
            self.hwindow.move_resize(*self.hallocation)
            self.queue_draw()


    def add_with_viewport(self, child):
        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(child)
        vp.show()
        self.add(vp)

    def add_child(self, child):
        self.add_with_viewport(child)
        #raise Exception, "use add_with_viewport instead add_child"


    def do_add(self, child):
        self.child = None
        gtk.Bin.do_add(self, child)

        child.set_scroll_adjustments(self.hadjustment, self.vadjustment)
        
    def do_size_request(self, requsition):
        if self.child:
            #print "sel size_request", (requsition.width, requsition.height)
            self.child.do_size_request(self.child, requsition)
            #print "child size request:", (requsition.width, requsition.height)

    def do_size_allocate(self, allocation):
        #print "do_size_allocate", allocation
        self.allocation = allocation

        if self.get_realized():
            self.binwindow.move_resize(*self.allocation)

        #must before calc_xxx_length, because we need child to cumpute the adjustment value
        if self.child:
            (allocation.x, allocation.y) = (0, 0)
            self.child.do_size_allocate(self.child, allocation)

            if self.get_realized():
                self.calc_vbar_length()
                self.calc_hbar_length()
                self.make_bar_smaller(gtk.ORIENTATION_VERTICAL)
                self.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
                self.vadjustment.emit('value-changed')
                self.hadjustment.emit('value-changed')

    def do_unrealize(self):
        #print "do_unrealize"

        self.binwindow.set_user_data(None)
        self.binwindow.destroy()
        self.binwindow = None
        self.vwindow.set_user_data(None)
        self.vwindow.destroy()
        self.vwindow = None
        self.hwindow.set_user_data(None)
        self.hwindow.destroy()
        self.hwindow = None

        assert(self.get_realized() == True)
        gtk.Bin.do_unrealize(self)
        assert(self.get_realized() == False)


    def do_realize(self):
        #print "self.get_parent_window():", self.get_parent_window()
        #print "do_realize", self.get_realized()

        assert(self.get_realized() == False)
        gtk.Bin.do_realize(self)
        assert(self.get_realized() == True)

        self.binwindow = gtk.gdk.Window(self.get_parent_window(),
                x=self.allocation.x,
                y=self.allocation.y,
                width=self.allocation.width,
                height=self.allocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                event_mask=(self.get_events()| gdk.EXPOSURE_MASK | gdk.VISIBILITY_NOTIFY_MASK),
                visual=self.get_visual(),
                colormap=self.get_colormap(),
                )
        self.binwindow.set_user_data(self)

        self.vwindow = gtk.gdk.Window(self.binwindow,
                x=self.vallocation.x,
                y=self.vallocation.y,
                width=self.vallocation.width,
                height=self.vallocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                visual=self.get_visual(),
                colormap=self.get_colormap(),
                event_mask=(self.get_events()
                    | gdk.EXPOSURE_MASK
                    | gdk.ENTER_NOTIFY_MASK | gdk.LEAVE_NOTIFY_MASK | gdk.BUTTON_RELEASE_MASK
                    | gdk.BUTTON_MOTION_MASK
                    | gdk.POINTER_MOTION_HINT_MASK | gdk.BUTTON_PRESS_MASK
                    )
                )
        self.vwindow.set_user_data(self)
        #sefl.vwindow.get_
        #self.vwindow.set_background(self.bar_background)

        self.hwindow = gtk.gdk.Window(self.binwindow,
                x=self.hallocation.x,
                y=self.hallocation.y,
                width=self.hallocation.width,
                height=self.hallocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                colormap=self.get_colormap(),
                visual=self.get_visual(),
                event_mask=(self.get_events()
                    | gdk.EXPOSURE_MASK
                    | gdk.ENTER_NOTIFY_MASK | gdk.LEAVE_NOTIFY_MASK | gdk.BUTTON_RELEASE_MASK
                    | gdk.BUTTON_MOTION_MASK
                    | gdk.POINTER_MOTION_HINT_MASK | gdk.BUTTON_PRESS_MASK
                    )
                )
        self.hwindow.set_user_data(self)
        #self.hwindow.set_background(self.bar_background)

        if self.child:
            self.child.set_parent_window(self.binwindow)

        self.queue_resize()

    def set_shadow_type(self, t):
        #raise Warning("dtk's scrolledwindow didn't support this function")
        return

    def set_policy(self, h, v):
        #raise Warning("dtk's scrolledwindow didn't support this function,\
        #        policy is always automatic!")
        return

    def do_map(self):
        gtk.Bin.do_map(self)  #must before self.xwindow.show(), didn't know the reason.
        self.binwindow.show()
        self.hwindow.show()
        self.vwindow.show()
        if self.child and not self.child.get_mapped() and self.child.get_visible():
            self.child.do_map(self.child)

    def do_unmap(self):
        #self.set_mapped(False)
        self.binwindow.hide()
        self.hwindow.hide()
        self.vwindow.hide()
        gtk.Bin.do_unmap(self)

    def get_vadjustment(self):
        return self.vadjustment

    def get_hadjustment(self):
        return self.hadjustment

    def set_hadjustment(self, adj):
        self.hadjustment = adj
        remove_callback_id(self._horizaontal.value_change_id)
        self.hadj_callback_id = self.hadjustment.connect('value-changed', self.hadjustment_changed)
        #self.hadjustment.connect('changed', self.hadjustment_changed)
    def set_vadjustment(self, adj):
        self.vadjustment = adj
        remove_callback_id(self._vertical.value_change_id)
        self.vadj_callback_id = self.vadjustment.connect('value-changed', self.vadjustment_changed)
        #self.vadjustment.connect('changed', self.vadjustment_changed)


    def _test_calc(self):
        for i in xrange(0, int(self.vadjustment.upper-self.vadjustment.page_size), 30):
            pos = value2pos(i, self._vertical.virtual_len, self.vadjustment.upper)
            print "value:%f --> pos:%d" % (i, pos),
            assert(pos <= self.allocation.height-self._vertical.bar_len),\
                "pos(%f) should small than(%f)"  % (pos, self.allocation.height-self._vertical.bar_len)
            value = pos2value(pos, self._vertical.virtual_len, self.vadjustment.upper)
            print "\t pos:%d -->value:%f" % (pos, value)

        print "v_len:%f, height:%f, vir_bar_len:%d" % ( self._vertical.virtual_len,
                self.allocation.height, self._vertical.bar_len)

gobject.type_register(ScrolledWindow)
