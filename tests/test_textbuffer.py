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

import unittest
import sys
import gtk

from common import srcDir

sys.path.insert(0, srcDir)

from textbuffer import TextIter, TextBuffer

class TextIterTest(unittest.TestCase):
    def setUp(self):
        self.__iter = TextIter(text = u"开始test\ntextiter\nline3\nline4")

    def tearDown(self):
        pass

    def testGetChar(self):
        self.assertEqual(self.__iter.get_char(), u"开")

    def testForwardChar(self):
        self.__iter.forward_char()
        self.assertEqual(self.__iter.get_char(), u"始")

        for x in range(0, 5):
            self.__iter.forward_char()
        self.assertEqual(self.__iter.get_char(), u"\n") # point to line end

        self.__iter.forward_char()
        self.assertEqual(self.__iter.get_char(), u"t") # to next line

    def testGetSlice(self):
        end = TextIter(text = u"开始test\ntextiter\nline3\nline4", line_number = 1, line_offset = 4)
        self.assertEqual(self.__iter.get_slice(end), u"开始test\ntext")

    def testGetSliceReverse(self):
        end = TextIter(text = u"开始test\ntextiter\nline3\nline4", line_number = 0, line_offset = 0)
        self.__iter.set_line(1)
        self.__iter.set_line_offset(4)
        self.assertEqual(self.__iter.get_slice(end), u"开始test\ntext")

class TextBufferTest(unittest.TestCase):
    def setUp(self):
        self.__buf = TextBuffer(text = u"开始test\ntextiter\nline3\nline4")

    def tearDown(self):
        pass

    def testGetLineCount(self):
        self.assertEqual(self.__buf.get_line_count(), 4)

    def testGetCharCount(self):
        self.assertEqual(self.__buf.get_char_count(), len(u"开始test\ntextiter\nline3\nline4"))

    def testGetText(self):
        self.assertEqual(self.__buf.get_text(), u"开始test\ntextiter\nline3\nline4")

    def testSetText(self):
        self.__buf.set_text(u"new\ntext")
        self.assertEqual(self.__buf.get_text(), u"new\ntext")

    def testGetIterAtCursor(self):
        self.assertEqual(self.__buf.get_iter_at_cursor().get_char(), u"开")

    def testInsertText(self):
        self.__buf.insert_text(self.__buf.get_iter_at_cursor(), u"newtextatstart")
        self.assertEqual(self.__buf.get_line_count(), 4)
        self.assertEqual(self.__buf.get_text(), u"newtextatstart开始test\ntextiter\nline3\nline4")

    def testInsertTextWithNewLine(self):
        ir = self.__buf.get_iter_at_cursor()
        self.__buf.insert_text(ir, u"newline1\nline0\nnotnewline")
        self.assertEqual(self.__buf.get_line_count(), 6)
        self.assertEqual(self.__buf.get_text(), u"newline1\nline0\nnotnewline开始test\ntextiter\nline3\nline4")
        self.assertEqual(ir.get_line_offset(), 10)

    def testGetIterAtLine(self):
        ir = self.__buf.get_iter_at_line(1)
        self.assertEqual(ir.get_line(), 1) # check line number
        self.assertEqual(ir.get_line_offset(), 0) # check line offset

    def testDelete(self):
        start = self.__buf.get_iter_at_line(0)
        end = self.__buf.get_iter_at_line(2)
        start.set_line_offset(1)
        end.set_line_offset(2)
        self.__buf.delete(start, end)
        self.assertEqual(self.__buf.get_text(), u"开ne3\nline4") # check text
        self.assertEqual(self.__buf.get_line_count(), 2) # check line count
        self.assertEqual(start.get_line_offset(), end.get_line_offset()) # start and end should point to the same place

    def testGetIterAtOffset(self):
        ir = self.__buf.get_iter_at_offset(17)
        self.assertEqual(ir.get_line(), 2)
        self.assertEqual(ir.get_line_offset(), 1)

        ir = self.__buf.get_iter_at_offset(16)
        self.assertEqual(ir.get_line(), 2)
        self.assertEqual(ir.get_line_offset(), 0)

        ir = self.__buf.get_iter_at_offset(15)
        self.assertEqual(ir.get_line(), 1)
        self.assertEqual(ir.get_line_offset(), 8)


    def testBackspace(self):
        ir = self.__buf.get_iter_at_line(1)
        ir.set_line_offset(1)
        original_count = ir.get_chars_in_line()
        self.__buf.backspace(ir)
        self.assertEqual(self.__buf.get_text(), u"开始test\nextiter\nline3\nline4")
        self.assertEqual(ir.get_char(), u"e")
        self.assertEqual(ir.get_line_offset(), 0) # check line offset
        self.__buf.backspace(ir)
        self.assertEqual(ir.get_line(), 0) # join the lines
        self.assertEqual(ir.get_line_offset(), 6) # should be at line end
        self.assertEqual(self.__buf.get_text(), u"开始testextiter\nline3\nline4") # join lines
        self.assertEqual(self.__buf.get_line_count(), 3) # one line less

    def testSelection(self):
        ir = self.__buf.get_iter_at_offset(0)
        ir2 = self.__buf.get_iter_at_offset(8)
        self.__buf.select_text(ir, ir2)

        ir, ir2 = self.__buf.get_selection()

        self.assertEqual(ir.get_offset(), 0)
        self.assertEqual(ir2.get_offset(), 8)
        self.assertEqual(ir2.get_char(), u"e")
        self.assertEqual(self.__buf.get_has_selection(), True)

        self.__buf.delete_selection()
        self.assertEqual(self.__buf.get_has_selection(), False) # should deselect
        self.assertEqual(self.__buf.get_line_count(), 3) # three lines left
        self.assertEqual(self.__buf.get_text(), u"extiter\nline3\nline4")
        self.assertEqual(ir.is_valid(), False) # should be invalid due to deletion

    def testCursor(self):
        ir = self.__buf.get_iter_at_offset(8)

        self.__buf.place_cursor(ir)

        ir = self.__buf.get_iter_at_cursor()

        self.assertEqual(ir.get_offset(), 8)
        self.assertEqual(ir.get_char(), u"e")

    def testPasteAndCut(self):
        ir = self.__buf.get_iter_at_offset(0)
        ir2 = self.__buf.get_iter_at_offset(8)

        self.__buf.select_text(ir, ir2)
        self.__buf.place_cursor(ir)

        clipboard = gtk.Clipboard()
        self.__buf.cut_clipboard(clipboard)
        self.__buf.paste_clipboard(clipboard)

        self.assertEqual(self.__buf.get_text(), u"开始test\ntextiter\nline3\nline4")
        self.assertEqual(self.__buf.get_iter_at_cursor().get_offset(), 8) # cursor should be moved


if __name__ == "__main__":
    unittest.main()

