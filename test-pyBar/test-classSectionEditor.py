#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
try:
  import gi
except:
  print("Librairie pygtk indisponible")
  sys.exit(0)
try:
  gi.require_version('Gtk', '3.0')
except:
  print("Nécessite pygtk3.0")
  sys.exit(0)
from gi.repository import Gtk, Gdk, Pango, GObject
import classSectionEditor
from file_tools import *

import classSection

class fakeW(classSectionEditor.SectionWindow):

  def __init__(self):
    super(fakeW, self).__init__("pas défini")

  def on_open(self, widget=None, path=None):
    self.path = ""
    self.modified = False
    self.s = classSection.StringAnalyser(string)
    classSectionEditor.Nodes.NODES = self.s.nodes
    classSectionEditor.Nodes.ARCS = self.s.arcs
    self.ini_box()
    GObject.idle_add(self.update_drawing)

  def on_save(self, widget):
      string = self.get_xml()
      print('<?xml version="1.0" encoding="UTF-8"?>'+string)


# exemples ats 
string="""<?xml version="1.0" encoding="UTF-8"?><xml><nodes><node d="2.6,0" id="N1" /><node d="4.1,1.8" id="N2" /><node d="-4.1,1.8" id="N3" /><node d="-2.6,0" id="N4" /><node d="0,0.8" id="N5" /><node d="1.6,0.8" id="N6" /><node d="-1.6,0.8" id="N7" /></nodes><path d="N1 N2 N3 N4" fill="true" id="C1" /><circle center="N5" fill="false" id="C2" r="0.4" /><circle center="N6" fill="false" id="C3" r="0.4" /><circle center="N7" fill="false" id="C4" r="0.4" /></xml>"""
#string="""<?xml version="1.0" encoding="UTF-8"?><xml><nodes><node d="49,0" id="N1" /><node d="49,35" id="N2" /><node d="26.5,35" id="N3" /><node d="21.5,94" id="N4" /><node d="-21.5,94" id="N5" /><node d="-26.5,35" id="N6" /><node d="-49,35" id="N7" /><node d="-49,0" id="N8" /></nodes><path d="N1 N2 N3 N4 N5 N6 N7 N8" fill="true" id="C1" /></xml>"""

#string = """<?xml version="1.0" encoding="UTF-8"?><xml><nodes><node d="0,0" id="N1" /><node d="1,0" id="N2" /><node d="1,1" id="N3" /><node d="0,1" id="N4" /></nodes><circle center="N1" point="N2" fill="true" id="C2" /><circle center="N1" r="0.5" fill="true" id="C3" /><path d="N1 N2 N3 N4" fill="true" id="C1" /></xml>"""




if __name__ == "__main__":

  try:
    app = fakeW()
    app.window.connect("delete-event", app.on_destroy_main)
    Gtk.main()
  except KeyboardInterrupt:
    sys.exit(0)


