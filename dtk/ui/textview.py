#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Jack River
# 
# Author:     Jack River <ritksm@gmail.com>
# Maintainer: Jack River <ritksm@gmail.com>
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

#TODO fix utf8 problem move_up move_down should be changed

from constant import DEFAULT_FONT_SIZE, DEFAULT_FONT
from contextlib import contextmanager 
from draw import draw_hlinear
from keymap import get_keyevent_name
from menu import Menu
from theme import ui_theme
from utils import propagate_expose, cairo_state, color_hex_to_cairo, get_content_size, is_double_click, is_right_button, is_left_button, alpha_color_hex_to_cairo
from textbuffer import TextBuffer, TextIter
import gobject
import gtk
import pango
import pangocairo

class TextView(gtk.EventBox):
    
    def __init__(self, 
                content = "", 
                padding_x = 5, 
                padding_y = 2, 
                line_spacing = 5, 
                font_size = DEFAULT_FONT_SIZE, 
                text_color="#000000", 
                text_select_color="#000000", 
                background_select_color="#000000", ):
        gtk.EventBox.__init__(self)
        self.set_visible_window(False) # for transparent background
        self.__buffer = TextBuffer(content)
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.line_spacing = line_spacing
        self.font_size = font_size
        self.text_color = text_color
        self.text_select_color = text_select_color
        self.background_select_color = background_select_color
        self.grab_focus_flag = False
        self.set_can_focus(True)
        self.drag_start_index = (0, 0)
        self.drag_end_index = (0, 0)
        self.offset_x = 0
        self.offset_y = 0
        self.double_click_flag = False
        self.left_click_flag = False
        
        self.im = gtk.IMMulticontext()
        self.im.connect("commit", lambda im, input_text: self.commit_entry(input_text))
        
        # Add keymap.
        self.keymap = {
                "Left" : self.move_to_left,
                "Right" : self.move_to_right,
                "Up" : self.move_up, 
                "Down" : self.move_down, 
                "Home" : self.move_to_start,
                "End" : self.move_to_end,
                "BackSpace" : self.backspace,
                "Delete" : self.press_delete,
                "S-Left" : self.select_to_left,
                "S-Right" : self.select_to_right,
                "S-Home" : self.select_to_start,
                "S-End" : self.select_to_end,
                "C-a" : self.select_all,
                "C-x" : self.cut_to_clipboard,
                "C-c" : self.copy_to_clipboard,
                "C-v" : self.paste_from_clipboard,
                "Return" : self.press_return,
                "PageDown" : self.press_page_down,
                "PageUp" : self.press_page_up }
        
        self.__buffer.connect("changed", self.redraw)

        self.connect("key-press-event", self.key_press_textview)
        self.connect("expose-event", self.expose_textview)
        self.connect("focus-in-event", self.focus_in_textview)
        self.connect("focus-out-event", self.focus_out_textview)
        self.connect("button-press-event", self.button_press_textview)
        self.connect("button-release-event", self.button_release_textview)
        self.connect("motion-notify-event", self.motion_notify_text_view)

    def redraw(self, obj):
        self.queue_draw()

    def move_to_left(self):
        self.__buffer.move_cursor_left()
        self.queue_draw()
        
    
    def move_to_right(self):
        self.__buffer.move_cursor_right()
        self.queue_draw()
        
    def move_up(self):
        pass

    def move_down(self):
        pass

    def move_to_start(self):
        self.__buffer.move_cursor_to_line_start()
        self.queue_draw()
    
    def move_to_end(self):
        self.__buffer.move_cursor_to_line_end()
        self.queue_draw()
    
    def backspace(self):
        """when press backspace, delete one char"""
        ir = self.__buffer.get_iter_at_cursor()
        self.__buffer.backspace(ir)
        self.queue_draw()
    
    def press_delete(self):
        """when press delete, delete one char"""
        self.__buffer.reverse_backspace()
        self.queue_draw()
        
    def press_page_down(self):
        pass
    
    def press_page_up(self):
        pass
    
    def select_to_left(self):
        pass
    
    def select_to_right(self):
        pass
    
    def select_to_start(self):
        pass
    
    def select_to_end(self):
        pass
    
    def select_all(self):
        pass
    
    def cut_to_clipboard(self):
        cb = gtk.Clipboard()
        self.__buffer.cut_clipboard(cb)
        self.queue_draw()
    
    def copy_to_clipboard(self):
        cb = gtk.Clipboard()
        self.__buffer.copy_clipboard(cb)
    
    def paste_from_clipboard(self):
        cb = gtk.Clipboard()
        self.__buffer.paste_clipboard(cb)
        self.queue_draw()
    
    def press_return(self):
        self.__buffer.new_line_at_cursor()
        self.queue_draw()
    
    def motion_notify_text_view(self, widget, event):
        self.queue_draw()
        
    def button_press_textview(self, widget, event):
        '''Button press textview.'''
        # Get input focus.
        self.grab_focus()
        
        self.grab_focus_flag = True
        
        if is_left_button(event):
            self.left_click_flag = True
            self.left_click_coordindate = (event.x, event.y)
            
            self.drag_start_index = self.get_index_at_event(widget, event)

    def button_release_textview(self, widget, event):
        '''Button release textview.'''
        if not self.double_click_flag:
            self.drag_end_index = self.get_index_at_event(widget, event)    
            start_line_offset, start_line = self.drag_start_index
            end_line_offset, end_line = self.drag_end_index

            ir = self.__buffer.get_iter_at_line(start_line)
            ir2 = self.__buffer.get_iter_at_line(end_line)
            ir.set_line_offset(start_line_offset)
            ir2.set_line_offset(end_line_offset)

            self.__buffer.select_text(ir, ir2)

            ir, ir2 = self.__buffer.get_selection()

            print self.__buffer.get_slice(ir, ir2)

            self.queue_draw()

        self.double_click_flag = False
        self.left_click_flag = False

    def get_index_at_event(self, widget, event):
        '''Get index at event.'''
        cr = widget.window.cairo_create()
        context = pangocairo.CairoContext(cr)
        layout = context.create_layout()
        layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.font_size)))
        layout.set_text(self.__buffer.get_text())
        text_width = self.get_content_width("x")
        text_height = get_content_size("好Height", self.font_size)[-1]
        index_x = 0
        index_y = 0
        event.x -= self.padding_x
        event.y -= self.padding_y
        for x in range(0, self.__buffer.get_line_count()):
            if text_height * x < event.y and event.y < text_height * (x + 1):
                index_y = x

        ir = self.__buffer.get_iter_at_line(index_y)

        for x in range(0, ir.get_chars_in_line()):
            if self.get_content_width(ir.get_line_text()[0:x]) < event.x and event.x < self.get_content_width(ir.get_line_text()[0:x+1]):
                index_x = x

        return (index_x, index_y)

    def focus_in_textview(self, widget, event):
        '''Callback for `focus-in-event` signal.'''
        self.grab_focus_flag = True

        # Focus in IMContext.
        self.im.set_client_window(widget.window)
        self.im.focus_in()

        self.queue_draw()
            
    def focus_out_textview(self, widget, event):
        '''Callback for `focus-out-event` signal.'''
        self.grab_focus_flag = False

        # Focus out IMContext.
        self.im.focus_out()

        self.queue_draw()
    
    def expose_textview(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # draw text
        self.draw_text(cr, rect)
        
        # draw cursor
        if self.grab_focus_flag:
            self.draw_cursor(cr, rect)
        
        propagate_expose(widget, event)

        # resize widget for scrolledwindow-support
        max = 0
        for x in range(0, self.__buffer.get_line_count()):
             if max < self.get_content_width(self.__buffer.get_iter_at_line(x).get_line_text()):
                max = self.get_content_width(self.__buffer.get_iter_at_line(x).get_line_text())
        height = get_content_size("好Height", self.font_size)[-1] * (self.__buffer.get_iter_at_cursor().get_line())
        self.set_size_request(max + 10, height)
        
        return True

    def draw_background(self, cr, rect):
        pass
        
    def draw_text(self, cr, rect):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        with cairo_state(cr):
            draw_x = x + self.padding_x
            draw_y = y + self.padding_y
            draw_width = w - self.padding_x * 2
            draw_height = h - self.padding_y * 2
            cr.rectangle(draw_x, draw_y, draw_width, draw_height)
            cr.clip()
            
            # pango context
            context = pangocairo.CairoContext(cr)
            
            # pango layout
            layout = context.create_layout()
            layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, self.font_size)))
            
            text = self.__buffer.get_text()
            layout.set_text(text)
            
            (text_width, text_height) = layout.get_pixel_size()
            cr.move_to(x + self.padding_x , y + self.padding_y)
            
            cr.set_source_rgb(0,0,0)
            context.update_layout(layout)
            context.show_layout(layout)
            

    def __is_utf_8_text_in_line(self, line):
        decode_list = list(self.__buffer.get_iter_at_line(line).get_line_text().decode('utf-8'))
        for l in decode_list:
            if len(l.encode('utf-8')) != 1:
                # utf-8 character length >= 1
                return True

    def draw_cursor(self, cr, rect):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        cursor_ir = self.__buffer.get_iter_at_cursor()
        left_str = cursor_ir.get_line_text()[0:cursor_ir.get_line_offset()]
        left_str_width = self.get_content_width(left_str)
        
        current_line = cursor_ir.get_line()

        line_offset = 0
        
        utf_8_height = get_content_size("好Height", self.font_size)[-1]
        no_utf_8_height = get_content_size("Height", self.font_size)[-1]

        for x in range(0, current_line):
            if self.__is_utf_8_text_in_line(x):
                line_offset += utf_8_height
            else:
                line_offset += no_utf_8_height

        temp_line_offset = 1 # solve the offset problem while adding lines
        

        cr.set_source_rgb(0,0,0)
        cr.rectangle(x + self.padding_x + left_str_width - temp_line_offset * current_line, y  + line_offset + utf_8_height - no_utf_8_height , 1, no_utf_8_height)
        cr.fill()
        
        
    def set_text(self, text):
        self.content = self.__parse_content(text)
        self.current_line = len(self.content.keys()) - 1 # currrent line index
        self.current_line_offset = len(self.content[self.current_line]) # offset in current line
        self.queue_draw()
        
    def key_press_textview(self, widget, event):
        input_method_filt = self.im.filter_keypress(event)
        if not input_method_filt:
            self.handle_key_event(event)
        return False
        
    def handle_key_event(self, event):
        '''Handle key event.'''
        key_name = get_keyevent_name(event)

        if self.keymap.has_key(key_name):
            self.keymap[key_name]()
            

    def get_content_width(self, content):
        '''Get content width.'''
        (content_width, content_height) = get_content_size(content, self.font_size)
        return content_width
    
    def commit_entry(self, input_text):
        self.__buffer.insert_text_at_cursor(input_text)
        self.queue_draw()
        
    def get_utf8_string(self, content, index):
        '''Get utf8 string.'''
        try:
            return list(content.decode('utf-8'))[index].encode('utf-8')
        except Exception, e:
            print "get_utf8_string got error: %s" % (e)
            return ""
            
gobject.type_register(TextView)


if __name__ == "__main__":
    window = gtk.Window()
    
    tv = TextView(content = "hello\nworld\nline3")
    
    sw = gtk.ScrolledWindow()
    sw.add_with_viewport(tv)

    window.add(sw)
    
    window.set_size_request(300, 200)
    
    window.connect("destroy", lambda w: gtk.main_quit())
    
    window.show_all()
    
    gtk.main()
