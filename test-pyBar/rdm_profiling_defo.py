#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cProfile
import math
import os
from numpy import *
from xml.dom import minidom
from classRdm import *
import function

def fakeReadXMLFile(string):
    """Fonction de test
    Lecture des données dans une chaines de caractères"""
    return minidom.parseString(string)

class fakeRdm(R_Structure) :
  """Programme de calcul RDM"""

  
  def __init__(self, string):
    # si on n'écrit pas ici explicitement le init de la classe parent, ce dernier n'est pas exécuté
    xml = fakeReadXMLFile(string)
    self.struct = Structure(xml)

    Noeuds={}
    Barres={}
    L = {}
    A = {}
    n=100
    for i in range(n+1):
      node = "N%d" % i
      Noeuds[node] = (float(i)/n,0.)
      if i == 0: 
        prec = node
        continue
      barre = "B%d" % i
      Barres[barre] = (prec,node,0,0)
      A[barre] = 0.
      L[barre] = float(i)/n
      prec = node

    self.struct.Nodes = Noeuds
    self.struct.Barres = Barres
    self.struct.Angles = A
    self.struct.Lengths = L
    self.struct._RelaxNode()
    self.struct._MakeLiDDL()
    matK = self.struct.MatriceK()
    self.struct.InvMatK = numpy.linalg.inv(matK)



    #rdm = classRdm.R_Structure(struct)
    self.Cases = self.GetCasCharge()
    self.CombiCoef = self.GetCombi()
    xmlnode = self.struct.XMLNodes["char"].getElementsByTagName('case')
    self.Chars = {}
    for cas in self.Cases:
      Char = CasCharge(cas, xmlnode, self.struct)
      self.Chars[cas] = Char
    self.SolveCombis()

def test():
  string="<data version='1.15'><elem id=\"node\"><node d=\"0,0\" id=\"N0\" liaison=\"1\"/><node d=\"1.,0\" id=\"N2\" liaison=\"2\"/></elem><elem id=\"barre\"><barre d=\"N0,N2,0,0\" id=\"B1\"/></elem><elem id=\"geo\"><barre s=\"1e-3\" igz=\"1e-8\" id=\"*\"/></elem><elem id=\"material\"><barre young=\"200000000.0\" id=\"*\"/></elem><elem id=\"char\"><case id=\"cas 1\"><barre id=\"B1\" fp=\"%50,0.0,1.0,1.0\"/></case></elem><elem id=\"combinaison\"><combinaison d=\"1.0\" id=\"combi1\"/></elem></data>"
  rdm = fakeRdm(string)

  for barre in rdm.struct.Barres:
    rdm.DefoBarre(barre, 100, 'cas 1', False)
  print "terminé temps initial = 0,711s"
  print "terminé temps dernier test = 0,475s"
cProfile.run('test()')
