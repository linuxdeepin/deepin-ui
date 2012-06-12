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

from constant import WIDGET_POS_TOP_LEFT, WIDGET_POS_TOP_RIGHT, WIDGET_POS_TOP_CENTER, WIDGET_POS_BOTTOM_LEFT, WIDGET_POS_BOTTOM_CENTER, WIDGET_POS_BOTTOM_RIGHT, WIDGET_POS_LEFT_CENTER, WIDGET_POS_RIGHT_CENTER, WIDGET_POS_CENTER, DEFAULT_FONT, COLOR_NAME_DICT, BLACK_COLOR_MAPPED, WHITE_COLOR_MAPPED, COLOR_SEQUENCE
from contextlib import contextmanager 
import cairo
import gtk
import math
import gobject
import os
import pango
import pangocairo
import subprocess
import time

def tree_view_get_toplevel_node_count(treeview):
    '''Get toplevel node count.'''
    model = treeview.get_model()
    if model != None:
        return model.iter_n_children(None)
    else:
        return 0
    
def tree_view_get_selected_path(treeview):
    '''Get selected path.'''
    selection = treeview.get_selection()
    (_, tree_paths) = selection.get_selected_rows()
    if len(tree_paths) != 0:
        return (tree_paths[0])[0]
    else:
        return None
 
def tree_view_focus_first_toplevel_node(treeview):
    '''Focus first toplevel node.'''
    treeview.set_cursor((0))
    
def tree_view_focus_last_toplevel_node(treeview):
    '''Focus last toplevel node.'''
    node_count = tree_view_get_toplevel_node_count(treeview)
    if node_count > 0:
        path = (node_count - 1)
    else:
        path = (0)
    treeview.set_cursor(path)
    
def tree_view_scroll_vertical(treeview, scroll_up=True):
    '''Scroll tree view vertical.'''
    # Init.
    scroll_num = 9
    candidate_count = tree_view_get_toplevel_node_count(treeview)
    cursor = treeview.get_cursor()
    (path, column) = cursor
    max_candidate = candidate_count - 1
    
    # Get candidate at cursor.
    if path == None:
        current_candidate = max_candidate
    else:
        (current_candidate,) = path
        
    # Set cursor to new candidate.
    if scroll_up:
        new_candidate = max(0, current_candidate - scroll_num)
    else:
        new_candidate = min(current_candidate + scroll_num, max_candidate)
        
    treeview.set_cursor((new_candidate))
    
def tree_view_focus_next_toplevel_node(treeview):
    '''Focus next toplevel node.'''
    selected_path = tree_view_get_selected_path(treeview)
    if selected_path != None:
        node_count = tree_view_get_toplevel_node_count(treeview)
        if selected_path < node_count - 1:
            treeview.set_cursor((selected_path + 1))

def tree_view_focus_prev_toplevel_node(treeview):
    '''Focus previous toplevel node.'''
    selected_path = tree_view_get_selected_path(treeview)
    if selected_path != None:
        if selected_path > 0:
            treeview.set_cursor((selected_path - 1))

def get_entry_text(entry):
    '''Get entry text.'''
    return entry.get_text().split(" ")[0]

def set_cursor(widget, cursor_type=None):
    '''Set cursor.'''
    if cursor_type == None:
        widget.window.set_cursor(None)
    else:
        widget.window.set_cursor(gtk.gdk.Cursor(cursor_type))
    
    return False

def set_clickable_cursor(widget):
    '''Set clickable cursor.'''
    set_hover_cursor(widget, gtk.gdk.HAND2)

def set_hover_cursor(widget, cursor_type):
    '''Set cursor of hover event'''
    widget.connect("enter-notify-event", lambda w, e: set_cursor(w, cursor_type))
    widget.connect("leave-notify-event", lambda w, e: set_cursor(w))

def get_widget_root_coordinate(widget, pos_type=WIDGET_POS_BOTTOM_CENTER):
    '''Get widget's root coordinate.'''
    # Get coordinate.
    (wx, wy) = widget.window.get_origin()
    toplevel_window = widget.get_toplevel()
    if toplevel_window:
        (x, y) = widget.translate_coordinates(toplevel_window, wx, wy)
    else:
        (x, y) = (wx, wy)
        
    # Get offset.
    rect = widget.allocation
    if pos_type == WIDGET_POS_TOP_LEFT:
        offset_x = 0
        offset_y = 0
    elif pos_type == WIDGET_POS_TOP_RIGHT:
        offset_x = rect.width
        offset_y = 0
    elif pos_type == WIDGET_POS_TOP_CENTER:
        offset_x = rect.width / 2
        offset_y = 0
    elif pos_type == WIDGET_POS_BOTTOM_LEFT:
        offset_x = 0
        offset_y = rect.height
    elif pos_type == WIDGET_POS_BOTTOM_RIGHT:
        offset_x = rect.width
        offset_y = rect.height
    elif pos_type == WIDGET_POS_BOTTOM_CENTER:
        offset_x = rect.width / 2
        offset_y = rect.height
    elif pos_type == WIDGET_POS_LEFT_CENTER:
        offset_x = 0
        offset_y = rect.height / 2
    elif pos_type == WIDGET_POS_RIGHT_CENTER:
        offset_x = rect.width
        offset_y = rect.height / 2
    elif pos_type == WIDGET_POS_CENTER:
        offset_x = rect.width / 2
        offset_y = rect.height / 2
        
    return (x + offset_x, y + offset_y)

def get_event_root_coords(event):
    '''Get event root coordinates.'''
    (rx, ry) = event.get_root_coords()
    return (int(rx), int(ry))

def get_event_coords(event):
    '''Get event coordinates.'''
    (rx, ry) = event.get_coords()
    return (int(rx), int(ry))

def propagate_expose(widget, event):
    '''Propagate expose to children.'''
    if "get_child" in dir(widget) and widget.get_child() != None:
        widget.propagate_expose(widget.get_child(), event)
        
def move_window(widget, event, window):
    '''Move window.'''
    window.begin_move_drag(
        event.button, 
        int(event.x_root), 
        int(event.y_root), 
        event.time)
    
    return False
    
def resize_window(widget, event, window, edge):
    '''Resize window.'''
    window.begin_resize_drag(
        edge,
        event.button,
        int(event.x_root),
        int(event.y_root),
        event.time)
        
    return False

def add_in_scrolled_window(scrolled_window, widget, shadow_type=gtk.SHADOW_NONE):
    '''Like add_with_viewport in ScrolledWindow, with shadow type.'''
    scrolled_window.add_with_viewport(widget)
    viewport = scrolled_window.get_child()
    if viewport != None:
        viewport.set_shadow_type(shadow_type)
    else:
        print "add_in_scrolled_window: Impossible, no viewport widget in ScrolledWindow!"

def is_single_click(event):
    '''Whether an event is single click.'''
    return event.button == 1 and event.type == gtk.gdk.BUTTON_PRESS
        
def is_double_click(event):
    '''Whether an event is double click?'''
    return event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS

def is_left_button(event):
    '''Whether event is left button.'''
    return event.button == 1

def is_right_button(event):
    '''Whehter event is right button.'''
    return event.button == 3

def is_middle_button(event):
    '''Whehter event is middle button.'''
    return event.button == 2

def foreach_container(w, callback):
    '''docs'''
    callback(w)
    
    if isinstance(w, gtk.Container): 
        foreach_recursive(w, callback)

def foreach_recursive(container, callback):
    '''Callback for all childs.'''
    container.foreach(lambda w: foreach_container(w, callback))

def container_remove_all(container):
    '''Remove all child widgets from container.'''
    container.foreach(lambda widget: container.remove(widget))
    
def get_screen_size(widget):
    '''Get widget's screen size.'''
    screen = widget.get_screen()
    width = screen.get_width()
    height = screen.get_height()
    return (width, height)

def is_in_rect((cx, cy), (x, y, w, h)):
    '''Whether coordinate in rectangle.'''
    return (cx >= x and cx <= x + w and cy >= y and cy <= y + h)

def scroll_to_top(scrolled_window):
    '''Scroll scrolled window to top.'''
    scrolled_window.get_vadjustment().set_value(0)
    
def scroll_to_bottom(scrolled_window):
    '''Scroll scrolled window to bottom.'''
    vadjust = scrolled_window.get_vadjustment()
    vadjust.set_value(vadjust.get_upper() - vadjust.get_page_size())

def get_content_size(text, size):
    '''Get size of text, in pixel.'''
    if text:
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0) # don't need give size
        cr = cairo.Context(surface)
        context = pangocairo.CairoContext(cr)
        layout = context.create_layout()
        layout.set_font_description(pango.FontDescription("%s %s" % (DEFAULT_FONT, size)))
        layout.set_text(text)
        
        return layout.get_pixel_size()
    else:
        return (0, 0)
    
def create_directory(directory, remove_first=False):
    '''Create directory.'''
    if remove_first and os.path.exists(directory):
        remove_directory(directory)
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
def remove_file(path):
    '''Remove file.'''
    if os.path.exists(path):
        os.remove(path)
        
def remove_directory(path):
    """equivalent to command `rm -rf path`"""
    for i in os.listdir(path):
        full_path = os.path.join(path, i)
        if os.path.isdir(full_path):
            remove_directory(full_path)
        else:
            os.remove(full_path)
    os.rmdir(path)        

def touch_file(filepath):
    '''Touch file.'''
    # Create directory first.
    dir = os.path.dirname(filepath)
    if not os.path.exists(dir):
        os.makedirs(dir)
        
    # Touch file.
    open(filepath, "w").close()

def read_file(filepath, check_exists=False):
    '''Read file.'''
    if check_exists and not os.path.exists(filepath):
        return ""
    else:
        r_file = open(filepath, "r")
        content = r_file.read()
        r_file.close()
        
        return content

def read_first_line(filepath, check_exists=False):
    '''Read first line.'''
    if check_exists and not os.path.exists(filepath):
        return ""
    else:
        r_file = open(filepath, "r")
        content = r_file.readline().split("\n")[0]
        r_file.close()
        
        return content

def eval_file(filepath, check_exists=False):
    '''Eval file content.'''
    if check_exists and not os.path.exists(filepath):
        return None
    else:
        try:
            read_file = open(filepath, "r")
            content = eval(read_file.read())
            read_file.close()
            
            return content
        except Exception, e:
            print e
            
            return None

def write_file(filepath, content):
    '''Write file.'''
    f = open(filepath, "w")
    f.write(content)
    f.close()

def kill_process(proc):
    '''Kill process.'''
    try:
        if proc != None:
            proc.kill()
    except Exception, e:
        print "kill_process got error: %s" % (e)
    
def get_command_output_first_line(commands):
    '''Run command and return result.'''
    process = subprocess.Popen(commands, stdout=subprocess.PIPE)
    process.wait()
    return process.stdout.readline()

def get_command_output(commands):
    '''Run command and return result.'''
    process = subprocess.Popen(commands, stdout=subprocess.PIPE)
    process.wait()
    return process.stdout.readlines()
    
def run_command(command):
    '''Run command.'''
    subprocess.Popen("nohup %s > /dev/null 2>&1" % (command), shell=True)
    
def get_os_version():
    '''Get OS version.'''
    version_infos = get_command_output_first_line(["lsb_release", "-i"]).split()
    
    if len(version_infos) > 0:
        return version_infos[-1]
    else:
        return ""

def get_current_time():
    '''Get current time.'''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

def add_in_list(e_list, element):
    '''Add element in list.'''
    if not element in e_list:
        e_list.append(element)
        
def remove_from_list(e_list, element):
    '''Remove element from list.'''
    if element in e_list:
        e_list.remove(element)
        
def sort_alpha(e_list):
    '''Get alpha list.'''
    return sorted(e_list, key=lambda e: e)

def get_dir_size(dirname):
    '''Get directory size.'''
    total_size = 0
    for root, dirs, files in os.walk(dirname):
        for filepath in files:
            total_size += os.path.getsize(os.path.join(root, filepath))
            
    return total_size

def print_env():
    '''Print environment variable.'''
    for param in os.environ.keys():
        print "*** %20s %s" % (param,os.environ[param])                

def print_exec_time(func):
    '''Print execute time.'''
    def wrap(*a, **kw):
        start_time = time.time()
        ret = func(*a, **kw)
        print "%s time: %s" % (str(func), time.time() - start_time)
        return ret
    return wrap

def get_font_families():
    '''Get all font families in system.'''
    fontmap = pangocairo.cairo_font_map_get_default()
    return map (lambda f: f.get_name(), fontmap.list_families())

def format_file_size(bytes, precision=2):
    '''Returns a humanized string for a given amount of bytes'''
    bytes = int(bytes)
    if bytes is 0:
        return '0B'
    else:
        log = math.floor(math.log(bytes, 1024))
        quotient = 1024 ** log
        size = bytes / quotient
        remainder = bytes % quotient
        if remainder < 10 ** (-precision): 
            prec = 0
        else:
            prec = precision
        return "%.*f%s" % (prec,
                           size,
                           ['B', 'KB', 'MB', 'GB', 'TB','PB', 'EB', 'ZB', 'YB']
                           [int(log)])

def add_color_stop_rgba(pat, pos, color_info):
    '''ADd color stop RGBA.'''
    # Pick color.
    (color, alpha) = color_info
    (r, g, b) = color_hex_to_cairo(color)
    
    pat.add_color_stop_rgba(pos, r, g, b, alpha) 
    
def alpha_color_hex_to_cairo((color, alpha)):
    '''Alpha color hext to cairo color.'''
    (r, g, b) = color_hex_to_cairo(color)
    return (r, g, b, alpha)

def color_hex_to_rgb(color):
    '''Convert hex RGB to (r, g, b)'''
    if color[0] == '#': 
        color = color[1:] 
    return (int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)) 
    
def color_hex_to_cairo(color):
    """ 
    Convert a html (hex) RGB value to cairo color. 
     
    @type color: html color string 
    @param color: The color to convert. 
    @return: A color in cairo format. 
    """ 
    if color[0] == '#': 
        color = color[1:] 
    (r, g, b) = (int(color[:2], 16), 
                 int(color[2:4], 16),  
                 int(color[4:], 16)) 
    return color_rgb_to_cairo((r, g, b)) 

def color_rgb_to_hex(rgb_color):
    '''Convert (r, g, b) to hex color.'''
    return "#%02X%02X%02X" % rgb_color

def color_rgb_to_cairo(color): 
    """ 
    Convert a 8 bit RGB value to cairo color. 
     
    @type color: a triple of integers between 0 and 255 
    @param color: The color to convert. 
    @return: A color in cairo format. 
    """ 
    return (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0) 

def get_match_parent(widget, matchType):
    '''Get parent widget match given type, otherwise return None.'''
    parent = widget.get_parent()
    if parent == None:
        return None
    elif type(parent).__name__ == matchType:
        return parent
    else:
        return get_match_parent(parent, matchType)
        
def widget_fix_cycle_destroy_bug(widget):
    '''Fix bug that PyGtk destroys cycle too early.'''
    # This code to fix PyGtk bug <<Pygtk destroys cycle too early>>, 
    # The cycle is wrongly freed 
    # by Python's GC because Pygobject does not tell Python that the widget's 
    # wrapper object is referenced by the underlying GObject.  As you have 
    # found, in order to break the cycle Python zeros out the callback 
    # closure's captured free variables, which is what causes the "referenced 
    # before assignment" exception. 
    # detail see: https://bugzilla.gnome.org/show_bug.cgi?id=546802 .
    # 
    # Otherwise, will got error : "NameError: free variable 'self' referenced before assignment in enclosing scope".
    widget.__dict__

def map_value(value_list, get_value_callback):
    '''Map value.'''
    if value_list == None:
        return []
    else:
        return map(get_value_callback, value_list)

def get_same_level_widgets(widget):
    '''Get widget match given type, those widget at same level with widget argument.'''
    parent = widget.get_parent()
    if parent == None:
        return []
    else:
        return filter(lambda w:type(w).__name__ == type(widget).__name__, parent.get_children())

def mix_list_max(list_a, list_b):
    '''Mix max item in two list.'''
    if list_a == []:
        return list_b
    elif list_b == []:
        return list_a
    elif len(list_a) == len(list_b):
        result = []
        for (index, item_a) in enumerate(list_a):
            if item_a > list_b[index]:
                result.append(item_a)
            else:
                result.append(list_b[index])
        
        return result        
    else:
        print "mix_list_max: two list's length not same."
        return []

def unzip(unzip_list):
    '''Unzip [(1, 'a'), (2, 'b'), (3, 'c')] to ([1, 2, 3], ['a', 'b', 'c']).'''
    first_list, second_list = zip(*unzip_list)
    return (list(first_list), list(second_list))

def is_seriate_list(test_list):
    '''Whether is seriate list.'''
    for (index, item) in enumerate(test_list):
        if item != test_list[0] + index:
            return False
    
    return True

def get_disperse_index(disperse_list, value):
    '''Get index in disperse list.'''
    for (index, _) in enumerate(disperse_list):
        start_value = sum(disperse_list[0:index])
        end_value = sum(disperse_list[0:index + 1])
        if start_value <= value < end_value:
            return (index, value - start_value)
        
    # Return last one.
    return (last_index(disperse_list), disperse_list[-1])

def window_is_max(widget):
    '''Whether window is maximized status.'''
    toplevel_window = widget.get_toplevel()
    if toplevel_window.window.get_state() == gtk.gdk.WINDOW_STATE_MAXIMIZED:
        return True
    else:
        return False
    
def last_index(test_list):
    '''Return last index of list.'''
    return len(test_list) - 1

@contextmanager
def cairo_state(cr):
    '''Protected cairo context state for operate cairo safety.'''
    cr.save()
    try:  
        yield  
    except Exception, e:  
        print 'with an cairo error %s' % e  
    else:  
        cr.restore()

@contextmanager
def cairo_disable_antialias(cr):
    '''Disable cairo antialias temporary.'''
    # Save antialias.
    antialias = cr.get_antialias()
    
    cr.set_antialias(cairo.ANTIALIAS_NONE)
    try:  
        yield  
    except Exception, e:  
        print 'with an cairo error %s' % e  
    else:  
        # Restore antialias.
        cr.set_antialias(antialias)

@contextmanager
def exec_time():
    '''Print execute time.'''
    start_time = time.time()
    try:  
        yield  
    except Exception, e:  
        print 'exec_time error %s' % e  
    else:  
        print "time: %f" % (time.time() - start_time)

def remove_callback_id(callback_id):
    '''Remove callback id.'''
    if callback_id:
        gobject.source_remove(callback_id)
        callback_id = None

def print_callback_args(*args):
    '''Print callback arguments.'''
    print "******************"
    print args

def enable_shadow(widget):
    '''Return True if widget support composited.'''
    return widget.is_composited()

def rgb2hsb(r_value, g_value, b_value):
    "Convert color from RGB to HSB format, detail look http://zh.wikipedia.org/wiki/HSL%E5%92%8CHSV%E8%89%B2%E5%BD%A9%E7%A9%BA%E9%97%B4."
    r = r_value
    g = g_value
    b = b_value

    max_v = max(r, g, b)
    min_v = min(r, g, b)
    
    h = 0.0

    if max_v == min_v:
        h = 0
    elif max_v == r and g >= b:
        h = 60 * (g - b) / (max_v - min_v)
    elif max_v == r and g < b:
        h = 60 * (g - b) / (max_v - min_v) + 360
    elif max_v == g:
        h = 60 * (b - r) / (max_v - min_v) + 120
    elif max_v == b:
        h = 60 * (r - g) / (max_v - min_v) + 240
    
    if max_v == 0:
        s = 0.0
    else:
        s = 1.0 - min_v / max_v

    b = max_v
    
    return (h, s, b)

def find_similar_color(search_color):
    '''Find simliar color match search_color, detail look hsb(hsv).png in current directory.'''
    (search_h, search_s, search_b) = rgb2hsb(*color_hex_to_cairo(search_color))
    hsb_colors = map(lambda name: (name, rgb2hsb(*color_hex_to_cairo(COLOR_NAME_DICT[name]))), COLOR_SEQUENCE)
    
    similar_color_name = None
    similar_color_value = None
    # Return black color if brightness (height) < 0.3
    if search_b < 0.3:
        similar_color_name = BLACK_COLOR_MAPPED
    # Return white color if saturation (radius) < 0.05
    elif search_s < 0.05:
        similar_color_name = WHITE_COLOR_MAPPED
    # Otherwise find nearest color in hsb color space.
    else:
        min_color_distance = None
        for (color_name, (h, s, b)) in hsb_colors:
            color_distance = abs(h - search_h)
            if min_color_distance == None or color_distance < min_color_distance:
                min_color_distance = color_distance
                similar_color_name = color_name

    similar_color_value = COLOR_NAME_DICT[similar_color_name]
    return (similar_color_name, similar_color_value)

def end_with_suffixs(filepath, suffixs):
    '''File endswith given suffixs.'''
    for suffix in suffixs:
        if filepath.endswith(suffix):
            return True
        
    return False    

def place_center(refer_window, place_window):
    '''Place place_window in center of refer_window.'''
    (center_x, center_y) = get_widget_root_coordinate(refer_window, WIDGET_POS_CENTER)
    place_window.move(
        center_x - place_window.allocation.width / 2,
        center_y - place_window.allocation.height / 2
        )

def get_pixbuf_support_foramts():
    '''Get formats that support by pixbuf.'''
    support_formats = []
    for support_format in gtk.gdk.pixbuf_get_formats():
        support_formats += support_format.get("extensions")
        
    return support_formats    

def get_parent_dir(filepath, level=1):
    '''Get parent dir.'''
    parent_dir = os.path.realpath(filepath)
    
    while(level > 0):
        parent_dir = os.path.dirname(parent_dir)
        level -= 1
    
    return parent_dir

def gdkcolor_to_string(gdkcolor):
    '''Gdk color to string '''
    return "#%0.2X%0.2X%0.2X" % (gdkcolor.red / 256, gdkcolor.green / 256, gdkcolor.blue / 256)

def is_long(string):
    '''Is long.'''
    if string == "":
        return True
    
    try:
        long(string)
        return True
    except ValueError:
        return False

def is_int(string):
    '''Is int.'''
    if string == "":
        return True
    
    try:
        int(string)
        return True
    except ValueError:
        return False

def is_float(string):
    '''Is float.'''
    if string == "":
        return True
    
    try:
        float(string)
        return True
    except ValueError:
        return False

def is_hex_color(string):
    '''Is hex color'''
    HEX_CHAR = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                "a", "b", "c", "d", "e", "f",
                "A", "B", "C", "D", "E", "F",
                "#"
                ]
    
    if string == "":
        return True
    else:
        for c in string:
            if not c in HEX_CHAR:
                return False
            
        if string.startswith("#"):
            if len(string) > 7:
                return False
            else:
                return True
        else:            
            if len(string) > 6:
                return False
            else:
                return True    

def run_with_profile(func, sort='time', amount=20):  
  import hotshot    
  import hotshot.stats  
  prof = hotshot.Profile("tmp_prof.txt", 1)    
  prof.runcall(func)   
  prof.close()    
  print "----------------------parsing profile data---------------------"
  p = hotshot.stats.load("tmp_prof.txt")   
  p.sort_stats(sort).print_stats(amount)
