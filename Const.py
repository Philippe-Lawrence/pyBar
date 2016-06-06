#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2007 Philippe LAWRENCE
#
# This file is part of pyBar.
#    pyBar is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    pyBar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pyBar; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA



# -----------------------------------------------------
#
#    CLASSES POUR LES CONSTANTES
#
#-------------------------------------------------------
import sys, os


if sys.platform == 'win32':
  PATH = os.path.join(os.environ['USERPROFILE'], 'pyBar')
  SYS = 'win32'
  #FONT = 'Arial'
  FONT_SIZE = 13
else:
  PATH = os.path.join(os.environ['HOME'], 'pyBar')
  SYS = 'linux'
  #FONT = 'Georgia'
  FONT_SIZE = 12

# pyBar version
VERSION = '3.3'
AUTHOR = 'Philippe LAWRENCE'
SOFT = 'pyBar'
CONTACT = 'philippe.lawrence@pybar.fr'
SITE_URL = "http://pybar.fr/index.php?page=logiciel-pybar"
HELP_URL = "http://pybar.fr/index.php?page=tutoriels"
DOWNLOAD_URL = "http://pybar.fr/index.php?page=download"
VERSION_URL = "http://pybar.fr/download/version"

#print "Const::VERSION_URL test"
#
# default size
#
AREA_W = 507
AREA_H = 443
AREA_MARGIN = 100
AREA_MARGIN_MIN = 50
ARROW_SIZE_MIN = 20. # float
ARROW_SIZE_MAX = 40. # float
GRAPH_SIZE_MIN = 40.
GRAPH_SIZE_MED = 100.
GRAPH_SIZE_MAX = 120.
SIGMA_SIZE_MAX = 100 # entier
DRAWING_SIZE = 150
DRAWING_SIZE_MAX = 600
DRAWING_SIZE_MED = 300

DEFO_MAX = 30. # float
SCALE = 80.
PAS = 4 # px,
# tester HOME USERPROFILE
FILEPREFS = 'pref.cfg'
DIREXEMPLES = "Fichiers pyBar"
USERDIRLIBRARY = "library"
PROFILFILELIBRARY = "section.xml"
MATFILELIBRARY = "material.xml"
XML = '<data pyBar="%s" version="%s"><elem id = "node" /><elem id = "barre" /><elem id = "geo" /><elem id = "material" /><elem id = "char" /><elem id = "combinaison" /><elem id = "prefs" /></data>'
XML_LIB = '<data pyBar="%s" version="%s" />'
DEFAULT_CASE = "cas 1"

# Arc
ARCPRECISION = 100

# attention, bien mettre des nombres flottants dans units
UNITS = { 
	'L' : {"m" : 1., 'cm' : 1e-2, 'mm': 1e-3},
	'I' : {'m<sup>4</sup>' : 1., 'cm<sup>4</sup>' : 1e-8, 'mm<sup>4</sup>' : 1e-12},
	'S' : {"m<sup>2</sup>" : 1., 'cm<sup>2</sup>' : 1e-4, 'mm<sup>2</sup>': 1e-6},
	'F' : {"N" : 1., 'daN' : 10., 'kN' : 1000.},
	'E' : {"Pa" : 1., 'MPa' : 1.e6, 'GPa' : 1.e9},
	'M' : {"kg/m<sup>3</sup>" : 1., 'kg/dm<sup>3</sup>' : 1.e3},
	'C' : {"Pa" : 1., 'kPa' : 1.e3, 'MPa' : 1.e6}
}
UNITS2 = { 
	'L' : {"in" : 0.0254},
	'I' : {'in<sup>4</sup>' : 4.16231e-7},
	'S' : {"in<sup>2</sup>" : 6.4516e-4},
	'F' : {"lbf" : 4.44822},
	'E' : {"psi" : 6894.76},
	'M' : {"lbs/in<sup>3</sup>" : 0.45359237},
	'C' : {"psi" : 6894.76}
}

G = 9.81
CONV = 1

def default_unit():
  """Retourne un dictionnaire du type 'I' : 1 """
  default = {}
  for name, di in UNITS.items():
    default[name] = 1.
  return default

# inutilisée
def default_unit_texts():
  """Retourne un dictionnaire du type 'I' : m4 
  contenant les unités par défaut"""
  default = {}
  for name, di in UNITS.items():
    for text, val in di.items():
      if val == 1.:
        default[name] = text
        break
  return default

def get_default_unit_text(key, isSI):
  """Retourne un dictionnaire du type 'I' : m4 
  contenant les unités par défaut"""
  if isSI:
    di = UNITS[key]
    for text, val in di.items():
      if val == 1.:
        return text
    print("debug in default_unit_text key=%s" % key)
    return None
  return list(UNITS2[key].keys())[0] # une seule valeur dans ce cas

# Inutilisée
# Classes pour les constantes qui évitent que les constantes puissent être 
# modifiées
class Const:

  def __init__(self): 
       Const.__items = {}
       self.area_w, self.area_h = 485, 435
       self.margin = 80
       self.defo_max = 80.
  def __getattr__(self, attr):
       try:
           return Const.__items[attr]
       except:
           return self.__dict__[attr]
  def __setattr__(self, attr, value):
       if attr in Const.__items:
           raise "Cannot reassign constant %s" % attr
       else:
           Const.__items[attr] = value
  def __str__(self):
       return '\n'.join(['%s: %s' % (str(k), str(v)) for k,v in Const.__items.items()])

