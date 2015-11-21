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
import classEditor
from file_tools import *
#import classDrawing
import classRdm
import Const
import classProfilManager
import classPrefs
import classCMenu
import function
from time import sleep
from xml.etree.ElementTree import fromstring, ElementTree, tostring

class fakeW1(object):

  def update_from_editor(self, widget=None):
    ed = self.Editor
    if not ed.data_editor.is_changed:
      print("Pas de modif")
      return
    if not ed.xml_status == -1:
      ed.data_editor.set_xml_structure()
    root = ed.data_editor.XML.getroot()
    function.indent(root)
    print(tostring(root).decode())
    ed.data_editor.is_changed = False
    ed.update_editor_title(False)

  def update_drawing(self, page=None):
    print("update_drawing")

class EditorTest(classEditor.Editor):

  def __init__(self, study, w1app):
    super(EditorTest, self).__init__(study, w1app)

    #self.w1app = w1app


  def destroy_editor(self, widget, event):
    Gtk.main_quit()




def fakeReadXMLFile(string):
    """Fonction de test
    Lecture des données dans une chaines de caractères"""
    E = fromstring(string)
    return ElementTree(E)

string = """<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.0">
  <elem id="node">
    <node d="0,0" id="N1" liaison="0" />
    <node d="@N1,3&lt;4" id="N2" />
    <node d="@N1,7.5&lt;45" id="N3" />
    <node d="@N3,4.5&lt;-45" id="N4" />
    <node d="@N4,3&lt;-45" id="N5" liaison="0" />
  </elem>
  <elem id="barre">
    <barre end="N2" id="B1" r0="0" r1="0" start="N1" />
    <barre end="N3" id="B2" r0="0" r1="0" start="N2" />
    <barre end="N4" id="B3" r0="0" r1="0" start="N3" />
    <barre end="N5" id="B4" r0="0" r1="0" start="N4" />
    <barre end="N4" id="B5" r0="0" k0="1000" k1="5" start="N2" />
    <rot_elast barre="B5" kz="1000" node="N4" />
  </elem>
  <elem id="geo">
    <barre h="0.4" id="B5" igz="0.0001" profil="" s="0.0091" v="0.2" />
    <barre h="0.3" id="B1,B2,B3,B4" igz="0.00045" profil="" s="0.06" v="0.15" />
    <barre id="Parabole6" igz="2" s="1" />
  </elem>
  <elem id="material">
    <barre id="*" mv="1000" young="10000000000" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <barre id="B2" qu="@,%0.30,%0.60,0.0,-100.0" />
      <barre fp="1,0.0,10.0,10.0" id="B3" />
      <barre id="B2" tri="@,%0,%1,-10.0,-20.0,90.0" />
      <barre fp="1,1,0,0" id="B1" />
    </case>
    <case id="cas 2">
      <node d="&gt;,-1000.0,30.0,0.0" id="N3" />
      <barre id="B1" qu="@,%0,%10,0.0,-700.0" />
      <barre id="B4" qu="0.3,2,-600.0,0.0" />
    </case>
  </elem>
  <elem id="combinaison">
    <combinaison d="1.0,1.0" id="Combi 1" />
    <combinaison d="0.8,2.0" id="combi 2" />
  </elem>
  <elem id="prefs">
    <unit d="1.0" id="C" />
    <unit d="1.0" id="E" />
    <unit d="1.0" id="F" />
    <unit d="1.0" id="I" />
    <unit d="1.0" id="M" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="S" />
    <const g="9.81" />
    <conv conv="1.0" />
  </elem>
  <draw id="prefs">
    <drawing axis="false" bar_name="true" node_name="true" scale="31.4" scale_pos="83.0,62.0,63,25" show_title="true" status="7,3" title="173.0,249.0,154,25,charpente2" values="{3:{0:{'N5':{1:{0:(18.26406871192853,2.0,False)}}}}}" x0="83.0" y0="280.0" />
  </draw>
</data>"""
string2 = """<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.24">
  <elem id="node">
    <node d="0,0" id="N1" />
    <node d="4.17&lt;16.7" id="N2" liaison="2" />
    <arc d="0.148" id="N3" liaison="1" name="B1" pos_on_curve="true" r="0" />
  </elem>
  <elem id="barre">
    <mbarre end="N2" id="B1" r0="0" r1="0" start="N1" />
  </elem>
  <elem id="geo">
    <barre id="*" igz="2.25e-5" profil="" s="0.012" />
  </elem>
  <elem id="material">
    <barre id="*" mv="800" young="11" />
  </elem>
  <elem id="char">
    <case id="pp">
      <pp d="true" />
      <barre id="B1" qu=",,0,-266.8" />
    </case>
    <case id="q">
      <barre id="B1" qu=",,0,-870" />
    </case>
  </elem>
  <elem id="combinaison">
    <combinaison d="1.0,1.0" id="Combinaison 1" />
  </elem>
  <elem id="prefs">
    <unit d="1.0" id="C" />
    <unit d="1000000000.0" id="E" />
    <unit d="1.0" id="F" />
    <unit d="1.0" id="I" />
    <unit d="1.0" id="M" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="S" />
    <const g="9.81" />
    <conv conv="1.0" />
  </elem>
  <draw id="prefs">
    <drawing axis="false" bar_name="true" node_name="false" scale="111.163415682" scale_pos="48.0,24.0,63,25" show_title="true" status="0" title="142.0,148.0,174,23,extension" x0="92.0" y0="234.0" />
  </draw>
</data>"""
string2 = """<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.33">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="10,0" id="N2" liaison="2" />
    <node d="20,0" id="N3" liaison="2" />
    <node d="30,0" id="N4" liaison="2" />
  </elem>
  <elem id="barre">
    <arc center="N2" end="N3" id="arc1" r0="0" r1="0" start="N1" />
    <barre d="N1,N2,0,0" id="B1" />
    <barre d="N2,N3,0,0" id="B2" />
    <barre start="N3" end="N4" r0="1" r1="1" id="B3" mode="1" />
  </elem>
  <elem id="geo">
    <barre h="0.16" id="*" igz="9.25e-06" profil="UPN 160" s="0.0024" v="0.08" />
    <barre id="B1" igz="9.25e-06" profil="UPN 200" s="0.0024" />
  </elem>
  <elem id="material">
    <barre id="B2,B3" profil='acier' mv="3000" young="200000000000" alpha='1' />
    <barre id="B1" mv="6000" young="210000000000" />
    <barre id="arc1" mv="6000" young="210000000000" />
  </elem>
  <elem id="char">
    <case id="CP">
      <barre id="*" pp="true" />
      <node d="0.0,10.0,0.0" id="N4" />
	<barre fp="%50,0,-10,0" id="B2"/>
	<barre fp="%50,0,-10,0" id="B1"/>
    </case>
    <case id="Q1">
      <barre id="B1" qu="0,,0.0,-10000.0" />
    </case>
    <case id="Q2">
      <barre id="B2" qu="0,,0.0,-10000.0" />
    </case>
    <case id="Q3">
      <barre id="B3" qu="0,,0.0,-10000.0" />
    </case>
  </elem>
  <elem id="combinaison">
    <combinaison d="1.35,1.5,0.0,0.0" id="1,35G+1,5Q1" />
    <!--<combinaison d="1.35,1.5,1.5,1.5" id="1,35G+1,5Q1+1,5Q2+1,5Q3" />
    <combinaison d="1.35,1.5,0.0,1.5" id="1,35G+1,5Q1+1,5Q3" /> -->
    <combinaison d="1.35,0.0,1.5,0.0" id="1,35G+1,5Q2" /> 
    <combinaison d="1.35,0.0,0.0,1.5" id="1,35G+1,5Q3" />
    <combinaison d="1.0,1.0,1.0,1.0" id="G+Q1+Q2+Q3" /> 
  </elem>
  <elem id="prefs">
    <unit d="1.0" id="C" />
    <unit d="1.0" id="E" />
    <unit d="1.0" id="F" />
    <unit d="1.0" id="I" />
    <unit d="1.0" id="M" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="S" />
    <const g="9.81" />
    <conv conv="1.0" />
  </elem>
  <draw id="prefs">
    <drawing axis="false" bar_name="false" node_name="true" scale="12.4" scale_pos="56.0,213.0,70,25" show_title="true" status="1" title="150.0,238.0,153,25,poutre4appuis" x0="100.0" y0="278.0" />
  </draw>
</data>
"""


class fakeEmptyRdm(classRdm.EmptyRdm) :
  """Programme de calcul RDM"""
  
  def __init__(self):
    self.XMLNodes = None
    self.name = 'test'

  def GetUnits(self, UP=None):
    return Const.default_unit()

class fakeRdm(classRdm.R_Structure):
  """Programme de calcul RDM"""
  
  def __init__(self, xml):
    # si on n'écrit pas ici explicitement le init de la classe parent, ce dernier n'est pas exécuté
    #self.struct = classRdm.StructureFile("exemples/portique-simple2.dat")
    #self.struct = classRdm.StructureFile("exemples/barre-affaissement-appui.dat")
    xml = fakeReadXMLFile(xml)
    self.struct = classRdm.Structure(xml)
    self.XMLNodes = self.struct.XMLNodes
    self.struct.file = "test_file"
    self.struct.name = "Nouvelle étude"
    self.char_error = []
    self.conv = self.GetConv()


    self.Cases = self.GetCasCharge()
    self.CombiCoef = self.GetCombi()
    xmlnode = self.struct.XMLNodes["char"].getiterator('case')
    self.Chars = {}
    for cas in self.Cases:
      Char = classRdm.CasCharge(cas, xmlnode, self.struct)
      self.Chars[cas] = Char
    self.SolveCombis()

class fakeEmptyStudy(object):
  def __init__(self):
    string = '<data pyBar="http://open.btp.free.fr/?/pyBar" version="%s"><elem id = "node"><node d="0,0" id="N1" /></elem><elem id = "barre"></elem><elem id = "geo"></elem><elem id = "material"></elem><elem id = "char"></elem><elem id = "combinaison"></elem><elem id = "prefs"></elem></data>' % Const.VERSION
    xml = ElementTree(fromstring(string))

    rdm = classRdm.EmptyRdm(xml)
    rdm.SetStructName() # revoir

    self.rdm = rdm
    self.id = 0

class fakeStudy(object):
  def __init__(self):
    rdm = fakeRdm(string)
    self.rdm = rdm
    self.id = 0

def main():
    Gtk.main()
    return 0

if __name__ == "__main__":

  study = fakeStudy()
  #study = fakeEmptyStudy()
  try:
    for error in study.rdm.struct.errors:
      print(error[0])
  except AttributeError:
      pass
  try:
    w1app = fakeW1()
    MyApp = EditorTest(study, w1app)
    w1app.Editor = MyApp
    MyApp.w2.connect("delete-event", MyApp.destroy_editor)
    #MyApp.record_button.connect("clicked", MyApp.test)
    main()
  except KeyboardInterrupt:
    sys.exit(0)


