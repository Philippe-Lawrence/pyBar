#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import os
from numpy import *
from xml.etree.ElementTree import fromstring
import xml.etree.ElementTree as ET

from classRdm import *
import function

__version__='1.3'

__date__ = "2008-7-1"

def fakeReadXMLFile(file):
    """Fonction de test
    Lecture des données dans une chaines de caractères"""
    return ET.parse(file)

def fakeReadXMLString(string):
    """Fonction de test
    Lecture des données dans une chaines de caractères"""
    E = fromstring(string)
    return ET.ElementTree(E)


class fakeRdm(R_Structure) :
  """Programme de calcul RDM"""

  
  def __init__(self, xml):
    # si on n'écrit pas ici explicitement le init de la classe parent, ce dernier n'est pas exécuté
    self.struct = Structure(xml)
    structure = self.struct
    self.status = structure.status
    if self.status == -1:
      return
    self.char_error = []
    self.conv = 1
    self.Cases = self.GetCasCharge()
    self.CombiCoef = self.GetCombi()
    xmlnode = list(structure.XMLNodes["char"].iter('case'))

    KS1 = KStructure(structure) 
    self.Chars = {}
    for cas in self.Cases:
      Char = CasCharge(cas, xmlnode, structure)
      if Char.NodeDeps:
        KS = KStructure(structure, Char.NodeDeps)
      else:
        KS = KS1
      Char.KS = KS
      Char.status = KS.status
      self.Chars[cas] = Char
    self.bar_values = {}
    self.SolveCombis()



