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

if __name__ == "__main__":
    unittest.main()


