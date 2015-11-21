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
    self.conv = 1
    self.char_error = []
    Noeuds={}
    Barres={}
    L = {}
    A = {}

    angle = math.pi/2
    xa, ya = 1.4142, 0
    xc, yc = 0.7071, -0.7071
    r = ((xa-xc)**2+(ya-yc)**2)**0.5
    print "r=", r
    teta0 = -function.AngleSegment((xc, yc), (xa, ya))
    print  'teta', teta0  

    n=100
    teta = teta0
    for i in range(n+1):
      node = i
      #node = "N%d" % i
      x = xc+r*math.cos(teta)
      y = yc+r*math.sin(teta)
      teta += angle/n
      Noeuds[node] = (x, y)
      if i == 0:
        prec = node
        x_prec = x
        y_prec = y
        continue
      barre = i
      #barre = "B%d" % i
      Barres[barre] = (prec,node,0,0)
      A[barre] = math.atan((y-y_prec)/(x-x_prec)) # revoir avec teta
      L[barre] = ((x-x_prec)**2+(y-y_prec)**2)**0.5 
      prec = node
      x_prec = x
      y_prec = y
    print Noeuds[0]
    print Noeuds[50]
    print Noeuds[100]

    self.struct.Liaisons = {0: 1, 100: 1}
    self.struct.Nodes = Noeuds
    self.struct.Barres = Barres
    self.struct._GetBarreByNode()

    self.struct.Angles = A
    self.struct.Lengths = L
    self.struct._RelaxNode()
    self.struct._MakeLiDDL()
    matK = self.struct.MatriceK()
    self.struct.InvMatK = numpy.linalg.inv(matK)


    self.Cases = self.GetCasCharge()
    self.CombiCoef = self.GetCombi()
    xmlnode = self.struct.XMLNodes["char"].getElementsByTagName('case')
    self.Chars = {}
    for cas in self.Cases:
      Char = CasCharge(cas, xmlnode, self.struct)
      self.Chars[cas] = Char
    self.Chars['cas 1'].charNode = {50: (0, -1000, 0)}
    self.SolveCombis()


def test():
  string="<data version='1.15'><elem id=\"node\"><node d=\"0,0\" id=\"N0\" liaison=\"1\"/><node d=\"1.,0\" id=\"N2\" liaison=\"2\"/></elem><elem id=\"barre\"><barre d=\"N0,N2,0,0\" id=\"B1\"/></elem><elem id=\"geo\"><barre s=\"1\" igz=\"1\" id=\"*\"/></elem><elem id=\"material\"><barre young=\"200000000.0\" id=\"*\"/></elem><elem id=\"char\"><case id=\"cas 1\"></case></elem><elem id=\"combinaison\"><combinaison d=\"1.0\" id=\"combi1\"/></elem></data>"
  rdm = fakeRdm(string)


  print rdm.Chars['cas 1'].Reactions
  #print "terminé", rdm.valid
test()
#cProfile.run('test()')
