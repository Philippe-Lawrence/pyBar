#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
try:
  import gi
except:
  print "Librairie pygtk indisponible"
  sys.exit(0)
try:
  gi.require_version('Gtk', '3.0')
except:
  print "Nécessite pygtk2.0"
  sys.exit(0)
from gi.repository import Gtk
#print Gtk.pygtk_version
#print Gtk.gtk_version
import Gtk.glade
#from gi.repository import Pango
import classResuParBarre
#from file import *
import classRdm
import Const
#import classProfilManager
#import classPrefs
#import classCMenu
from gi.repository import GObject
#import function
#from time import sleep
from xml.dom import minidom
#from fakeclassRdm import fakeRdm

string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.3">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="10,0" id="N2" liaison="2"/>
		<node d="22,0" id="N3" liaison="2"/>
		<node d="30,0" id="N4" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre d="N1,N2,0,0" id="B1"/>
		<barre d="N2,N3,0,0" id="B2"/>
		<barre d="N3,N4,0,0" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.14" id="*" igz="6.05e-06" profil="UPN 140" s="0.00204" v="0.07"/>
	</elem>
	<elem id="material">
		<barre id="B2,B3" mv="3000.0" young="200000000000.0"/>
		<barre id="B1" mv="7800.0" young="210000000000.0"/>
	</elem>
	<elem id="char">
		<case id="CP">
			<barre id="B2" qu="0,,0.0,-10000.0"/>
		</case>
		<case id="Q1">
			<barre fp="%50,0.0,10000.0,0.0" id="B1"/>
		</case>
		<case id="Q2">
			<barre id="B2" qu="0,,0.0,-10000.0"/>
		</case>
		<case id="Q3">
			<barre id="B3" qu="0,,0.0,-10000.0"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.35,0.0,0.0,1.5" id="1,35G+1,5Q3"/>
		<combinaison d="1.35,0.0,1.5,0.0" id="1,35G+1,5Q2"/>
		<combinaison d="1.35,1.5,0.0,0.0" id="1,35G+1,5Q1"/>
		<combinaison d="1.0,1.0,1.0,1.0" id="G+Q1+Q2+Q3"/>
		<combinaison d="1.35,1.5,1.5,1.5" id="1,35G+1,5Q1+1,5Q2+1,5Q3"/>
		<combinaison d="1.35,1.5,0.0,1.5" id="1,35G+1,5Q1+1,5Q3"/>
	</elem>
	<elem id="units">
		<unit d="1000000.0" id="C"/>
		<unit d="1000000000.0" id="E"/>
		<unit d="1000.0" id="F"/>
		<unit d="1e-08" id="I"/>
		<unit d="1000.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="0.0001" id="S"/>
	</elem>
</data>"""

def fakeReadXMLFile(string):
    """Fonction de test
    Lecture des données dans une chaines de caractères"""
    return minidom.parseString(string)


class ResuTest(classResuParBarre.ResuParBarre):

  def __init__(self, parent, barre, n_case):
    self.parent = parent
    #tab = parent.active_tab
    #self.drawing = tab.active_drawing
    #id_study = self.drawing.id_study
    #study = parent.studies[id_study]
    self.rdm = parent.rdm
    self.unit_conv = Const.default_unit()
    self.status = 4

    self.Char = self.rdm.GetCharByNumber(n_case)
    self.barre = barre
    self.xml = Gtk.glade.XML("glade/pyBar.glade", "window3")
    self.window3 = self.xml.get_widget("window3")
    self._ini_window()
    self.combobox = self.xml.get_widget("w3_comboboxentry1") 
    self._combobox_regen()
    self.combo_barre_active()
    self.xml.signal_autoconnect({
	"on_w3_button1_clicked" : self._destroy, 
	"on_w3_button2_clicked" : self._export, 
	"on_w3_combobox_changed" : self._barre_changed,# executé au constructeur
	"on_window3_destroy" : self._window_destroy, 
	"on_w3_checkbutton1" : self._change_unit,
        "on_w3_configure_event" : self._configure_event
	#"on_w3_spinbutton1" : self._get_point_value
		})
    self.area = self.xml.get_widget("w3_drawingarea")
    #self.w, self.h = 300, 300
    #self.area.set_size_request(300, 300)
    self.area.connect("expose-event", self._expose_event)
    style = self.area.get_style()
    self.gc = style.fg_gc[Gtk.StateType.NORMAL]
    self._chart = classResuParBarre.SigmaDraw(self.area)

    # connexion du bouton 
    button = self.xml.get_widget("spinbutton1")
    button.connect('changed', self._get_point_value)
    self._get_point_value()
    #self.do_calculate()

  def _get_point_value(self, widget=None, export=True):
    """Lance le calcul des sollicitations en un point d'une barre
    Dessine un point sur la barre dans la fenetre w1"""

    u = self.do_calculate()




class fakeRdm(classRdm.R_Structure) :
  """Programme de calcul RDM"""
  
  def __init__(self, xml):
    # si on n'écrit pas ici explicitement le init de la classe parent, ce dernier n'est pas exécuté
    #self.struct = classRdm.StructureFile("exemples/portique-simple2.dat")
    #self.struct = classRdm.StructureFile("exemples/barre-affaissement-appui.dat")
    xml = fakeReadXMLFile(string)
    self.struct = classRdm.Structure(xml)
    self.XMLNodes = self.struct.XMLNodes
    self.struct.file = "test_file"
    self.struct.name = "test_name"
    self.char_error = []

    self.Cases = self.GetCasCharge()
    self.CombiCoef = self.GetCombi()
    xmlnode = self.struct.XMLNodes["char"].getElementsByTagName('case')
    self.Chars = {}
    for cas in self.Cases:
      Char = classRdm.CasCharge(cas, xmlnode, self.struct)
      self.Chars[cas] = Char
    self.BGCalculate()

class Main(object):

  def __init__(self, rdm):
    self.rdm = rdm

def main():
    Gtk.main()
    return 0

if __name__ == "__main__":
  rdm = fakeRdm(string)
  parent = Main(rdm)
  try:
    MyApp = ResuTest(parent, "B1", 0)
    #MyApp.record_button.connect("clicked", MyApp.get_xml_structure, 0)
    main()
  except KeyboardInterrupt:
    sys.exit(0)


