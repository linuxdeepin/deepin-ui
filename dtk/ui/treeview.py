#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Hailong Qiu <qiuhailong@linuxdeepin.com>
# Maintainer: Hailong Qiu <qiuhailong@linuxdeepin.com>
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

# from dtk.ui.skin_config import skin_config
# from dtk.ui.theme import Theme, ui_theme

import gtk
import gobject
from collections import OrderedDict

from draw import draw_pixbuf, draw_vlinear, draw_font
from utils import (get_content_size, is_single_click, is_double_click, is_right_button, color_hex_to_cairo,
                   cairo_state, get_match_parent)
from theme import ui_theme
from skin_config import skin_config

# (cr, text, font_size, font_color, x, y, width, height, font_align
class TreeView(gtk.DrawingArea):
    
    __gsignals__ = {
        "single-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "double-click-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        "right-press-item" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, gobject.TYPE_INT, gobject.TYPE_INT)),
        }
    
    def __init__(self, width=20, height = 30,
                 font_size = 10, font_x_padding=5, font_width=120, font_height = 0,font_align=0,
                 arrow_x_padding = 10, 
                 normal_pixbuf = ui_theme.get_pixbuf("treeview/arrow_right.png"), 
                 press_pixbuf = ui_theme.get_pixbuf("treeview/arrow_down.png")):        
        gtk.DrawingArea.__init__(self)
        self.root = Tree()
        self.tree_list = []
        self.tree_all_node_list = [] # Save all node.
        
        self.tree_id_list = []        
        self.tree_id_num = 0
        self.scan_save_item = None
        
        self.set_can_focus(True)
        # Init DrawingArea event.
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.connect("button-press-event", self.tree_view_press_event)
        self.connect("motion-notify-event", self.tree_view_motion_event)
        self.connect("expose-event", self.tree_view_expose_event)
        self.connect("key-press-event", self.tree_view_key_press_event)
        self.connect("leave-notify-event", self.tree_view_leave_notify_event)
        self.connect("realize", lambda w: self.grab_focus()) # focus key after realize
        
        self.width = width
        self.height = height
        # Draw icon.
        self.normal_pixbuf = normal_pixbuf
        self.press_pixbuf = press_pixbuf
        self.arrow_x_padding = arrow_x_padding
        # Draw move background. 
        self.move_height = -1
        self.move_draw_bool = False
        self.move_index_num = None
        # Draw press background.
        self.press_height = -1
        self.press_draw_bool = False
        # Draw font.
        self.font_x_padding = font_x_padding
        self.font_width = font_width
        self.font_height = font_height
        self.font_align = font_align
        self.font_size = font_size
        
        self.highlight_index = None
        
        if not self.font_size:
            self.font_size = self.height/2 - 4
            
        if self.font_size > self.height - 15:    
            self.font_size = self.height - 15
        
    # DrawingArea event function.           
    def tree_view_press_event(self, widget, event):
        self.press_notify_function(event) 
        
        
    def press_notify_function(self, event):    
        temp_press_height = self.press_height
        self.press_height = event.y
        index_len = len(self.tree_list)
        index = int(self.press_height / self.height)
        self.highlight_index = index
        
        if index_len > index:
            if is_single_click(event):
                self.press_draw_bool = True
            
                if self.tree_list[index].child_items:        
                    self.tree_list[index].show_child_items_bool = not self.tree_list[index].show_child_items_bool 
                    self.sort()
                    self.queue_draw()
            
            if is_single_click(event):
                self.emit("single-click-item", self.tree_list[index].tree_view_item)
            elif is_double_click(event):    
                self.emit("double-click-item", self.tree_list[index].tree_view_item)
            elif is_right_button(event):    
                self.emit("right-press-item", self.tree_list[index].tree_view_item, event.x_root, event.y_root)
                
        else:
            self.press_height = temp_press_height
                    
    def set_highlight_index(self, index):        
        index_len = len(self.tree_list)
        self.highlight_index = index
        if index_len > index:
            self.press_height =  self.height * index
            self.press_draw_bool = True
            self.queue_draw()
            
    def get_highlight_index(self):    
        return self.highlight_index
        
    def get_highlight_item(self):
        return self.tree_list[self.highlight_index].tree_view_item
    
    def tree_view_motion_event(self, widget, event):
        temp_move_height = self.move_height # Save move_height.
        self.move_height = event.y
        index_len = len(self.tree_list)
        index_num = int(self.move_height) / self.height 
                        
        if index_len > index_num: 
            self.move_index_num = index_num
            self.move_draw_bool = True
            self.queue_draw()       
        else:
            self.move_height = temp_move_height
                                
    # print get_match_parent(self, "ScrolledWindow")    
    def get_offset_coordinate(self, widget):
        '''Get offset coordinate.'''
        # Init.
        rect = widget.allocation

        # Get coordinate.
        viewport = get_match_parent(widget, "Viewport")
        if viewport: 
            coordinate = widget.translate_coordinates(viewport, rect.x, rect.y)
            if len(coordinate) == 2:
                (offset_x, offset_y) = coordinate
                return (-offset_x, -offset_y, viewport)
            else:
                return (0, 0, viewport)
        else:
            return (0, 0, viewport)
            
    def draw_mask(self, cr, x, y, w, h):
        draw_vlinear(cr, x, y, w, h,
                     ui_theme.get_shadow_color("linearBackground").get_color_info())
            
    def tree_view_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Get offset.
        (offset_x, offset_y, viewport) = self.get_offset_coordinate(widget)
        
        
        # Draw background.
        with cairo_state(cr):
            scrolled_window = get_match_parent(self, "ScrolledWindow")
            cr.translate(-scrolled_window.allocation.x, -scrolled_window.allocation.y)
            cr.rectangle(offset_x, offset_y, 
                         scrolled_window.allocation.x + scrolled_window.allocation.width, 
                         scrolled_window.allocation.y + scrolled_window.allocation.height)
            cr.clip()
            
            (shadow_x, shadow_y) = self.get_toplevel().get_shadow_size()
            skin_config.render_background(cr, self, offset_x + shadow_x, offset_y + shadow_y)
            
        # Draw mask.
        self.draw_mask(cr, offset_x, offset_y, viewport.allocation.width, viewport.allocation.height)
        
        if self.press_draw_bool:
            self.draw_y_padding = int(self.press_height) / self.height * self.height
            draw_vlinear(
                cr,
                x, y + self.draw_y_padding, w, self.height,
                ui_theme.get_shadow_color("treeItemSelect").get_color_info())
        
        if self.move_draw_bool:
            if int(self.press_height) / self.height * self.height != int(self.move_height) / self.height * self.height:
                self.draw_y_padding = int(self.move_height) / self.height * self.height
                draw_vlinear(
                    cr,
                    x, y + self.draw_y_padding, w, self.height,
                    ui_theme.get_shadow_color("treeItemHover").get_color_info())
            
        if self.tree_list:    
            temp_height = 0
            # (cr, text, font_size, font_color, x, y, width, height, font_align
            for (widget_index, draw_widget) in enumerate(self.tree_list):
                if draw_widget.text:
                    index = int(self.press_height) / self.height
                    if widget_index == index:
                        font_color = ui_theme.get_color("treeItemSelectFont").get_color()
                    else:
                        font_color = ui_theme.get_color("treeItemNormalFont").get_color()
                    draw_font(cr, 
                              draw_widget.text,
                              self.font_size,
                              font_color,
                              self.font_x_padding + draw_widget.width,
                              temp_height + self.height/2, 
                              self.font_width, self.font_height, self.font_align)                   
                    
                font_w, font_h = get_content_size(draw_widget.text, self.font_size)    
                if draw_widget.tree_view_item.get_has_arrow():
                    if not draw_widget.show_child_items_bool:
                        draw_pixbuf(cr, self.normal_pixbuf.get_pixbuf(), 
                                    font_w + self.font_x_padding + draw_widget.width + self.arrow_x_padding, 
                                    temp_height + (self.height - self.normal_pixbuf.get_pixbuf().get_height()) / 2)
                    else:
                        draw_pixbuf(cr, self.press_pixbuf.get_pixbuf(), 
                                    font_w + self.font_x_padding + draw_widget.width + self.arrow_x_padding, 
                                    temp_height + (self.height - self.normal_pixbuf.get_pixbuf().get_height()) / 2)
                else:        
                    pixbuf = draw_widget.tree_view_item.get_left_image()
                    image_width = draw_widget.tree_view_item.image_width
                    image_height = draw_widget.tree_view_item.image_height
                    if (not image_width) or (not image_height):
                        image_width = self.font_size + 4
                        image_height = self.font_size + 4

                    pixbuf = pixbuf.scale_simple(image_width, image_height, gtk.gdk.INTERP_NEAREST)
                    draw_pixbuf(cr, pixbuf, 
                                int(draw_widget.tree_view_item.image_x_padding), 
                                temp_height + (self.height - self.normal_pixbuf.get_pixbuf().get_height()) / 2 + draw_widget.tree_view_item.image_y_padding)
                    
                temp_height += self.height     
               
               
    def tree_view_key_press_event(self, widget, event):
        pass
        
    def tree_view_leave_notify_event(self, widget, event):
        self.move_draw_bool = False
        self.move_index_num = None
        self.queue_draw()            
            
    def add_items(self, parent_id, child_items):
        if not isinstance(child_items, (tuple, list, set)):
            child_items = [ child_items ]
        for child_item in child_items:
            self.add_item(parent_id, child_item)
            
        self.queue_draw()    
        
    def add_item(self, parent_id, child_item):    
        temp_tree = self.create_tree(child_item)
        
        temp_child_id = self.tree_id_num

        if None == parent_id:            
            self.tree_id_list.append(self.tree_id_num)
            self.tree_list.append(temp_tree)
                        
        self.root.add_node(parent_id, temp_child_id, temp_tree)
        
        self.tree_id_num += 1        
        child_item.set_item_id(temp_child_id)
        return temp_child_id
        
    def create_tree(self, child_item):
        temp_tree = Tree()
        temp_tree.id = self.tree_id_num
        temp_tree.tree_view_item = child_item
        temp_tree.child_items = {}
        temp_tree.text = child_item.get_title()        
        return temp_tree
    
    
    def scan_item(self, item_id, node):
                
        for key in node.keys():            
            if node[key].id == item_id:                                           
                self.scan_save_item = node[key]
                break
            
            child_items = node[key].child_items
            if child_items:
                self.scan_item(item_id, child_items)                    
        return self.scan_save_item
    
    def clear_scan_save_item(self):
        self.scan_save_item = None
                        
    def del_item_index(self):
        if self.move_index_num is not None:
            self.del_item(self.tree_list[self.move_index_num].id)            
            index = int(self.press_height / self.height)
            if self.move_index_num == index:
                self.press_draw_bool = False
                self.queue_draw()
                
    def del_item_from_index(self, index):                
        item_id = self.tree_list[index].id
        self.del_item(item_id)
        
    def del_item(self, item_id):
        if item_id is not None:            
            item = self.scan_item(item_id, self.root.child_items)
            if not item:
                return
            
            item.child_items = {}
            if item.parent_item:
                del item.parent_item.child_items[item_id]
            else:
                del self.root.child_items[item_id]
        else:    
            del self.root.child_items
            del self.tree_list[:]

        self.sort()
        self.move_draw_bool = False
        self.queue_draw()
        self.clear_scan_save_item()
            
    def get_other_item(self, index):            
        other_item = []
        large_index = len(self.tree_list)
        if large_index <= index:
            return other_item
        else:
            for each_index, item in enumerate(self.tree_list):
                if each_index != index:
                    other_item.append(item.tree_view_item)
            return other_item        
            
    def get_item_from_index(self, index):    
        return self.tree_list[index].tree_view_item
    
    def get_items(self, parent_id):        
        if parent_id is not None:
            scan_results = self.scan_item(parent_id, self.root.child_items)
            self.clear_scan_save_item()
            return [item.tree_view_item for item in scan_results.child_items.values()]
        else:
            return [item.tree_view_item for item in self.root.child_items.values()]
            
    def set_text(self, item):        
        pass
    
    def get_text(self, item):
        pass
    
    def clear(self):
        del self.root.child_items
        del self.tree_list[:]
            
        self.move_draw_bool = False     
        self.queue_draw()
        
    def sort_all_nodes(self, nodes):        
        for key in nodes.keys():
            self.tree_all_node_list.append(nodes[key])
            if nodes[key].child_items:
                self.sort_all_nodes(nodes[key].child_items)
            
    def get_all_items(self):        
        self.tree_all_node_list = []
        self.sort_all_nodes(self.root.child_items)
        return self.tree_all_node_list
    
    def sort(self):               
        self.tree_list = []
        for key in self.root.child_items.keys():
            self.tree_list.append(self.root.child_items[key])
            if self.root.child_items[key].child_items:
                self.sort2(self.root.child_items[key], self.width)                                        
            
    def sort2(self, node, width):
        for key in node.child_items.keys():            
            if node.child_items[key].parent_item.show_child_items_bool:                      
                node.child_items[key].width = width
                self.tree_list.append(node.child_items[key])
                if node.child_items[key].child_items:
                    self.sort2(node.child_items[key], width + self.width)                
    
class Tree(object):
    def __init__(self):
        self.id = None
        
        self.tree_view_item = None
        self.parent_item = None
        
        self.child_items = OrderedDict()    
        self.child_items = {}
        self.text = ""
        self.show_child_items_bool = False
        
        self.has_arrow = True
        self.item_left_image = None
        
        self.width = 0
        
    
    def add_node(self, root_id, node_id, node_item):
        # Root node add child widget.
        if None == root_id:
            self.child_items[node_id] = node_item
        else:        
            for key in self.child_items.keys():
                if key == root_id:
                    node_item.parent_item = self.child_items[key] # Save parent Node.
                    self.child_items[key].child_items[node_id] = node_item
                    return True
        
                if self.scan_node(self.child_items[key], root_id, node_id, node_item):
                    return True
            
    def scan_node(self, root_node, root_id, node_id, node_item):
        if root_node.child_items:
            for key in root_node.child_items.keys():
                if key == root_id:                    
                    node_item.parent_item = root_node.child_items[key] # Save parent Node.
                    root_node.child_items[key].child_items[node_id] = node_item                
                    return True
                else:    
                    self.scan_node(root_node.child_items[key], root_id, node_id, node_item)        
                
gobject.type_register(TreeView)               

class TreeViewItem(object):    
    def __init__(self, item_title, has_arrow=True, 
                 item_left_image=None, image_x_padding=0, image_y_padding=0, image_width=0, image_height=0):
        self.item_title = item_title
        self.has_arrow = has_arrow
        self.item_left_image = item_left_image
        self.image_x_padding = image_x_padding
        self.image_y_padding = image_y_padding
        self.image_width = image_width
        self.image_height = image_height
        self.item_id = None
        
    def get_title(self):    
        return self.item_title
    
    def get_has_arrow(self):
        return self.has_arrow
    
    def get_left_image(self):
        return self.item_left_image                    
            
        
    def set_item_id(self, new_id):
        self.item_id = new_id
        
    def get_item_id(self):    
        return self.item_id
    
    
    
