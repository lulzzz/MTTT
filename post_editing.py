# !/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# PyKeylogger: TTT for Linux and Windows
# Copyright (C) 2016 Roxana Lafuente <roxana.lafuente@gmail.com>
#                    Miguel Lemos <miguelemosreverte@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
gi.require_version('WebKit', '3.0')
from gi.repository import WebKit
import json
import os
import sys
import urlparse
import time
import itertools
from table import Table
from statistics import html_injector

class PostEditing:

    def __init__(self, post_editing_source, post_editing_reference, notebook, grid):
        self.post_editing_source = post_editing_source
        self.post_editing_reference = post_editing_reference
        self.translation_tab_grid = grid
        self.notebook = notebook
        self.modified_references =  []
        self.saved_modified_references = []

        self.tables = {}
        self.paulaslog = {}

        self.saved_absolute_path = os.path.abspath("saved")
        self.statistics_absolute_path = os.path.abspath("statistics")
        filename = post_editing_source[post_editing_source.rfind('/'):]
        filename_without_extension = os.path.splitext(filename)[0]
        filename_extension = os.path.splitext(filename)[1]
        self.saved_origin_filepath = os.path.abspath("saved") + filename
        self.saved_reference_filepath = os.path.abspath("saved") + filename_without_extension + "_modified" + filename_extension


        self.tables["translation_table"] =  Table("translation_table",self.post_editing_source,self.post_editing_reference, self._saveChangedFromPostEditing_event,self._saveChangedFromPostEditing,self.translation_tab_grid)

        self.paulas_log_filepath = self.saved_absolute_path + '/paulaslog.json'
        self.old_html_filepath = self.statistics_absolute_path + '/index.html'
        #TODO remove the following line, it destroys the last session saved logs
        #suggestion: load the last session saved logs, save it as old, and then do delete it.

        if os.path.exists(self.paulas_log_filepath):
          os.remove(self.paulas_log_filepath)
        if os.path.exists(self.old_html_filepath):
          os.remove(self.old_html_filepath)

    def calculateStatistics(self):
        seconds_spent_by_segment = {}
        percentaje_spent_by_segment = {}
        total_time_spent = 0
        #again with the closure, lets see how it plays out.
        def pairwise(iterable):
            a, b = itertools.tee(iterable)
            next(b, None)
            return itertools.izip(a, b)

        #calculate time spent by segment
        for current_timestamp,next_timestamp in pairwise(sorted(self.paulaslog.keys())):
            #for current_timestamp,next_timestamp in sorted(self.paulaslog.keys()):
            delta = (int(next_timestamp) - int(current_timestamp))/1000
            for segment_index in self.paulaslog[current_timestamp]:
                if segment_index in seconds_spent_by_segment:
                    seconds_spent_by_segment[segment_index] += delta
                else:
                    seconds_spent_by_segment[segment_index] = delta
        #calculate total time spent
        for a in seconds_spent_by_segment:
            total_time_spent += seconds_spent_by_segment[a]
        #calculate percentajes
        for a in seconds_spent_by_segment:
            percentaje_spent_by_segment[a] = float(seconds_spent_by_segment[a]) *100 / float(total_time_spent)

        pie_as_json_string_list = []
        table_data_list = []
        for a in percentaje_spent_by_segment:
            string = '{label: "' + str(a) + '", data: ' + str(percentaje_spent_by_segment[a]) + '}'
            pie_as_json_string_list.append(string)
            string = "<tr><td>"+str(a)+"</td>"
            string += "<td>"+str(0)+"</td>"
            string += "<td>"+str(0)+"</td>"
            string += "<td>"+str(percentaje_spent_by_segment[a])+"</td></tr>"
            table_data_list.append(string)
        pie_as_json_string = ','.join(pie_as_json_string_list)
        table_data = ''.join(table_data_list)
        if table_data and pie_as_json_string:
            html_injector.inject_into_html(pie_as_json_string, table_data)
            self.addStatistics()
            
    def addStatistics(self):
        self.notebook.remove_page(6)
        html = "<h1>This is HTML content</h1><p>I am displaying this in python</p"
        win = Gtk.Window()
        view = WebKit.WebView()
        view.open(html)
        uri = "statistics" + '/index.html'
        uri = os.path.realpath(uri)
        uri = urlparse.ParseResult('file', '', uri, '', '', '')
        uri = urlparse.urlunparse(uri)
        view.load_uri(uri)
        win.add(view)
        childWidget = win.get_child()
        win.remove(childWidget)
        win.destroy()

        self.notebook.insert_page(childWidget, Gtk.Label('Git Statistics'), 6)
        self.notebook.show_all()

    def addDifferencesTab(self):
        self.preparation = Gtk.VBox()
        self.notebook.remove_page(5)
        self.preparation.pack_start(self.diff_tab_grid, expand =True, fill =True, padding =0)
        self.notebook.insert_page(self.preparation, Gtk.Label('Differences'), 5)
        self.notebook.show_all()


    def save_not_using_git(self):
        #lets see how using closure is seen by the team... here's hope it plays out!
        def savefile(text, filename):
            text_file = open(filename, "w")
            text_file.write(text)
            text_file.close()
        savefile('\n'.join(self.tables["translation_table"].tables_content[self.tables["translation_table"].source_text_lines]), self.saved_origin_filepath)
        savefile('\n'.join(self.tables["translation_table"].tables_content[self.tables["translation_table"].reference_text_lines]),self.saved_reference_filepath)

    def load_paulas_log(self):
        anonymousjsonlog = {}
        try:
            with open(self.paulas_log_filepath) as json_data:
                anonymousjsonlog= json.load(json_data)
        except: open(self.paulas_log_filepath, 'w').close()
        return anonymousjsonlog

    def save_using_paulas_version_of_a_version_control_system(self):
        #self.paulaslog = self.load_paulas_log()

        for index in range(0, len(self.tables["translation_table"].tables_content[1])):
            if index in self.tables["translation_table"].translation_reference_text_TextViews_modified_flag:
                modified_reference = self.tables["translation_table"].translation_reference_text_TextViews_modified_flag[index]
                if modified_reference not in self.saved_modified_references:
                    self.saved_modified_references.append(modified_reference)
                    if self.last_change_timestamp not in self.paulaslog:
                        self.paulaslog[self.last_change_timestamp] = {}
                    self.paulaslog[self.last_change_timestamp][index] = modified_reference
        with open(self.paulas_log_filepath, 'w') as outfile:
            json.dump(self.paulaslog, outfile)


    def _saveChangedFromPostEditing(self):
        self.last_change_timestamp = int(time.time() * 1000)
        #reconstruct all cells from the table of the target column
        for index in range(0, len(self.tables["translation_table"].tables_content[1])):
            if index in self.tables["translation_table"].translation_reference_text_TextViews_modified_flag:
                self.modified_references.append(self.tables["translation_table"].translation_reference_text_TextViews_modified_flag[index])
            else:
                self.modified_references.append(self.tables["translation_table"].tables_content[1][index])

        self.save_not_using_git()
        string = self.post_editing_reference

        self.diff_tab_grid = Gtk.Grid()
        self.diff_tab_grid.set_row_spacing(1)
        self.diff_tab_grid.set_column_spacing(20)
        self.tables["diff_table"] =  Table("diff_table",self.post_editing_source,self.post_editing_reference, self._saveChangedFromPostEditing_event,self._saveChangedFromPostEditing, self.diff_tab_grid)
        self.addDifferencesTab()

        self.save_using_paulas_version_of_a_version_control_system()
        self.calculateStatistics()


        self.tables["translation_table"].save_post_editing_changes_button.hide()


    def _saveChangedFromPostEditing_event(self, button):
        self._saveChangedFromPostEditing()
