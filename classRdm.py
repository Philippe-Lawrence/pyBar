#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Copyright 2007 Philippe LAWRENCE
#
# This file is part of pyBar.
#    pyBar is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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

# ------------- CLASSE DE CALCUL RDM --------------------

import math
import os
import numpy
import xml.etree.ElementTree as ET
import function
import Const
import copy
import classPrefs

def Rotation(a, x, y):
  """x, y étant les coordonnées d'un point dans un repère 1, retourne les coordonnées du point dans le repère 2 obtenu par rotation d'angle a"""
  x1 = x*math.cos(a) + y*math.sin(a)
  y1 = -x*math.sin(a) + y*math.cos(a)
  return x1, y1


def SumList(li1, li2):
  #assert len(li1) == len(li2)
  return [li1[i]+li2[i] for i in range(len(li1))]


  # Retourne la somme des produits li1[i]*li2[i]
def ListScalaire(li1, li2): 
    if len(li1) != len(li2): # inutile ralenti
      print("Rdm::ListScalaire erreur, taille de liste différente")
    resu = 0
    for i in range(len(li1)):
      resu = resu+li1[i]*li2[i]
    return resu

  # Retourne les composantes d'un vecteur données dans (u,v)
  # dans le repère (X,Y)
  # (u,v) étant obtenu par rotation d'angle téta par rapport à (X,Y)
  # du repère local vers le repère global par exemple

def get_control_points(pt1, pt2, pt3):
    """Retourne les 3 points de controles de la courbe de Bézier à partir des 3 points d'une parabole (les points sont donnés dans le format (x0, soll0) x0 en m par rapport à l'origine de la barre)
    Cairo : dessiner EN COORDONNÉES RELATIVES (rel_curve_to)
    pt1 : origine sur la barre
    pt2 : intermédiaire
    pt3 : fin"""
    x1, y1 = pt1
    tx, ty = pt1 # sauvegarde origine
    x2, y2 = pt2
    x3, y3 = pt3
    h31 = (y3-y1)/(x3-x1)
    h21 = (y2-y1)/(x2-x1)
    if abs(h31 - h21) < 1e-5:
      #Points alignés, on ne pas trace pas de Bezier
      return ((x3-tx, y3-ty), )

    a = (h31-h21)/(x3-x2) # y = ax2+bx+c
    b = h21 - a*(x2+x1)
    c = y1 - a*x1*x1 - b*x1
    x0 = -b/2/a # apex
    y0 = c - b**2/4/a
    #print("parabole apex=", x0, y0, a, b, c)
    tx, ty = x0-tx, y0-ty

    # coordonnées des controles par rapport à M0(x0, y0)
    x1 -= x0
    y1 -= y0
    x3 -= x0
    y3 -= y0
    C1x = 1./3*(2*x1+x3)
    C1y = a*x1/3*(x1+2*x3)
    C2x = 1./3*(x1+2*x3)
    C2y = a*x3/3*(2*x1+x3)
    return  (x3+tx, y3+ty), (C1x+tx, C1y+ty), (C2x+tx, C2y+ty), (0., a, b, c)

def ProjL2G(vec, teta):
    """Effectue un changement de repère du vecteur vec selon une rotation de téta"""
    x = vec[0]*math.cos(teta)-vec[1]*math.sin(teta)
    y = vec[0]*math.sin(teta)+vec[1]*math.cos(teta)
    vec[0], vec[1] = x, y

def ProjL2GCoors(x0, y0, teta):
    """Effectue un changement de repère du vecteur vec selon une rotation de téta"""
    x = x0*math.cos(teta)-y0*math.sin(teta)
    y = x0*math.sin(teta)+y0*math.cos(teta)
    return x, y



  # Retourne les composantes d'un vecteur après changement de repère
  # du repère global vers le repère local

def ProjG2LCoors(x0, y0, teta):
    x = x0*math.cos(teta)+y0*math.sin(teta)
    y = -x0*math.sin(teta)+y0*math.cos(teta)
    return x, y

def ProjG2L(vec, teta):
    u = vec[0]*math.cos(teta)+vec[1]*math.sin(teta)
    v = -vec[0]*math.sin(teta)+vec[1]*math.cos(teta)
    vec[0], vec[1] = u, v

    return
    if len(vec) == 2:
      return [u, v]
    elif len(vec) == 3:
      return [u, v, vec[2]]
    return [u, v, vec[2], vec[3]]

class Error(Exception):
  """Base class for exceptions in this module."""
  pass

class XMLError(Error):
  """Exception raised for errors in the input.
  Attributes:
      expr -- input expression in which the error occurred
      msg  -- explanation of the error
  """

  def __init__(self, msg):
    self.msg = msg
    print(self.msg)

# prévoir ici d'autres type d'erreurs

class UserNode(object):

  def __init__(self, name, u, r):
    self.name = name
    self.u = u
    self.r = r # relaxation

class BarreNode(UserNode):
  """Classe conteneur des points sur une barre à noeuds multiples"""

  def __init__(self, name, u, r):
    UserNode.__init__(self, name, u, r)

class ParabolaNode(UserNode):
  """Classe conteneur des points sur un arcs"""

  def __init__(self, name, u, r):
    UserNode.__init__(self, name, u, r)

class ArcNode(UserNode):
  """Classe conteneur des points sur un arcs"""

  def __init__(self, name, a, on_curve, u, r):
    UserNode.__init__(self, name, u, r)
    self.a = a # angle par rapport au centre de l'arc
    self.on_curve = on_curve # XXX ne sert à rien

class CurvedStruct(object):
  """Classe parent pour les arcs et paraboles"""

  def __init__(self):
    pass

  def set_nodes(self, user_nodes):
    """Crée les attributs des points utilisateur sur la courbe"""
    self.user_nodes = user_nodes

  def set_bars_end(self, b0=None, b1=None):
    """Crée les attributs b0, b1"""
    if not b0 is None:
      self.b0 = b0
    if not b1 is None:
      self.b1 = b1

  def get_curve_abs(self, b, u, lengths):
    """Retourne la longueur sur l'arc d'un point donné par la barre et la position relative sur la barre"""
    l = lengths[b]*u
    return self.pos[b]+l

  def get_bar_and_pos(self, u):
    """Retourne la barre et la longueur sur la barre à partir de la longueur depuis le début de l'arc"""
    if u < 0.:
      u = 0
    pos = 0.
    for b in self.pos: # vérifier que l'ordre est bon
      s = self.pos[b]
      if s > u:
        s0 = self.pos[b-1]
        lbarre = s - s0
        pos = (u - s0)/lbarre
        break
    assert b-1 >= self.b0
    if pos < 0:
      pos = 0.
    elif pos > 1:
      pos = 1.
    return b-1, pos
      

class Parabola(CurvedStruct):
  """Classe pour les paraboles"""

  def __init__(self, f, l, a):
    self.f = f # flèche
    self.l = l # corde
    self.a = a # angle

  def draw(self, cr, struct):
    """Dessine la structure courbe dans la cairo context"""
    nodes = self.user_nodes
    start = nodes[0].name
    end = nodes[-1].name
    a = self.a
    u0, v0 = struct.Nodes[start]
    u2, v2 = struct.Nodes[end]
    u1, v1 = self.l/2, self.f
    li = get_control_points((0., 0.), (u1, v1) , (self.l, 0.))
    if cr is None:
      print(li)
      return # debug
    cr.move_to(u0, -v0)
    x, y = li[0]
    if len(li) == 1:
      c1x, c1y = x/3, -y/3
      c2x, c2y = 2*x/3, -2*y/3
      self.coefs = (0, 0)
    else:
      c1x, c1y = li[1]
      c2x, c2y = li[2]
      self.coefs = li[3][1:3]
    if not a == 0:
      x, y = Rotation(-a, x, y)
      c1x, c1y = Rotation(-a, c1x, c1y)
      c2x, c2y = Rotation(-a, c2x, c2y)
    cr.rel_curve_to(c1x, -c1y, c2x, -c2y, x, -y)
    cr.stroke()
    self.bezier = (c1x, -c1y, c2x, -c2y)


  def set_user_nodes(self, data, start, end, rel0, rel1, struct):
    """Crée les points intermédiaires sur la parabole"""
    di = {}
    Node = ParabolaNode(start, 0., rel0)
    self.user_nodes = [Node]
    #data.sort(function.compare2)
    x0, y0 = struct.Nodes[start]
    a = self.a
    for u, name, on_curve, r in data:
      Node = ParabolaNode(name, u, r)
      self.user_nodes.append(Node)
      v = 4*self.f*u*(1-u)
      u = u*self.l
      if not a == 0:
        u, v = Rotation(-a, u, v)
      x = u+x0
      y = v+y0
      di[name] = (x, y)
    Node = ParabolaNode(end, 1., rel1)
    self.user_nodes.append(Node)
    struct.Nodes.update(di)
    #return di

  def get_angle(self):
    """Retourne l'angle de la corde de l'arc"""
    return self.a

# finir si None
  def get_size(self, lengths=None):
    """Retourne la longueur de la parabole"""
    try:
      return self.l0
    except AttributeError:  
      l = 0
      for i in range(self.b0, self.b1+1):
        l += lengths[i]
    self.l0 = l
    return l
    

  def get_segments(self, n):
    """Retourne une liste des nombres de segments entre les points sur une courbe et """
    pos = [i.u for i in self.user_nodes]
    xprec = 0.
    segments, pas = [], []
    for x in pos[1:]: # on enlève les extrémités
      # 2 barres mini par tronçon
      n_seg = max(2, int(round((x-xprec)*n)))
      segments.append(n_seg)
      pas.append((x-xprec)/n_seg*self.l)
      xprec = x
    return segments, pas

class Arc(CurvedStruct):
  """Classe pour les arcs"""

  def __init__(self, center, r, teta1, teta2, l):
    self.l = l # longueur de l'arc
    self.c = center
    self.r = r
    self.teta1 = teta1
    self.teta2 = teta2


  def draw(self, cr, struct):
    """Dessine la structure courbe dans le cairo context"""
    Centers = struct.Centers
    center, r, teta1, teta2 = self.c, self.r, self.teta1, self.teta2
    if teta1 == teta2: # cercle complet
      teta2 -= 6.283
    xc, yc = Centers[center]
    cr.arc(xc, -yc, r, -teta1, -teta2)
    cr.stroke()

  def get_size(self, lengths=None):
    """Retourne la longueur de l'arc"""
    return self.l

  def get_angle(self):
    """Retourne l'angle de la corde de l'arc"""
    dteta = self.teta1-self.teta2
    if dteta <= 0:
      dteta += 2*math.pi
    return dteta

class SuperBar(object):

  def __init__(self, l, a):
    self.l = l # length
    self.a = a # angle

  def get_angle(self):
    """Retourne l'angle de la barre multiple"""
    return self.a

  def get_size(self, lengths=None):
    """Retourne la longueur de la barre multiple"""
    return self.l

  def set_end_bars(self, b0, b1):
    """Crée les attributs pour la barre origine et la barre de fin"""
    self.b0 = b0
    self.b1 = b1

  def set_user_nodes(self, data, start, end, rel0, rel1, struct):
    """Crée les points intermédiaires pour une super barre"""
    Node = BarreNode(start, 0., rel0)
    self.user_nodes = [Node]
    #data.sort(function.compare2)
    x0, y0 = struct.Nodes[start]
    x1, y1 = struct.Nodes[end]
    dx, dy = x1-x0, y1-y0
    for tu in data:
      alpha, node, on_curve, rel = tu
      Node = BarreNode(node, alpha, rel)
      self.user_nodes.append(Node)
      struct.Nodes[node] = (x0+dx*alpha, y0+dy*alpha)
    Node = BarreNode(end, 1., rel1)
    self.user_nodes.append(Node)

  def draw(self, cr, struct):
    """Dessine la structure courbe dans le cairo context"""
    N0 = self.user_nodes[0].name
    N1 = self.user_nodes[-1].name
    x0, y0 = struct.Nodes[N0]
    x1, y1 = struct.Nodes[N1]
    cr.move_to(x0, -y0)
    cr.line_to(x1, -y1)
    cr.stroke()

class EmptyKStructure(object):

  def __init__(self, struct, NodeDeps={}):
    self.struct = struct
    self.NodeDeps = NodeDeps
    self.status = 0

class KStructure(object):
  """Contient les matrices de rigidité"""

  CODES_DDL = {
		0: (0, 0, 0), 
		1: (0, 0, 1),
		2: (0, 1, 0),
		3: (0, 1, 1),
		4: (1, 0, 0),
		5: (1, 0, 1),
		6: (1, 1, 0),
		7: (1, 1, 1),
		8: (0, 0, 0, 1),
		11: (0, 0, 1, 1),
		111: (0, 1, 1, 1),
		1011: (1, 0, 1, 1),
		1111: (1, 1, 1, 1)
		}

  def __init__(self, struct, NodeDeps={}):
    #print("init KStructure")
    self.struct = struct
    self.NodeDeps = NodeDeps
    self.status = 0

    MatK = self.GetInvMatK()
    if not MatK is None:
      self.status = 1
      self.InvMatK = MatK

  def GetInvMatK(self):
    #print("GetInvMatK status=", self.status)
    struct = self.struct
    if struct.status == 1:
      matK = self.MatriceK()
      if matK.size == 0:
        return matK
      det = numpy.linalg.slogdet(matK)[1] # evite un overflow
      trace = numpy.trace(matK)
      trace = math.log(trace)
      if abs(det/trace < 1):
        struct.PrintError("Matrice non inversible\nLe système présente trop de degré de liberté \nou ne peut être résolu selon l'hypothèse des petits déplacements", 0)
        #print("non inversible debug")
        return None # tester
      try:
        return numpy.linalg.inv(matK)
      except numpy.linalg.linalg.LinAlgError:
        struct.PrintError("Singular matrix", 0)
        return None

  def MatriceK(self):
    """Crée la liste des ddl et la matrice de rigidité"""
    #print("MatriceK")
    struct = self.struct
    self._MakeLiDDL()
    size = self.n_ddl
    if size == 0:
      return numpy.empty(0)
    # initialisation rigidity matrix
    matK = numpy.zeros((size, size))
    noeuds = struct.Nodes
    codeDDL = self.codeDDL
    raideurs = struct.RaideurAppui
    RotuleElast = struct.RotuleElast
    for noeud0 in noeuds:
      code0 = codeDDL[noeud0][0]
      ddls0 = self.CODES_DDL[code0]
      pos0 = self.get_ddl_pos(noeud0)
      if pos0 == None:
        continue

      row = pos0
      # appuis élastiques
      if noeud0 in raideurs:
        self._add_elastic(matK, row, ddls0, raideurs[noeud0])

      beamStart, beamEnd = struct.BarByNode[noeud0]
      if ddls0[0] == 1: 
        # projection suivant X
        self._projX(matK, noeud0, beamStart, beamEnd, row, ddls0, code0)
        row += 1
      if ddls0[1] == 1: 
        # projection suivant Y
        self._projY(matK, beamStart, beamEnd, row, pos0, ddls0, code0)
        row += 1
      if ddls0[2] == 1: 
        # équation du moment
        self._projM(matK, beamStart, beamEnd, row, pos0, ddls0, code0)
        row += 1
      content = RotuleElast.get(noeud0)
      if not content is None:
        # équation supplémentaire de compatibilité au niveau de la rotule
        self._RotuleElasM(matK, noeud0, content, row)
        row += 1
    #print("matK", matK)
    return matK

  def _MakeLiDDL(self):
    """Crée un attribut codeDDL de format {noeud: (octal_ddl, position_first_ddl}
    Crée un attribut n_liaison pour le nombre de liaison
    Crée un attribut n_ddl pour le nombre de ddl"""
    struct = self.struct
    n_liaisons = 0
    codeDDL = {}
    posDDL = 0
    liaisons = struct.Liaisons
    relaxs = struct.IsRelax
    nodes = struct.Nodes
    for noeud in nodes:
      i = -1 # par défaut noeud libre
      if noeud in liaisons:
        i = liaisons[noeud]
      posDDL, n_liaisons = self._GetNodeDdl(noeud, i, codeDDL, posDDL, n_liaisons, relaxs)
    self.codeDDL = codeDDL
    #print("codeDDL", codeDDL)
    struct.n_liaison = n_liaisons # renommer

    # Calcul du nombre de ddl non nuls
    n_ddl = 0
    for noeud in codeDDL:
      ind = codeDDL[noeud][0]
      ddls = self.CODES_DDL[ind]
      for val in ddls:
          if not val == 0:
            n_ddl += 1
    self.n_ddl = n_ddl

  def _GetNodeDdl(self, noeud, n_liaison, codeDDL, posDDL, n_liaisons, relaxs):
    """Retourne un tuple contenant la position des ddl et le nombre de liaisons"""
    struct = self.struct
    if n_liaison == -1:
      if noeud in relaxs:
        code = 6
        nDDL = 2
      else:
        code = 7
        nDDL = 3
      if noeud in struct.RotuleElast:
        if code == 6: print("debug GetNodeDdl, pas de rotule elast si noeud relaxé")
        code = 1111
        nDDL += 1
      # on supprime u et v si déplacements imposés
      if noeud in self.NodeDeps:
        if code == 7:
          code = 1
        elif code == 6:
          code = 0
        elif code == 1111:
          code = 11
        nDDL -= 2

    elif n_liaison == 0: # le noeud ne peut pas être relaxé
      if noeud in struct.RotuleElast:
        codeDDL[noeud] = (8, posDDL)
        posDDL += 1
        n_liaisons += 3
      else:
        codeDDL[noeud] = (0, None)
        n_liaisons += 3
      return posDDL, n_liaisons

    elif n_liaison == 1:
      #if relaxs[noeud] == 0:
      if noeud in relaxs:
        code = 0
        nDDL = 0
      else:
        code = 1
        nDDL = 1
      n_liaisons += 2
      if noeud in struct.RotuleElast:
        if code == 0: print("debug GetNodeDdl, pas de rotule elast si noeud relaxé")
        code = 11
        nDDL += 1

    elif n_liaison == 2:
      #if relaxs[noeud] == 0:
      if noeud in relaxs:
        code = 4
        nDDL = 1
      else:
        code = 5
        nDDL = 2
      n_liaisons += 1
      if noeud in struct.RotuleElast:
        if code == 4: print("debug GetNodeDdl, pas de rotule elast si noeud relaxé")
        code = 1011
        nDDL += 1

    elif n_liaison == 3:
      octal = 0
      oct = 4 # utilisation de la notation chmod octal 4 2 1
      pos = 0
      liRaideur = struct.RaideurAppui[noeud]
      #for j in range(3):
      # suivant x
      if liRaideur[0] == "inf": 
        n_liaisons += 1
      elif liRaideur[0] == 0: 
        octal += oct
        pos += 1
      else: 
        n_liaisons += 1
        pos += 1
        octal += oct
      oct /= 2
      # suivant y
      if liRaideur[1] == "inf": 
        n_liaisons += 1
      elif liRaideur[1] == 0: 
        octal += oct
        pos += 1
      else: 
        n_liaisons += 1
        pos += 1
        octal += oct
      oct /= 2
      # suivant z
      if noeud in struct.IsRelax:
        pass
      else:
        if liRaideur[2] == "inf": 
          n_liaisons += 1
        elif liRaideur[2] == 0:
          octal += oct
          pos += 1
        else: 
          n_liaisons += 1
          pos += 1
          octal += oct

      code = octal
      nDDL = pos
      if noeud in struct.RotuleElast:
        string = ""
        ddl = self.CODES_DDL[code]
        # on recrée le codeDDL et on ajoute 1 en 4ieme position
        for ind in ddl:
          string += str(ind)
        string += "1"
        code = int(string)
        nDDL += 1

    codeDDL[noeud] = (code, posDDL)
    posDDL += nDDL
    return posDDL, n_liaisons

  def get_ddl_pos(self, node):
    """retourne la position du premier ddl pour le noeud donné dans la liste des ddl non nuls"""
    return self.codeDDL[node][1]

  def _add_elastic(self, matK, row, ddl, values):
    """Ajoute les valeurs des raideurs sur les appuis élastiques
    Si rotule élastique, on prend la valeur de gauche (wG) comme rotation
    pour l'appui élastique"""
    #print("add_elastic", row, ddl, values)
    col = row
    for i, val in enumerate(ddl):
      if val == 0 or i == 3:
        continue
      matK[col, col] += values[i]
      col += 1

  def _projX(self, matK, noeud0, beamStart, beamEnd, row, ddls0, code0):
    #print("_projX", noeud0)
    struct = self.struct
    pos0 = row
    cos = math.cos # inutile pour améliorer le temps
    sin = math.sin
    appuis_inclines = struct.AppuiIncline
    RotuleElast = struct.RotuleElast

    # changement d'axe de projection si appui incliné
    teta = 0.
    if noeud0 in appuis_inclines:
      teta = appuis_inclines[noeud0]

    # barre démarrant sur le noeud
    for name in beamStart:
      angle = struct.Angles[name]
      barre = struct.Barres[name]
      noeud0, noeud1, relax0, relax1 = barre
      
      N0, N1 = self._getN1(name, noeud0, noeud1)
# XXX inutile de récupérer V0,V1 si angle == 0?????
      V0, V1 = self._getV1(name, noeud0, noeud1, relax0, relax1)
      self.ChangeAxis(appuis_inclines, noeud0, noeud1, N0, N1, V0, V1)

      pos1 = self.get_ddl_pos(noeud1)
      code1 = self.codeDDL[noeud1][0]
      ddls1 = self.CODES_DDL[code1]

      # modification valeurs pour le noeud 0
      pos = pos0
      rot_elast = False
      if noeud0 in RotuleElast:
        barre_elast = RotuleElast[noeud0][0]
        if name == barre_elast:
          rot_elast = True
      if teta:
        #a = self._get_angle_proj(angle, teta)
        a = teta - angle

      if ddls0[0] == 1:
        if teta: # projection sur l'axe de l'appui incliné
          value = N0[0]*cos(a) + V0[0]*sin(a)
        else:
          value = N0[0]*cos(angle) - V0[0]*sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls0[1] == 1:
        # pas d'équation si teta différent 0
        value = N0[1]*cos(angle) - V0[1]*sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls0[2] == 1:
        if not rot_elast:
          if teta:
            value = N0[2]*cos(a) + V0[2]*sin(a)
          else:
            value = N0[2]*cos(angle) - V0[2]*sin(angle)
          matK[row, pos] += value
        pos += 1
      if rot_elast:
        if teta:
          value = N0[2]*cos(a) + V0[2]*sin(a)
        else:
          value = N0[2]*cos(angle) - V0[2]*sin(angle)
        matK[row, pos] += value

      # modification valeurs pour le noeud 1
      pos = pos1
      rot_elast = False
      if noeud1 in RotuleElast:
        barre_elast = RotuleElast[noeud1][0]
        if name == barre_elast:
          rot_elast = True

      if ddls1[0] == 1:
        if teta: # projection sur l'axe de l'appui incliné
          value = N1[0]*cos(a) + V1[0]*sin(a)
        else:
          value = N1[0]*cos(angle) - V1[0]*sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls1[1] == 1:
        if teta: # projection sur l'axe de l'appui incliné
          value = N1[1]*cos(a) + V1[1]*sin(a)
        else:
          value = N1[1]*cos(angle) - V1[1]*sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls1[2] == 1:
        if not rot_elast:
          if teta:
            value = N1[2]*cos(a) + V1[2]*sin(a)
          else:
            value = N1[2]*cos(angle) - V1[2]*sin(angle)
          matK[row, pos] += value
        pos += 1
      if rot_elast:
        if teta:
          value = N1[2]*cos(a) + V1[2]*sin(a)
        else:
          value = N1[2]*cos(angle) - V1[2]*sin(angle)
        matK[row, pos] += value

    # barre arrivant sur le noeud
    for name in beamEnd:
      angle = struct.Angles[name]
      barre = struct.Barres[name]
      noeud0, noeud1, relax0, relax1 = barre
      N0, N1 = self._getN2(name, noeud0, noeud1)
      V0, V1 = self._getV2(name, noeud0, noeud1, relax0, relax1)
      self.ChangeAxis(appuis_inclines, noeud0, noeud1, N0, N1, V0, V1)

      pos0 = self.get_ddl_pos(noeud0)
      pos1 = self.get_ddl_pos(noeud1)
      code0 = self.codeDDL[noeud0][0]
      ddls0 = self.CODES_DDL[code0]
      code1 = self.codeDDL[noeud1][0]
      ddls1 = self.CODES_DDL[code1]

      # modification valeurs pour le noeud 0
      pos = pos0
      rot_elast = False
      if noeud0 in RotuleElast:
        barre_elast = RotuleElast[noeud0][0]
        if name == barre_elast:
          rot_elast = True
      if teta:
        #a = self._get_angle_proj(angle, teta)
        a = teta - angle
      if ddls0[0] == 1:
        if teta: # projection sur l'axe de l'appui incliné
          value = N0[0]*cos(a) + V0[0]*sin(a)
        else:
          value = N0[0]*cos(angle) - V0[0]*sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls0[1] == 1:
        if teta: # projection sur l'axe de l'appui incliné
          value = N0[1]*cos(a) + V0[1]*sin(a)
        else:
          value = N0[1]*cos(angle) - V0[1]*sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls0[2] == 1:
        if not rot_elast:
          if teta:
            value = N0[2]*cos(a) + V0[2]*sin(a)
          else:
            value = N0[2]*cos(angle) - V0[2]*sin(angle)
          matK[row, pos] += value
        pos += 1
      if rot_elast:
        if teta:
          value = N0[2]*cos(a) + V0[2]*sin(a)
        else:
          value = N0[2]*cos(angle) - V0[2]*sin(angle)
        matK[row, pos] += value

      # modification valeurs pour le noeud 1
      pos = pos1
      rot_elast = False
      if noeud1 in RotuleElast:
        barre_elast = RotuleElast[noeud1][0]
        if name == barre_elast:
          rot_elast = True
      if ddls1[0] == 1:
        if teta: # projection sur l'axe de l'appui incliné
          value = N1[0]*cos(a) + V1[0]*sin(a)
        else:
          value = N1[0]*cos(angle) - V1[0]*sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls1[1] == 1:
        value = N1[1]*cos(angle) - V1[1]*sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls1[2] == 1:
        if not rot_elast:
          if teta:
            value = N1[2]*cos(a) + V1[2]*sin(a)
          else:
            value = N1[2]*cos(angle) - V1[2]*sin(angle)
          matK[row, pos] += value
        pos += 1
      if rot_elast:
        if teta:
          value = N1[2]*cos(a) + V1[2]*sin(a)
        else:
          value = N1[2]*cos(angle) - V1[2]*sin(angle)
        matK[row, pos] += value


  def _projY(self, matK, beamStart, beamEnd, row, col, ddls0, code0):
    #print("_projY")
    struct = self.struct
    pos0 = col
    # barre démarrant sur le noeud
    RotuleElast = struct.RotuleElast
    appuis_inclines = struct.AppuiIncline
    for name in beamStart:
      angle = struct.Angles[name]
      barre = struct.Barres[name]
      noeud0, noeud1, relax0, relax1 = barre
      N0, N1 = self._getN1(name, noeud0, noeud1)
      V0, V1 = self._getV1(name, noeud0, noeud1, relax0, relax1)
      self.ChangeAxis(appuis_inclines, noeud0, noeud1, N0, N1, V0, V1)

      pos1 = self.get_ddl_pos(noeud1)
      code1 = self.codeDDL[noeud1][0]
      ddls1 = self.CODES_DDL[code1]

      # modification valeurs pour le noeud 0
      pos = pos0
      rot_elast = False
      if noeud0 in RotuleElast:
        barre_elast = RotuleElast[noeud0][0]
        if name == barre_elast:
          rot_elast = True
      if ddls0[0] == 1:
        value = V0[0]*math.cos(angle) + N0[0]*math.sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls0[1] == 1:
        value = V0[1]*math.cos(angle) + N0[1]*math.sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls0[2] == 1:
        if not rot_elast:
          value = V0[2]*math.cos(angle) + N0[2]*math.sin(angle)
          matK[row, pos] += value
        pos += 1
      if rot_elast:
        value = V0[2]*math.cos(angle) + N0[2]*math.sin(angle)
        matK[row, pos] += value

      # modification valeurs pour le noeud 1
      if pos1 == None: continue
      pos = pos1
      rot_elast = False
      if noeud1 in RotuleElast:
        barre_elast = RotuleElast[noeud1][0]
        if name == barre_elast:
          rot_elast = True

      if ddls1[0] == 1:
        value = V1[0]*math.cos(angle) + N1[0]*math.sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls1[1] == 1:
        value = V1[1]*math.cos(angle) + N1[1]*math.sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls1[2] == 1:
        if not rot_elast:
          value = V1[2]*math.cos(angle) + N1[2]*math.sin(angle)
          matK[row, pos] += value
        pos += 1
      if rot_elast:
        value = V1[2]*math.cos(angle) + N1[2]*math.sin(angle)
        matK[row, pos] += value


    # barre arrivant sur le noeud
    for name in beamEnd:
      angle = struct.Angles[name]
      barre = struct.Barres[name]
      noeud0, noeud1, relax0, relax1 = barre
      N0, N1 = self._getN2(name, noeud0, noeud1)
      V0, V1 = self._getV2(name, noeud0, noeud1, relax0, relax1)
      self.ChangeAxis(appuis_inclines, noeud0, noeud1, N0, N1, V0, V1)

      pos0 = self.get_ddl_pos(noeud0) # revoir
      pos1 = self.get_ddl_pos(noeud1)
      code0 = self.codeDDL[noeud0][0]
      ddls0 = self.CODES_DDL[code0]
      code1 = self.codeDDL[noeud1][0]
      ddls1 = self.CODES_DDL[code1]

      # modification valeurs pour le noeud 0
      pos = pos0
      rot_elast = False
      if noeud0 in RotuleElast:
        barre_elast = RotuleElast[noeud0][0]
        if name == barre_elast:
          rot_elast = True
      if ddls0[0] == 1:
        value = V0[0]*math.cos(angle) + N0[0]*math.sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls0[1] == 1:
        value = V0[1]*math.cos(angle) + N0[1]*math.sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls0[2] == 1:
        if not rot_elast:
          value = V0[2]*math.cos(angle) + N0[2]*math.sin(angle)
          matK[row, pos] += value
        pos += 1
      if rot_elast:
        value = V0[2]*math.cos(angle) + N0[2]*math.sin(angle)
        matK[row, pos] += value

      # modification valeurs pour le noeud 1
      if pos1 == None: continue
      pos = pos1
      rot_elast = False
      if noeud1 in RotuleElast:
        barre_elast = RotuleElast[noeud1][0]
        if name == barre_elast:
          rot_elast = True
      if ddls1[0] == 1:
        value = V1[0]*math.cos(angle) + N1[0]*math.sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls1[1] == 1:
        value = V1[1]*math.cos(angle) + N1[1]*math.sin(angle)
        matK[row, pos] += value
        pos += 1
      if ddls1[2] == 1:
        if not rot_elast:
          value = V1[2]*math.cos(angle) + N1[2]*math.sin(angle)
          matK[row, pos] += value
        pos += 1
      if rot_elast:
        value = V1[2]*math.cos(angle) + N1[2]*math.sin(angle)
        matK[row, pos] += value



  def _RotuleElasM(self, matK, noeud, content, row):
    """On écrit que le moment Mij d'une barre dont l'extrémité est une rotule élastique doit être équivalent au moment élastique transmis
    Attention il ne peut y avoir que 2 barres par noeuds
    """
    #print("_RotuleElasM", noeud)
    struct = self.struct
    RotuleElast = struct.RotuleElast
    bar_name = content[0]
    kz = content[1]
    appuis_inclines = struct.AppuiIncline
    barre = struct.Barres[bar_name]
    noeud0, noeud1, relax0, relax1 = barre
    pos0 = self.get_ddl_pos(noeud0)
    code0 = self.codeDDL[noeud0][0]
    ddls0 = self.CODES_DDL[code0]
    pos1 = self.get_ddl_pos(noeud1)
    code1 = self.codeDDL[noeud1][0]
    ddls1 = self.CODES_DDL[code1]
    # noeud avec rotule élastique à l'origine de la barre
    if noeud == noeud0:
      rz = False
      if noeud1 in RotuleElast and RotuleElast[noeud1][0] == bar_name:
        rz = True
      # calcul de Mij
      M0, M1 = self._getM1(bar_name, noeud0, noeud1, relax0, relax1)
      self.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)
      # modification matrice
      if ddls0[0] == 1:
        matK[row, pos0] += M0[0]
        pos0 += 1
      if ddls0[1] == 1:
        matK[row, pos0] += M0[1]
        pos0 += 1
      if ddls0[2] == 1:
        matK[row, pos0] += -kz
        pos0 += 1
      if ddls0[3] == 1:
        matK[row, pos0] += kz+M0[2]
    
      if ddls1[0] == 1:
        matK[row, pos1] += M1[0]
        pos1 += 1
      if ddls1[1] == 1:
        matK[row, pos1] += M1[1]
        pos1 += 1
      if ddls1[2] == 1 and rz:
        pos1 += 1
      if ddls1[2] == 1 or rz:
        matK[row, pos1] += M1[2]
    else:
    # noeud avec rotule élastique à l'extrémité de la barre
      M0, M1 = self._getM2(bar_name, noeud0, noeud1, relax0, relax1)
      self.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)
      if ddls0[0] == 1:
        matK[row, pos0] += M0[0]
        pos0 += 1
      if ddls0[1] == 1:
        matK[row, pos0] += M0[1]
        pos0 += 1
      rz = False
      if noeud0 in RotuleElast and RotuleElast[noeud0][0] == bar_name:
        rz = True
      if ddls0[2] == 1 and rz:
        pos0 += 1
      if ddls0[2] == 1 or rz:
        matK[row, pos0] += M0[2]
    
      if ddls1[0] == 1:
        matK[row, pos1] += M1[0]
        pos1 += 1
      if ddls1[1] == 1:
        matK[row, pos1] += M1[1]
        pos1 += 1
      if ddls1[2] == 1:
        matK[row, pos1] += -kz
        pos1 += 1
      if ddls1[3] == 1:
        matK[row, pos1] += kz + M1[2]


  def _projM(self, matK, beamStart, beamEnd, row, col, ddls0, code0):
    #print("_projM")
    struct = self.struct
    pos0 = col
    RotuleElast = struct.RotuleElast
    appuis_inclines = struct.AppuiIncline
    # barre démarrant sur le noeud
    for name in beamStart:
      angle = struct.Angles[name]
      barre = struct.Barres[name]
      noeud0, noeud1, relax0, relax1 = barre
      M0, M1 = self._getM1(name, noeud0, noeud1, relax0, relax1)
      self.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)

      pos1 = self.get_ddl_pos(noeud1)
      code1 = self.codeDDL[noeud1][0]
      ddls1 = self.CODES_DDL[code1]

      # modification valeurs pour le noeud 0
      pos = pos0
      rot_elast = False
      if noeud0 in RotuleElast:
        barre_elast = RotuleElast[noeud0][0]
        if name == barre_elast:
          rot_elast = True
      if ddls0[0] == 1:
        matK[row, pos] += M0[0]
        pos += 1
      if ddls0[1] == 1:
        matK[row, pos] += M0[1]
        pos += 1
      if ddls0[2] == 1:
        if not rot_elast:
          matK[row, pos] += M0[2]
        pos += 1
      if rot_elast:
        matK[row, pos] += M0[2]


      # modification valeurs pour le noeud 1
      pos = pos1
      rot_elast = False
      if noeud1 in RotuleElast:
        barre_elast = RotuleElast[noeud1][0]
        if name == barre_elast:
          rot_elast = True
      if ddls1[0] == 1:
        matK[row, pos] += M1[0]
        pos += 1
      if ddls1[1] == 1:
        matK[row, pos] += M1[1]
        pos += 1
      if ddls1[2] == 1:
        if not rot_elast:
          matK[row, pos] += M1[2]
        pos += 1
      if rot_elast:
        matK[row, pos] += M1[2]

    # barre arrivant sur le noeud
    for name in beamEnd:
      angle = struct.Angles[name]
      barre = struct.Barres[name]
      noeud0, noeud1, relax0, relax1 = barre
      M0, M1 = self._getM2(name, noeud0, noeud1, relax0, relax1)
      self.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)

      pos0 = self.get_ddl_pos(noeud0) # revoir
      pos1 = self.get_ddl_pos(noeud1)
      code0 = self.codeDDL[noeud0][0]
      ddls0 = self.CODES_DDL[code0]
      code1 = self.codeDDL[noeud1][0]
      ddls1 = self.CODES_DDL[code1]

      # modification valeurs pour le noeud 0
      pos = pos0
      rot_elast = False
      if noeud0 in RotuleElast:
        barre_elast = RotuleElast[noeud0][0]
        if name == barre_elast:
          rot_elast = True
      if ddls0[0] == 1:
        matK[row, pos] += M0[0]
        pos += 1
      if ddls0[1] == 1:
        matK[row, pos] += M0[1]
        pos += 1
      if ddls0[2] == 1:
        if not rot_elast:
          matK[row, pos] += M0[2]
        pos += 1
      if rot_elast:
        matK[row, pos] += M0[2]

      #for i in range(3):
      #  if ddls0[i] == 0: continue
      #  if i == 2 and rot_elast:
      #    pos += 1
      #  matK[row, pos] += M0[i]
      #  pos += 1

      # modification valeurs pour le noeud 1
      pos = pos1
      rot_elast = False
      if noeud1 in RotuleElast:
        barre_elast = RotuleElast[noeud1][0]
        if name == barre_elast:
          rot_elast = True
      if ddls1[0] == 1:
        matK[row, pos] += M1[0]
        pos += 1
      if ddls1[1] == 1:
        matK[row, pos] += M1[1]
        pos += 1
      if ddls1[2] == 1:
        if not rot_elast:
          matK[row, pos] += M1[2]
        pos += 1
      if rot_elast:
        matK[row, pos] += M1[2]

  def _getN1(self, barre, noeud0, noeud1): 
    """Retourne les coefficients intrinsèques d'une barre pour l'effort normal
    exprimés dans le repère global des ddls
    Coefficients pour l'origine de la barre"""
    struct = self.struct
    angle = struct.Angles[barre]
    E = struct._GetYoung(barre)
    S = struct._GetSection(barre)
    coef = E*S/struct.Lengths[barre]
    ddl0 = [coef, 0., 0.]
    if not angle == 0:
      ProjL2G(ddl0, angle) 
    ddl1 = [-i for i in ddl0]
    return ddl0, ddl1

  def _getN2(self, barre, noeud0, noeud1): 
    """Retourne les coefficients intrinsèques d'une barre pour l'effort normal
    exprimés dans le repère global des ddls
    Coefficients pour l'extrémité de la barre"""
    struct = self.struct
    angle = struct.Angles[barre]
    E = struct._GetYoung(barre)
    S = struct._GetSection(barre)
    coef = E*S/struct.Lengths[barre]
    ddl0 = [-coef, 0., 0.]
    if not angle == 0:
      ProjL2G(ddl0, angle) 
    ddl1 = [-i for i in ddl0]
    return ddl0, ddl1

  def _getV1(self, barre, noeud0, noeud1, relax0, relax1):
    """Retourne les coefficients intrinsèques d'une barre pour l'effort tranchant
    exprimés dans le repère global des ddls
    Coefficients pour l'origine de la barre"""
    struct = self.struct
    angle = struct.Angles[barre]
    E = struct._GetYoung(barre)
    I = struct._GetMQua(barre)
    coef = E*I
    l = struct.Lengths[barre]
    if relax0 == 0:
      if relax1 == 0:
        # Noeud non relaxé, noeud suivant non relaxé
        ddl0, ddl1 = [0., 12./l**3, 6./l**2], [0, -12./l**3, 6./l**2]
      elif relax1 == 1:
        # Noeud non relaxé, noeud suivant relaxé
        ddl0, ddl1 = [0., 3./l**3, 3./l**2], [0., -3./l**3, 0]
    elif relax0 == 1:
      if relax1 == 0:
        # Noeud relaxé, noeud suivant non relaxé
        ddl0, ddl1 = [0., 3./l**3, 0.], [0., -3./l**3, 3./l**2]
      elif relax1 == 1:
        # Noeud relaxé, noeud suivant relaxé
         return [0.]*3, [0.]*3
    if not angle == 0:
      ProjL2G(ddl0, angle)
      ProjL2G(ddl1, angle)
    return [i*coef for i in ddl0], [i*coef for i in ddl1]

  def _getV2(self, barre, noeud0, noeud1, relax0, relax1):
    """Retourne les coefficients intrinsèques d'une barre pour l'effort tranchant
    exprimés dans le repère global des ddls
    Coefficients pour l'extrémité de la barre"""
    struct = self.struct
    angle = struct.Angles[barre]
    E = struct._GetYoung(barre)
    I = struct._GetMQua(barre)
    coef = E*I
    l = struct.Lengths[barre]
    if relax0 == 0:
      if relax1 == 0:
        # Noeud non relaxé, noeud suivant non relaxé
        ddl0, ddl1 = [0., -12./l**3, -6./l**2], [0, 12./l**3, -6./l**2]
      elif relax1 == 1:
        # Noeud non relaxé, noeud suivant relaxé
        ddl0, ddl1 = [0., -3./l**3, -3./l**2], [0., 3./l**3, 0]
    elif relax0 == 1:
      if relax1 == 0:
        # Noeud relaxé, noeud suivant non relaxé
        ddl0, ddl1 = [0., -3./l**3, 0.], [0., 3./l**3, -3./l**2]
      elif relax1 == 1:
        # Noeud relaxé, noeud suivant relaxé
         return [0.]*3, [0.]*3
    if not angle == 0:
      ProjL2G(ddl0, angle)
      ProjL2G(ddl1, angle)
    return [i*coef for i in ddl0], [i*coef for i in ddl1]

  def _getM1(self, barre, noeud0, noeud1, relax0, relax1):
    """Retourne les coefficients intrinsèques d'une barre pour les moments
    exprimés dans le repère global des ddls
    Coefficients pour l'origine de la barre"""
    struct = self.struct
    angle = struct.Angles[barre]
    E = struct._GetYoung(barre)
    I = struct._GetMQua(barre)
    coef = E*I
    l = struct.Lengths[barre]
    if relax0 == 1:
      return [0]*3, [0]*3
    if relax1 == 0:
      # Noeud non relaxé, noeud suivant non relaxé
      ddl0, ddl1 = [0., 6./l**2, 4./l], [0., -6./l**2, 2./l]
    elif relax1 == 1:
      # Noeud non relaxé, noeud suivant relaxé
      ddl0, ddl1 = [0., 3./l**2, 3./l], [0., -3./l**2, 0.]
    if not angle == 0:
      ProjL2G(ddl0, angle)
      ProjL2G(ddl1, angle)
    return [i*coef for i in ddl0], [i*coef for i in ddl1]

  def _getM2(self, barre, noeud0, noeud1, relax0, relax1):
    """Retourne les coefficients intrinsèques d'une barre pour les moments
    exprimés dans le repère global des ddls
    Coefficients pour l'extrémité de la barre"""
    struct = self.struct
    angle = struct.Angles[barre]
    E = struct._GetYoung(barre)
    I = struct._GetMQua(barre)
    coef = E*I
    l = struct.Lengths[barre]
    if relax1 == 1:
      return [0]*3, [0]*3
    if relax0 == 0:
      # Noeud non relaxé, noeud suivant non relaxé
      ddl0, ddl1 = [0., 6./l**2, 2./l], [0., -6./l**2, 4./l]
    elif relax0 == 1:
      # Noeud non relaxé, noeud suivant relaxé
      ddl0, ddl1 = [0., 3./l**2, 0.],[0., -3./l**2, 3./l]
    if not angle == 0:
      ProjL2G(ddl0, angle)
      ProjL2G(ddl1, angle)
    return [i*coef for i in ddl0], [i*coef for i in ddl1]

  def ChangeAxis(self, appuis_inclines, noeud0, noeud1, N0, N1, V0, V1):
    """Change le repère des ddl si le noeud est un appui incliné, pour les composantes N et V en passant dans le repère de l'appui incliné"""
    struct = self.struct
    if noeud0 in appuis_inclines:
      teta = appuis_inclines[noeud0]
      struct._SetAppuiIncline(teta, N0)
      struct._SetAppuiIncline(teta, V0)
    if noeud1 in appuis_inclines:
      teta = appuis_inclines[noeud1]
      struct._SetAppuiIncline(teta, N1)
      struct._SetAppuiIncline(teta, V1)

  def ChangeAxis2(self, appuis_inclines, noeud0, noeud1, M0, M1):
    """Change le repère des ddl si le noeud est un appui incliné, pour les composantes de M en passant dans le repère de l'appui incliné"""
    struct = self.struct
    if noeud0 in appuis_inclines:
      teta = appuis_inclines[noeud0]
      struct._SetAppuiIncline(teta, M0)
    if noeud1 in appuis_inclines:
      teta = appuis_inclines[noeud1]
      struct._SetAppuiIncline(teta, M1)

class Structure(object):
  """Classe contenant la structure"""



  def __init__(self, xml, path=None):
    #print("Structure::__init__")
    if not path is None:
      self.name = os.path.basename(path)
      self.file = path
    self.XML = xml
    self.errors = []
    self.width, self.height = 0, 0
    try:
      self.GetXMLElem()
    except:
      self.status = -1
      return
    self.status = 1
    # -1: xml error, 0: erreur lecture, 1: données valide mais erreur inversion
    # 2: inversion matrice rigidité ok
    try:
      self._ExtractData()
    except XMLError:
      self.status = -1
      return

# ------------------ LECTURE DES DONNEES ----------------------


  def RenameObject(self, path):
    """Fonction utilisée pour changer les attributs name et file 
    de l'objet Rdm"""
    self.file = path
    self.name = os.path.basename(path)

# revoir minidom
  def fakeReadXMLFile(self, string):
    """Fonction de test
    Lecture des données dans une chaines de caractères"""
    self.XML = minidom.parseString(string)

  def RawReadFile(self):
    """Retourne le contenu XLM du fichier de données"""
    f = open(self.file, 'r')
    content = f.read()
    f.close()
    return content


  def PrintErrorConsole(self):
    #print("Rdm::PrintErrorConsole")
    if len(self.errors) == 0: return
    for error in self.errors:
      if error[1] == 0:
        name = 'Error::'
      elif error[1] == 1:
        name = 'Warning::'
      else: return
      print('%s%s' % (name, error[0]))

  def PrintError(self, text, code):
    """Fonction de formatage du message d'erreur
    code 0 : error; code 1 : warning"""
    #print("PrintError", text)
    self.errors.append((text, code))
      
  def _ExtractData(self):
    """A partir du fichier de données, création des attributs de l'objet
    pour la classe Rdm"""
    #print("Rdm::_ExtractData")
    # Détection des noeuds
    self.units = self.GetUnits()
    self.GetNode()
    # Détection des barres, longueurs, angles
    self.Lengths = {}
    self.Angles = {}
    self._n_bar = 0
    self._n_node = 0
    # Caractéristiques géométriques des barres autres que arc
    self._SetBars()
    #print("Barres=", self.UserBars)
    self._SetCaracs()
    del (self.ArcNodesData)
    n_nodes = len(self.UserNodes)
    if n_nodes == 0:
      self.PrintError("Aucun noeud n'a été défini.", 0)
    elif n_nodes == 1:
      self.PrintError("Vous devez définir au moins 2 noeuds.", 0)
    self._GetBarreByNode()
    if len(self.Barres) == 0:
      self.PrintError("Vous devez définir les barres.", 0)

# créer une méthode qui initialise les attributs

    # Liaisons
    self._GetLiaison()
    self._GetRotulePlast()
    # relaxation du noeud si toutes les barres sont relaxées
    self._RelaxNode()
    # élimination les noeuds non liés
    self._GetNodeNotLinked()

    # Caractéristiques mécaniques des barres
    # Module d'Young
    self._SetYoung()
    # largeur / hauteur
    self._GetDim()
    self.G = self.GetG()

  def _SetBars(self):
    precision = Const.ARCPRECISION
    self.Barres = {}
    self.UserBars = []
    self.Curves = {}
    self.Centers = {}
    self.SuperBars = {}
    self.assym_b = {}
    self.RotuleElast = {}
    try:
      elems = self.XMLNodes["barre"].iter()
    except KeyError:
      text = "Erreur dans XML::pas de barre"
      self.PrintError(text, 0)
      raise XMLError(text)
    n = len(list(self.XMLNodes["barre"].iter('arc')))
    if n >= 4:
      precision = precision*4/n # limitation du nombre de points à partir de 4 arcs
    for elem in elems:
      tag = elem.tag
      if tag == "elem":
        continue
      if tag == 'barre':
        self._SetSegment(elem)
      elif tag == 'mbarre':
        self._SetMBarre(elem)
      elif tag == 'arc':
        self._SetArc(elem, precision)
      elif tag == 'parabola':
        self._SetParabola(elem, precision)
      else:
        print("Unexpected tag %s in _SetBars" % tag)
    # suppression des centres de la liste des noeuds
    for node in self.Centers:
      if node in self.NodeNotLinked:
        del(self.Nodes[node])
        self.NodeNotLinked.remove(node)
        self.UserNodes.remove(node)
    self._SetEmptyNodes()

# tester l'ordre d'apparition des points : risque de bug
  def _SetEmptyNodes(self):
    """Calcule les coordonnées des points relatifs à un noeud inclu dans un arc"""
    #print("_SetEmptyNodes", self.__EmptyNodes)
    f = function.Str2NodeCoors
    for node in self.__EmptyNodes:
      content = self.__EmptyNodes[node]
      coors = f(content, self.Nodes, unit=self.units['L'])
      if coors is False:
        #print("Erreur inattendue dans _SetEmptyNodes")
        continue
      self.Nodes[node] = coors
    del(self.__EmptyNodes)

  def GetUnits(self):
    """Crée le dictionnaire des conversions d'unité
    à partir des données xml du fichiers .dat"""
    if not "prefs" in self.XMLNodes:
      return {'C': 1., 'E': 1., 'F': 1., 'I': 1., 'M': 1., 'L': 1., 'S': 1.}
    di = {}
    for node in self.XMLNodes["prefs"].iter('unit'):
      name = node.get("id")
      content = node.get("d")
      try:
        di[name] = float(content)
      except (TypeError, ValueError):
        continue
    keys = ['C', 'E', 'F', 'I', 'M', 'L', 'S']
    for key in keys:
      if not key in di:
        di[key] = 1.
    return di


  def GetG(self, UP=None):
    """Récupère la valeur de G"""
    G = None
    if 'g' in self.CONST: G = self.CONST['g']
    try:
      return float(G)
    except ValueError:
      return Const.G
    except TypeError:
      return Const.G

  def GetConv(self, UP=None):
    """Récupère la valeur de la convention de signe"""
    if 'conv' in self.CONST: 
      conv = self.CONST['conv']
      try:
        conv = int(conv)
      except ValueError:
        conv = None
    else : conv = None
    if conv == 1 :
      return conv
    if conv == -1:
      return conv
    return Const.CONV

  def _GetDim(self):
    """Crée les attributs width et height de la structure
    translate les points de la structure de façon à prendre comme origine (0, 0) le coin bas gauche"""
    def translate(nodes, dx, dy):
      for node in nodes:
        try:
          x, y = nodes[node]
        except ValueError:
          return
        x -= dx
        y -= dy
        nodes[node] = (x, y)

    nodes = self.Nodes
    node_names = list(nodes.keys()) # porting 2.7 -> 3
    if len(nodes) == 0:
      self.width = 0
      self.height = 0
      return
    coors = nodes[node_names[0]]
    if len(coors) == 0:
      self.width = 0
      self.height = 0
      return
    xmax = xmin = coors[0]
    ymax = ymin = coors[1]
    for node in node_names[1:]:
      coors = nodes[node]
      if len(coors) == 0:
        continue
      if coors[0] < xmin:
        xmin = coors[0]
      elif  coors[0] > xmax:
        xmax = coors[0]
      if coors[1] < ymin:
        ymin = coors[1]
      elif  coors[1] > ymax:
        ymax = coors[1]
    self.width = abs(xmax-xmin)
    self.height = abs(ymax-ymin)

    # translation
    if (xmin == 0 and ymin == 0):
      return
    translate(self.Nodes, xmin, ymin)
    translate(self.Centers, xmin, ymin)
    translate(self.NodeNotLinked, xmin, ymin)

  def GetXMLElem(self):
    """Crée le dictionnaire des éléments "elem" du fichier XML"""
    root = self.XML.getroot()
    self.version = root.get("version")
    # Retourne None si l'attribut n'est pas trouvé
    #print("Version %s" % self.version)
    self.XMLNodes = {}
    self.CONST = {}
    for Node in root.iter('elem'):
      self.XMLNodes[Node.get("id")] = Node
    try:
      node = self.XMLNodes["prefs"]
    except KeyError:
      return 
    di = {}
    for node in self.XMLNodes["prefs"].iter('const'):
      name = node.get("name")
      if name is None : continue
      val = node.get("value")
      di[name] = val
    self.CONST = di

  def GetNode(self):
    """Crée les dictionnaires des noeuds"""
    #print("Rdm::GetNode")
# prevoir de supprimer les noeud relatifs si défini par rapport au précédent
    self.Nodes = {}
    self.UserNodes = []
    self.ArcNodesData = {} # renommer avec __
    self.__EmptyNodes = {} # noeud relatif dépendant d'un arc
    # ne contient que les noeuds relaxés avec pour valeur (inutile) 1
    self.IsRelax = {}
    noeud_precedent = None
    try:
      nodes = self.XMLNodes["node"].iter('node')
    except KeyError:
      text = "Erreur dans XMLNodes::pas de clé node"
      self.PrintError(text, 0)
      raise XMLError(text)
    if len(self.XMLNodes["node"]) == 0:
      self.PrintError("Aucun noeud n'a été défini", 0)
      self.status = 0
      #return
    f = function.Str2NodeCoors
    for node in nodes:
      noeud = node.get("id")
      content = node.get("d")
      coors = f(content, self.Nodes, noeud_precedent, self.units['L'])
      if coors is False:
        self.Nodes[noeud] = ()
        self.__EmptyNodes[noeud] = content
      else:
        self.Nodes[noeud] = coors
      self.UserNodes.append(noeud)
      noeud_precedent = noeud

    doubles = {}
    nodes = self.XMLNodes["node"].iter('arc')
    for node in nodes:
      name = node.get("id")
      arc = node.get("name")
      try:
        d = float(node.get("d"))
      except (TypeError, ValueError):
        self.PrintError("Valeur incorrecte pour la position du point: %s" % name, 0)
        self.status = 0
        continue
      if d <= 0. or d >= 1.: # n'accepte que des valeurs relatives : TODO
        self.PrintError("Valeur incorrecte pour la position du point: %s" % name, 0)
        self.status = 0
        continue
      doubles.setdefault(name, [])
      
      if d in doubles[name]:
        self.PrintError("Point %s en double" % name, 0)
        self.status = 0
        continue
      doubles[name].append(d)
      on_curve = node.get("pos_on_curve")
      if on_curve == 'true':
        on_curve = True
      elif on_curve == 'false' or on_curve is None:
        on_curve = False
      #on_curve = True # debug
      try:
        r = int(node.get("r"))
        if not (r == 0 or r == 1):
          self.PrintError("Valeur incorrecte pour la relaxation du point: %s" % name, 0)
          r = 0
      except (TypeError, ValueError):
        r = 0
      self.Nodes[name] = ()
      self.UserNodes.append(name)
      self.ArcNodesData.setdefault(arc, []).append((d, name, on_curve, r))
    self.NodeNotLinked = list(self.Nodes.keys()) # tous les noeuds au départ
    #print("self.UserNodes=",self.UserNodes)
    #print("self.__EmptyNodes=", self.__EmptyNodes)

  def _GetNodeNotLinked(self):
    """Supprime les noeuds non liés à une barre et les place dans un attribut"""
    NotLinked = {}
    for node in self.NodeNotLinked:
      NotLinked[node] = self.Nodes[node]
    self.NodeNotLinked = NotLinked
    #self.n_nodes = len(self.Nodes)
    if not len(NotLinked) == 0:
      self.PrintError("Certains noeuds ne sont pas reliés par une barre.", 0)

  def _SetParabola(self, node, n):
    """Lecture des données pour les arcs"""
    unit_L = self.units['L']
    Barres = self.Barres
    Nodes = self.Nodes
    Angles = self.Angles
    Lengths = self.Lengths
    n_bar = self._n_bar
    n_node = self._n_node
    name = node.get("id")
    start = node.get("start")
    end = node.get("end")
    if start == end:
      self.PrintError("Point identique dans la parabole %s" % name, 0)
      self.status = 0
      return
    try:
      f = float(node.get("f"))*unit_L
    except (TypeError, ValueError):
      self.PrintError("Flèche incorrecte dans la parabole" % name, 0)
      self.status = 0
      return
    try:
      rel0 = int(node.get("r0"))
      if not (rel0 == 0 or rel0 == 1):
        self.PrintError("Valeur incorrecte pour la relaxation à l'extrémité de l'arc: %s" % name, 0)
        rel0 = 0
    except (TypeError, ValueError):
      rel0 = 0
    try:
      rel1 = int(node.get("r1"))
      if not (rel1 == 0 or rel1 == 1):
        self.PrintError("Valeur incorrecte pour la relaxation à l'extrémité de l'arc: %s" % name, 0)
        rel1 = 0
    except (TypeError, ValueError):
      rel1 = 0
    try:
      N1 = Nodes[start]
      N2 = Nodes[end]
    except KeyError:
      self.PrintError("Erreur dans les noeuds pour la parabole %s" % name, 0)
      self.status = 0
      return
    if start in self.NodeNotLinked:
      self.NodeNotLinked.remove(start)
    if end in self.NodeNotLinked:
      self.NodeNotLinked.remove(end)
    try:
      x1, y1 = N1
    except ValueError:
      try:
        content = self.__EmptyNodes[start]
        coors = function.Str2NodeCoors(content, Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        Nodes[start] = coors
        x1, y1 = coors
        del(self.__EmptyNodes[start])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (start, name), 0)
        self.status = 0
        return
    try:
      x2, y2 = N2
    except ValueError:
      try:
        content = self.__EmptyNodes[end]
        coors = function.Str2NodeCoors(content, Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        Nodes[end] = coors
        x2, y2 = coors
        del(self.__EmptyNodes[end])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (end, name), 0)
        self.status = 0
        return

    a = function.get_vector_angle((x1, y1), (x2, y2))
    l = ((x2-x1)**2+(y2-y1)**2)**0.5
    para = Parabola(f, l, a)
    data = self.ArcNodesData.get(name, [])
    para.set_user_nodes(data, start, end, rel0, rel1, self)
    segments, li_pas = para.get_segments(n)
    user_nodes = para.user_nodes
    # suppression noeud lié
    for Node in user_nodes:
      if Node.name in self.NodeNotLinked:
        self.NodeNotLinked.remove(Node.name)
    u = 0
    S = {}
    s = 0 # curve abs
    for i, seg in enumerate(segments):
      if i == 0:
        para.set_bars_end(b0=n_bar)
      Node = user_nodes[i]
      start_name = Node.name
      rel0 = Node.r
      Node = user_nodes[i+1]
      end_name = Node.name
      rel1 = Node.r
      pas = li_pas[i]
      for j in range(seg):
        u += pas
        v = 4*f*u*(1-u/l)/l
        if not a == 0:
          x, y = Rotation(-a, u, v)
        else:
          x, y = u, v
        vprime = 4*f/l*(1-2*(u-pas/2)/l) # décalage moitié milieu de barre
        if j == 0:
          Nodes[n_node] = (x1+x, y1+y)
          Barres[n_bar] = [start_name, n_node, rel0, 0]
          n_node += 1
        elif j == seg-1:
          Barres[n_bar] = [n_node-1, end_name, 0, rel1]
          para.set_bars_end(b1=n_bar)
        else:
          Nodes[n_node] = (x1+x, y1+y)
          Barres[n_bar] = [n_node-1, n_node, 0, 0]
          n_node += 1
        Angles[n_bar] = math.atan(vprime)+a
        long =  pas*(1+vprime**2)**0.5
        Lengths[n_bar] = long
        Node.end = n_bar
        S[n_bar] = s
        #S[n_bar] = s+pas/2 # milieu de barre
        s += pas
        n_bar += 1
    para.pos = S
    self.Curves[name] = para

    self._n_bar = n_bar
    self._n_node = n_node


  def _SetArc(self, node, precision):
    """Lecture des données pour un arc"""
    n_bar = self._n_bar
    n_node = self._n_node
    name = node.get("id")
    start = node.get("start")
    center = node.get("center")
    end = node.get("end")
    try:
      rel0 = int(node.get("r0"))
      if not (rel0 == 0 or rel0 == 1):
        self.PrintError("Valeur incorrecte pour la relaxation à l'extrémité de l'arc: %s" % name, 0)
        rel0 = 0
    except (TypeError, ValueError):
      rel0 = 0
    try:
      rel1 = int(node.get("r1"))
      if not (rel1 == 0 or rel1 == 1):
        self.PrintError("Valeur incorrecte pour la relaxation à l'extrémité de l'arc: %s" % name, 0)
        rel1 = 0
    except (TypeError, ValueError):
      rel1 = 0
    data = self.ArcNodesData.get(name, [])
    try:
      N1 = self.Nodes[start]
      N2 = self.Nodes[end]
      C = self.Nodes[center]
    except KeyError:
      self.PrintError("Erreur dans les noeuds pour l'arc %s" % name, 0)
      self.status = 0
      return
    if len(N1) == 0 or len(N2) == 0 or len(C) == 0:
      self.PrintError("Erreur dans les noeuds pour l'arc %s" % name, 0)
      self.status = 0
      return
    teta1 = function.get_vector_angle(C, N1) # atan2
    teta2 = function.get_vector_angle(C, N2)
    alpha = teta1-teta2
    if alpha <= 0:
      alpha += 2*math.pi
    try:
      x1, y1 = N1
    except ValueError:
      try:
        content = self.__EmptyNodes[start]
        coors = function.Str2NodeCoors(content, Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        Nodes[start] = coors
        x1, y1 = coors
        N1 = coors
        del(self.__EmptyNodes[start])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (start, name), 0)
        self.status = 0
        return
    try:
      x2, y2 = N2
    except ValueError:
      try:
        content = self.__EmptyNodes[end]
        coors = function.Str2NodeCoors(content, Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        Nodes[end] = coors
        x2, y2 = coors
        N2 = coors
        del(self.__EmptyNodes[end])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (end, name), 0)
        self.status = 0
        return
    try:
      xc, yc = C
    except ValueError:
      try:
        content = self.__EmptyNodes[center]
        coors = function.Str2NodeCoors(content, Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        Nodes[center] = coors
        xc, yc = coors
        C = coors
        del(self.__EmptyNodes[center])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (center, name), 0)
        self.status = 0
        return
    r = ((xc-x1)**2+(yc-y1)**2)**0.5
    if r == 0:
      self.PrintError("Rayon nul pour l'arc %s" % name, 0)
      self.status = 0
    r2 = ((xc-x2)**2+(yc-y2)**2)**0.5
    if not r2 == r:
      self.PrintError("Rayons différents pour les 2 points donnés dans l'arc %s" % name, 0)
      self.status = 0
      return
    arc = Arc(center, r, teta1, teta2, alpha*r)
    self.Centers[center] = C
    user_nodes = self.GetInArcNodes(name, data, r, C, N1, N2, teta1, teta2)
    Node = ArcNode(start, teta1, False, 0., rel0)
    user_nodes.insert(0, Node)
    Node = ArcNode(end, teta2, False, 1., rel1)
    user_nodes.append(Node)
    aprec = teta1
    ind = 0
    segments = []
    pas = []
    n = max(int(precision*alpha/6.28), 1)
    angles = [i.a for i in user_nodes]
    for a in angles[1:-1]: # on enlève les extrémités
      da = aprec-a
      if da < 0:
        da += 2*math.pi
      nb = max(2, int(round(da/alpha*n)))
      segments.append(nb)
      pas.append(da/nb)
      aprec = a
      ind += nb
    if ind:
      nb = max(2, n-ind)
      segments.append(nb)
      a = aprec-teta2
      if a < 0:
        a += 2*math.pi
      pas.append(a/nb)
    else:
      segments = [n]
      pas = [alpha/n]
    # suppression noeud lié
    for Node in user_nodes:
      if Node.name in self.NodeNotLinked:
        self.NodeNotLinked.remove(Node.name)

    arc_nodes = {}
    arc_bars = {}
    a = teta1
    prec = N1
    n_seg = len(segments)
    S = {}
    s = 0 # curve abs
    for i, nb in enumerate(segments):
      if i == 0:
        arc.set_bars_end(b0=n_bar)
      da = pas[i]
      Node = user_nodes[i]
      start_name = Node.name
      rel0 = Node.r
      Node = user_nodes[i+1]
      end_name = Node.name
      rel1 = Node.r
      for j in range(nb):
        a -= da
        x = xc+r*math.cos(a)
        y = yc+r*math.sin(a)
        pt = (x, y)
        if j == 0:
          if nb == 1: # ne se produit pas car 2 segments mini
            arc_bars[n_bar] = [start_name, end_name, rel0, rel1]
          else:
            arc_nodes[n_node] = (x, y)
            arc_bars[n_bar] = [start_name, n_node, rel0, 0]
            n_node += 1
          long = function.get_vector_size(prec, pt) # = da*r ????
          angle = function.get_vector_angle(prec, pt)
        elif j == nb-1:
          arc_bars[n_bar] = [n_node-1, end_name, 0, rel1]
          arc.set_bars_end(b1=n_bar)
        else:
          arc_nodes[n_node] = (x, y)
          arc_bars[n_bar] = [n_node-1, n_node, 0, 0]
          n_node += 1
        S[n_bar] = s
        #S[n_bar] = s+long/2 # milieu de barre
        s += long
        self.Lengths[n_bar] = long # tous les segments ont meme longueur
        self.Angles[n_bar] =  angle
        Node.end = n_bar
        n_bar += 1
        angle -= da
        prec = pt
      if i == n_seg-1:
        arc.set_bars_end(b1=n_bar-1)
    arc.pos = S # dict longueur cumulée
    #self._SetArcCarac(arc, name, di_caracs, S)
    self.Barres.update(arc_bars)
    self.Nodes.update(arc_nodes)
    arc.set_nodes(user_nodes)
    self.Curves[name] = arc

    #print("Barres=", self.Barres)
    #print("UserNodes=", self.UserNodes)
    self._n_bar = n_bar
    self._n_node = n_node

  def _SetMBarre(self, node):
    """Lecture des données pour les barres à noeuds multiples"""
    n_bar = self._n_bar
    n_node = self._n_node
    barres = self.Barres
    Nodes = self.Nodes

    name = node.get("id")
    start = node.get("start")
    end = node.get("end")
    try:
      rel0 = int(node.get("r0"))
      if not (rel0 == 0 or rel0 == 1):
        self.PrintError("Valeur incorrecte pour la relaxation à l'extrémité de l'arc: %s" % name, 0)
        rel0 = 0
    except (TypeError, ValueError):
      rel0 = 0
    try:
      rel1 = int(node.get("r1"))
      if not (rel1 == 0 or rel1 == 1):
        self.PrintError("Valeur incorrecte pour la relaxation à l'extrémité de l'arc: %s" % name, 0)
        rel1 = 0
    except (TypeError, ValueError):
      rel1 = 0
    data = self.ArcNodesData.get(name, [])
    try:
      N1 = self.Nodes[start]
    except KeyError:
      self.PrintError("Noeud %s non défini dans la barre: %s" % (start, name), 0)
      self.status = 0
      return
    try:
      N2 = self.Nodes[end]
    except KeyError:
      self.PrintError("Noeud %s non défini dans la barre: %s" % (end, name), 0)
      self.status = 0
      return
    try:
      x1, y1 = N1
    except ValueError:
      try:
        content = self.__EmptyNodes[start]
        coors = function.Str2NodeCoors(content, Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        Nodes[start] = coors
        x1, y1 = coors
        N1 = coors
        del(self.__EmptyNodes[start])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (start, name), 0)
        self.status = 0
        return
    try:
      x2, y2 = N2
    except ValueError:
      try:
        content = self.__EmptyNodes[end]
        coors = function.Str2NodeCoors(content, Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        Nodes[end] = coors
        x2, y2 = coors
        N2 = coors
        del(self.__EmptyNodes[end])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (end, name), 0)
        self.status = 0
        return
    angle = function.get_vector_angle(N1, N2)
    l = ((x2-x1)**2+(y2-y1)**2)**0.5# length
    if l == 0:
      self.PrintError("Noeud identique dans la barre: %s" % name, 0)
      self.status = 0
      return
    bar = SuperBar(l, angle)
    bar.set_user_nodes(data, start, end, rel0, rel1, self)
    user_nodes = bar.user_nodes
    start_node = user_nodes[0]
    bar.set_end_bars(n_bar, n_bar+len(user_nodes)-2)
    #bar.b0, bar.b1 = n_bar, n_bar+len(user_nodes)-2
    for node in user_nodes[1:]:
      start_name = start_node.name
      rel0 = start_node.r
      u0 = start_node.u
      u1 = node.u
      end_name = node.name
      dl = (u1-u0)*l
      rel1 = node.r
      barres[n_bar] = [start_name, end_name, rel0, rel1]
      self.Lengths[n_bar] = dl
      self.Angles[n_bar] = angle
      start_node = node
      n_bar += 1
    # suppression noeud lié
    for Node in user_nodes:
      if Node.name in self.NodeNotLinked:
        self.NodeNotLinked.remove(Node.name)
    self.SuperBars[name] = bar
    self._n_bar = n_bar
    self._n_node = n_node
    #print("Nodes=", self.Nodes)
    #print("Barres=", self.Barres)
    #print("L=", self.Lengths)
    #print("UserNodes=", self.UserNodes)
    #print("Not link=", self.NodeNotLinked)




  def GetInArcNodes(self, arc, data, r, c, N0, N1, teta1, teta2):
    """Retourne la liste  des points intérieurs à un arc, calcule les coordonnées de ces points dans self.Nodes.
    u, v: coordonnées dans le repère local
    x, y dans le repère global"""
    xc, yc = c
    x0, y0 = N0
    x1, y1 = N1
    l = ((x0-x1)**2+(y0-y1)**2)**0.5# corde
    angle = function.get_vector_angle(N0, N1)
    if angle is None:
      closed = True
    else:
      closed = False
    li, di = [], {}
    if closed:
      for tu in data:
        alpha, node, on_curve, rel = tu
        a = self.SetArcSpecificPoint(alpha, node, c, r, teta1, teta2)
        li.append(a)
        Node = ArcNode(node, a, on_curve, alpha, rel)
        di[a] = Node
      li.sort(reverse=True)
      li = [di[i] for i in li]
      return li

    uc, vc = Rotation(angle, xc-x0, yc-y0)
    aprec = 0.
    for tu in data:
      alpha, node, on_curve, rel = tu
      if on_curve:
        a = self.SetArcSpecificPoint(alpha, node, c, r, teta1, teta2)
      else:
        a = self.SetArcSpecificPoint2(alpha, node, l, uc, vc, r, angle, x0, y0, c)
      if a == aprec:
        text = "Le point %s existe déjà dans %s" % (node, arc)
        self.PrintError(text, 0)
        continue
      Node = ArcNode(node, a, on_curve, alpha, rel)
      di[a] = Node
      li.append(a)
      aprec = a
    li.sort(reverse=True)
    li = [di[i] for i in li]
    return li

  def SetArcSpecificPoint(self, alpha, node, c, r, teta1, teta2):
    """Retourne l'angle d'un point sur l'arc et calcule les coordonnées du point à partir de la position sur l'arc"""
    xc, yc = c
    dteta = teta1-teta2
    if dteta <= 0:
        dteta += 2*math.pi
    if teta1 < 0:
      teta1 += 2*math.pi
    a = teta1 - alpha*dteta
    u3, v3 = r*math.cos(a)+xc, r*math.sin(a)+yc
    self.Nodes[node] = (u3, v3)
    return a

  def SetArcSpecificPoint2(self, alpha, node, l, uc, vc, r, angle, x0, y0, c):
    """Retourne l'angle d'un point sur l'arc et calcule les coordonnées du point à partir de la position sur la corde"""
    #print(" SetArcSpecificPoint2")
    xc, yc = c
    #print("SetArcSpecificPoint2", alpha, l, alpha*l)
    u2 = alpha*l
    v3 = (r**2-(u2-uc)**2)**0.5 + vc
    u3, v3 = Rotation(-angle, u2, v3)
    u3, v3 = u3+x0, v3+y0
    a = function.get_vector_angle(c, (u3, v3)) # dans le repère global
    self.Nodes[node] = (u3, v3)
    return a



  def _SetSegment(self, node):
    """Lecture des données XML pour les barres"""
    barre = node.get("id")

    noeud1 = node.get('start')
    noeud2 = node.get('end')
    try:
      rel1 = int(node.get('r0'))
    except:
      rel1 = 0
    try:
      rel2 = int(node.get('r1'))
    except:
      rel2 = 0
    k0 = node.get('k0')
    if not k0 is None:
      try:
        k0 = float(k0)
        self.RotuleElast[noeud1] = (barre, k0)
      except:
        self.PrintError("Erreur pour la rotule élastique du noeud : %s" % noeud1, 1)
    
    k1 = node.get('k1')
    if not k1 is None:
      try:
        k1 = float(k1)
        self.RotuleElast[noeud2] = (barre, k1)
      except:
        self.PrintError("Erreur pour la rotule élastique du noeud : %s" % noeud2, 1)
    

    mode = node.get('mode')
    if not mode is None:
      try:
        mode = int(mode)
      except ValueError:
        mode = 0
      if not mode == 0:
        self.assym_b[barre] = mode
    if noeud1 == noeud2:
      self.PrintError("Noeud identique dans %s" % barre, 0)
      self.status = 0
      return False
    if not (rel1 == 1 or rel1 == 0):
      self.status = 0
    if not (rel2 == 1 or rel2 == 0):
      self.status = 0
    try:
      pt1 = self.Nodes[noeud1]
    except KeyError:
      self.PrintError("Le noeud n'existe pas dans %s" % barre, 0)
      self.status = 0
      return
    try:
      pt2 = self.Nodes[noeud2]
    except KeyError:
      self.PrintError("Le noeud n'existe pas dans %s" % barre, 0)
      self.status = 0
      return
    if not len(pt1) == 2:
      try:
        content = self.__EmptyNodes[noeud1]
        coors = function.Str2NodeCoors(content, self.Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        self.Nodes[noeud1] = coors
        pt1 = coors
        del(self.__EmptyNodes[noeud1])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (noeud1, barre), 0)
        self.status = 0
        return
    if not len(pt2) == 2:
      try:
        content = self.__EmptyNodes[noeud2]
        coors = function.Str2NodeCoors(content, self.Nodes, unit=self.units['L'])
        if coors is False:
          raise KeyError
        self.Nodes[noeud2] = coors
        pt2 = coors
        del(self.__EmptyNodes[noeud2])
      except KeyError:
        self.PrintError("Noeud %s non défini dans la barre: %s" % (noeud2, barre), 0)
        self.status = 0
        return
    angle = function.get_vector_angle(pt1, pt2)
    long = function.get_vector_size(pt1, pt2)
    if long == 0:
      self.PrintError("La barre %s a une longueur nulle" % barre, 0)
      self.status = 0
        #return
    self.Lengths[barre] = long
    self.Angles[barre] = angle

# utile???
    if noeud1 in self.NodeNotLinked:
      #del(self.NodeNotLinked[noeud1])
      self.NodeNotLinked.remove(noeud1)
    if noeud2 in self.NodeNotLinked:
      self.NodeNotLinked.remove(noeud2)
      #del(self.NodeNotLinked[noeud2])

    self.Barres[barre] = [noeud1, noeud2, rel1, rel2]
    self.UserBars.append(barre)



  def _SetCaracs(self):
    """Affecte les caractéristiques géométriques des sections droites"""
    UB = self.UserBars
    CU = self.Curves
    SB = self.SuperBars
    Lengths = self.Lengths
    self.Sections = {}
    self.MQua = {}
    self.Section_H = {}
    self.Section_v = {}
    try:
      li_node = self.XMLNodes["geo"].iter('barre')
    except KeyError:
      text = "Erreur dans XMLNodes::pas de clé geo"
      self.PrintError(text, 0)
      raise XMLError(text)
      return
    li_warning_h, li_warning_v = [], []
    for node in li_node:
      barres = node.get("id")
      if barres == "*":
        b = "*"
        S = self._GetS(b, node)
        if not S is None:
          self.Sections[b] = S
        I = self._GetI(b, node)
        if not I is None:
          self.MQua[b] = I
        H = self._GetH(b, node)
        if not H is None:
          self.Section_H[b] = H
        else:
          li_warning_h.append(b)
        v = self._Getv(b, node)
        if not v is None:
          self.Section_v[b] = v
        else:
          li_warning_v.append(b)
      else:
        barres = barres.split(",")
        for b in barres:
          if b in UB:
            S = self._GetS(b, node)
            if not S is None:
             self.Sections[b] = S
            I = self._GetI(b, node)
            if not I is None:
              self.MQua[b] = I
            H = self._GetH(b, node)
            if not H is None:
              self.Section_H[b] = H
            else:
              li_warning_h.append(b)
            v = self._Getv(b, node)
            if not v is None:
              self.Section_v[b] = v
            else:
              li_warning_v.append(b)
            
          elif b in CU:
            arc = CU[b]
            l = arc.l # l peut être une variable dans eval
            b0, b1 = arc.b0, arc.b1
            S = self._GetS(b, node, False)
            I = self._GetI(b, node, False)
            H = self._GetH(b, node)
            v = self._Getv(b, node)
            if not H is None:
              self.Section_H[b] = H
            if not v is None:
              self.Section_v[b] = v
            if not S is None and not I is None:
              self.Sections[b] = S
              self.MQua[b] = I
              if H is None:
                li_warning_h.append(b)
              if v is None:
                li_warning_v.append(b)
              continue
            sym = self._GetSym(b, node)
            sS = self._GetSEval(b, node)
            if sS is None:
              continue
            sI = self._GetIEval(b, node)
            if sI is None:
              continue
            n = self._Getn(b1-b0+1, sym)
            if sym:
              n += 1
            sH = self._GetHEval(b, node)
            sv = self._GetvEval(b, node)
            if sH is None:
              li_warning_h.append(b)
            if sv is None:
              li_warning_v.append(b)
            i = b1
            s = 0 # curve abs
            for b in range(b0, b0+n+1):
              x = s + Lengths[b]/2 # x pour "eval"
              S = eval(sS)
              self.Sections[b] = S
              I = eval(sI)
              self.MQua[b] = I
              if not sH is None:
                H = eval(sH)
                self.Section_H[b] = H
              if not sv is None:
                v = eval(sv)
                self.Section_v[b] = v
              if sym:
                self.Sections[i] = S
                self.MQua[i] = I
                if not sH is None:
                  self.Section_H[i] = H
                if not sv is None:
                  self.Section_v[i] = v
              s += Lengths[b]
              i -= 1

          elif b in SB:
            sb = SB[b]
            b0, b1 = sb.b0, sb.b1
            S = self._GetS(b, node)
            I = self._GetI(b, node)
            H = self._GetH(b, node)
            if H is None:
              li_warning_h.append(b)
            v = self._Getv(b, node)
            if v is None:
              li_warning_v.append(b)
            if S is None or I is None:
              continue
            for i in range(b0, b1+1):
              self.Sections[i] = S
              self.MQua[i] = I
              if not H is None:
                self.Section_H[i] = H
              if not v is None:
                self.Section_v[i] = v

    # Affichage des warnings
    if li_warning_h:
      string = ','.join(li_warning_h)
      self.PrintError("Hauteur de section non valide ou absente pour les barres %s.\nCalcul des contraintes normales impossible." % string, 1)
    if li_warning_v:
      string = ','.join(li_warning_v)
      self.PrintError("Distance entre le cdg et la fibre supérieure non valide ou absente pour les barres %s.\nCalcul des contraintes normales impossible." % string, 1)

    self._SectionsValidate()

  def _GetS(self, name, node, stop_execution=True):
    """Retourne la valeur numérique de la section droite"""
    text = node.get("s")
    try:
      S = float(text)
      if S < 0:
        self.PrintError("Valeur nulle ou négative pour la section droite dans %s" % name, 0)
        self.status = 0
        return None
      return S*self.units['S']
    except (TypeError, ValueError):
      try:
        S = eval(text.replace('^', '**'))
        if S < 0:
          self.PrintError("Valeur nulle ou négative pour la section droite dans %s" % name, 0)
          self.status = 0
          return None
        return S*self.units['S']
      except:
        pass
      if stop_execution:
        self.PrintError("Section droite non valide pour la barre %s." % name, 0)
        self.status = 0
    return None


  def _GetSEval(self, name, node):
    """Retourne la valeur numérique de la section droite pour eval"""
    text = node.get("s")
    x, l = 1., 1.
    try:
      eval(text)
      return text
    except:
      self.PrintError("Equation non valide dans %s pour la section droite." % name, 0)
      self.status = 0
      return None

  def _GetI(self, name, node, stop_execution=True):
    """Retourne la valeur numérique de I"""
    text = node.get("igz")
    try:
      MQua = float(text)
      if MQua < 0:
        self.PrintError("Valeur nulle ou négative pour le moment quadratique dans %s" % name, 0)
        self.status = 0
        return None
      return MQua*self.units['I']
    except (TypeError, ValueError):
      try:
        MQua = eval(text.replace('^', '**'))
        if MQua < 0:
          self.PrintError("Valeur nulle ou négative pour le moment quadratique dans %s" % name, 0)
          self.status = 0
          return None
        return MQua*self.units['I']
      except:
        pass
      if stop_execution:
        self.PrintError("Moment quadratique non valide pour la barre %s." % name, 0)
        self.status = 0
    return None

  def _GetIEval(self, name, node):
    """Retourne la valeur numérique de le moment quadratique pour eval"""
    text = node.get("igz")
    x, l = 1., 1.
    try:
      eval(text)
      return text
    except:
      self.PrintError("Equation  non valide dans %s pour le moment quadratique." % name, 0)
      self.status = 0
      return None

  def GetH(self, name):
    """Retourne la valeur de la hauteur de la section droite à partir du dictionnaire"""
    H = self.Section_H
    if name in H:
      return H[name]
    Curves = self.Curves
    for arc in Curves:
      b0, b1 = Curves[arc].b0, Curves[arc].b1
      if name >= b0 and name <= b1:
        if arc in H:
          return H[arc]
    if "*" in H:
      return H["*"]
    return None

  def _GetH(self, name, node):
    """Retourne la valeur numérique de H à partir du XML"""
    try:
      H = float(node.get("h")) # voir pour abs
      return H*self.units['L']
    except (TypeError, ValueError):
      return None

  def _GetHEval(self, name, node):
    """Retourne la valeur numérique de H pour eval"""
    text = node.get("h")
    if text == '':
      return None
    x, l = 1., 1.
    try:
      eval(text)
      return text
    except:
      self.PrintError("Equation  non valide dans %s pour la hauteur H." % name, 0)
      self.status = 0
      return None

  def _Getv(self, name, node):
    """Retourne la valeur numérique de v"""
    try:
      v = float(node.get("v"))
      return v*self.units['L']
    except (TypeError, ValueError):
      return None

  def Getv(self, name):
    """Retourne la valeur de la hauteur de v à partir du dictionnaire"""
    v = self.Section_v
    if name in v:
      return v[name]
    Curves = self.Curves
    for arc in Curves:
      b0, b1 = Curves[arc].b0, Curves[arc].b1
      if name >= b0 and name <= b1:
        if arc in v:
          return v[arc]
    if "*" in v:
      return v["*"]
    return None

  def _GetvEval(self, name, node):
    """Retourne la valeur numérique de v pour eval"""
    text = node.get("v")
    if text == '':
      return None
    x, l = 1., 1.
    try:
      eval(text)
      return text
    except:
      self.PrintError("Equation  non valide dans %s pour la hauteur v." % name, 0)
      self.status = 0
      return None

  def _GetSym(self, name, node):
    """Teste si l'arc est symétrique au niveau des sections droites"""
    sym = node.get("sym")
    if sym == "0" or sym is None:
      sym = False
    elif sym == "1":
      sym = True
    return sym

  def _Getn(self, n, sym):
    """Retourne la moitié des barres ou la totalité suivant la symétrie"""
    if sym:
      if n % 2 == 0:
        n_iter = n/2
      else:
        n_iter = int(n/2) + 1
    else:
      n_iter = n-1
    return n_iter




  def _SectionsValidate(self):
    """Retourne vrai ou faux selon la validité du dictionnaire des sections droites"""
    #print("Sections=", self.Sections)
    if "*" in self.Sections:
      return
    Curves = self.Curves
    for barre in self.UserBars:
      if not barre in self.Sections:
        self.PrintError("La barre %s n'a pas de section droite" % barre, 0)
        self.status = 0
        return False
      if not barre in self.MQua:
        self.PrintError("La barre %s n'a pas de moment quadratique" % barre, 0)
        self.status = 0
        return False
    for arc in Curves:
      if not arc in self.Sections:
        b0 = self.Curves[arc].b0
        try:
          self.Sections[b0] # on teste une seule barre de l'arc
        except KeyError:
          self.PrintError("L'arc %s n'a pas de section droite" % arc, 0)
          self.status = 0
          return False
    return True

  def _SetYoung(self):
    """Récupération des modules d'Young"""
    self.Youngs = {}
    try:
      li_node = self.XMLNodes["material"].iter('barre')
    except KeyError:
      text = "Erreur dans XMLNodes::pas de clé material"
      self.PrintError(text, 0)
      raise XMLError(text)
    if not li_node:
      self.PrintError("Module d'Young manquant", 0)
      self.status = 0
      return
    for node in li_node:
      barre = node.get("id")
      try:
        content = node.get("young")
        young = abs(float(content))*self.units['E']
      except (TypeError, ValueError):
        self.PrintError("Module d'Young non valide dans %s" % barre, 0)
        self.status = 0
        return
      if barre == "*":
        self.Youngs['*'] = young
        continue
      barres = barre.split(",")
      for elem in barres:
        if elem in self.Curves:
          arc = self.Curves[elem]
          b0, b1 = arc.b0, arc.b1
          for barre in range(b0, b1+1):
            self.Youngs[barre] = young
          continue
        if elem in self.SuperBars:
          arc = self.SuperBars[elem]
          b0, b1 = arc.b0, arc.b1
          for barre in range(b0, b1+1):
            self.Youngs[barre] = young
          continue
        self.Youngs[elem] = young
    self._YoungValidate()

  def _YoungValidate(self):
    if "*" in self.Youngs:
      return
    for barre in self.UserBars:
      if not barre in self.Youngs:
        self.PrintError("La barre %s n'a pas de module élastique" % barre, 0)
        self.status = 0
        return False


  def _GetYoung(self, barre):
    """Retourne la valeur du modue d'Young"""
    if barre in self.Youngs:
      return self.Youngs[barre]
    return self.Youngs["*"]

  def GetBarreName(self, name):
    """Retourne le nom d'une barre à partir de la barre incrémentale"""
    barres = self.UserBars
    if name in barres:
      return name
    Curves = self.Curves
    for arc in Curves:
      if name == arc:
        return arc
    if isinstance(name, str): raise TypeError("name de type str au lieu int")
    super_bars = self.SuperBars
    barres = self.Barres
    for b in super_bars:
      sb = self.SuperBars[b]
      b0, b1 = sb.b0, sb.b1
      if name >= b0 and name <= b1:
        N0, N1 = barres[name][0:2]
        return "%s (%s, %s)" % (b, N0, N1)
    return None

  def GetSBarreName(self, name):
    """Retourne le nom d'une super barre à partir de la barre incrémentale"""
    super_bars = self.SuperBars
    barres = self.Barres
    for b in super_bars:
      sb = self.SuperBars[b]
      b0, b1 = sb.b0, sb.b1
      if name >= b0 and name <= b1:
        N0, N1 = barres[name][0:2]
        return "%s (%s, %s)" % (b, N0, N1)
    return None

  def GetBars(self):
    """Retourne la liste des barres utilisateurs et des sous-barres d'une barre continue""" 
    names = list(self.UserBars)
    for name in self.SuperBars:
      sbar = self.SuperBars[name]
      b0, b1 = sbar.b0, sbar.b1
      for b in range(b0, b1+1):
        names.append(b)
    return names

  def GetBarsNames(self):
    """Retourne un dictionnaire contenant comme clé le nom d'une barre et comme valeur le nom complet - Contient les barres normales et les barres des SuperBar"""
    di = {}
    bars = self.UserBars
    for bar in bars:
      di[bar] = bar
    sbs = self.SuperBars
    for key in sbs:
      sb = sbs[key]
      di.update(self.GetSBarsNames(sb, key))
    return di

  def GetBarsNames2(self, barres):
    """Retourne un dictionnaire des noms des barres d'une barre de type SuperBar dans le format B1 (N1, N2)"""
    UserBars = self.UserBars
    di = {}
    for b in barres:
      if b in UserBars:
        di[b] = b
        continue
      name = self.GetSBarreName(b)
      if b is None:
        continue
      di[b] = name
    return di

  def GetSBarsNames(self, sb, sb_name):
    """Retourne les noms des barres d'une barre de type SuperBar dans le format B1 (N1, N2)"""
    barres = self.Barres
    di = {}
    for b in range(sb.b0, sb.b1+1):
      N0, N1 = barres[b][0:2]
      di[b] = "%s (%s, %s)" % (sb_name, N0, N1)
    return di


  def GetLength(self, name):
    """Retourne la valeur de la longueur d'une barre ou d'un arc complet"""
    lengths = self.Lengths
    if name in lengths:
      return lengths[name]
    super_bars = self.SuperBars
    if name in super_bars:
      sb = super_bars[name]
      return sb.get_size(lengths)
    Curves = self.Curves
    if not name in Curves:
      return None
    arc =  Curves[name]
    l = arc.get_size(lengths)
    return l

  def GetAngle(self, name):
    """Retourne la valeur d'une section droite d'une barre ou d'un arc à partir de son nom"""
    #barres = self.UserBars
    Angles = self.Angles
    if name in Angles:
      return Angles[name]
    super_bars = self.SuperBars
    if name in super_bars:
      sb = super_bars[name]
      return sb.get_angle()
    Curves = self.Curves
    if not name in Curves:
      return None
    arc =  Curves[name]
    return arc.get_angle()

  def GetSection(self, name):
    """Retourne la valeur d'une section droite d'une barre ou d'un arc à partir de son nom"""
    Sections = self.Sections
    if name in Sections:
      return Sections[name]
    Curves = self.Curves
    if name in Curves:
      arc =  Curves[name]
      try:
        return Sections[arc]
      except KeyError:
        pass # finir section variable
    if '*' in Sections:
      return Sections["*"]
    return None

  def GetMQua(self, name):
    """Retourne la valeur d'un moment quadratique d'une barre ou d'un arc à partir de son nom"""
    MQua = self.MQua
    if name in MQua:
      return MQua[name]
    Curves = self.Curves
    if name in Curves:
      arc =  Curves[name]
      try:
        return MQua[arc]
      except KeyError:
        pass # finir section variable
    if '*' in MQua:
      return MQua["*"]
    return None

  def _GetSection(self, name):
    """Retourne la valeur de la surface de la section droite"""
    Sections = self.Sections
    if name in Sections:
      return Sections[name]
    Curves = self.Curves
    try:
      name = int(name)
      for arc in Curves:
        if not arc in Sections:
          continue
        b0, b1 = Curves[arc].b0, Curves[arc].b1
        if name >= b0 and name <= b1:
          return Sections[arc]
      return Sections["*"]
    except ValueError:
      return Sections["*"]


  def _GetMQua(self, name):
    """Retourne la valeur du moment quadratique de la section droite"""
    MQua = self.MQua
    if name in MQua:
      return MQua[name]
    Curves = self.Curves
    try:
      name = int(name)
      for arc in Curves:
        if not arc in MQua:
          continue
        b0, b1 = Curves[arc].b0, Curves[arc].b1
        if name >= b0 and name <= b1:
          return MQua[arc]
      return MQua["*"]
    except ValueError:
      return MQua["*"]

  def GetMV(self, barre):
    """Retourne la masse volumique d'une barre"""
    if barre in self.VolMass:
      return self.VolMass[barre]
    return self.VolMass["*"]

  def SetMV(self):
    """Attribue la masse volumique des barres"""
    self.VolMass = {}
    try:
      li_node = self.XMLNodes["material"].iter('barre')
    except KeyError:
      text = "Erreur dans XMLNodes::pas de clé material"
      self.PrintError(text, 0)
      raise XMLError(text)
    if len(self.XMLNodes["material"]) == 0:
      return False
    for node in li_node:
      barre = node.get("id")
      try:
        content = node.get("mv")
        mv = abs(float(content))*self.units['M']
      except (TypeError, ValueError):
        self.PrintError("Masse volumique non valide dans %s" % barre, 0)
        return False
      if barre == "*":
        self.VolMass["*"] = mv
        continue
      # plusieurs barres par lignes
      liBarre = barre.split(",")
      for elem in liBarre:
        self.VolMass[elem] = mv
    return True

  def VerifAlphaExist(self, barres):
    """Pour chaque barre dans barres, vérifie si alpha est disponible"""
    #print("vvv", self.Alphas)
    if "*" in self.Alphas:
      return True
    for barre in barres:
      if not barre in self.Alphas:
        self.PrintError("Il manque le coefficient de dilatation pour la barre: %s" % barre, 0)
        return False
    return True

  def VerifHExist(self, charBarTherm, ArcChars):
    """Pour chaque barre ou arc, vérifie si la hauteur des sections
    droites est disponible"""
    if '*' in self.Section_H:
      if not self.Section_H['*'] is None:
        return True
    barres = self.UserBars
    for barre in barres:
      if not barre in charBarTherm:
        continue
      if not barre in self.Section_H:
        self.PrintError("Il manque la hauteur de la section droite pour la barre: %s" % barre, 0)
        return False
    for arc in ArcChars:
      if not "th" in ArcChars[arc]:
        continue
      if not arc in self.Section_H:
        return False
    return True

  def _SetAlpha(self):
    """Récupération des coefficients de dilatation
    Attention : la récupération des chargements doit précéder"""
    # évite de recalculer pour chaque cas de charge
    #print("_SetAlpha")
    if hasattr(self, 'Alphas'):
      return
    self.Alphas = {}
    try:
      li_node = self.XMLNodes["material"].iter('barre')
    except KeyError:
      text = "Erreur dans XMLNodes::pas de clé material"
      self.PrintError(text, 0)
      raise XMLError(text)
    for node in li_node:
      barre = node.get("id")
      try:
        content = node.get("alpha")
        alpha = abs(float(content))
      except (TypeError, ValueError):
        continue
      if barre == "*":
        self.Alphas["*"] = alpha
        continue
      barres = barre.split(",")
      for elem in barres:
        if elem in self.Curves:
          arc = self.Curves[elem]
          b0, b1 = arc.b0, arc.b1
          for barre in range(b0, b1+1):
            self.Alphas[barre] = alpha
          continue
        if elem in self.SuperBars:
          arc = self.SuperBars[elem]
          b0, b1 = arc.b0, arc.b1
          for barre in range(b0, b1+1):
            self.Alphas[barre] = alpha
          continue
        self.Alphas[elem] = alpha

  def _GetAlpha(self, barre):
    """Retourne le coefficient de dilatation"""
    if barre in self.Alphas:
      return self.Alphas[barre]
    return self.Alphas["*"]

  # recherche les liaisons et les affaissements d'appuis
  def _GetLiaison(self):
    self.Liaisons = {}
    self.AppuiIncline = {}
    self.RaideurAppui = {}
    try:
      li_node = self.XMLNodes["node"].iter()
    except KeyError:
      text = "Erreur dans XMLNodes::pas de liaison"
      self.PrintError(text, 0)
      raise XMLError(text)
    #li_arc = self.XMLNodes["node"].iter('arc')
    #li_node.extend(li_arc)
    for node in li_node:
      if node.get("liaison") is None:
        continue
      noeud = node.get("id")
      content = node.get("liaison")
      content = content.split(",") 
      try:
        liaison = int(content[0])
      except ValueError:
        continue
      if liaison == 3:
        li = []
        for i in range(1, 4):
          if content[i].lower() == 'inf':
            val = "inf" # rigidité infinie
          else:
            try:
              val = abs(float(content[i])*self.units['F'] / self.units['L'])
            except ValueError:
              self.PrintError("Erreur pour les rigidités du noeud: %s" % noeud, 0)
              self.status = 0
              continue
          li.append(val)
          self.RaideurAppui[noeud] = li
      elif liaison == 2 and len(content) == 2:
        # on limite entre -90 et 90°
        try:
          teta = math.pi/180*float(content[1])
        except (IndexError, ValueError):
          self.PrintError("Erreur pour l'appui incliné du noeud: %s" % noeud, 0)
          self.status = 0
          continue
        if teta >= 0:
          teta = min(teta, math.pi/2)
        else:
          teta = max(teta, -math.pi/2)
        if not teta == 0:
          self.AppuiIncline[noeud] = teta
      self.Liaisons[noeud] = liaison
    if self.status and len(self.Liaisons) == 0:
      self.PrintError("Erreur: pas de liaison", 0)
      self.status = 0
      return


  def _GetRotulePlast(self):
    self.RotulePlast = {}
    try:
      li_node = self.XMLNodes["barre"].iter('rot_plast')
    except KeyError:
      text = "Erreur dans XMLNodes::pas de clé barre"
      self.PrintError(text, 0)
      raise XMLError(text)
    for xml in li_node:
      barres = xml.get("barre")
      barres = barres.split(',')
      mp = xml.get("mp")
      noeud = xml.get("node")
      try:
        mp = float(mp)
# vérifier si le noeud existe et est sur la barre

      except ValueError:
        self.status = 0
        self.PrintError("Erreur pour la rotule élastique du noeud : %s" % noeud, 1)
        continue
      self.RotulePlast[noeud] = (barres[0], barres[1], mp)
      #print("self.RotulePlast=", self.RotulePlast)


  
  def FirstBarre(self):
    """Retourne la première barre par ordre alphabétique"""
    barres = self.UserBars
    if not len(barres) == 0:
      return barres[0]
    sb = list(self.SuperBars.values())
    if not len(sb) == 0:
      b = sb[0]
      return b.b0
    return None


  def IsHorizontal(self):
    """Vérifie que la structure est bien une poutre droite  """
    try:
      return self.is_horizontal
    except AttributeError:
      self.is_horizontal = self.GetIsHorizontal()
      return self.is_horizontal
      
# finir pour les arcs? 
  def GetIsHorizontal(self):
    if self.status == 0:
      return False
    for barre, angle in self.Angles.items():
      if not angle == 0.:
        return False
    return True

 
  # retourne le maximum de la hauteur et de la largeur de la structure
  def MaxSize(self, box):
    return max(box[2]-box[0], box[3]-box[1])


  #------------------ ECRITURE DE LA MATRICE DES DDL ------------------------




  def CalculDegreH(self):
    """Calcul du degré d'hyperstaticité"""
    nbbarreparnoeud = self.nBarByNode
    nbbarrerelax = self.RBarByNode
    H = 0
    for noeud in self.Nodes:
      n = nbbarreparnoeud.get(noeud, 2)
      m = nbbarrerelax.get(noeud, 0)
      if n == m:
        H += n*2-2
      else:
        H += (n-m)*3+m*2-3
    n_bars = len(self.Barres)
    H = H-n_bars*3+self.n_liaison
    return H


  def _RelaxNode(self):
    """Relaxe les noeuds
    Crée le dictionnaire des noeuds relaxés"""
    relaxs = self.IsRelax # vide
    liaisons = self.Liaisons
    n_bar_node = self.nBarByNode
    n_relax_bar_node = self.RBarByNode
    li = []
    for noeud in self.UserNodes:
      n = n_bar_node.get(noeud, 2)
      n_relax = n_relax_bar_node.get(noeud, 0)
      if n == n_relax:
        if not n == 0:
          relaxs[noeud] = 1
        if noeud in liaisons and liaisons[noeud] == 0:
          # on transforme l'encastrement en rotule
          liaisons[noeud] = 1
      elif n >= 2 and n == n_relax+1:
        if noeud in liaisons and liaisons[noeud] in [0, 3]:
          continue
        relaxs[noeud] = 1
        li.append(noeud)

    barres = self.Barres
    for barre in barres: # on relaxe la barre qui ne l'est pas
      _barres = barres[barre]
      if _barres[0] in li:
        _barres[2] = 1
      if _barres[1] in li:
        _barres[3] = 1

  def _GetBarreByNode(self):
    """Crée un attribut de type dictionnaire contenant pour chaque noeud une double liste des barres commencant ou se terminant sur le noeud"""
    BarByNode = {}
    nBarByNode = {}
    nRelaxByNode = {}
    nodes = self.Nodes
    for node in nodes:
      BarByNode[node] = [[], []]
      nBarByNode[node] = 0
      nRelaxByNode[node] = 0
    barres = self.Barres
    for barre in barres:
      node0, node1, relax0, relax1 = barres[barre]
      BarByNode[node0][0].append(barre)
      nBarByNode[node0] += 1
      nRelaxByNode[node0] += relax0

      BarByNode[node1][1].append(barre)
      nBarByNode[node1] += 1
      nRelaxByNode[node1] += relax1
    self.BarByNode = BarByNode
    # 2 est la valeur par défaut avec di.get(noeud, 2), fonctionne donc sans valeur si n = 2
    self.nBarByNode = nBarByNode
    self.RBarByNode = nRelaxByNode

  def _SetAppuiIncline(self, teta, li):
    """Modifie la liste des coefficients des sollicitations afin d'effectuer un changement de repère (du repère de la barre vers le repère lié à l'appui simple
   pour tenir compte de la présence d'un appui simple incliné"""
    x, y = li[0], li[1]
    li[0] = x*math.cos(teta) + y*math.sin(teta)
    li[1] = -x*math.sin(teta) + y*math.cos(teta) # XXX test



class StructureDrawing(Structure):
  def __init__(self, xml):
    self.XML = xml
    self.errors = []
    self.width, self.height = 0, 0
    self.status = -1
    try:
      self.GetXMLElem()
    except:
      return
    #self.status = 1
    # -1: xml error, 0: erreur lecture, 1: données valide mais erreur inversion
    # 2: inversion matrice rigidité ok
    try:
      self._ExtractData()
    except XMLError:
      #self.status = -1
      pass

class StructureFile(Structure):

  def __init__(self, file):
    self.errors = []
    self.file = file
    self.name = os.path.basename(file)
    xml = self._ReadXMLFile(file)
    self.width, self.height = 0, 0
    if xml is None: 
      self.PrintError("Une erreur est survenue dans la structure XML du document.\nMerci de corriger l'erreur en éditant le fichier avec un éditeur de texte.", 0)
      self.status = -1
      return
    Structure.__init__(self, xml)
    
  def _ReadXMLFile(self, file):
    """Création de l'objet XML à partir du fichier"""
    try:
      tree = ET.parse(file)
    except:
      tree = None
    return tree


class ArcCharTh(object):

  def __init__(self):
    pass

class ArcCharPP(object):

  def __init__(self, struct, Char, arc, mv):
    b0, b1 = arc.b0, arc.b1
    lengths = struct.Lengths
    barres = struct.Barres
    for barre in range(b0, b1+1):
      S = struct._GetSection(barre)
      l = lengths[barre]
      qy = -S*mv*struct.G*l/2
      N0, N1 = barres[barre][0:2]
      if N0 in Char._charArcNode:
        Char._charArcNode[N0][1] += qy
      else:
        Char._charArcNode[N0] = [0., qy, 0.]
      if N1 in Char._charArcNode:
        Char._charArcNode[N1][1] += qy
      else:
        Char._charArcNode[N1] = [0., qy, 0.]
    self.points = [0., 1.]
    S = struct._GetSection(b0)
    qy0 = -S*mv*struct.G
    S = struct._GetSection(b1)
    qy1 = -S*mv*struct.G
    self.values = {0.: [0., 0., 0., qy0], 1.: [0., qy1, 0., 0.]}
    self.barres = {}
    self.barres[0.] = (b0, 0.)
    l = lengths[b1]
    self.barres[1.] = (b1, l)

class ArcCharFp(object):
  """Classe pour les chargements ponctuels sur un arc"""

  def __init__(self, struct, Char, dl, b, alpha, fpx, fpy, mz):
    print("init ArcChar" , dl, b, alpha, fpx, fpy, mz)
    self.values = {}
    self.add(struct, Char, dl, b, alpha, fpx, fpy, mz)

  def add(self, struct, Char, dl, b, alpha, fpx, fpy, mz):
    barres = struct.Barres
    if alpha in self.values:
      b, dl, fpx0, fpy0, mz0 = self.values[alpha]
      self.values[alpha] = [b, dl, fpx0+fpx, fpy0+fpy, mz0+mz]
    else:
      self.values[alpha] = [b, dl, fpx, fpy, mz]
    N0, N1 = barres[b][0:2]
    if N0 in Char._charArcNode:
      Char._charArcNode[N0][0] += fpx*(1-dl)
      Char._charArcNode[N0][1] += fpy*(1-dl)
      Char._charArcNode[N0][2] += mz*(1-dl)
    else:
      Char._charArcNode[N0] = [fpx*(1-dl), fpy*(1-dl), mz*(1-dl)]
    if N1 in Char._charArcNode:
      Char._charArcNode[N1][0] += fpx*dl
      Char._charArcNode[N1][1] += fpy*dl
      Char._charArcNode[N1][2] += mz*dl
    else:
      Char._charArcNode[N1] = [fpx*dl, fpy*dl, mz*dl]

class ArcCombiFp(object):
  """Classe pour les chargements ponctuels sur un arc"""

  def __init__(self, Char, coef):
    self.values = {}
    self.add(Char, coef)

  def add(self, Char, coef):
    for alpha in Char.values:
      b0, dl0, fpx0, fpy0, mz0 = Char.values[alpha]
      if alpha in self.values:
        b, dl, fpx, fpy, mz = self.values[alpha]
        self.values[alpha] = [b, dl, fpx+fpx0*coef, fpy+fpy0*coef, mz+mz0*coef]
      else:
        self.values[alpha] = [b0, dl0, fpx0*coef, fpy0*coef, mz0*coef]
 
class ArcCharQu(object):
  """Classe de base pour les chargements linéiques sur un arc"""

  def __init__(self, struct, Char, arc, pos0, pos1, qx0, qy0, qx1, qy1):
    if pos0 == 0.:
      self.points = [pos0]
      self.values = {0.: [0., 0., qx0, qy0]}
    else:
      self.points = [0., pos0]
      self.values = {0.: [0., 0., 0., 0.], pos0: [0., 0., qx0, qy0]}
    if not pos1 == 1.:
      self.points.append(pos1)
      self.values[1.] = [0., 0., 0., 0.]
    self.values[pos1] = [qx1, qy1, 0., 0.]
    self.points.append(1.)
    self.barres = {}
    self.GetAffectedNodes(struct, Char, arc, pos0, pos1, qx0, qy0, qx1, qy1)

  def add(self, pos0, pos1, qx0, qy0, qx1, qy1, coef=1):
    """Ajoute un chargement trapézoidal à des chargements existants"""
    #print("add", pos0, pos1)
    if not coef == 1.:
      qx0, qy0, qx1, qy1 = qx0*coef, qy0*coef, qx1*coef, qy1*coef
    values = self.values
    points = self.points
    #print("points=", points, values)
    if not pos0 in points:
      points.append(pos0)
    if not pos1 in points:
      points.append(pos1)
    points.sort()
    n0 = points.index(pos0)
    n1 = points.index(pos1)
    if not pos0 in values:
      if n0 + 1 == n1:
        next_pos = points[n1]
        if not next_pos in values:
          next_pos = points[n1+1]
      else:
        next_pos = points[n0+1]
      next_val = values[next_pos]
      prec_pos = points[n0-1]
      prec_val = values[prec_pos]
      valx = prec_val[2]+(next_val[0]-prec_val[2])*(pos0-prec_pos)/(next_pos-prec_pos)
      valy = prec_val[3]+(next_val[1]-prec_val[3])*(pos0-prec_pos)/(next_pos-prec_pos)
      values[pos0] = [valx, valy, valx, valy]

    if not pos1 in values:
      next_pos = points[n1+1]
      next_val = values[next_pos]
      prec_pos = points[n1-1]
      prec_val = values[prec_pos]
      valx = prec_val[2]+(next_val[0]-prec_val[2])*(pos1-prec_pos)/(next_pos-prec_pos)
      valy = prec_val[3]+(next_val[1]-prec_val[3])*(pos1-prec_pos)/(next_pos-prec_pos)
      values[pos1] = [valx, valy, valx, valy]

    values[pos0][2] += qx0
    values[pos0][3] += qy0
    values[pos1][0] += qx1
    values[pos1][1] += qy1
    if not n1-n0 == 1:
      for i in range(n0+1, n1):
        pos = points[i]
        qx = qx0 + (qx1-qx0)/(pos1-pos0)*(pos-pos0)
        qy = qy0 + (qy1-qy0)/(pos1-pos0)*(pos-pos0)
        values[pos][0] += qx
        values[pos][1] += qy
        values[pos][2] += qx
        values[pos][3] += qy


  def GetAffectedNodes(self, struct, Char, name, rpos0, rpos1, qx0, qy0, qx1, qy1):
    """Retourne un dictionnaire des noeuds et longueurs sur laquelle la charge doit etre appliquée pour la transformer en charge nodale"""
    def proj(a, is_proj):
      if is_proj == 1:
        return math.cos(a)
      return 1.

    is_proj = self.proj
    lengths = struct.Lengths
    angles = struct.Angles
    barres = struct.Barres
    arc = struct.Curves[name]
    l = arc.get_size(lengths)
    pos0, pos1 = rpos0*l, rpos1*l
    dl = pos1-pos0
    b0, b1 = arc.b0, arc.b1
    start = (b0, 0.)
    end = (b1, l-lengths[b1])
    s = 0.
    di = {} # valeur identique pour proj =0 ou 2 !!!
    dsprec = 0.
    x = 0
    for barre in range(b0, b1+1):
      N0, N1 = barres[barre][0:2]
      ds = lengths[barre]
      a = angles[barre]
      if s + ds < pos0:
        dsprec = ds
        s += ds
        start = (barre+1, s)
        continue
      dF = ds/2*proj(a, is_proj)
      x+=dF
      if N0 in di:
        di[N0] += dF
        #node_pos[N0] += ds/2
      else:
        di[N0] = dF
        #node_pos[N0] = ds/2
      if N1 in di:
        di[N1] += dF
        #node_pos[N1] += ds/2
      else:
        di[N1] = dF
        #node_pos[N1] = ds/2
      if s + ds >= pos1:
        end = (barre, s)
        break
      dsprec = ds
      s += ds
    # réglage des extrémités de l'intervalle
    b0, u0 = start
    b1, u1 = end
    l0 = lengths[b0]
    N0, N1 = barres[b0][0:2]
    self.barres[rpos0] = (b0, pos0-u0)
    self.barres[rpos1] = (b1, pos1-u1)
    #print(pos1, u1)
    a = angles[b0]
    if b0 == b1:
      if self.u1 <= l0/2:
        di[N0] = (self.u1-self.u0)*proj(a, is_proj)
        #node_pos[N0] = self.u1-self.u0
        del(di[N1])
        #del(node_pos[N1])
      elif self.u0 >= l0/2:
        del(di[N0])
        del(node_pos[N0])
        di[N1] = (self.u1-self.u0)*proj(a, is_proj)
        #node_pos[N1] = self.u1-self.u0
      else:
        di[N0] = (l/2-self.u0)*proj(a, is_proj)
        #node_pos[N0] = l/2-self.u0
        di[N1] = (self.u1-l/2)*proj(a, is_proj)
        #node_pos[N1] = self.u1-l/2
    else:
      if u0+l0/2 > pos0:
        di[N0] -= (pos0-u0)*proj(a, is_proj)
        #node_pos[N0] -= pos0-u0
      else:
        del(di[N0])
        #del(node_pos[N0])
        di[N1] -= (pos0-u0-l0/2)*proj(a, is_proj) 
        #node_pos[N1] -= pos0-u0-l0/2
      N0, N1 = barres[b1][0:2]
      l0 = lengths[b1]
      if u1+l0/2 > pos1:
        di[N0] -= (u1+l0/2-pos1)*proj(a, is_proj)
        #node_pos[N0] -= u1+l0/2-pos1
        del(di[N1])
        #del(node_pos[N1])
      else:
        di[N1] -= (u1+l0-pos1)*proj(a, is_proj)
        #node_pos[N1] -= u1+l0-pos1
# ------- test ----------
    #i=0
    #for n in di:
    #  i += di[n]
    #print(i, pos1-pos0)
    #assert abs(i - (pos1-pos0)) < 1e-5
# ------ fin test --------
    if is_proj == 2: # radial
      self._SetArcChar2(arc, struct, Char, di, qy0, qy1, dl)
    else:
      self._SetArcChar(Char, di, qx0, qy0, qx1, qy1, dl)

  def _SetArcChar(self, Char, di, qx0, qy0, qx1, qy1, l0):
    """Remplit l'attribut des charges nodales pour l'arc"""
    l = 0
    for node in di:
      #dl = node_pos[node]
      dl = di[node]
      if node in Char._charArcNode:
        Char._charArcNode[node][0] += (qx0+(qx1-qx0)/l0*l)*dl
        Char._charArcNode[node][1] += (qy0+(qy1-qy0)/l0*l)*dl
      else:
        Char._charArcNode[node] = [(qx0+(qx1-qx0)/l0*l)*dl, (qy0+(qy1-qy0)/l0*l)*dl, 0.]
      l += dl

  def _SetArcChar2(self, arc, struct, Char, di, q0, q1, l0):
    """Remplit l'attribut des charges nodales pour l'arc pour une charge radiale"""
    b0, b1 = arc.b0, arc.b1
    barres = struct.Barres
    angles = struct.Angles
    l = 0
    first = True
    for barre in range(b0, b1+1):
      N0 = barres[barre][0]
      if not N0 in di:
        continue
      dl = di[N0]
      q = q0+(q1-q0)/l0*l
      if first:
        a = angles[barre]
        first = False
      else:
        a = (angles[barre-1]+angles[barre])/2
      if N0 in Char._charArcNode:
        Char._charArcNode[N0][0] += -q*dl*math.sin(a)
        Char._charArcNode[N0][1] += q*dl*math.cos(a)
      else:
        Char._charArcNode[N0] = [-q*dl*math.sin(a), q*dl*math.cos(a), 0.]
      l += dl
    N1 = barres[b1][1]
    if not N1 in di:
      return
    dl = di[N1]
    a = angles[b1] # prendre la moyenne
    if N1 in Char._charArcNode:
      Char._charArcNode[N1][0] += -q1*dl*math.sin(a)
      Char._charArcNode[N1][1] += q1*dl*math.cos(a)
    else:
      Char._charArcNode[N1] = [-q1*dl*math.sin(a), q1*dl*math.cos(a), 0.]

class ArcCombiQu(ArcCharQu):
  """Classe pour le chargement d'un arc dans une combinaison - Ne sert qu'au dessin"""

  def __init__(self, char, coef):
  # ne pas executer init classe parent
    self.points = list(char.points)
    self.barres = copy.deepcopy(char.barres)
    self.values = copy.deepcopy(char.values)
    if not coef == 1.:
      for key, values in self.values.items():
        self.values[key] = [i*coef for i in values]

class ArcCharQu0(ArcCharQu):
  """Classe pour un cas de charge sur un arc de type linéique"""

  def __init__(self, struct, Char, arc, pos0, pos1, qx0, qy0, qx1, qy1):
    self.proj = 0
    ArcCharQu.__init__(self, struct, Char, arc, pos0, pos1, qx0, qy0, qx1, qy1)

class ArcCharQu1(ArcCharQu):
  """Classe pour un cas de charge sur un arc de type répartie projetée"""

  def __init__(self, struct, Char, arc, pos0, pos1, qx0, qy0, qx1, qy1):
    self.proj = 1
    ArcCharQu.__init__(self, struct, Char, arc, pos0, pos1, qx0, qy0, qx1, qy1)

class ArcCharQu2(ArcCharQu):
  """Classe pour un cas de charge sur un arc de type radiale"""

  def __init__(self, struct, Char, arc, pos0, pos1, qx0, qy0, qx1, qy1):
    self.proj = 2
    ArcCharQu.__init__(self, struct, Char, arc, pos0, pos1, qx0, qy0, qx1, qy1)




class CasCharge(object):

  def __init__(self, name, xmlnode, struct):
    self.name = name
    self.struct = struct
    # status :: 0: warning lecture, 1: lecture ok 
    self.status = -1
    self._SetChar(name, xmlnode)
    self._GetNodeDeps(name, xmlnode)

  def Solve(self, struct, MatK, MatChar):
    """Résolution du système pour un cas donné"""
    #print("Solve")
    #n = size(matK)**0.5
    #trace1 = matK.trace()
    #det1 = linalg.det(matK) 
    #print("trace1 = ", trace1,"det = ", det1)
    #print("rapport = ", det1/trace1, det1/trace1**n)
    if MatK is None:
      struct.PrintError("Les valeurs des degrés de liberté sont excessives dans \"%s\".\nVérifier le degré d'Hyperstaticité de la structure ou que\nle chargement n'est pas trop grand par rapport à la rigidité des barres." % self.name, 0)
      self.status = 0
      return 
    if MatK.size == 0:
      self._DdlEmpty()
      self._GetRotationIso()
      self.status = 1
    else:
      resu = numpy.dot(MatK, MatChar)
      resu = resu.transpose()[0]
      self.GetDDLValues(resu)

    if self._TestInfiniteDep() == False:
      struct.PrintError("Les valeurs des degrés de liberté sont excessives dans \"%s\".\nVérifier le degré d'Hyperstaticité de la structure ou que\nle chargement n'est pas trop grand par rapport à la rigidité des barres." % self.name, 0)
      self.status = 0
      self._DdlEmpty()
      return 
    self._GetEndBarSol()
    self.GetReac()

  def _GetNodeDeps(self, name, xml):
    """Récupère les déplacements d'appui suivant X et Y.
    Si appui incliné, le déplacement est unique et correspond au déplacement perpendiculaire à l'appui."""
    struct = self.struct
    self.NodeDeps = {}
    for i, case in enumerate(xml):
      case_name = case.get("id")
      #print("case_name=", case_name)
      if not case_name == name:
        continue
      lichar = case.iter('depi')
      for char in lichar:
        noeud = char.get("id")
        if not noeud:
          continue
        value = char.get("d")
        if value is None:
          continue
        value = value.split(",")
        if len(value) == 2:
          try:
            depX = float(value[0])*self.struct.units['L']
          except ValueError:
            struct.PrintError("Erreur pour l'affaissement d'appui du noeud (X): %s" % noeud, 1)
            depX = 0.
          try:
            depY = float(value[1])*self.struct.units['L']
          except ValueError:
            struct.PrintError("Erreur pour l'affaissement d'appui du noeud (Y): %s" % noeud, 1)
            depY = 0.
        else:
          try:
            depY = float(value[0])*self.struct.units['L']
            depX = 0.
          except ValueError:
            struct.PrintError("Erreur pour l'affaissement d'appui du noeud: %s" % noeud, 0)
            continue
        self.NodeDeps[noeud] = [depX, depY, 0]
    #print("NodeDeps=",  self.NodeDeps)

# homogénéiser les codes des messages d'erreur
  def _SetChar(self, name, xmlnode):
    """A partir du contenu xml, calcule une combinaison de charge
    et crée les dictionnaires des charges correspondants"""
    #print("Rdm::_SetChar", name)
    self.status = 1
    struct = self.struct
    rot_elast = struct.RotuleElast
 
    self.charBarTri = {} # format {B1: {x: (qx, qy)}} charge triangulaire (nulle pour x=0)
    self.charNode = {}
    self._charArcNode = {} # attribut intermédiaire
    self.charBarQu = {}
    self.charBarFp = {}
    self.charBarTherm = {}
    self.ArcChars = {}
    di = {}
    for i, case in enumerate(xmlnode):
      case_name = case.get("id")
      #print("case_name=", case_name)
      if not case_name == name:
        continue
      if i == 0:
        pp = list(case.iter('pp'))
        if len(pp) == 1:
          content = pp[0].get("d")
          if not content is None:
            if not self._SetPP(content):
              self.status = 0
              continue
      lichar = case.iter('node')
      for char in lichar:
        name = char.get("id")
        if not name:
          continue
        content = char.get("d")
        content = content.split(",")
        if len(content) == 4:
          try:
            Fx = float(content[1])*math.cos(float(content[2])/180*math.pi)
            Fy = float(content[1])*math.sin(float(content[2])/180*math.pi)
            li = [Fx, Fy, float(content[3])]
          except (KeyError, ValueError):
            self.status = 0
            struct.PrintError("Erreur dans le chargement nodal: %s %s" % (case_name, name), 0)
            continue
        else:
          try:
            li = [float(content[0]), float(content[1]), float(content[2])]
          except (KeyError, ValueError):
            self.status = 0
            struct.PrintError("Erreur dans le chargement nodal: %s %s" % (case_name, name), 0)
            continue
        li = [j*struct.units['F'] for j in li]
        if name in self.charNode:
          char_prec = self.charNode[name]
          self.charNode[name] = SumList(li, char_prec)
        else: 
          self.charNode[name] = li
      lichar = case.iter('arc')
      for char in lichar:
        arc = char.get("id")
        if not arc in self.ArcChars:
          self.ArcChars[arc] = {}
        content = char.get("fp")
        if not content is None:
          content = content.split(",")
          data = self._ReadArcCharFp(arc, content)
          if data is False:
            self.status = 0
            struct.PrintError("Une erreur est survenue pour la charge ponctuelle de l'arc %s dans %s" % (arc, case_name), 1)
          elif data is True:
            continue
          else:
            du, b, alpha, fpx, fpy, mz = data
            if "fp" in self.ArcChars[arc]:
              arc_char = self.ArcChars[arc]["fp"]
              arc_char.add(struct, self, du, b, alpha, fpx, fpy, mz)
            else:
              arc_char = ArcCharFp(struct, self, du, b, alpha, fpx, fpy, mz)
              self.ArcChars[arc]["fp"] = arc_char
        elif not char.get("qu") is None:
          data = self._ReadArcChar(char, arc)
          if data is False:
            self.status = 0
            struct.PrintError("Erreur dans le chargement : %s %s" % (case_name, arc), 0)
            continue
          pos0, pos1, qx0, qy0, qx1, qy1, proj = data
          if proj == 0:
            self.add_qu0(struct, arc, pos0, pos1, qx0, qy0, qx1, qy1)
          elif proj == 1: # projetée type neige
            if "qu1" in self.ArcChars[arc]:
              arc_char = self.ArcChars[arc]["qu1"]
              arc_char.add(pos0, pos1, qx0, qy0, qx1, qy1)
              arc_char.GetAffectedNodes(struct, self, arc, pos0, pos1, qx0, qy0, qx1, qy1)
            else:
              arc_char = ArcCharQu1(struct, self, arc, pos0, pos1, qx0, qy0, qx1, qy1)
              self.ArcChars[arc]["qu1"] = arc_char
          elif proj == 2: # radiale
            if "qu2" in self.ArcChars[arc]:
              arc_char = self.ArcChars[arc]["qu2"]
              arc_char.add(pos0, pos1, qx0, qy0, qx1, qy1)
              arc_char.GetAffectedNodes(struct, self, arc, pos0, pos1, qx0, qy0, qx1, qy1)
            else:
              arc_char = ArcCharQu2(struct, self, arc, pos0, pos1, qx0, qy0, qx1, qy1)
              self.ArcChars[arc]["qu2"] = arc_char
        content = char.get("therm")
        if not content is None:
          content = content.split(",")
          if not self._SetTherm(arc, content):
            struct.PrintError("Une erreur est survenue pour le chargement thermique de l'arc %s dans %s" % (arc, case_name), 0)
          arc_char = ArcCharTh()
          self.ArcChars[arc]["th"] = arc_char

      lichar = case.iter('barre')
      for char in lichar:
        barre = char.get("id")
        # Chargement Uniformément répartis des barres
        content = char.get("qu")
        if not content is None:
          content = content.split(",")
          if not self._SetQu(barre, content):
            self.status = 0
            struct.PrintError("Une erreur est survenue pour la charge uniformément répartie de la barre %s dans %s" % (barre, case_name), 0)
        content = char.get("fp")
        if not content is None:
          content = content.split(",")
          if not self._SetFp(barre, content):
            self.status = 0
            struct.PrintError("Une erreur est survenue pour la charge ponctuelle de la barre %s dans %s" % (barre, case_name), 1)
        content = char.get("tri")
        if not content is None:
          content = content.split(",")
          if not self._SetCharTri(barre, content):
            self.status = 0
            struct.PrintError("Une erreur est survenue pour la charge triangulaire de la barre %s dans %s" % (barre, case_name), 0)
        content = char.get("therm")
        if not content is None:
          content = content.split(",")
          if not self._SetTherm(barre, content):
            struct.PrintError("Une erreur est survenue pour le chargement thermique de la barre %s dans %s" % (barre, case_name), 0)
    if not self.charBarTherm == {}:
      struct._SetAlpha()
      if not struct.VerifHExist(self.charBarTherm, self.ArcChars):
        self.status = 0
        self.charBarTherm = {}
      if not struct.VerifAlphaExist(list(self.charBarTherm.keys())):
        self.status = 0
        self.charBarTherm = {}
    # on supprime les couples si la rotule est élastique (inutile pour les relaxations car pas d'équation de moment
    for noeud in rot_elast:
      if noeud in self.charNode and not self.charNode[noeud][2] == 0:
        self.charNode[noeud][2] = 0.
        struct.PrintError("Impossible d'avoir un moment sur le noeud %s contenant une rotule élastique dans %s" % (noeud, case_name), 1)
    self.UserNodesChar = copy.deepcopy(self.charNode) # pour dupliquer les listes contenues dans le dictionnaire
    for node in self._charArcNode: # superposition charges nodales arcs
      char = self._charArcNode[node]
      if node in self.charNode:
        self.charNode[node][0] += char[0]
        self.charNode[node][1] += char[1]
        self.charNode[node][2] += char[2] # ajout 6/2/2019
      else:
        self.charNode[node] = char
    del(self._charArcNode)

  def add_qu0(self, struct, arc, pos0, pos1, qx0, qy0, qx1, qy1):
    """Initialise ou complète un chargement sur un arc de type qu0"""
    if "qu0" in self.ArcChars[arc]: # type poids propre
      arc_char = self.ArcChars[arc]["qu0"]
      arc_char.add(pos0, pos1, qx0, qy0, qx1, qy1)
      arc_char.GetAffectedNodes(struct, self, arc, pos0, pos1, qx0, qy0, qx1, qy1)
    else:
      arc_char = ArcCharQu0(struct, self, arc, pos0, pos1, qx0, qy0, qx1, qy1)
      self.ArcChars[arc]["qu0"] = arc_char
    
  def _SetTherm(self, barre, content): 
    """Récupération du chargement thermique."""
    try:
      degrees = [float(content[0]), float(content[1])]
    except (IndexError, ValueError):
      return False
    struct = self.struct
    lengths = struct.Lengths
    super_bars = struct.SuperBars
    arcs = struct.Curves
    if barre in struct.UserBars:
      self.charBarTherm[barre] = degrees
    elif barre in super_bars:
      sb = super_bars[barre]
      b0, b1 = sb.b0, sb.b1
      for b in range(b0, b1+1):
        self.charBarTherm[b] = degrees
    elif barre in arcs:
      arc = arcs[barre]
      b0, b1 = arc.b0, arc.b1
      for b in range(b0, b1+1):
        self.charBarTherm[b] = degrees
    return True

  def _SetCharTri(self, barre, content): 
    """Transforme le contenu brut d'une charge triangulaire
    et le place dans le dictionnaire charBarTri
    N"accepte qu'une seule barre pour un contenu
    N'accepte pas *"""
    if not barre:
      return False
    struct = self.struct
    lengths = struct.Lengths
    super_bars = struct.SuperBars
    if barre in struct.UserBars:
      angle = struct.Angles[barre]
      l = lengths[barre]
      is_super_bar = False
    elif barre in super_bars:
      sb = super_bars[barre]
      b0, b1 = sb.b0, sb.b1
      user_nodes = sb.user_nodes
      angle = sb.get_angle()
      l = sb.get_size(lengths)
      is_super_bar = True
    else:
      return False
    data = self._GetTriContent(content, l, angle)
    if data is False:
      return False
    a0, a1, Q0x, Q0y, Q1x, Q1y = data
    if is_super_bar:
      prec = user_nodes[0]
      b = b0
      for node in user_nodes[1:]:
        u1 = node.u
        u0 = prec.u
        if a0 >= u1 or a1 < u0:
          prec = node
          b += 1
          continue
        if a0 >= u0:
          x0 = (a0-u0)/(u1-u0)
          q0x = Q0x
          q0y = Q0y
        else:
          x0 = 0.
          q0x = (Q1x-Q0x)*(u0-a0)/(a1-a0)+Q0x
          q0y = (Q1y-Q0y)*(u0-a0)/(a1-a0)+Q0y

        if a1 >= u1:
          x1 = 1.
          q1x = (Q1x-Q0x)*(u1-a0)/(a1-a0)+Q0x
          q1y = (Q1y-Q0y)*(u1-a0)/(a1-a0)+Q0y
        else:
          x1 = (a1-u0)/(u1-u0)
          q1x = Q1x
          q1y = Q1y

        self._ConvertCharTri(b, x0, x1, q0x, q0y, q1x, q1y)
        prec = node
        b += 1
    else:
      self._ConvertCharTri(barre, a0, a1, Q0x, Q0y, Q1x, Q1y)
    #print("Qu=", self.charBarQu)
    #print("Tri=", self.charBarTri)
    return True



  def _ConvertCharTri(self, barre, a1, a2, q1x, q1y, q2x, q2y):
    """Transforme un chargement trapézoidal en charge tri et qu"""
    if a1 == 0. and q1x == 0. and q1y == 0.: # basic case
      self._AddCharTri(barre, a2, q2x, q2y)
    elif a1 == 0.: # qu pour q1y + tri pour q2y-q1y
      self._AddCharTri(barre, a2, q2x-q1x, q2y-q1y)
      self._AddCharQu(barre, a2, q1x, q1y)
    else: # ajout de 4 chargements (2 triangulaires, 2 uniform)
      kx = (q2x*a1-q1x*a2)/(a1-a2)
      ky = (q2y*a1-q1y*a2)/(a1-a2)
      self._AddCharTri(barre, a1, kx-q1x, ky-q1y)
      self._AddCharTri(barre, a2, q2x-kx, q2y-ky)
      self._AddCharQu(barre, a1, -kx, -ky)
      self._AddCharQu(barre, a2, kx, ky)

  def _GetTriContent(self, content, l, angle):
    """Retourne le contenu pour une charge de type triangulaire"""
    struct = self.struct
    tagRelatif = False
    if not len(content) == 6:
      return False
    if content[0] == "@":
      tagRelatif = True

    a1 = content[1]
    a2 = content[2]
    if a1 == '' or a1 == '%':
      a1 = 0.
    elif a1[0] == '%':
      a1 = a1[1:]
      try:
        a1 = float(a1)
      except ValueError:
        return False
    else:
      try:
        a1 = float(a1)
      except ValueError:
        return False
      a1 = a1/l*struct.units['L']

    if a2 == '' or a2 == '%':
      a2 = 1.
    elif a2[0] == '%':
      a2 = a2[1:]
      try:
        a2 = float(a2)
      except ValueError:
        return False
    else:
      try:
        a2 = float(a2)
      except ValueError:
        return False
      a2 = a2/l*struct.units['L']
    if not (a1 >= 0 and a1 <= 1):
      return False
    if not (a2 >= 0 and a2 <= 1):
      return False

    try:
      q1 = float(content[3])*struct.units['F'] # q1 est une force et pas une charge linéaire
      q2 = float(content[4])*struct.units['F']
      a = float(content[5])
    except (IndexError, ValueError):
      return False
    a = a/180*math.pi
    if not tagRelatif:
      a = a - angle
    q1x = q1*math.cos(a)
    q1y = q1*math.sin(a)
    q2x = q2*math.cos(a)
    q2y = q2*math.sin(a)
    return a1, a2, q1x, q1y, q2x, q2y


  def _ReadArcCharFp(self, name, content):
    """Traite le contenu d'une charge ponctuelle sur un arc"""
    print("_ReadArcCharFp", name, content)
    struct = self.struct
    if not name in struct.Curves:
      return False
    arc = struct.Curves[name]
    lengths = struct.Lengths
    l = arc.get_size(lengths)
    data = self.GetFpContent(content, name, l, 0) # finir angle
    if data is False:
      return False
    elif data is True:
      return True
    alpha, fpx, fpy, mz = data
    s = 0
    l0 = l*alpha
    b0, b1 = arc.b0, arc.b1
    for b in range(b0, b1+1):
      lb = lengths[b]
      s += lb
      if s >= l0:
        dl = (l0-s+lb)/lb
        break
    return dl, b, alpha, fpx, fpy, mz

  def _SetFp(self, barre, content): 
    """Transforme le contenu brut d'une charge fp
    et le place dans le dictionnaire charBarFp
    N"accepte qu'une seule barre pour un contenu
    N'accepte pas *"""
    struct = self.struct
    lengths = struct.Lengths
    super_bars = struct.SuperBars
    if barre in struct.UserBars:
      angle = struct.Angles[barre]
      l = lengths[barre]
      is_super_bar = False
    elif barre in super_bars:
      sb = super_bars[barre]
      b0, b1 = sb.b0, sb.b1
      user_nodes = sb.user_nodes
      angle = sb.get_angle()
      l = sb.get_size(lengths)
      is_super_bar = True
    else:
      return False
    data = self.GetFpContent(content, barre, l, angle)
    if data is False:
      return False
    elif data is True:
      return True
    alpha, fpx, fpy, mz = data
    if is_super_bar:
      prec = user_nodes[0]
      b = b0
      for node in user_nodes[1:]:
        u1 = node.u
        u0 = prec.u
        if alpha >= u0 and alpha <= u1:
          barre = b
          alpha = (alpha-u0)/(u1-u0)
          break
        b += 1
        prec = node
    
    if not barre in self.charBarFp:
      self.charBarFp[barre] = {}
    if alpha in self.charBarFp[barre]:
      char = self.charBarFp[barre][alpha]
      char = [char[0] + fpx, char[1] + fpy, char[2] + mz]
      self.charBarFp[barre][alpha] = char
      return True
    self.charBarFp[barre][alpha] = [fpx, fpy, mz]
    #print("charBarFp=", self.charBarFp)
    return True

  def GetFpContent(self, content, barre, l, angle):
    """Valide le contenu d'une charge de type fp
    Retourne alpha compris entre 0 et 1
    Retourne fpx, fpy, M"""
    struct = self.struct
    tagRelatif = False
    tagPol = False
    if len(content) == 5:
      if content[0] == "@":
        tagRelatif = True
      elif content[0] == "@<":
        tagRelatif = True
        tagPol = True
      elif content[0] == "<":
        tagPol = True
      del(content[0])

    alpha = content[0]
    if not alpha == '' and alpha[0] == '%':
      l_is_relative = True
      alpha = alpha[1:]
    else:
      l_is_relative = False
    try:
      alpha = float(alpha)
    except ValueError:
      return False
    if not l_is_relative and not alpha == 0.:
      alpha = alpha/l*struct.units['L']
    try:
      fpx = float(content[1])
      fpy = float(content[2]) # renommer car peut être angle
      mz = float(content[3])
    except (IndexError, ValueError):
      return False
    if tagPol:
      f = fpx
      fpx = f*math.cos(fpy/180*math.pi)
      fpy = f*math.sin(fpy/180*math.pi)
    
    if not (alpha >= 0 and alpha <= 1+1e-12):
      return False
    unit = struct.units['F']
    fpx, fpy, mz = fpx*unit, fpy*unit, mz*unit
    # si alpha = a/l vaut 1 ou 0, on transforme le chargement de la barre
    # en chargement nodal
#    if alpha == 1: # debug 6/2/2019
#      # on repasse dans le repère global
#      if barre in struct.Barres:
#        noeud = struct.Barres[barre][0]
#      elif barre in struct.SuperBars:
#        b = struct.SuperBars[barre]
#        noeud = b.user_nodes[0].name
#      elif barre in struct.Curves:
#        arc = struct.Curves[barre]
#        noeud = arc.user_nodes[0].name
#      else:
#        print("debug in FpContent")
#        return False
#      if tagRelatif and not angle == 0:
#        fpx, fpy = ProjL2GCoors(fpx, fpy, angle)
#      if noeud in self.charNode:
#        char = self.charNode[noeud]
#        char[0] += fpx
#        char[1] += fpy
#        char[2] += mz
#        self.charNode[noeud] = char
#      else:
#        self.charNode[noeud] = [fpx, fpy, mz]
#      return True 
#    elif alpha == 1: # debug
#      if barre in struct.Barres:
#        noeud = struct.Barres[barre][1]
#      else:
#        noeud = barre.user_nodes[-1].name
#      if tagRelatif and not angle == 0:
#        fpx, fpy = ProjL2GCoors(fpx, fpy, angle)
#      if noeud in self.charNode:
#        char = self.charNode[noeud]
#        char[0] += fpx
#        char[1] += fpy
#        char[2] += mz
#        self.charNode[noeud] = char
#      else:
#        self.charNode[noeud] = [fpx, fpy, mz]
#      return True
    if not tagRelatif:
      if not angle == 0:
        fpx, fpy = ProjG2LCoors(fpx, fpy, angle)
    return alpha, fpx, fpy, mz

  def _SetPP(self, content): 
    """Ajoute le poids propre comme une charge uniformément répartie dans l'atribut self.charBarQu"""
    if content == "false":
      return True
    struct = self.struct
    if not struct.SetMV():
      return False
    barres = struct.GetBars()
    for barre in barres:
      angle = struct.Angles[barre]
      S = struct._GetSection(barre)
      qx = 0.
      mv = struct.GetMV(barre)
      qy = -S*mv*struct.G
      if not angle == 0:
        qx, qy = ProjG2LCoors(qx, qy, angle)
      # écriture du dictionnaire
      self._AddCharQu(barre, 1., qx, qy)
    arcs = struct.Curves
    for name in arcs:
      arc = arcs[name]
      mv = struct.GetMV(name)
      if not name in self.ArcChars:
        self.ArcChars[name] = {}
      self.ArcChars[name]["pp"] = ArcCharPP(struct, self, arc, mv)
    return True

  def _ReadArcChar(self, char, name):
    """Lit les données xml pour le chargement de type charge uniforme pour un arc"""
    struct = self.struct
    arcs = struct.Curves
    if not name in arcs:
      return False
    arc = arcs[name]
    proj = False
    proj = char.get("proj")
    if not proj is None:
      if proj == "1":
        proj = 1
      elif proj == "2":
        proj = 2
      else:
        proj = 0
    content = char.get("qu")
    content = content.split(",")
    pos0, pos1, qx0, qy0, qx1, qy1 = content
    try:
      qx0 = float(qx0)*struct.units['F']
      qy0 = float(qy0)*struct.units['F']
      qx1 = float(qx1)*struct.units['F']
      qy1 = float(qy1)*struct.units['F']
    except ValueError:
      return False
    if pos0[0] == "%":
      pos0 = pos0[1:]
      try:
        pos0 = float(pos0)
      except ValueError:
        pos0 = 0.
      try:
        pos1 = float(pos1)
      except ValueError:
        pos1 = 1.
    else:
      l = arc.get_size(struct.Lengths)
      try:
        pos0 = float(pos0)*struct.units['L']/l
      except ValueError:
        pos0 = 0.
      try:
        pos1 = float(pos1)*struct.units['L']/l
      except ValueError:
        pos1 = 1.
    if pos1 <= pos0:
      return False
    if pos0 < 0.:
      return False
    if pos0 >= 1.:
      return False
    if pos1 < 0.:
      return False
    if pos1 > 1.:
      return False
    return pos0, pos1, qx0, qy0, qx1, qy1, proj

  def _SetQu(self, barre, content): 
    """Transforme le contenu brut d'une charge qu 
    et le place dans le dictionnaire charBarQu
    accepte * ou une suite de barre de type B1,B3"""
    struct = self.struct
    super_bars = struct.SuperBars
    user_bars = struct.UserBars
    lengths = struct.Lengths
    Barres = struct.Barres
    rel_tag = False
    if content[0] == "@" :
      del(content[0])
      rel_tag = True

    if barre == "*":
      barres = user_bars
      barres2 = list(super_bars.keys())
    else:
      barres = barre.split(",")
      barres2 = []
      for b in list(barres):
        if b in super_bars:
          barres.remove(b)
          barres2.append(b)
    for name in barres2:
      sb = super_bars[name]
      user_nodes = sb.user_nodes
      b0, b1 = sb.b0, sb.b1
      angle = sb.get_angle()
      l = sb.get_size(lengths)
      data = self.GetQuContent(content, l, angle, rel_tag)
      if data is False:
        return False
      alphas, qx, qy = data
      alpha0, alpha1 = alphas
      prec = user_nodes[0]
      b = b0
      for node in user_nodes[1:]:
        u1 = node.u
        u0 = prec.u
        if alpha1 >= u1:
          if alpha0 >= u1:
            prec = node
            b += 1
            continue
          self._AddCharQu(b, 1., qx, qy)
        elif alpha1 >= u0:
          alpha = (alpha1-u0)/(u1-u0)
          self._AddCharQu(b, alpha, qx, qy)
        if alpha0 <= u0:
          prec = node
          b += 1
          continue
        alpha = (alpha0-u0)/(u1-u0)
        self._AddCharQu(b, alpha, -qx, -qy)
        prec = node
        b += 1

    for barre in barres:
# mettre un warning ici
      if not barre in Barres:
        continue
      angle = struct.Angles[barre]
      l = lengths[barre]
      data = self.GetQuContent(content, l, angle, rel_tag)
      if data is False:
        return False
      alphas, qx, qy = data
      # on rajoute le chargement opposé si le chargement est compris 
      # entre alpha1 et alpha2
      alpha = alphas[0]
      alpha1 = alphas[1]
      self._AddCharQu(barre, alpha1, qx, qy)
      alpha0 = alphas[0]
      if not alpha0 == 0.:
        self._AddCharQu(barre, alpha, -qx, -qy)
    #print("Rdm::_SetQu", self.charBarQu)
    return True

  def GetQuContent(self, content, l, angle, relative_tag):
    """Valide et retourne le contenu d'une charge de type qu"""
    struct = self.struct
    if not len(content) == 4:
      return False
    # cas d'une charge répartie entre alpha1 et alpha2
    alpha1 = content[0]
    if alpha1 == '':
      alpha1 = 0.
    elif alpha1[0] == '%':
      try:
        alpha1 = float(alpha1[1:])
      except (IndexError, ValueError):
        alpha1 = 0.
    else:
      try:
        alpha1 = float(alpha1) / l*struct.units['L']
      except (KeyError, ValueError):
        alpha1 = 0.
    alpha2 = content[1]
    if alpha2 == '':
      alpha2 = 1.
    elif alpha2[0] == '%':
      try:
        alpha2 = float(alpha2[1:])
      except (IndexError, ValueError):
        alpha2 = 1.
    else:
      try:
        alpha2 = float(alpha2) /l*struct.units['L']
      except (KeyError, ValueError):
        alpha2 = 1.
    if alpha1 < 0:
      alpha1 = 0.
    elif alpha1 > 1:
      alpha1 = 1.
    if alpha2 < 0:
      alpha2 = 0.
    elif alpha2 > 1:
      alpha2 = 1.
    if alpha1 >= alpha2:
      return False
    li_alpha = [alpha1, alpha2]

    try:
      qx = float(content[2])
      qy = float(content[3])
    except (IndexError, ValueError):
      return False

    qx, qy = qx*struct.units['F']/struct.units['L'], qy*struct.units['F']/struct.units['L']
    # si la charge est donnée dans le repère global: conversion
    if not relative_tag:
        if not angle == 0:
          qx, qy = ProjG2LCoors(qx, qy, angle)
    return li_alpha, qx, qy

  def _AddCharTri(self, barre, alpha, qx, qy):
    """Ajoute une charge triangulaire sur une barre"""
    if not barre in self.charBarTri:
      self.charBarTri[barre] = {}
    if alpha in self.charBarTri[barre]:
      q = self.charBarTri[barre][alpha]
      q[0] += qx
      q[1] += qy
      self.charBarTri[barre][alpha] = q
    else:
      self.charBarTri[barre][alpha] = [qx, qy]
  
  def _AddCharQu(self, barre, alpha, qx, qy):
    """Ajoute une charge qu sur une barre"""
    if not barre in self.charBarQu:
      self.charBarQu[barre] = {}
    if alpha in self.charBarQu[barre]:
      q = self.charBarQu[barre][alpha]
      q[0] += qx
      q[1] += qy
      self.charBarQu[barre][alpha] = q
    else:
      self.charBarQu[barre][alpha] = [qx, qy]

  def _GetFNodji(self, barre):
    """Retourne les efforts de chargements à l'extrémité de la barre
    Prend en compte les relaxations des barres
    Attention, efforts exercés de la barre sur le noeud"""
    struct = self.struct
    l = struct.Lengths[barre]
    angle = struct.Angles[barre]
    noeud0, noeud1, relax0, relax1 = struct.Barres[barre]
    if relax0 == 1 and relax1 == 1:
      liCoefji = self._GetFNodIsoji(barre)
      if angle:
        ProjL2G(liCoefji, angle)
      return liCoefji
    liCoefij, liCoefji = self._FNod(barre)
    mp = 0.
    #Modification des chargements nodaux en fonction des relaxations 
    if relax0 == 1 and relax1 == 0 : #noeud relaxé
      if noeud0 in struct.RotulePlast:
        if struct.RotulePlast[noeud0][0] == barre \
			or struct.RotulePlast[noeud0][1] == barre:
          mp = struct.RotulePlast[noeud0][2]
      liCoefji = [liCoefji[0], liCoefji[1]+1.5*liCoefij[2]/l-1.5*mp/l,
				liCoefji[2]-0.5*liCoefij[2] + 0.5*mp]
    elif relax0 == 0 and relax1 == 1: #noeud relaxé
      if noeud1 in struct.RotulePlast:
        if struct.RotulePlast[noeud1][0] == barre \
			or struct.RotulePlast[noeud1][1] == barre:
          mp = struct.RotulePlast[noeud1][2]
      liCoefji = [liCoefji[0], liCoefji[1]+1.5*liCoefji[2]/l+1.5*mp/l, 0.]
    if angle:
      ProjL2G(liCoefji, angle)
    return liCoefji

  def _GetFNodij(self, barre):
    """Retourne les efforts de chargements à l'origine de la barre
    Prend en compte les relaxations des barres
    Effort de la barre sur le noeud"""
    struct = self.struct
    l = struct.Lengths[barre]
    angle = struct.Angles[barre]
    noeud0, noeud1, relax0, relax1 = struct.Barres[barre]
    #Modification des chargements nodaux en fonction des relaxations 
    if relax0 == 1 and relax1 == 1: # 2 noeuds relaxés
      liCoefij = self._GetFNodIsoij(barre)
      if angle:
        ProjL2G(liCoefij, angle)
      return liCoefij

    liCoefij, liCoefji = self._FNod(barre)
    mp = 0. # moment plastique
    if relax0 == 1 and relax1 == 0: # 1 noeud relaxé
      if noeud0 in struct.RotulePlast:
        if struct.RotulePlast[noeud0][0] == barre \
		or struct.RotulePlast[noeud0][1] == barre:
          mp = struct.RotulePlast[noeud0][2]
      liCoefij = [liCoefij[0], liCoefij[1]-1.5*liCoefij[2]/l+1.5*mp/l, 0.]
    elif relax0 == 0 and relax1 == 1: # 1 noeud relaxé
      if noeud1 in struct.RotulePlast:
        if struct.RotulePlast[noeud1][0] == barre \
			or struct.RotulePlast[noeud1][1] == barre:
          mp = struct.RotulePlast[noeud1][2]
# pourquoi créer une nouvelle liste?
      liCoefij = [liCoefij[0], liCoefij[1]-1.5*liCoefji[2]/l-1.5*mp/l, liCoefij[2]-0.5*liCoefji[2] - 0.5*mp]
    if angle:
      ProjL2G(liCoefij, angle)
    return liCoefij


# ajouter RotulePlast
  def _GetFNodIsoji(self, barre):
    """Calcule les efforts isostatiques aux noeuds d'une barre biarticulée
    Retourne ([Nji°,Tji°,0])"""
    struct = self.struct
    l = struct.Lengths[barre]
    FNodji = [0., 0., 0.]

    chars = self.charBarFp.get(barre, {})
    for alpha, char in chars.items():
      FNodji[0] += alpha*char[0]
      FNodji[1] += alpha*char[1]
      FNodji[1] += char[2] / l
    chars = self.charBarQu.get(barre, {})
    for a, char in chars.items():
      a = a*l
      FNodji[0] += char[0]*a**2/2/l
      FNodji[1] += char[1]*a**2/2/l

    chars = self.charBarTri.get(barre, {})
    for a, char in chars.items():
      a = a*l
      coef = a**2/3/l
      FNodji[0] += char[0]*coef
      FNodji[1] += char[1]*coef

    if barre in self.charBarTherm: 
      E = struct._GetYoung(barre)
      S = struct._GetSection(barre)
      char = self.charBarTherm[barre]
      alpha = struct._GetAlpha(barre)
      FNodji[0] += alpha*(char[0]+char[1])/2*S*E
    return FNodji

# ajouter RotulePlast
  def _GetFNodIsoij(self, barre):
    """Calcule les efforts isostatiques aux noeuds d'une barre biarticulée
    Retourne ([Nij°,Tij°,0])"""
    struct = self.struct
    l = struct.Lengths[barre]
    FNodij = [0., 0., 0.]
    chars = self.charBarFp.get(barre, {})
    for alpha, char in chars.items():
      FNodij[0] += (1-alpha)*char[0]
      FNodij[1] += (1-alpha)*char[1]
      FNodij[1] += -char[2] / l
    chars = self.charBarQu.get(barre, {})
    for a, char in chars.items():
      a = a*l
      FNodij[0] += a*char[0]*(2*l-a)/2/l
      FNodij[1] += a*char[1]*(2*l-a)/2/l

    chars = self.charBarTri.get(barre, {})
    for a, char in chars.items():
      a = a*l
      coef = a*(0.5-a/3/l)
      FNodij[0] += char[0]*coef
      FNodij[1] += char[1]*coef

    if barre in self.charBarTherm: 
      E = struct._GetYoung(barre)
      S = struct._GetSection(barre)
      char = self.charBarTherm[barre]
      alpha = struct._GetAlpha(barre)
      FNodij[0] += -alpha*(char[0]+char[1])/2*S*E
    return FNodij

  def _FNod(self, barre):
    """Calcule les efforts de blocage équivalents aux noeuds
    Retourne ([Nij°,Tij°,Mij°], [Nji°,Tji°,Mji°])"""
    struct = self.struct
    l = struct.Lengths[barre]
    E = struct._GetYoung(barre)
    S = struct._GetSection(barre)
    I = struct._GetMQua(barre)
    liCoefji = [0.]*3
    liCoefij = [0.]*3
    # cas du chargement uniformément réparti
    dichar = self.charBarQu.get(barre, {})
    for alpha, char in dichar.items():
      a = alpha*l
      #Coefji = [l/2., l/2.,-l**2/12.] coef pour charge uniformément répartie
      Mji = char[1]*a**2/12/l**2*(3*a**2-4*a*l)
      Mij = char[1]*a**2/12/l**2*(6*l**2+3*a**2-8*a*l)
      Fxij = char[0]*a*(2*l-a)/2/l
      Fxji = char[0]*(a**2)/2/l
      Coefji = [Fxji, char[1]*a**2/2/l-(Mij+Mji)/l, Mji]
      #Coefij = [l/2., l/2., l**2/12.] coef pour charge uniformément répartie
      Coefij = [Fxij, char[1]*a*(2*l-a)/2/l+(Mij+Mji)/l, Mij]
      liCoefji = SumList(liCoefji, Coefji)
      liCoefij = SumList(liCoefij, Coefij)
    # cas d'un effort ponctuel
    dichar = self.charBarFp.get(barre, {})
    for alpha, char in dichar.items():
      # [Nji°,Tji°,Mji°]
      Coefji = [alpha*char[0], char[1]*alpha**2*(3-2*alpha)+6*char[2]/l*alpha*(1-alpha),-char[1]*l*alpha**2*(1-alpha)-char[2]*alpha*(2-3*alpha)] 
      # [Nij°,Tij°,Mij°]
      Coefij = [(1-alpha)*char[0], char[1]*(1-alpha)**2*(1+2*alpha)-6*char[2]/l*alpha*(1-alpha), char[1]*l*alpha*(1-alpha)**2-char[2]*(1-alpha)*(3*alpha-1)] 
      liCoefji = SumList(liCoefji, Coefji)
      liCoefij = SumList(liCoefij, Coefij)
    # cas des charges thermiques
    if barre in self.charBarTherm: 
      H = struct.GetH(barre)
      char = self.charBarTherm[barre]
      alpha = struct._GetAlpha(barre)
      Fxij = -alpha*(char[0]+char[1])/2*S*E
      Mij = -alpha*(char[1]-char[0])/H*I*E
      Coefij = [Fxij, 0, Mij]
      Coefji = [-Fxij, 0, -Mij]
      liCoefji = SumList(liCoefji, Coefji)
      liCoefij = SumList(liCoefij, Coefij)

    # chargement triangulaire
    dichar = self.charBarTri.get(barre, {})
    for alpha, char in dichar.items():
        a = alpha*l
        Mji = char[1]*a**2*(a**2/5/l**2-a/4/l)
        Mij = char[1]*a**2*(a**2/5/l**2+1./3-a/2/l)
        #Fxij = -char[0]*a/l*(a/3-l/2)
        Fxij = char[0]*a*(0.5-a/3/l)
        Fxji = char[0]*a**2/3/l
        Coefji = [Fxji, char[1]*a**2/3/l-(Mij+Mji)/l, Mji]
        Coefij = [Fxij, char[1]*a*(0.5-a/3/l)+(Mij+Mji)/l, Mij]
        liCoefji = SumList(liCoefji, Coefji)
        liCoefij = SumList(liCoefij, Coefij)

    return (liCoefij, liCoefji)


  def _GetAff2Char(self, noeud, beamStart, beamEnd):
    """Transforme les affaissements d'appuis en chargement nodal
    retourne une liste [FX,FY,M] ou [FX,FY,M,M'] si rotule élastique"""
    #print("_GetAff2Char", noeud)
    KS = self.KS
    struct = self.struct
    affs = self.NodeDeps
    appuis_inclines = struct.AppuiIncline
    rot_elast = struct.RotuleElast
    if noeud in rot_elast:
      n = 4
      barre_elast = rot_elast[noeud][0]
    else:
      n = 3
    charAff = [0.]*n

    # terme pour l'équation de la rotule élastique
    # on ajoute les termes correspondants à u et v bloqués
    if n == 4:
      noeud0, noeud1, relax0, relax1 = struct.Barres[barre_elast]
      if noeud0 in affs:
        dep0 = list(affs[noeud0])
      else:
        dep0 = [0, 0, 0]
      if noeud1 in affs:
        dep1 = list(affs[noeud1])
      else:
        dep1 = [0, 0, 0]
# XXX finir appui incline ???????

      if noeud in appuis_inclines:
        teta = appuis_inclines[noeud]

      if noeud0 == noeud:
        M0, M1 = KS._getM1(barre_elast, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)
        charAff[3] = -M0[0]*dep0[0]-M0[1]*dep0[1]-M1[0]*dep1[0]-M1[1]*dep1[1]
      else:
        M0, M1 = KS._getM2(barre_elast, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)
        charAff[3] = -M0[0]*dep0[0]-M0[1]*dep0[1]-M1[0]*dep1[0]-M1[1]*dep1[1]

    # termes pour équation proj X, Equation proj Y, Moment
    for barre in beamEnd:
      char = [0.]*n
      noeud0, noeud1, relax0, relax1 = struct.Barres[barre]
      angle = struct.Angles[barre]
      if noeud0 in affs:
        dep = affs[noeud0]
        N0, N1 = KS._getN2(barre, noeud0, noeud1)
        V0, V1 = KS._getV2(barre, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis(appuis_inclines, noeud0, noeud1, N0, N1, V0, V1)
        N = N0[0]*dep[0]+N0[1]*dep[1]
        V = V0[0]*dep[0]+V0[1]*dep[1]
        char[0] += -N*math.cos(angle) + V*math.sin(angle)
        char[1] += -N*math.sin(angle) - V*math.cos(angle)
        M0, M1 = KS._getM2(barre, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)
        char[2] += -M0[0]*dep[0]
        char[2] += -M0[1]*dep[1]
      if noeud1 in affs:
        dep = affs[noeud1]
        N0, N1 = KS._getN2(barre, noeud0, noeud1)
        V0, V1 = KS._getV2(barre, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis(appuis_inclines, noeud0, noeud1, N0, N1, V0, V1)
        N = N1[0]*dep[0]+N1[1]*dep[1]
        V = V1[0]*dep[0]+V1[1]*dep[1]
        char[0] += -N*math.cos(angle) + V*math.sin(angle)
        char[1] += -N*math.sin(angle) - V*math.cos(angle)
        M0, M1 = KS._getM2(barre, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)
        char[2] += -M1[0]*dep[0]
        char[2] += -M1[1]*dep[1]
      charAff = SumList(char, charAff)

    for barre in beamStart:
      char = [0.]*n
      noeud0, noeud1, relax0, relax1 = struct.Barres[barre]
      angle = struct.Angles[barre]
      if noeud0 in affs:
        dep = affs[noeud0]
        N0, N1 = KS._getN1(barre, noeud0, noeud1)
        V0, V1 = KS._getV1(barre, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis(appuis_inclines, noeud0, noeud1, N0, N1, V0, V1)
        N = N0[0]*dep[0]+N0[1]*dep[1]
        V = V0[0]*dep[0]+V0[1]*dep[1]
        char[0] += -N*math.cos(angle) + V*math.sin(angle)
        char[1] += -N*math.sin(angle) - V*math.cos(angle)
        M0, M1 = KS._getM1(barre, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)
        char[2] += -M0[0]*dep[0]
        char[2] += -M0[1]*dep[1]
      if noeud1 in affs:
        dep = affs[noeud1]
        N0, N1 = KS._getN1(barre, noeud0, noeud1)
        V0, V1 = KS._getV1(barre, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis(appuis_inclines, noeud0, noeud1, N0, N1, V0, V1)
        N = N1[0]*dep[0]+N1[1]*dep[1]
        V = V1[0]*dep[0]+V1[1]*dep[1]
        char[0] += -N*math.cos(angle) + V*math.sin(angle)
        char[1] += -N*math.sin(angle) - V*math.cos(angle)
        M0, M1 = KS._getM1(barre, noeud0, noeud1, relax0, relax1)
        KS.ChangeAxis2(appuis_inclines, noeud0, noeud1, M0, M1)
        char[2] += -M1[0]*dep[0]
        char[2] += -M1[1]*dep[1]
      charAff = SumList(char, charAff)
    #print('Aff=', charAff)
    return charAff

  def GetMatChar(self):
    """Crée la matrice de chargement"""
    struct = self.struct
    size = self.KS.n_ddl
    if size == 0:
      return numpy.zeros((size, 1))
    mat = numpy.zeros((size, 1))
    codeDDL = self.KS.codeDDL
    appuis_inclines = struct.AppuiIncline
    rot_elast = struct.RotuleElast
    # on crée la liste des ddl à partir du dico des ddl
    n_aff = len(self.KS.NodeDeps)
    nodes = struct.Nodes
    for noeud in struct.Nodes:
      code0 = codeDDL[noeud][0]
      ddls = self.KS.CODES_DDL[code0]
      pos0 = self.KS.get_ddl_pos(noeud)
      if pos0 == None:
        continue
      chars = [0.]*3
      if noeud in rot_elast:
        chars.append(0.)
        barre_elast = rot_elast[noeud][0]
        noeud0, noeud1 = struct.Barres[barre_elast][0:2]
        # on ajoute les M0ij dans l'équation de la rotule élastique
        if noeud == noeud0:
          char = self._GetFNodij(barre_elast)
        else:
          char = self._GetFNodji(barre_elast)
        chars[3] += char[2] # ddls[2 ou 3] non nul

      if noeud in self.charNode:
        charF = self.charNode[noeud] # force ponctuelle
        for i, val in enumerate(charF):
          if val == 0: continue
          chars[i] += val

      # moment plastique
      if noeud in struct.RotulePlast:
        #if struct.RotulePlast[noeud][0] == barre:
        #  mp = struct.RotulePlast[noeud1][1]
          print("finir .RotulePlast")

      beamStart, beamEnd = struct.BarByNode[noeud]
      for barre in beamStart:
        char = self._GetFNodij(barre)
        for i, val in enumerate(char):
          if val == 0: continue
          chars[i] += val
      for barre in beamEnd:
        char = self._GetFNodji(barre)
        for i, val in enumerate(char):
          if val == 0: continue
          chars[i] += val

      # affaissement d'appuis
      if not n_aff == 0: # XXX revoir: calculé pour tous les noeuds si un seul aff !!
        aff = self._GetAff2Char(noeud, beamStart, beamEnd)
        for i, val in enumerate(aff):
          if val == 0: continue
          chars[i] += val

      # changement de repère si appui incliné
      if noeud in appuis_inclines:
        teta = appuis_inclines[noeud]
        chars[0] = chars[0]*math.cos(teta)+chars[1]*math.sin(teta)
        # on laisse inchangé char[1] qui n'intervient pas
      # écriture dans la matrice
      i = 0
      for j, val in enumerate(chars):
        if ddls[j] == 0: continue
        if val == 0: 
          i += 1
          continue
        mat[pos0+i, 0] += val
        i += 1
    #print('matchar', mat)
    return mat

  #---------------- TRAITEMENT DES RESULTATS -------------------------

  # si la matrice de rigidité est vide, crée une liste de ddl nul
  def _DdlEmpty(self):
    struct = self.struct
    self.RelaxBarRotation = {}
    self.ddlValue = {}
    for noeud in self.struct.Nodes:
      self.ddlValue[noeud] = [0, 0, 0]
    for barre in struct.Barres:
      self.RelaxBarRotation[barre] = {1 : 0, 2 : 0}

  def _TestInfiniteDep(self):
    """Vérifie si il n'y a pas de degrè de liberté trop grand"""
    crit = 1. # à tester
    for noeud in self.struct.Nodes:
      dep = self.ddlValue[noeud] 
      for i in [0, 1, 2]:
        if abs(dep[i]) > crit:
          return False
    return True


  # Retourne la liste des valeurs des ddl par noeuds y compris valeurs nulles 
  def GetDDLValues(self, liResu):
    #print("ResuDdlParNoeud", liResu)
    struct = self.struct
    KS = self.KS
    appuis_inclines = struct.AppuiIncline
    j, n = 0, 0
    resu = {}
    codeDDL = KS.codeDDL
    nodes = struct.Nodes
    for noeud in nodes:
      li = []
      ind = codeDDL[noeud][0]
      ddls = KS.CODES_DDL[ind]
      for ddl in ddls:
        if ddl == 0:
          li.append(0.)
        else:
          li.append(liResu[n])
          n += 1
      resu[noeud] = li
      j += 1
    ddlValue = resu

    # si appui simple incliné, on calcule la valeur des ddl manquants
    for noeud, teta in appuis_inclines.items():
      val = ddlValue[noeud][0]
      ddlValue[noeud][1] = val*math.sin(teta)
      ddlValue[noeud][0] = val*math.cos(teta)

    # on ajoute les déplacements d'appuis imposés
    for noeud in self.NodeDeps:
      aff = self.NodeDeps[noeud]
      if noeud in appuis_inclines:
        teta = appuis_inclines[noeud]
        depY = aff[1]
        aff = [-depY*math.sin(teta), depY*math.cos(teta), 0]
      for i, val in enumerate(aff):
        ddlValue[noeud][i] += val
    self.ddlValue = ddlValue
    #print("ddlValue=", ddlValue)
    rot_plast = self._GetRotationPlast()
    self._GetRotationIso()

    # on calcule les rotations des barres relaxées
    self.RelaxBarRotation = {}
    Barres = struct.Barres
    for barre in Barres:
      if Barres[barre][2] == 1 or Barres[barre][3] == 1:
        if not barre in self.RelaxBarRotation:
          self.RelaxBarRotation[barre] = {}
        if Barres[barre][2] == 1:
          wij = self._Rotationij(barre)
          if barre in rot_plast:
            wij += rot_plast[barre][0]
          self.RelaxBarRotation[barre][1] = wij # 1 = origine !!
        if Barres[barre][3] == 1:
          wji = self._Rotationji(barre)
          if barre in rot_plast:
            wji += rot_plast[barre][1]
          self.RelaxBarRotation[barre][2] = wji
    #print("ddlValue", ddlValue)
      
 
  def _Rotationij(self, barre): 
    """Calcul de la rotation ij de l'origine d'une barre relaxée"""
    struct = self.struct
    noeud0, noeud1, relax0, relax1 = struct.Barres[barre]
    RotuleElast = struct.RotuleElast
    l = struct.Lengths[barre]
    angle = struct.Angles[barre]
    ddl = self.ddlValue
    ddlNDeb, ddlNFin = list(self.ddlValue[noeud0]), list(self.ddlValue[noeud1]) 
    if noeud1 in RotuleElast:
      if barre == RotuleElast[noeud1][0]:
        del(ddlNFin[2])
    if angle:
      ProjG2L(ddlNDeb, angle)
      ProjG2L(ddlNFin, angle)
    if relax0 == 1 and relax1 == 1:
      wiso = 0
      if barre in self._RotationIso:
        wiso = self._RotationIso[barre][0]
      return (ddlNFin[1]-ddlNDeb[1])/l + wiso
    # condensation coefficients [0, -1.5/l, 0], [0, 1.5/l, -0.5]
    wrelax = 0
    if barre in self._RotationIso:
      wiso0, wiso1 = self._RotationIso[barre]
      wrelax = wiso0 + wiso1/2
    return -1.5/l*ddlNDeb[1]+1.5/l*ddlNFin[1]-0.5*ddlNFin[2] + wrelax

  def _Rotationji(self, barre):
    """Calcul de la rotation ji de l'extrémité d'une barre relaxée"""
    struct = self.struct
    noeud0, noeud1, relax0, relax1 = struct.Barres[barre]
    RotuleElast = struct.RotuleElast
    l = struct.Lengths[barre]
    angle = struct.Angles[barre]
    ddlNDeb, ddlNFin = list(self.ddlValue[noeud0]), list(self.ddlValue[noeud1])
    if noeud0 in RotuleElast:
      if barre == RotuleElast[noeud0][0]:
        del(ddlNFin[2])
    if angle:
      ProjG2L(ddlNDeb, angle)
      ProjG2L(ddlNFin, angle)
    if relax0 == 1 and relax1 == 1:
      wiso = 0
      if barre in self._RotationIso:
        wiso = self._RotationIso[barre][1]
      return (ddlNFin[1]-ddlNDeb[1])/l + wiso
    # condensation coefficients [0, -1.5/l, -0.5], [0, 1.5/l, 0]
    wrelax = 0
    if barre in self._RotationIso:
      wiso0, wiso1 = self._RotationIso[barre]
      wrelax = wiso0/2 + wiso1
    return -1.5/l*ddlNDeb[1]-0.5*ddlNDeb[2]+1.5/l*ddlNFin[1] + wrelax

  def _GetBarrePlast(self):
    """Retourne deux listes de barres ayant à une extrémité une rotule plastique
    - liste1 : origine
    - liste2 : fin
    """
    struct = self.struct
    barres = struct.Barres
    RotulePlast = struct.RotulePlast
    li1, li2 = [], []
    for noeud in RotulePlast:
      barre0 = RotulePlast[noeud][0]
      barre1 = RotulePlast[noeud][1]
      if noeud == barres[barre0][0]: # rotation origine
        li1.append(barre0)
      else:
        li2.append(barre0)
      if noeud == barres[barre1][0]: # rotation origine
        li1.append(barre1)
      else:
        li2.append(barre1)
    return li1, li2


  def _GetRotationPlast(self):
    """Calcule les rotations dues au moment plastique à une extrémité"""
# XXX deux extrémités plastifiées ???????? finir superposer les valeurs
    struct = self.struct
    barres = struct.Barres
    RotulePlast = struct.RotulePlast
    di = {}
    li1, li2 = self._GetBarrePlast()

    # rotule plast sur l'origine
    for barre in li1:
      noeud0, noeud1, relax0, relax1 = barres[barre]
      mp = RotulePlast[noeud0][2]
      E = struct._GetYoung(barre)
      I = struct._GetMQua(barre)
      l = struct.Lengths[barre]

      #if not barre in di:
      #  di[barre] = []
      # on applique -mp sur l'origine de la barre XXX vérifier
      wi_iso = -mp*l/3/E/I
      wj_iso = mp*l/6/E/I
      if relax1 == 0:
        wi = wi_iso + wj_iso/2
        wj = 0.
      else:
        wi = wi_iso
        wj = wj_iso
      di[barre] = [wi, wj]

    # rotule plast sur fin de barre
    for barre in li2:
      noeud0, noeud1, relax0, relax1 = barres[barre]
      mp = RotulePlast[noeud1][2]
      E = struct._GetYoung(barre)
      I = struct._GetMQua(barre)
      l = struct.Lengths[barre]

      #if not barre in di:
      #  di[barre] = []
      # on applique mp sur l'extrémité de la barre XXX vérifier
      wi_iso = -mp*l/6/E/I
      wj_iso = mp*l/3/E/I
      if relax0 == 0:
        wi = 0.
        wj = wj_iso + wi_iso/2
      else:
        wi = wi_iso
        wj = wj_iso
      di[barre] = [wi, wj]
    return di


  # calcule les rotations dues au chargement des barres
  def _GetRotationIso(self):
    struct = self.struct
    _RotationIso = {}
    #barres = struct.UserBars
    barres = struct.GetBars()
    for barre in barres:
      E = struct._GetYoung(barre)
      I = struct._GetMQua(barre)
      l = struct.Lengths[barre]
      wiso1, wiso2 = 0., 0.
      if barre in self.charBarTherm: 
        H = struct.GetH(barre)
        char = self.charBarTherm[barre]
        alpha = struct._GetAlpha(barre)
        w = alpha*(char[1]-char[0])/H*l/2
        wiso1 -= w
        wiso2 += w
      if barre in self.charBarTri:
        dichar = self.charBarTri[barre]
        for alpha, char in dichar.items():
          a = alpha*l
          w1 = char[1]*a**2*(a**2/30/l+l/9-a/8)/E/I
          w2 = char[1]*a**2*(-l/18+a**2/30/l)/E/I
          wiso1 += w1
          wiso2 += w2

      if barre in self.charBarQu:
        dichar = self.charBarQu[barre]
        for alpha, char in dichar.items():
          a = alpha*l
          w1 = char[1]*a**2/24/l*(2*l-a)**2/E/I
          w2 = char[1]*a**2/24/l*(a**2-2*l**2)/E/I
          wiso1 += w1
          wiso2 += w2
      if barre in self.charBarFp:
        dichar = self.charBarFp[barre]
        for alpha, char in dichar.items():
          fp = char[1]
          Mp = char[2]
          if not fp == 0:
            w = fp*l**2*alpha*(1-alpha)*(2-alpha)/6/E/I
            wiso1 += w
            w = -fp*l**2*alpha*(1-alpha)*(1+alpha)/6/E/I
            wiso2 += w
          if not Mp == 0:
            w = -Mp*l*(6*alpha-3*alpha**2-2)/6/E/I
            wiso1 += w
            w = Mp*l*(3*alpha**2-1)/6/E/I
            wiso2 += w
      if not wiso1 == 0. or not wiso2 == 0.:
        if not barre in _RotationIso:
          _RotationIso[barre] = [wiso1, wiso2]
        else:
          _RotationIso[barre][0] += wiso1
          _RotationIso[barre][1] += wiso2
    self._RotationIso = _RotationIso
    #print("rotation iso",  _RotationIso)



  # Retourne les termes (Nji,Vji,Mji) d'une barre 
  def _Resuji(self, barre):
    struct = self.struct
    E = struct._GetYoung(barre)
    S = struct._GetSection(barre)
    I = struct._GetMQua(barre)
    angle = struct.Angles[barre]
    noeud1, noeud2, relax1, relax2 = struct.Barres[barre]
    ddlValue = self.ddlValue
    RotuleElast = struct.RotuleElast
    RotulePlast = struct.RotulePlast
    if noeud1 in RotuleElast:
      if barre == RotuleElast[noeud1][0]:
        ddl1 = list(ddlValue[noeud1][0:2])
        ddl1.append(ddlValue[noeud1][3])
      else:
        ddl1 = list(ddlValue[noeud1][0:3])
    else:
      ddl1 = list(ddlValue[noeud1])
    if noeud2 in RotuleElast:
      if barre == RotuleElast[noeud2][0]:
        ddl2 = list(ddlValue[noeud2][0:2])
        ddl2.append(ddlValue[noeud2][3])
      else:
        ddl2 = list(ddlValue[noeud2][0:3])
    else:
      ddl2 = list(ddlValue[noeud2])
    if relax1 == 1:
      ddl1[2] = self.RelaxBarRotation[barre][1]
    if relax2 == 1:
      ddl2[2] = self.RelaxBarRotation[barre][2]
    if angle:
      ProjG2L(ddl1, angle)
      ProjG2L(ddl2, angle)

    charNod = self._FNod(barre)[1] # revoir cette fonction pour ne pas calculer les deux termes

    resu = []
    # calcul de N
    value = -E*S*(ddl1[0]-ddl2[0])/struct.Lengths[barre]
    value -= charNod[0]
    resu.append(value)
    # calcul de V
    value = -E*I/struct.Lengths[barre]**2*(6*ddl2[2]+6*ddl1[2]+(12*ddl1[1]-12*ddl2[1])/struct.Lengths[barre])
    value -= charNod[1]
    resu.append(value)
    # calcul de Mf
    #print("value=", barre, E*I/struct.Lengths[barre]*(4*ddl2[2]+2*ddl1[2]+(6*ddl1[1]-6*ddl2[1])/struct.Lengths[barre]))
    if relax2 == 0:
      value = E*I/struct.Lengths[barre]*(4*ddl2[2]+2*ddl1[2]+(6*ddl1[1]-6*ddl2[1])/struct.Lengths[barre])
      value -= charNod[2]
      resu.append(value)
    else:
      value = 0.
      #if barre in self.charBarFp and (1 in self.charBarFp[barre]):
# XXX provisoire 6/2/2019
        #value = self.charBarFp[barre][1][2]
# faut il mettre cette partie ici? XXX
      if noeud2 in RotulePlast:
        if RotulePlast[noeud2][0] == barre \
			or RotulePlast[noeud2][1] == barre:
          value += RotulePlast[noeud2][2]
# XXX remplacer par calcul ????
          #print("test", E*I/struct.Lengths[barre]*(4*ddl2[2]+2*ddl1[2]+(6*ddl1[1]-6*ddl2[1])/struct.Lengths[barre]))
      resu.append(value)
    return resu


  # Retourne les termes (Nij,Vij,Mij) d'une barre 
  def _Resuij(self, barre):
    struct = self.struct
    E = struct._GetYoung(barre)
    S = struct._GetSection(barre)
    I = struct._GetMQua(barre)
    resu = []
    noeud1, noeud2, relax1, relax2 = struct.Barres[barre]
    angle = struct.Angles[barre]
    ddlValue = self.ddlValue
    RotuleElast = struct.RotuleElast
    RotulePlast = struct.RotulePlast
    RelaxBarRotation = self.RelaxBarRotation
    if noeud1 in RotuleElast:
      if barre == RotuleElast[noeud1][0]:
        ddl1 = list(ddlValue[noeud1][0:2])
        ddl1.append(ddlValue[noeud1][3])
      else:
        ddl1 = list(ddlValue[noeud1][0:3])
    else:
      ddl1 = list(ddlValue[noeud1])
    if noeud2 in RotuleElast:
      if barre == RotuleElast[noeud2][0]:
        ddl2 = list(ddlValue[noeud2][0:2])
        ddl2.append(ddlValue[noeud2][3])
      else:
        ddl2 = list(ddlValue[noeud2][0:3])
    else:
      ddl2 = list(ddlValue[noeud2])
    if relax1 == 1:
      ddl1[2] = self.RelaxBarRotation[barre][1]
    if relax2 == 1:
      ddl2[2] = self.RelaxBarRotation[barre][2]
    if angle:
      ProjG2L(ddl2, angle)
      ProjG2L(ddl1, angle)
    charNod = self._FNod(barre)[0]

    # calcul de N
    value = E*S*(ddl1[0]-ddl2[0])/struct.Lengths[barre]
    value -= charNod[0]
    resu.append(value)
    # calcul de V
    value = E*I/struct.Lengths[barre]**2*(6*ddl2[2]+6*ddl1[2]+(12*ddl1[1]-12*ddl2[1])/struct.Lengths[barre])
    value -= charNod[1]
    resu.append(value)
    # calcul de Mf
    if relax1 == 0:
      value = E*I/struct.Lengths[barre]*(2*ddl2[2]+4*ddl1[2]+(6*ddl1[1]-6*ddl2[1])/struct.Lengths[barre])
      value -= charNod[2]
      resu.append(value)
    else:
      value = 0.
# XXX provisoire 6/2/2019
      #if barre in self.charBarFp and (0 in self.charBarFp[barre]):
       # value = self.charBarFp[barre][0][2]
# XXX provisoire
      if noeud1 in RotulePlast:
        if RotulePlast[noeud1][0] == barre \
			or RotulePlast[noeud1][1] == barre:
          value -= RotulePlast[noeud1][2]
      resu.append(value)
    return resu

  def _GetEndBarSol(self):
    """pour chaque barre, retourne deux listes des efforts (efforts exercé par le noeud correspondant sur la barre) à G et à D dans le repère local des barres"""
    resu = {}
    barres = self.struct.Barres
    for barre in barres:
      resu1 = self._Resuij(barre)
      resu2 = self._Resuji(barre)
      resu[barre] = (resu1, resu2)
    self.EndBarSol = resu
    #print("_GetEndBarSol", resu)

  def GetReac(self): 
    """calcul des réactions d'appuis"""
    struct = self.struct
    liaisons = struct.Liaisons
    deps = self.NodeDeps
    effort = {}
    # recherche des sollicitations pour les barres raccordées au noeud
    for noeud in struct.UserNodes:
      if not (noeud in liaisons or noeud in deps):
        continue
      beamStart, beamEnd = struct.BarByNode[noeud]
      resu = [0, 0, 0]
      for barre in beamStart:
        resu1 = list(self.EndBarSol[barre][0])
        angle = struct.Angles[barre]
        if not angle == 0:
          ProjL2G(resu1, angle)
        resu = SumList(resu, resu1)
      for barre in beamEnd:
        resu1 = list(self.EndBarSol[barre][1])
        angle = struct.Angles[barre]
        if not angle == 0:
          ProjL2G(resu1, angle)
        resu = SumList(resu, resu1)
      # on rajoute l'opposé du chargement nodal
      charF = [0]*3
      if noeud in self.charNode:
        charF = [-i for i in self.charNode[noeud]]
      resu = SumList(resu, charF)
      effort[noeud] = resu
    diReac = {}
    for noeud in effort:
      diReac[noeud] = {}
      Fx, Fy, Mz = effort[noeud]
      diReac[noeud]["Fx"] = Fx
      diReac[noeud]["Fy"] = Fy
      diReac[noeud]["Mz"] = Mz
    self.Reactions = diReac

  def SearchReacMax(self): 
    """Retourne le maximum de Fx et Fy"""
    maxF, maxM = 0., 0.
    try:
      reactions = self.Reactions
    except AttributeError:
      return 0, 0
    for elem in reactions.values():
      if 'Fx' in elem and abs(elem["Fx"]) > maxF:
        maxF = abs(elem["Fx"])
      if 'Fy' in elem and abs(elem["Fy"]) > maxF:
        maxF = abs(elem["Fy"])
      if 'Mz' in elem and abs(elem["Mz"]) > maxM:
        maxM = abs(elem["Mz"])
    return maxF, maxM

  # Affichage des ddl calculés
  def GetBarreRotation(self):
    """Retourne un dictionnaire du type {N1: {B1: w1, B2: w2}} des rotations pour les noeuds relaxés. Attention ddlValue[N1][2] n'est pas forcément nul"""
    struct = self.struct
    di = {}
    w_relax = {}
    for barre, rots in self.RelaxBarRotation.items():
      for i, w in rots.items():
        node = struct.Barres[barre][i-1] # XXX pas terrible à cause indice 1 et 2
        if not node in w_relax:
          w_relax[node] = {}
        w_relax[node][barre] = w
    for node in struct.RotuleElast:
      barre_elast = struct.RotuleElast[node][0]
      w = self.ddlValue[node][3]
      if not node in w_relax:
        w_relax[node] = {}
      w_relax[node][barre_elast] = w
    return w_relax

  # Retourne un affichage des sollicitations aux extremités des barres
  def GetSollicitationBarre(self, conv=1):
    #print("GetSollicitationBarre", conv)
    di = {}
    struct = self.struct
    names = struct.UserBars
    barres = struct.Barres
    for barre in names:
      di[barre] = {}
      noeud = barres[barre][0]
      li = self.EndBarSol[barre][0]
      if conv == 1:
        li = [-i for i in li]
      di[barre][noeud] = li
      noeud = barres[barre][1]
      li = self.EndBarSol[barre][1]
      if conv == -1:
        li = [-i for i in li]
      di[barre][noeud] = li
    return di


class CombiChar(CasCharge):

  def __init__(self, name, coefs, Chars, struct, char_error):
    # renommer char_error
    self.struct = struct
    self.name = name
    self._CharsCoef = coefs
    self.Chars = Chars
    self.GetCombiChar()

  def Solve2(self):
    self._GetEndBarSolC()
    self.GetCombiDDL()
    self.Reactions = self.GetCombiReac()


  def _GetEndBarSolC(self):
    def add_soll(tu1, tu2, coef):
      li1 = tu1[0]
      li2 = tu2[0]
      li3 = tu1[1]
      li4 = tu2[1]
      for i, val in enumerate(li2):
        li1[i] += val*coef
      for i, val in enumerate(li4):
        li3[i] += val*coef
      return (li1, li3)

    combi = self._CharsCoef
    chars = self.Chars
    barres = self.struct.Barres
    struct = self.struct
    #names = struct.UserBars
    di = {}
    for barre in barres:
      di[barre] = ([0, 0, 0], [0, 0, 0])

    for cas in combi:
      coef = combi[cas]
      if coef == 0:
        continue
      Char = chars[cas]
      #print(Char.EndBarSol)
      for barre in barres:
        di[barre] = add_soll(di[barre], Char.EndBarSol[barre], coef)
    self.EndBarSol = di

  def GetCombiDDL(self):
    combi = self._CharsCoef
    chars = self.Chars
    nodes = self.struct.Nodes
    di = {}
    di2 = {}
    di3 = {}
    for i, cas in enumerate(combi):
      coef = combi[cas]
      if not i == 0 and coef == 0:
        continue
      Char = chars[cas]
      ddl = Char.ddlValue
      for node in nodes:
        if node in di:
          ddl0 = ddl[node]
          for j, val in enumerate(ddl0):
            di[node][j] += ddl[node][j]*coef
        else:
          di[node] = [j*coef for j in ddl[node]]
      RotIso = Char._RotationIso
      for barre in RotIso:
        if barre in di2:
          rot = RotIso[barre]
          for j, val in enumerate(rot):
            di2[barre][j] += val*coef
        else:
          di2[barre] = [j*coef for j in RotIso[barre]]
      RelaxBarW = Char.RelaxBarRotation
      for barre in RelaxBarW:
        rot = RelaxBarW[barre]
        if barre in di3:
          for key, val in rot.items():
            di3[barre][key] += val*coef
        else:
          di3[barre] = {}
          for key, val in rot.items():
            di3[barre][key] = val*coef

    self.ddlValue = di
    self._RotationIso = di2
    self.RelaxBarRotation = di3
        
  def GetCombiReac(self):
    combi = self._CharsCoef
    chars = self.Chars
    di = {}
    for cas in combi:
      coef = combi[cas]
      if coef == 0:
        continue
      Char = chars[cas]
      for noeud in Char.Reactions:
        if not noeud in di:
          di[noeud] = {}
        content = Char.Reactions[noeud]
        for key in content:
          if key in di[noeud]:
            di[noeud][key] += content[key]*coef
          else:
            di[noeud][key] = content[key]*coef
    return di

  def GetCombiChar(self):
    combi = self._CharsCoef
    chars = self.Chars
    self.ArcChars = {}
    charNode = {}
    charNodeU = {}
    charBarFp = {}
    charBarQu = {}
    charBarTri = {}
    charBarTherm = {}
    for cas in combi:
      coef = combi[cas]
      if coef == 0:
        continue
      Char = chars[cas]
      arc_chars = Char.ArcChars
      for arc in arc_chars:
        arc_char = arc_chars[arc]
        if not arc in self.ArcChars:
          self.ArcChars[arc] = {}
        for key in arc_char:
          char = arc_char[key]
          if key in self.ArcChars[arc]:
            combi_char = self.ArcChars[arc][key]
            if key == 'qu0' or key == 'qu1' or key == 'qu2':
              for i, pos1 in enumerate(char.points[1:]):
                pos0 = char.points[i]
                qx0, qy0 = char.values[pos0][2:]
                qx1, qy1 = char.values[pos1][:2]
                combi_char.add(pos0, pos1, qx0, qy0, qx1, qy1, coef)
                combi_char.barres.update(char.barres)
            elif key == 'fp':
              combi_char.add(char, coef)
          else:
            if key == 'pp':
              combi_char = ArcCombiQu(char, coef)
            elif key == 'qu0':
              combi_char = ArcCombiQu(char, coef)
            elif key == 'qu1':
              combi_char = ArcCombiQu(char, coef)
            elif key == 'qu2':
              combi_char = ArcCombiQu(char, coef)
            elif key == 'fp':
              combi_char = ArcCombiFp(char, coef)
            else:
              continue
            self.ArcChars[arc][key] = combi_char
      #print("------ Affichage chargement combi ---------")
      #for key in self.ArcChars[arc]:
      #  print("key=", key)
      #  print("\t", self.ArcChars[arc][key].values)

      fp = Char.charBarFp
      for barre in fp:
        params = fp[barre]
        if not barre in charBarFp:
          charBarFp[barre] = {}
        for alpha in params:
          if alpha in charBarFp[barre]:
            for i in range(3):
              charBarFp[barre][alpha][i] += params[alpha][i]*coef
          else:
            charBarFp[barre][alpha] = [j*coef for j in params[alpha]]

      qu = Char.charBarQu
      for barre in qu:
        params = qu[barre]
        if not barre in charBarQu:
          charBarQu[barre] = {}
        for alpha in params:
          if alpha in charBarQu[barre]:
            for i in range(2):
              charBarQu[barre][alpha][i] += params[alpha][i]*coef
          else:
            charBarQu[barre][alpha] = [j*coef for j in params[alpha]]

      tri = Char.charBarTri
      for barre in tri:
        params = tri[barre]
        if not barre in charBarTri:
          charBarTri[barre] = {}
        for alpha in params:
          if alpha in charBarTri[barre]:
            for i in range(2):
              charBarTri[barre][alpha][i] += params[alpha][i]*coef
          else:
            charBarTri[barre][alpha] = [j*coef for j in params[alpha]]

      therm = Char.charBarTherm
      for barre in therm:
        params = therm[barre]
        if barre in charBarTherm:
          for i in range(2):
            charBarTherm[barre][i] += params[i]*coef
        else:
          charBarTherm[barre] = [j*coef for j in therm[barre]]
      char = Char.UserNodesChar
      for node in char:
        params = char[node]
        if node in charNodeU:
          for i in range(2):
            charNodeU[node][i] += params[i]*coef
        else:
          charNodeU[node] = [j*coef for j in char[node]]
      char = Char.charNode
      for node in char:
        params = char[node]
        if node in charNode:
          for i in range(2):
            charNode[node][i] += params[i]*coef
        else:
          charNode[node] = [j*coef for j in char[node]]
    self.UserNodesChar = charNodeU
    self.charNode = charNode
    self.charBarFp = charBarFp
    self.charBarQu = charBarQu
    self.charBarTri = charBarTri
    self.charBarTherm = charBarTherm


class R_Structure(object):
  """Résolution de la structure chargée"""

  def __init__(self, struct):
    #print("init R_Structure")
    self.struct = struct
    self.errors = struct.errors
    self.status = struct.status
    if self.status == -1:
      return
    self.conv = self.GetConv()
    
    self.Cases = self.GetCasCharge()
    self.CombiCoef = self.GetCombi()
    self.n_cases = len(self.Cases)
    self.n_chars = self.n_cases + len(self.CombiCoef)
    self.XMLNodes = self.struct.XMLNodes
    if self.status == 0:
      return
    xmlnode = list(self.struct.XMLNodes["char"].iter('case'))

    KS1 = KStructure(self.struct) # calcul sans affaissement d'appui
    self.Chars = {}
    #self.char_error = [] # erreur en relation avec un chargement, provisoire
    for cas in self.Cases:
      #xmlnodes = self.struct.XMLNodes["char"].iter('case')
      Char = CasCharge(cas, xmlnode, self.struct)
      if Char.NodeDeps:
        KS = KStructure(self.struct, Char.NodeDeps)
      else:
        KS = KS1
      Char.KS = KS
      Char.status = KS.status
      self.Chars[cas] = Char
    self.bar_values = {}
    self.SolveCombis()

  def GetCharByNumber(self, n):
    """Retourne l'instance du chargement en fonction du numéro n (combinaison ou cas)"""
    n_cases = len(self.Cases)
    if n < n_cases:
      name = self.Cases[n]
      try:
        return self.Chars[name]
      except AttributeError:
        return None
    n = n - n_cases
    Combis = list(self.Combis.keys())
    Combis.sort()
    try:
      name = Combis[n]
    except IndexError:
      return None
    return self.Combis[name]

  def GetCharNameByNumber(self, n):
    """Retourne le nom du chargement en fonction du numéro n (combinaison ou cas)"""
    n_cases = len(self.Cases)
    if n < n_cases:
      return self.Cases[n]
    n = n - n_cases
    Combis = list(self.Combis.keys())
    Combis.sort()
    return Combis[n]

  def GetCasesCombis(self, indices):
    """Retourne la liste des noms des cas et des noms des combis sélectionnés à partir d'index (positif pour les cas, négatifs pour les combis)"""
    Cases = self.Cases
    Combis = list(self.CombiCoef.keys())
    Combis.sort()
    cases = []
    n_cases = len(Cases)
    for i in indices:
      if i < n_cases:
        cases.append(Cases[i])
      else:
        n = i - n_cases
        cases.append(Combis[n])
    return cases


  def GetStructName(self):
    """Retourne le nom de l'étude"""
    return self.struct.name

  def GetStructPath(self):
    """Retourne le chemin de l'étude"""
    return self.struct.file

  def SetStructName(self, name):
    """Définit le nom de l'étude"""
    self.struct.name = name

  def PrintError(self, text, code):
    """Fonction de formatage du message d'erreur
    code 0 : error; code 1 : warning"""
    #print("PrintError", text)
    try:
      self.errors.append((text, code))
    except AttributeError:
      self.errors = [(text, code)]

  def GetG(self, UP=None):  
    """Récupère la valeur de G"""
    try:
      return self.struct.G
    except AttributeError:
      return self.struct.GetG()
    
  def GetConv(self, UP=None):  
    """Récupère la valeur de G"""
    try:
      return self.conv
    except AttributeError:
      return self.struct.GetConv()
    
  def SolveCombis(self):
    """Lance les calculs necessaires aux calculs des cas et combinaisons"""
    self.Combis = {}
    status  = 1
    for i, cas in enumerate(self.Cases):
      Char = self.Chars[cas]
      if Char.status == 0:
        break
    if status == 0:
      return
    self.char_error = []
    self.SolveAllCases()

    self.CaseMax = self.SearchCasesMax()
    self.CombiMax = {'N': {}, 'V': {}, 'M': {}, 'u': {}}
    # il ne peut y avoir d'erreur dans les combis car pas d'inversion de matrice
    if self.char_error: # erreur dans un des cas de charge
      return
    self.SolveAllCombis()

  def SolveAllCombis(self):
    """Résout les combinaison à partir des chargements résolus"""
    #print('SolveAllCombis')
    struct = self.struct
    assym_b = struct.assym_b
    #print("barre asymétrique=",assym_b)
    for combi in self.CombiCoef:
      Combi = CombiChar(combi, self.CombiCoef[combi], self.Chars, self.struct, self.char_error)
      if assym_b:
        self.SolveAssymCombi(Combi, assym_b)
      else:
        Combi.Solve2()
      self.Combis[combi] = Combi
      Combi.status = 1

  def GetFirstCombi(self):
    """Retourne la première combinaison"""
    return self.Combis[list(self.Combis.keys())[0]]

  def SolveAssymCombi(self, Combi, assym_b):
    """Résout le cas de charge en cas de présence de barres traction/compression seule"""
    #print("SolveAssymCombi")
    struct = self.struct
    Backup_S = copy.deepcopy(struct.Sections)
    Sections = struct.Sections
    removed_b = []
    Combi.NodeDeps = {}
    Combi.KS = KStructure(self.struct) # calcul sans affaissement d'appui
    InvMatK = Combi.KS.InvMatK
    MatChar = Combi.GetMatChar()
    Combi.Solve(struct, InvMatK, MatChar)
    for b in assym_b:
      N = Combi.EndBarSol[b][0][0]
      if N > 0. and assym_b[b] == 1:
        removed_b.append(b)
        Sections[b] = 0.
      elif N < 0. and assym_b[b] == -1:
        removed_b.append(b)
        Sections[b] = 0.
    for b in removed_b:
      struct.status = 1
      Combi.KS = KStructure(self.struct) # calcul sans affaissement d'appui
      InvMatK = Combi.KS.InvMatK
      Combi.Solve(struct, InvMatK, MatChar)
    struct.Sections = copy.deepcopy(Backup_S) # on remet les sections droites



  def SolveAssym(self, assym_b):
    """Résout le cas de charge en cas de présence de barres traction/compression seule"""
    struct = self.struct
    Backup_S = copy.deepcopy(struct.Sections)
    for i, cas in enumerate(self.Cases):
      Sections = struct.Sections
      removed_b = []
      Char = self.Chars[cas]
      InvMatK = Char.KS.InvMatK
      MatChar = Char.GetMatChar()
      Char.Solve(struct, InvMatK, MatChar)
      for b in assym_b:
        N = Char.EndBarSol[b][0][0]
        if N > 0. and assym_b[b] == 1:
          removed_b.append(b)
          Sections[b] = 0.
        elif N < 0. and assym_b[b] == -1:
          removed_b.append(b)
          Sections[b] = 0.
# revoir ici
      #for b in removed_b:
      struct.status = 1
      InvMatK = Char.KS.GetInvMatK()
      Char.Solve(struct, InvMatK, MatChar)

      struct.Sections = copy.deepcopy(Backup_S) # on remet les sections droites

  def SolveAllCases(self):
    struct = self.struct
    assym_b = struct.assym_b
    if assym_b:
      self.SolveAssym(assym_b)
    else:
      for i, cas in enumerate(self.Cases):
        Char = self.Chars[cas]
        if Char.status == 0 : continue
        MatChar = Char.GetMatChar()
        Char.Solve(struct, Char.KS.InvMatK, MatChar)
        if Char.status == 0:
          self.char_error.append(i)
    #print(self.char_error)


  def GetUnits(self, UP=None):
    """Retourne le dictionnaire des unités"""
    try:
      return self.struct.units
    except AttributeError:
      return self.struct.GetUnits()


  def SearchCasesMax(self):
    """Retourne les maximum pour toutes les combinaisons confondues
    Termine le calcul par la combi active pour rendre le même objet rdm"""
    #print("Rdm::SearchCasesMax")
    diMax = {'u' : {}, 'N' : {}, 'V' : {}, 'M' : {}}
    maxiN, maxiV, maxiM, maxiU = 0, 0, 0, 0
    for cas in self.Cases:
      Char = self.Chars[cas]
      if Char.status == 0:
        continue
      cas = Char.name
      max0 = self._SearchDepMax(Char)
      max1 = self._SearchNMax(Char)
      max2 = self._SearchVMax(Char)
      max3 = self._SearchMfMax(Char)
      diMax['u'][cas] = max0
      diMax['N'][cas] = max1
      diMax['V'][cas] = max2
      diMax['M'][cas] = max3
      maxiU = max(maxiU, max0)
      maxiN = max(maxiN, max1)
      maxiV = max(maxiV, max2)
      maxiM = max(maxiM, max3)

    # suppression des valeurs si trop faibles
    maxSoll = max(maxiN, maxiV, maxiM)
    if maxSoll < 1e-12:
      maxiN, maxiV, maxiM = 0., 0., 0.
      for i in ['N', 'V', 'M']:
        for j in diMax[i]:
          diMax[i][j] = 0.
    # maxi des cas 
    # ce maximum sera pris si l'échelle est bloquée dans classDrawing
    diMax['u']['__all__'] = maxiU
    diMax['N']['__all__'] = maxiN
    diMax['V']['__all__'] = maxiV
    diMax['M']['__all__'] = maxiM
    return diMax


  # récupère la liste des noms des cas de charge
  def GetCasCharge(self):
    li = []    
    li_node = self.struct.XMLNodes["char"].iter('case')
    for case in li_node:
      li.append(case.get("id"))
    if len(li) == 0:
      return [Const.DEFAULT_CASE]
    return li

  # fonction qui permet d'affecter un seul cas de charge comme combinaison
  def _MakeCombiForCase(self, cas):
    liCas = self.Cases
    di = {}
    if len(liCas) == 0: return di
    if cas is None or not cas in liCas:
      cas = liCas[0]
    for val in liCas:
      if cas == val: di[val] = 1.
      else: di[val] = 0.
    return di

  def GetCombi(self):
    liCas = self.Cases
    nbCas = len(liCas)
    diCombi = {}
    li_node = self.struct.XMLNodes["combinaison"].iter('combinaison')
    for combi in li_node:
      name = combi.get("id")
      content = combi.get("d")
      content = content.split(",")
      if not len(content) == nbCas:
        continue
      i = 0
      di = {}
      for cas in content:
        try: # a revoir
          di[liCas[i]] = float(cas)
        except (KeyError, ValueError):
          #exception levée si tous les cas de charges sont supprimés
          di[liCas[i]] = 0.
        i += 1
      diCombi[name] = di
    return diCombi
    


  # ---------------- RECHERCHE DES MAXIMUMS -------------------------
  def GetCombiMax(self, mode, Char=None):
    """Retourne le maximum pour mode =N, V, M ou u du chargement spécifié Char. Si Char n'est pas spécifié, retourne le maxi pour tous les cas et combi"""
    #print("GetCombiMax")
    if mode == 'N':
      fct = self._SearchNMax
    elif mode == 'V':
      fct = self._SearchVMax
    elif mode == 'M':
      fct = self._SearchMfMax
    elif mode == 'u':
      fct = self._SearchDepMax
      #fct = self._SearchCombiDepMax

    if Char:
      if isinstance(Char, CombiChar):
        combi = Char.name
        if combi in self.CombiMax[mode]:
          return self.CombiMax[mode][combi]
        max1 = fct(Char)
        self.CombiMax[mode][combi] = max1
        return max1  
      else:
        name = Char.name
        return self.CaseMax[mode].get(name, 0)

    try:
      max1 = self.CaseMax[mode]['__all__']
    except AttributeError:
      return None
    Combis = self.Combis
    for combi in Combis: 
      try:
        maxCombi = self.CombiMax[mode][combi]
      except KeyError:
        try:
          maxCombi = fct(Combis[combi])
        except AttributeError: # has not EndBarSol
          continue
        self.CombiMax[mode][combi] = maxCombi
      if maxCombi > max1:
        max1 = maxCombi
    return max1

# regrouper les deux fonctions suivantes
# à supprimer
  def _SearchCombiDepMax(self, Combi):
    relaxs = self.struct.IsRelax
    max = 0
    dep_node = self.GetNodeDepMax(Combi) # déja pondéré par coef
    if dep_node > max:
      max = dep_node
    defo = self.GetMidBarDefoMax(Combi, relaxs)
    if defo > max:
      max = defo
    return max

  def _SearchDepMax(self, Char):
    """Recherche les déplacements maximums en x et y
    de la structure (noeud et travée)"""
    # attention, faire la différence entre les dep max et la rot max
    #print("_SearchDepMax")
    max = 0.
    dep_node = self.GetNodeDepMax(Char)
    if dep_node > max:
      max = dep_node
    
    relaxs = self.struct.IsRelax
    defo = self.GetMidBarDefoMax(Char, relaxs)
    if defo > max:
      max = defo

    long_max = 0.
    # comparaison du maxi avec les longueurs des barres
    for long in self.struct.Lengths.values():
      if long > long_max:
        long_max = long
    if max/long_max < 1e-10:
      max = 0.
    return max

  def GetNodeDepMax(self, Char):
    """Retourne le maximum des déplacements nodaux u et v"""
    max0 = 0
    if Char.status == 0: return max0
    ddl = Char.ddlValue
    if ddl == {}:
      return 0
    for noeud in self.struct.Nodes:
      dep = ddl[noeud]
      depX = abs(dep[0])
      depY = abs(dep[1])
      if depX > max0:
        max0 = depX
      if depY > max0:
        max0 = depY
    return max0


  def GetMidBarDefoMax(self, Char, relaxs):
    """Retourne le maximum des déplacements aux milieux des barres, perpendiculairement aux barres"""
    max0 = 0
    if Char.status == 0: return max0
    ddl = Char.ddlValue
    struct = self.struct
    if ddl == {}:
      return 0
    #barres = struct.UserBars
    barres = struct.GetBars()
    for barre in barres: 
      l = struct.Lengths[barre]
      angle = struct.Angles[barre]
      charFp = Char.charBarFp.get(barre, {})
      pos = list(charFp.keys())
      pos = [i/2 for i in pos if not charFp[i][2] == 0.]
      if not 0.5 in pos:
        pos.append(0.5)
      charQu = Char.charBarQu.get(barre, {})
      triangulars = Char.charBarTri.get(barre, {})
      liTherm = Char.charBarTherm.get(barre, [])
      chars = charFp, charQu, triangulars, liTherm
      # milieu de la barre
      for u in pos:
        defo = abs(self.DefoPoint(Char, barre, l, angle, u*l, ddl, relaxs, chars))
        if defo > max0:
          max0 = defo
    return max0

  def _SearchNMax(self, Combi): 
    #print("_SearchNMax", Combi.name)
    max1 = 0
    # valeur aux noeuds
    struct = self.struct
    EndBarSol = Combi.EndBarSol
    for barre in EndBarSol:
      value = EndBarSol[barre]
      val = max(abs(value[0][0]), abs(value[1][0]))
      if val > max1:
        max1 = val
    # valeurs aux milieux des barres
    #barres = struct.UserBars
    barres = struct.GetBars()
    Lengths = struct.Lengths
    for barre in barres:
      charFp = Combi.charBarFp.get(barre, {})
      charQu = Combi.charBarQu.get(barre, {})
      charTri = Combi.charBarTri.get(barre, {})
      l = Lengths[barre]
      pos = list(charFp.keys())
      if pos == []:
        pos = [0.5] # à valider on ajoute un point au milieu
      for x in pos:
        val = self.NormalPoint(Combi, barre, x*l, charQu, charFp, charTri, self.conv)
        if abs(val) > max1:
          max1 = abs(val)
    return max1

  def _SearchVMax(self, Combi):
    struct = self.struct
    max1 = 0
    EndBarSol = Combi.EndBarSol
    for barre in EndBarSol:
      value = EndBarSol[barre]
      val = max(abs(value[0][1]), abs(value[1][1]))
      if val > max1:
        max1 = val
    #barres = struct.UserBars
    barres = struct.GetBars()
    Lengths = struct.Lengths
    for barre in barres:
      l = Lengths[barre]
      charFp = Combi.charBarFp.get(barre, {})
      charQu = Combi.charBarQu.get(barre, {})
      charTri = Combi.charBarTri.get(barre, {})
      pos = list(charFp.keys())
      if pos == []:
        pos = [0.5] # à valider on ajoute un point au milieu
      for x in pos: # optimiser davantage en regardant ce que contient charFp?
        val = self.TranchantPoint(Combi, barre, x*l, charQu, charFp, charTri, self.conv)
        if abs(val) > max1:
          max1 = abs(val)
    return max1

  def _SearchMfMax(self, Combi):
    #print(Combi.name)
    max1 = 0
    struct = self.struct
    EndBarSol = Combi.EndBarSol
    for barre in EndBarSol:
      value = EndBarSol[barre]
      val = max(abs(value[0][2]), abs(value[1][2]))
      if val > max1:
        max1 = val
    #barres = struct.UserBars
    barres = struct.GetBars()
    Lengths = struct.Lengths
    for barre in barres:
      l = Lengths[barre]
      charFp = Combi.charBarFp.get(barre, {})
      charQu = Combi.charBarQu.get(barre, {})
      qu_pos = list(charQu.keys())
      if 1. in qu_pos:
        qu_pos.remove(1.)
      charTri = Combi.charBarTri.get(barre, {})
      pos = list(charFp.keys())
      posC = [i+1e-10 for i in pos if not charFp[i][2] == 0.]
      pos2 = qu_pos+posC
      for elem in pos2:
        if not elem in pos:
          pos.append(elem)
      if (charTri or charQu) and not 0.5 in pos:
        pos.append(0.5) # à valider on ajoute un point au milieu
      for x in pos: # optimiser davantage en regardant ce que contient charFp?
        val = self.MomentPoint(Combi, barre, x*l, charQu, charFp, charTri, self.conv)
        if abs(val) > max1:
          max1 = abs(val)
    return max1

  # Affichages des déformations maximales sur les barres
  # inutilisée
  def DefoMax(self, screen=True, n=20):
    """Calcule la flèche négative minimale et sa position
    Calcule la flèche positive maximale et sa position
    Affiche les messages ou retourne une liste"""
    #n nombre d'intervalles par barre
    struct = self.struct
    li = ["**Flèches maximales sur les barres"]
    relaxs = struct.IsRelax
    ddl = self.ddlValue
    barres = struct.UserBars
    for barre in barres:
      li.append("\tBarre: %s" % barre)
      l = struct.Lengths[barre]
      angle = struct.Angles[barre]
      charFp = self.charBarFp.get(barre, {})
      charQu = self.charBarQu.get(barre, {})
      triangulars = self.charBarTri.get(barre, {})
      liTherm = self.charBarTherm.get(barre, [])
      chars = charFp, charQu, triangulars, liTherm
      max = 0
      min = 0
      posmax = 0.
      posmin = 0.
      for i in range(n+1):
        pas = i * l / n
        defo = self.DefoPoint(Case, barre, l, angle, pas, ddl, relaxs, chars)
        if defo > max:
          max = defo
          posmax = pas
        if defo < min:
          min = defo
          posmin = pas
        #u += pas
      if not posmin == 0. and abs(posmin-l) > 1e-3:
        li.append("Flèche négative : %e m à x = %.4f" % (min, posmin))
      if not posmax == 0 and abs(posmax-l) > 1e-3:
        li.append("Flèche positive : %e m à x = %.4f" % (max, posmax))
    if not screen:
      return li
    print("\n".join(li))

  def GetSigma(self, Char, u, barre):
    """Retourne les contraintes normales en fibres supérieure et inférieure"""
    if Char.status == -1 or Char.status == 0:
      return None, None
    struct = self.struct
    charQu = Char.charBarQu.get(barre, {})
    charFp = Char.charBarFp.get(barre, {})
    charTri = Char.charBarTri.get(barre, None)
    l = struct.GetLength(barre)
    N = self.NormalPoint(Char, barre, u*l, charQu, charFp, charTri, self.conv)
    mf = self.MomentPoint(Char, barre, u*l, charQu, charFp, charTri, self.conv)
    S = struct._GetSection(barre)
    I = struct._GetMQua(barre)
    H = struct.GetH(barre)
    v = struct.Getv(barre)
    if H is None and v is None:
      return None, None
    try:
      sig_sup = N/S - mf*v/I
      sig_inf = N/S + mf*(H-v)/I
      return sig_inf, sig_sup
    except TypeError:
      return None, None


  # ----------- CALCUL DES DEFORMATIONS --------------------------

  # fonction pour le calcul de la déformée
# inutile
  def _Psi2(self, u, l):
    return 2*u**3/l**3-3*u**2/l**2+u/l # modif des fonctions 2 et 5

  def _Psi5(self, u, l):
    return -2*u**3/l**3+3*u**2/l**2-u/l

  def _Psi3(self, u, l):
    return u**3/l**2-2*u**2/l+u

  def _Psi6(self, u, l):
    return u**3/l**2-u**2/l
  

  def _PsiTherm(self, u, l, teta):
    return -teta*u**2+teta*u*l

  # deformée de la barre isostatique sous charge triangulaire
  # entre u = 0 et u = alpha*l
  def _PsiTri(self, alpha, u, l, young, Igz):
    if alpha == 1:
      return u*(3*u**4-10*l**2*u**2+7*l**4)/l/360/young/Igz
    a = alpha*l
    if u < a:
      k1 = a**2*(a**2/30/l+l/9-a/8)
      return u*(-a*u**2/12+a**2*u**2/18/l+u**4/120/a+k1)/young/Igz
    k2 = a**4/30/l+a**2*l/9
    k4 = -a**4/30
    return (-a**2*u**2/6+a**2*u**3/18/l+k2*u+k4)/young/Igz

  # deformée de la barre isostatique sous charge uniformément répartie
  # entre u = 0 et u = alpha*l
  def _PsiQu(self, alpha, u, l, young, Igz):
    if alpha == 1:
      return 1./24/young/Igz*u*(u**3-2*l*u**2+l**3)
    a = alpha*l
    if u < a:
      k1 = a**2*(2*l-a)**2/12
      return u*(l*u**3/12-a*l*u**2/3+a**2*u**2/6+k1)/2/l/young/Igz
    k3 = a**4/12+a**2*l**2/3
    k4 = -l*a**4/12
    return (a**2*u**3/6-l*a**2*u**2/2+k3*u+k4)/2/l/young/Igz

  # deformée de la barre isostatique sous charge ponctuelle
  # appliquée à la distance alpha = a/l
  def _PsiFp(self, u, l, alpha, young, Igz):
    if u/l>alpha:
      u = l-u 
      # changement de variable pour utiliser la même formule
      # valable uniquement entre 0 et a
      alpha = 1-alpha
    return (1.-alpha)*u/6/young/Igz*(l**2-l**2*(1-alpha)**2-u**2)

  # deformée de la barre isostatique sous moment ponctuel
  # appliquée à la distance alpha = a/l
  def _PsiMp(self, u, l, alpha, young, Igz):
    sens = 1
    if u/l>alpha:
      u = l-u 
      alpha = 1-alpha
      sens = -1 # car cas de charge non symétrique
    return -sens*u/6/young/Igz/l*(6*alpha*l**2-u**2-3*(alpha*l)**2-2*l**2)

  def DepPoint(self, Char, barre, u):
    """Retourne le vecteur de déplacement d'un point d'une barre dans le repère global (u en m)"""
    angle = self.struct.Angles[barre]
    l = self.struct.Lengths[barre]
    liTherm = Char.charBarTherm.get(barre, [])
    charTri = Char.charBarTri.get(barre, {})
    charQu = Char.charBarQu.get(barre, {})
    charFp = Char.charBarFp.get(barre, {})
    chars = charFp, charQu, charTri, liTherm

    relaxs = self.struct.IsRelax
    # pt 1 : origine barre
    pt1name = self.struct.Barres[barre][0]
    pt1 = self.struct.Nodes[pt1name] 
    # pt2 : extremité barre
    pt2name = self.struct.Barres[barre][1]
    pt2 = self.struct.Nodes[pt2name] 
    # Coordonnées du point avant déformation dans le rep G
    deltaX = pt2[0]-pt1[0]
    deltaY = pt2[1]-pt1[1]
    pt = [pt1[0]+deltaX/l*u, pt1[1]+deltaY/l*u]
    # Coordonnées du point origine après déformation dans rep G
    ddl = Char.ddlValue
    pt1defx, pt1defy = pt1[0]+ddl[pt1name][0], pt1[1]+ddl[pt1name][1]
    pt2defx, pt2defy = pt2[0]+ddl[pt2name][0], pt2[1]+ddl[pt2name][1]
    deltaX = pt2defx-pt1defx
    deltaY = pt2defy-pt1defy
    ptdef = [pt1defx+deltaX/l*u, pt1defy+deltaY/l*u]
    defo = self.DefoPoint(Char, barre, l, angle, u, ddl, relaxs, chars)
    fleche = [0., defo]
    if not angle == 0:
      ProjL2G(fleche, angle)
    ptdef[0] += fleche[0]
    ptdef[1] += fleche[1]
    depx = ptdef[0]-pt[0]
    depy = ptdef[1]-pt[1]
    return depx, depy

  def FlechePoint(self, Char, barre, u):
    """Calcule la flèche (déplacement perpendiculaire à la barre) d'un point défini par -u- dans le repère de la barre"""
    li = self.DepPoint(Char, barre, u) 
    angle = self.struct.Angles[barre]
    if not angle == 0:
      li = ProjG2LCoors(li[0], li[1], angle)
    return li



  def DefoBarre(self, barre, Char, is_coef=False):
    """Retourne une liste de valeurs pour le tracé du moment fléchissant
    sur une barre.
    -> Un tuple contenant un seul point pour chaque segment de droite ou discontinuité ((u, soll), )
    -> Un tuple de valeurs contenant les points de controles pour le tracé de la Bézier ((endX, endY), (C1x, C1y), (C2x, C2y), (a, b, c))
    a, b, c, d polynome coefs"""
    struct = self.struct
    l = struct.Lengths[barre]
    angle = struct.Angles[barre]
    relaxs = struct.IsRelax
    liTherm = Char.charBarTherm.get(barre, [])
    charTri = Char.charBarTri.get(barre, {})
    charQu = Char.charBarQu.get(barre, {})
    charFp = Char.charBarFp.get(barre, {})
    positions, discontinus = self._get_char_abs(barre, charQu, charFp, charTri, 2)
    chars = charFp, charQu, charTri, liTherm
    ddl = Char.ddlValue
    E = struct._GetYoung(barre)
    I = struct._GetMQua(barre)
    therm = 0.
    if liTherm:
      H = struct.GetH(barre)
      alpha = struct._GetAlpha(barre)
      ts = liTherm[0]
      ti = liTherm[1]
      therm = alpha*(ti-ts)/H
      #defo += alpha/2/H*self._PsiTherm(u, l, ts-ti)

    # rotation origine
# faire une fonction
    noeud1, noeud2, relax1, relax2 = struct.Barres[barre]
    rz = False
    if noeud1 in struct.RotuleElast:
      barre_elast = struct.RotuleElast[noeud1][0]
      if barre == barre_elast:
        rz = True
    if noeud1 in relaxs or relax1 == 1:
      rot_prec = Char.RelaxBarRotation[barre][1]
    elif rz:
      rot_prec = ddl[noeud1][3]
    else:
      rot_prec = ddl[noeud1][2]

# optimiser mieux pour le cas où la charge est achevée
    if not charTri == {}:
      deg = 5
    elif not charQu == {}:
      deg = 4
    elif not charFp == {}:
      deg = 3
    elif relax1 == 1 and relax2 == 1:
      # barre relaxée et non chargée
      deg = 1
    else:
      # barre sans chargement mais avec une rotation d'extrémité
      deg = 3
    li, li2 = [], []
    values = {}
    # start point
    uprec = 0.
    Mprec = self.MomentPoint(Char, barre, 0., charQu, charFp, charTri, 1)
    depUprec, depVprec = self.GetLocalDep(Char, barre, l, angle, 0., ddl, relaxs, chars)
    pt0 = (0., depUprec, depVprec)
    if not is_coef:
      li.append((pt0, ))
    for i, alpha in enumerate(positions):
      if alpha==0  : continue
      #print("u=", alpha, barre, 'deg=', deg)
      u = alpha*l
      deltaU = u-uprec
      depU, depV = self.GetLocalDep(Char, barre, l, angle, u, ddl, relaxs, chars)
      M = self.MomentPoint(Char, barre, u, charQu, charFp, charTri, 1)
      if deg == 1:
        if is_coef:
          b = (depV-depVprec)/(deltaU)
          c = depVprec - b*uprec
          li2.append((u, (b, c)))
        else:
          end_pt = (deltaU, depU-depUprec, depV-depVprec)
          li.append((end_pt, ))
        # on quitte la barre
        break # or continue 
      elif deg == 3: # inclu aussi degré 2
        tu = self._get_linear_coef(uprec, Mprec, u, M)
        a, b = tu[0] # EIv'' = M = a*u+b
        a, b = a/E/I, b/E/I
        b += therm
        # intégration 1
        a = a/2
        c = rot_prec-a*uprec**2-b*uprec
        has_r = self.get_zero(uprec, u, a, b, c)
        # intégration 2
        rot = a*u**2+b*u+c
        a, b = a/3, b/2
        d = depVprec-(a*uprec**3+b*uprec**2+c*uprec) # EIv = a*u**3+b*u**2+c*u+d
        C1, C2 = self._get_control_points2(rot_prec, rot, depVprec, depV, deltaU)
        if is_coef:
          li2.append((u, (a, b, c, d)))
        else:
          end_pt = (deltaU, depU-depUprec, depV-depVprec)
          li.append((end_pt, C1, C2, (a, b, c, d)))

        if not has_r is None:
          r = has_r
          dx = depUprec + (depU-depUprec)/deltaU*(r-uprec) # les dep X sont pris proportionnellement ce qui peut être faux
          values[r/l] = {0: (dx, a*r**3+b*r**2+c*r+d)}

      elif deg == 4: # coefs exacts mais tracé approché (on coupe en deux)
        M50 = self.MomentPoint(Char, barre, uprec+deltaU/2, charQu, charFp, charTri, 1)
        tu = self._get_parabolic_coef(uprec, Mprec, uprec+deltaU/2, M50, u, M)
        a, b, c = tu[0] # EIv'' = M = a*u**2+b*u+c
        a, b, c = a/E/I, b/E/I, c/E/I
        c += therm
        # intégration 1 => v'
        a, b = a/3, b/2
        d = rot_prec-a*uprec**3-b*uprec**2-c*uprec
        rot = a*u**3+b*u**2+c*u+d

        # recherche racine de v'
# finir si tous les termes sont nuls
        has_r = self.get_zero(uprec, u, a, b, c, d)
        if has_r is None:
          r = (u+uprec)/2
          rotr = a*r**3+b*r**2+c*r+d
        else:
          r = has_r
          rotr = 0.

        # intégration 2 => v
        a, b, c = a/4, b/3, c/2
        e = depV-(a*u**4+b*u**3+c*u**2+d*u)
        # on coupe l'intervalle en deux autour de r
        depVr = a*r**4+b*r**3+c*r**2+d*r+e
        C1, C2 = self._get_control_points2(rot_prec, rotr, depVprec, depVr, r-uprec)
        du = (depU-depUprec)/deltaU
        if is_coef:
          li2.append((u, (a, b, c, d, e)))
        else:
          end_pt = (r-uprec, du*(r-uprec), depVr-depVprec)
          li.append((end_pt, C1, C2, (a, b, c, d, e)))
        C1, C2 = self._get_control_points2(rotr, rot, depVr, depV, u-r)
        if not is_coef:
          end_pt = (u-r, du*(u-r), depV-depVr)
          li.append((end_pt, C1, C2, (a, b, c, d, e)))
        if not has_r is None:
          r = has_r
          dx = depUprec + du*(r-uprec) # les dep X sont pris proportionnellement ce qui peut être faux
          values[r/l] = {0: (dx, depVr)}

      elif deg == 5: # tracé approché (on coupe en deux)
        Vprec = self.TranchantPoint(Char, barre, uprec*(1+1e-10), charQu, charFp, charTri, 1)
        V = self.TranchantPoint(Char, barre, u, charQu, charFp, charTri, 1)
        V50 = self.TranchantPoint(Char, barre, uprec+deltaU/2, charQu, charFp, charTri, 1)
        tu = self._get_parabolic_coef(uprec, Vprec, uprec+deltaU/2, V50, u, V)
        a, b, c = tu[0] # V = a*u**2+b*u+c
        # intégration 1 => M
        a, b, c = -a/3, -b/2, -c
        d = Mprec-a*uprec**3-b*uprec**2-c*uprec
        d += therm
        # intégration 2 => v'
        a, b, c, d = a/4/E/I, b/3/E/I, c/2/E/I, d/E/I
        e = rot_prec-(a*uprec**4+b*uprec**3+c*uprec**2+d*uprec)
        rot = a*u**4+b*u**3+c*u**2+d*u+e
        # recherche racine de v'
        has_r = self.get_zero(uprec, u, a, b, c, d, e)
        if has_r is None:
          r = (u+uprec)/2
          rotr = a*r**4+b*r**3+c*r**2+d*r+e
        else:
          r = has_r
          rotr = 0.

        # intégration 3 => v
        a, b, c, d = a/5, b/4, c/3, d/2
        f = depV-(a*u**5+b*u**4+c*u**3+d*u**2+e*u)

        depVr = a*r**5+b*r**4+c*r**3+d*r**2+e*r+f
        C1, C2 = self._get_control_points2(rot_prec, rotr, depVprec, depVr, r-uprec)
        du = (depU-depUprec)/deltaU
        if is_coef:
          li2.append((u, (a, b, c, d, e, f)))
        else:
          end_pt = (r-uprec, du*(r-uprec), depVr-depVprec)
          li.append((end_pt, C1, C2, (a, b, c, d, e, f)))
        C1, C2 = self._get_control_points2(rotr, rot, depVr, depV, u-r)
        if not is_coef:
          end_pt = (u-r, du*(u-r), depV-depVr)
          li.append((end_pt, C1, C2, (a, b, c, d, e, f)))
        if not has_r is None:
          r = has_r
          dx = depUprec + du*(r-uprec) # les dep X sont pris proportionnellement ce qui peut être faux
          values[r/l] = {0: (dx, depVr)}
      else: 
        print("debug in DefoBarre")
        
      uprec = u
      if alpha in discontinus:
        M = self.MomentPoint(Char, barre, u*(1+1e-10), charQu, charFp, charTri, 1)
      Mprec = M
      depUprec = depU
      depVprec = depV
      rot_prec = rot
    self.bar_values[barre] = self._GetSortedVal2(values)
    #self.bar_values[barre] = values
    if is_coef:
      return li2
    #print("DefoBarre=",barre, li)
    return li




# renommer et remplacer defopoint chaque fois que defopoint appelée un nombre limité de fois
  def TestDefoPoint(self, Char, barre, u):
    """Fonction identique à DefoPoint mais sans tous ses arguments"""
    struct = self.struct
    l = struct.Lengths[barre]
    angle = struct.Angles[barre]
    ddl = Char.ddlValue
    relaxs = struct.IsRelax
    liTherm = Char.charBarTherm.get(barre, [])
    charTri = Char.charBarTri.get(barre, {})
    charQu = Char.charBarQu.get(barre, {})
    charFp = Char.charBarFp.get(barre, {})

    chars = charFp, charQu, charTri, liTherm
    return self.DefoPoint(Char, barre, l, angle, u, ddl, relaxs, chars)


  def DefoPoint(self, Char, barre, l, angleBarre, u, ddl, relaxs, chars):
    """Retourne le déplacement v perpendiculaire à une barre d'un point donné par u (absolu) dans le repère local de la barre"""
    struct = self.struct
    E = struct._GetYoung(barre)
    I = struct._GetMQua(barre)
    charFp, charQu, triangulars, liTherm = chars

    noeud1, noeud2, relax1, relax2 = struct.Barres[barre]
    rz = False
    if noeud1 in struct.RotuleElast:
      barre_elast = struct.RotuleElast[noeud1][0]
      if barre == barre_elast:
        rz = True
    # deplacements nodaux dans le repère global
    x1 = ddl[noeud1][0]
    y1 = ddl[noeud1][1] 
    if noeud1 in relaxs or relax1 == 1:
      w1 = Char.RelaxBarRotation[barre][1]
    elif rz:
      w1 = ddl[noeud1][3]
    else:
      w1 = ddl[noeud1][2]
    rz = False
    if noeud2 in struct.RotuleElast:
      barre_elast = struct.RotuleElast[noeud2][0]
      if barre == barre_elast:
        rz = True
    x2 = ddl[noeud2][0]
    y2 = ddl[noeud2][1]
    if noeud2 in relaxs or relax2 == 1:
      w2 = Char.RelaxBarRotation[barre][2]
    elif rz:
      w2 = ddl[noeud2][3]
    else:
      w2 = ddl[noeud2][2]
    if barre in Char._RotationIso:
      w1 -= Char._RotationIso[barre][0]
    if barre in Char._RotationIso:
      w2 -= Char._RotationIso[barre][1]
    # deplacements nodaux dans le repère local
    if not angleBarre == 0:
      u1, v1 = ProjG2LCoors(x1, y1, angleBarre)
    else:
      u1, v1 = x1, y1
    if not angleBarre == 0:
      u2, v2 = ProjG2LCoors(x2, y2, angleBarre)
    else:
      u2, v2 = x2, y2
    defo = self._Psi5(u, l)*(v2-v1)
    defo += self._Psi3(u, l)*w1
    defo += self._Psi6(u, l)*w2
    if charQu:
      for alpha, char in charQu.items():
        qu = char[1]
        defo += qu*self._PsiQu(alpha, u, l, E, I)
    if triangulars:
      for alpha, char in triangulars.items():
        q = char[1]
        defo += q*self._PsiTri(alpha, u, l, E, I)

    if charFp:
      for alpha, char in charFp.items():
        fp = char[1]
        Mp = char[2]
        if fp != 0 :
          defo += fp*self._PsiFp(u, l, alpha, E, I)
        if Mp != 0 :
          defo += Mp*self._PsiMp(u, l, alpha, E, I)
    if liTherm:
      H = struct.GetH(barre)
      #if barre in struct.Section_H:
      #  H = struct.Section_H[barre]
      #else:
      #  H = struct.Section_H["*"]
      alpha = struct._GetAlpha(barre)
      #alpha = struct.Alphas[barre]
      ts = liTherm[0]
      ti = liTherm[1]
      defo += alpha/2/H*self._PsiTherm(u, l, ts-ti)
    return defo

# identique à DefoPoint mais rajoute les translations nodales
# regrouper 
  def GetLocalDep(self, Char, barre, l, angleBarre, u, ddl, relaxs, chars):
    """Retourne le déplacement v perpendiculaire à une barre d'un point donné par u (absolu) dans le repère local de la barre"""
    struct = self.struct
    E = struct._GetYoung(barre)
    I = struct._GetMQua(barre)
    charFp, charQu, triangulars, liTherm = chars

    noeud1, noeud2, relax1, relax2 = struct.Barres[barre]
    rz = False
    if noeud1 in struct.RotuleElast:
      barre_elast = struct.RotuleElast[noeud1][0]
      if barre == barre_elast:
        rz = True
    # deplacements nodaux dans le repère global
    x1 = ddl[noeud1][0]
    y1 = ddl[noeud1][1] 
    if noeud1 in relaxs or relax1 == 1:
      w1 = Char.RelaxBarRotation[barre][1]
    elif rz:
      w1 = ddl[noeud1][3]
    else:
      w1 = ddl[noeud1][2]
    rz = False
    if noeud2 in struct.RotuleElast:
      barre_elast = struct.RotuleElast[noeud2][0]
      if barre == barre_elast:
        rz = True
    x2 = ddl[noeud2][0]
    y2 = ddl[noeud2][1]
    if noeud2 in relaxs or relax2 == 1:
      w2 = Char.RelaxBarRotation[barre][2]
    elif rz:
      w2 = ddl[noeud2][3]
    else:
      w2 = ddl[noeud2][2]
    if barre in Char._RotationIso:
    #if barre in Char._RotationIso and relax1 == 0:
      w1 -= Char._RotationIso[barre][0]
    if barre in Char._RotationIso:
    #if barre in Char._RotationIso and relax2 == 0:
      w2 -= Char._RotationIso[barre][1]
    # deplacements nodaux dans le repère local

    if not angleBarre == 0:
      u1, v1 = ProjG2LCoors(x1, y1, angleBarre)
      u2, v2 = ProjG2LCoors(x2, y2, angleBarre)
    else:
      u1, v1 = x1, y1
      u2, v2 = x2, y2
    depU = u1*(1-u/l)+u2*u/l
    depV = v1*(1-u/l)+v2*u/l
    depV += self._Psi5(u, l)*(v2-v1)
    depV += self._Psi3(u, l)*w1
    depV += self._Psi6(u, l)*w2
    if charQu:
      for alpha, char in charQu.items():
        qu = char[1]
        depV += qu*self._PsiQu(alpha, u, l, E, I)
    if triangulars:
      for alpha, char in triangulars.items():
        q = char[1]
        depV += q*self._PsiTri(alpha, u, l, E, I)

    if charFp:
      for alpha, char in charFp.items():
        fp = char[1]
        Mp = char[2]
        if fp != 0 :
          depV += fp*self._PsiFp(u, l, alpha, E, I)
        if Mp != 0 :
          depV += Mp*self._PsiMp(u, l, alpha, E, I)
    if liTherm:
      H = struct.GetH(barre)
      alpha = struct._GetAlpha(barre)
      ts = liTherm[0]
      ti = liTherm[1]
      depV += alpha/2/H*self._PsiTherm(u, l, ts-ti)
    return depU, depV
  



# ----------- CALCUL DES SOLLICITATIONS DANS LES BARRES -------------------
  def NormalPoint(self, Char, barre, u, charQu, charFp, charTri, conv):
    N = -Char.EndBarSol[barre][0][0]
    N += self.NormalIso(barre, u, charQu, charFp, charTri)
    crit = 1e-12
    if abs(N) < crit:
      return 0.
    if conv == -1:
      return -N
    return N

  def NormalIso(self, barre, u, charQu, charFp, charTri):
    l = self.struct.Lengths[barre]
    N0 = 0.
    if charTri:
      for alpha, val in charTri.items():
        q = val[0]
        if u >= alpha*l:
          N0 -= q*alpha*l/2
        else:
          N0 -= q*u**2/2/alpha/l
    if charQu:
      for alpha, val in charQu.items():
        qu = val[0]
        if u >= alpha*l:
          N0 -= qu*alpha*l
        else:
          N0 -= qu*u
    if charFp:
      for alpha, fp in charFp.items():
        if u > alpha*l:
          N0 -= fp[0]
    return N0




  def TranchantPoint(self, Char, barre, u, charQu, charFp, charTri, conv):
    """Retourne la valeur de l'effort tranchant dans la barre"""
    V1 = -Char.EndBarSol[barre][0][1]
    V0 = self.TranchantIso(barre, u, charQu, charFp, charTri)
    V = V1+V0
    crit = 1e-12
    if abs(V) < crit:
      return 0.
    if conv == -1:
      return -V
    return V

  def TranchantIso(self, barre, u, charQu, charFp, charTri):
    """Retourne la valeur de l'effort tranchant dans la barre isostatique équivalente
    En cas de discontinuité de V au point considéré, retourne la valeur à gauche
    u est une position abs sur la barre (et non un %)"""
    l = self.struct.Lengths[barre]
    V0 = 0.
    if charTri:
      for alpha, val in charTri.items():
        q = val[1]
        if u >= alpha*l:
          V0 -= q*alpha*l/2
        else:
          V0 -= q*u**2/alpha/l/2
    if charQu:
      for alpha, val in charQu.items():
        qu = val[1]
        if u >= alpha*l:
          V0 -= qu*alpha*l
        else:
          V0 -= qu*u
    if charFp:
      for alpha, fp in charFp.items():
        if u > alpha*l:
          V0 -= fp[1]
    return V0



  def _GetNextAlpha(self, alpha0, liAlpha):
    """Retourne la position alpha du chargement sur barre immédiatement 
    supérieur à alpha0"""
    if liAlpha == []: return 1.
    for i in liAlpha:
      if alpha0 < i: return i
    return 1.

  def GetArcValue(self, Char, status, b, pos):
    """Retourne une valeur (sollicitation ou déformée) pour le point d'un arc donné par la barre et la position relative. Retourne un tuple (valx, valy) dans le repère de la barre."""
    struct = self.struct
    unit_conv = struct.units
    if status == 4:
      val0 = -Char.EndBarSol[b][0][0]
      val1 = Char.EndBarSol[b][1][0]
      val = val0 + (val1-val0)*pos
      text = function.PrintValue(val, unit_conv['F'])
      val = (0., val)
    elif status == 5:
      val0 = -Char.EndBarSol[b][0][1]
      val1 = Char.EndBarSol[b][1][1]
      val = val0 + (val1-val0)*pos
      text = function.PrintValue(val, unit_conv['F'])
      val = (0., val)
    elif status == 6:
      val0 = -Char.EndBarSol[b][0][2]
      val1 = Char.EndBarSol[b][1][2]
      val = val0 + (val1-val0)*pos
      text = function.PrintValue(val, unit_conv['F']*unit_conv['L'])
      val = (0., val)
    elif status == 7:
      angle = struct.Angles[b]
      node0 = struct.Barres[b][0]
      val0x, val0y, w = Char.ddlValue[node0]
      node1 = struct.Barres[b][1]
      val1x, val1y, w = Char.ddlValue[node1]
      valx = val0x + (val1x-val0x)*pos
      valy = val0y + (val1y-val0y)*pos
      valxp = valx*math.cos(angle)+valy*math.sin(angle)
      valyp = -valx*math.sin(angle)+valy*math.cos(angle)
      dep = (valxp**2+valyp**2)**0.5
      text = function.PrintValue(dep, unit_conv['L'])
      val = (valxp, valyp)
    else:
      print("debug in GetArcValue")
    return val, text


# tranchant faire la moyenne
  def GetArcSollValues(self, name, Char, n_soll, crit):
    """Retourne les valeurs remarquables d'une courbe donnée par Char"""
    #print("GetArcSollValues")
    precision = crit*1e5
    struct = self.struct
    Lengths = struct.Lengths
    arc = struct.Curves[name]
    user_nodes = arc.user_nodes
    N0, N1 = user_nodes[0].name, user_nodes[-1].name
    b0, b1 = arc.b0, arc.b1
    resu = {}
    prec = -Char.EndBarSol[b0][0][n_soll]
    if abs(prec) > crit:
      resu[b0] = (prec, 0.)
    val = -Char.EndBarSol[b0+1][0][n_soll]
    l = Lengths[b0]+ Lengths[b0+1]
    for barre in range(b0+2, b1):
      next = -Char.EndBarSol[barre+1][0][n_soll]
      if (prec-val)*(val-next) > 0:
        l += Lengths[barre]
        prec, val = val, next
        continue
      if abs(val) <= precision:
        prec, val = val, next
        l += Lengths[barre]
        continue
      resu[barre] = (val, l)
      l += Lengths[barre]
      prec, val = val, next
    val = -Char.EndBarSol[b1-1][0][n_soll]
    next = Char.EndBarSol[b1][1][n_soll]
    if abs(next) > crit and abs(next-val) > crit:
      ltot = arc.get_size(Lengths)
      resu[b1] = (next, ltot)
    return resu

  def GetArcDefoValues(self, name, Char, n_soll, crit):
    """Retourne les valeurs remarquables d'une courbe donnée par Char"""
    return {}
    precision = crit*1e5
    struct = self.struct
    arc = struct.Curves[name]
    user_nodes = arc.user_nodes
    N0, N1 = user_nodes[0].name, user_nodes[-1].name
    b0, b1 = arc.b0, arc.b1
    barres = struct.Barres
    Angles = struct.Angles
    resu = {}
    maxi, mini = 0., 0.
    bmaxi, bmini = None, None
    lmaxi, lmini = 0., 0.
    l = 0.
    #print(Char.ddlValue)
    for barre in range(b0, b1+1):
      angle = Angles[barre]
      N0 = barres[barre][0]
      #if barre == 99:#XXX 
      #  N0 = barres[barre][1]
      u, v = Char.ddlValue[N0][0:2]
      beta = function.get_vector_angle((0, 0), (u, v))
      if beta is None:
        continue
      dep = (u**2+v**2)**0.5
      alpha = beta-(angle+math.pi/2)
      #val = dep
      val = dep*math.cos(alpha)
      print(barre, val, beta, angle, alpha)
      if val > maxi:
        maxi = val
        bmaxi = barre
        lmaxi = l
      elif val < mini:
        mini = val
        bmini = barre
        lmini = l
      l += struct.Lengths[barre]
    if not bmaxi is None:
      resu[bmaxi] = (maxi, lmaxi)
    if not bmini is None:
      resu[bmini] = (mini, lmini)
    print(resu)
    return resu

  def GetValue(self, barre, x, Char, status):
    """Retourne une valeur en un point en fonction du status
    x : longueur absolue"""
    charQu = Char.charBarQu.get(barre, {})
    charFp = Char.charBarFp.get(barre, {})
    charTri = Char.charBarTri.get(barre, {})
    if status == 4:
      val = self.NormalPoint(Char, barre, x, charQu, charFp, charTri, self.conv)
      tu = (0., val)
    elif status == 5:
      val = self.TranchantPoint(Char, barre, x, charQu, charFp, charTri, self.conv)
      tu = (0., val)
    elif status == 6:
      val = self.MomentPoint(Char, barre, x, charQu, charFp, charTri, self.conv)
      tu = (0., val)
    elif status == 7:
      tu = self.FlechePoint(Char, barre, x)
    #print("GetValue", barre, x, tu[1])
    return tu

  def GetDataEq(self, barre, Char, status):
    """Retourne les coefficients des équations des courbes"""
    try:
      Char.EndBarSol # provisoire 
    except AttributeError:
      return []
    if status == 4:
      points = self.ForceBarre(barre, Char, 0, is_coef=True)
    elif status == 5:
      points = self.ForceBarre(barre, Char, 1, is_coef=True)
    elif status == 6:
      points = self.MomentBarre(barre, Char, is_coef=True)
    elif status == 7:
      points = self.DefoBarre(barre, Char, is_coef=True)
    return points



  def ForceBarre(self, barre, Char, status, is_coef=False):
    """Retourne une liste de valeurs pour le tracé de l'effort normal ou tranchant sur une barre.
    Un tuple contenant un point pour chaque segment de droite et discontinuité
    Un tuple de valeurs contenant les points de controles pour le tracé de la Bézier"""
    l = self.struct.Lengths[barre]
    liTherm = Char.charBarTherm.get(barre, [])
    charTri = Char.charBarTri.get(barre, {})
    charQu = Char.charBarQu.get(barre, {})
    charFp = Char.charBarFp.get(barre, {})
    positions, discontinus = self._get_char_abs(barre, charQu, charFp, charTri, status)
    #print("valeur nulle de l'effort V finir", self.GetVZero(barre, Char))
    if charTri == {}:
      is_line = True
    else:
      is_line = False

    if status == 0:
      f = self.NormalPoint
    elif status == 1:
      f = self.TranchantPoint
    values = {} # format {u: {0:valG ou continue, 1: valD}}
    li, li2 = [], []
    uprec = 0.
    Vprec = f(Char, barre, 0., charQu, charFp, charTri, self.conv)
    pt0 = (uprec, Vprec)
    if not is_coef:
      li.append((pt0, ))
    values[0.] = {0: Vprec}
    for i, a in enumerate(positions):
      u = a*l
      # optimiser mieux pour le cas où la charge qu est achevée
      if is_line:
        V = f(Char, barre, u, charQu, charFp, charTri, self.conv)
        pt1 = (u-uprec, V-Vprec)
        if is_coef:
          b = (V-Vprec)/(u-uprec)
          c = Vprec - b*uprec
          li2.append((u, (b, c)))
        else:
          li.append((pt1, (uprec, u)))
        Vprec = V
        values[a] = {0: V}
        if a in discontinus:
          Vright = f(Char, barre, u*(1+1e-10), charQu, charFp, charTri, self.conv)
          V = -V + Vright
          discont = (0., V)
          li.append((discont, ))
          Vprec = Vright
          values[a][1] = Vright
      else:
        start_pt = (uprec, Vprec)
        mid_pos = (uprec+u)/2
        middle_pt = (mid_pos, f(Char, barre, mid_pos, charQu, charFp, charTri, self.conv))
        V = f(Char, barre, u, charQu, charFp, charTri, self.conv)
        end_pt = (u, V)
        resu = get_control_points(start_pt, middle_pt, end_pt)
        if is_coef:
          li2.append((u, resu[3]))
        else:
          if len(resu) == 1:
            li.append((resu[0], (uprec, u)))
          else:
            li.append(resu)
        # pas de valeur max pour les courbes paraboliques : a tester
        values[a] = {0: V}
        Vprec = V
        if a in discontinus:
          Vright = f(Char, barre, u*(1+1e-10), charQu, charFp, charTri, self.conv)
          V = -V + Vright
          li.append(((0., V), ))
          Vprec = Vright
          values[a][1] = Vright
      uprec = u
    #print("barre=", barre, values)
    self.bar_values[barre] = self._GetSortedVal(values)
    if is_coef:
      return li2
    return li

  def _GetSortedVal(self, values):
    """Tri les valeurs des sollicitations sur une barre de façon à supprimer les doublons et les valeurs faibles"""
# ne supprime pas les valeurs en doubles sur les noeuds
# il vaudrait mieux ne pas avoir mis les valeurs quasi nulles dans values
    crit = 1e-10
    di = {}
    maxi, mini = 0, 0
    for pos in values:
      for i in values[pos]:
        if abs(values[pos][i]) > crit:
          val = values[pos][i]
          di.setdefault(pos, {})[i] = val
          if val > maxi:
            maxi = val
          elif val < mini:
            mini = val
    positions = list(di.keys())
    prec = 0
    for pos in positions:
      values = list(di[pos].keys())
      values.sort()
      if pos == 0.:
        if 1 in values:
          prec = di[pos][1]
        elif 0 in values:
          prec = di[pos][0]
        continue
      if pos == 1.:
        continue
      if len(values) == 2:
        if abs(di[pos][0] - prec) < crit:
          del(di[pos][0])
        prec = di[pos][1]
        continue # on laisse les valeurs pour les discontinuités
      for i in values:
        val = di[pos][i]
        if not val == maxi or val == mini:
          del(di[pos][i])
          prec = val
          continue
        if abs(val - prec) < crit:
          del(di[pos][i])
        prec = val
    return di

  def _GetSortedVal2(self, values):
    crit = 1e-12
    di = {}
    #maxi, mini = 0, 0
    for pos in values:
      #for i in values[pos][0]:
      dx, dy = values[pos][0]
      if abs(dy) > crit:
        #val = values[pos][i]
        di.setdefault(pos, {})[0] = (dx, dy)
          #if val > maxi:
          #  maxi = val
          #elif val < mini:
          #  mini = val
    return di



  def MomentPoint(self, Char, barre, u, charQu, charFp, charTri, conv):
    """Retourne la valeur du moment fléchissant sur une barre à l'abscisse u
    u est une position abs sur la barre (et non un %)
    en cas de discontinuité, retourne la valeur à gauche"""
    #print("MomentPoint", charTri)
    l = self.struct.Lengths[barre]
    M1 = -Char.EndBarSol[barre][0][2]
    M2 = Char.EndBarSol[barre][1][2]
    mf0 = self.MomentIso(barre, u, charQu, charFp, charTri)
    M = M1+(M2-M1)/l*u+mf0
    crit = 1e-12
    if abs(M) < crit:
      return 0.
    if conv == -1:
      return -M
    return M

  def MomentIso(self, barre, u, charQu, charFp, charTri):
    """Retourne la valeur du moment fléchissant dans la barre isostatique équivalente
    # u est une position abs sur la barre (et non un %)
    # en cas de discontinuité, retourne la valeur à gauche"""
    l = self.struct.Lengths[barre]
    mf0 = 0.

    if charTri:
      for alpha, val in charTri.items():
        q = val[1]
        a = alpha*l
        if u >= a:
          mf0 += q*a**2*(-1./3+u/3/l)
        else:
          mf0 += q*(-a*u/2+a**2*u/3/l+u**3/6/a)

    if charQu: 
      for alpha, val in charQu.items():
        qu = val[1]
        a = alpha*l
        if u >= a:
        #mf0 += -qu/2.*u*(l-u) charge uniformément répartie
          mf0 += -qu*a**2/2/l*(l-u)
        else:
          mf0 += qu*u/2/l*(l*u-2*a*l+a**2)
    if charFp:
      for alpha, char in charFp.items():
        fp = char[1]
        Mp = char[2]
        if fp != 0 and u/l <= alpha:
          mf0 += -fp*(1-alpha)*u
        elif fp != 0 and u/l > alpha:
          mf0 += -fp*l*alpha*(1-u/l)
        if Mp != 0 :
          if alpha==0:
            mf0 += -Mp*(1-u/l)
          elif alpha==1:
            mf0 += Mp/l*u
          elif u/l <= alpha:
            mf0 += Mp/l*u
          else:
            mf0 += -Mp*(1-u/l)
    return mf0


  def MomentBarre(self, barre, Char, is_coef=False):
    """Retourne une liste de valeurs pour le tracé du moment fléchissant
    sur une barre.
    -> Un tuple contenant un seul point pour chaque segment de droite ou discontinuité ((u, soll), )
    -> Un tuple de valeurs contenant les points de controles pour le tracé de la Bézier ((endX, endY), (C1x, C1y), (C2x, C2y), (a, b, c))
    a, b, c, d polynome coefs"""
    l = self.struct.Lengths[barre]
    liTherm = Char.charBarTherm.get(barre, [])
    charTri = Char.charBarTri.get(barre, {})
    charQu = Char.charBarQu.get(barre, {})
    charFp = Char.charBarFp.get(barre, {})
    positions, discontinus = self._get_char_abs(barre, charQu, charFp, charTri, 2)
    if charQu == {} and charTri == {}:
      is_line = True
    else:
      is_line = False 
    li, li2 = [], []
    values = {} # format {u: {0:valG ou continue, 1: valD}}

    # start point
    uprec = 0.
    Mprec = self.MomentPoint(Char, barre, 0., charQu, charFp, charTri, self.conv)
    Vprec = self.TranchantPoint(Char, barre, 0., charQu, charFp, charTri, self.conv)
    pt0 = (uprec, Mprec)
    if not is_coef:
      li.append((pt0, ))
    values[0] = {0: Mprec}

    for i, alpha in enumerate(positions):
      u = alpha*l
      # optimiser mieux pour le cas où la charge qu est achevée
      if is_line: 
        M = self.MomentPoint(Char, barre, u, charQu, charFp, charTri, self.conv)
        pt1 = (u-uprec, M-Mprec)
        if is_coef:
          b = (M-Mprec)/(u-uprec)
          c = Mprec - b*uprec
          li2.append((u, (b, c)))
        else:
          li.append((pt1, (uprec, u)))
        Mprec = M
        values[alpha] = {0: M}
        if alpha in discontinus:
          Mright = self.MomentPoint(Char, barre, u*(1+1e-10), charQu, charFp, charTri, self.conv)
          M = -M + Mright
          discont = (0., M)
          li.append((discont, ))
          Mprec = Mright
          values[alpha][1] = Mright
      else:
        deltaU = u-uprec

# optimiser mieux
# revoir : faut il systématiquement prendre (1+1e-10) pour les val prec???
        Vprec = self.TranchantPoint(Char, barre, uprec*(1+1e-10), charQu, charFp, charTri, self.conv)
        V = self.TranchantPoint(Char, barre, u, charQu, charFp, charTri, self.conv)
        Mprec = self.MomentPoint(Char, barre, uprec*(1+1e-10), charQu, charFp, charTri, self.conv)
        M = self.MomentPoint(Char, barre, u, charQu, charFp, charTri, self.conv)

        V50 = self.TranchantPoint(Char, barre, uprec+deltaU/2, charQu, charFp, charTri, self.conv)
        tu = self._get_parabolic_coef(uprec, Vprec, uprec+deltaU/2, V50, u, V)
        a, b, c = tu[0]
        r = tu[1]
        
        # primitives pour y = ax**3+bx**2+cx+d
        a, b, c = -a/3, -b/2, -c
        d = Mprec - a*uprec**3 - b*uprec**2 - c*uprec
        if not r is None:
          values[r/l] = {0: a*r**3+b*r**2+c*r+d}

        # les points doivent être sur une progression arithmétique (deltaU/3)
        # pente = -V = dM/dx
        C1, C2 = self._get_control_points2(-Vprec, -V, Mprec, M, deltaU)
        if is_coef:
          li2.append((u, (a, b, c, d)))
        else:
          end_pt = (deltaU, M-Mprec)
          li.append((end_pt, C1, C2, (a, b, c, d)))
        Mprec = M
        values[alpha] = {0: M}
        if alpha in discontinus:
          Mright = self.MomentPoint(Char, barre, u*(1+1e-10), charQu, charFp, charTri, self.conv)
          M = -M + Mright
          li.append(((0., M), ))
          Mprec = Mright
          values[alpha][1] = Mright
      uprec = u
    #print("values=", barre, values)
    self.bar_values[barre] = self._GetSortedVal(values)
    if is_coef:
      return li2
    return li

  def GetVZero(self, barre, Char):
    """Retourne une liste la liste des abscisses pour lesquelles l'effort tranchant est nul"""
    #print("Rdm::MomentBarre", barre)
    l = self.struct.Lengths[barre]
    liTherm = Char.charBarTherm.get(barre, [])
    charTri = Char.charBarTri.get(barre, {})
    charQu = Char.charBarQu.get(barre, {})


    charFp = Char.charBarFp.get(barre, {})
    positions, discontinus = self._get_char_abs(barre, charQu, charFp, charTri, 1)

    if charTri == {}:
      is_line = True
    else:
      is_line = False

    li = []
    prec = 0.
    prec_val = self.TranchantPoint(Char, barre, 0., charQu, charFp, charTri, self.conv)
    for i, a in enumerate(positions):
      pos = a*l
      val = self.TranchantPoint(Char, barre, pos, charQu, charFp, charTri, self.conv)
      # optimiser mieux pour le cas où la charge qu est achevée
      if is_line:
        if val*prec_val <= 0:
          x0 = (prec*val-pos*prec_val)/(pos-prec)
          li.append(x0)
        prec_val = val
        if a in discontinus:
          right_val = self.TranchantPoint(Char, barre, pos*(1+1e-10), charQu, charFp, charTri, self.conv)
          if right_val*val <= 0:
            li.append(pos)
          prec_val = right_val
      else:
        prec_val = val
        if a in discontinus:
          right_val = self.TranchantPoint(Char, barre, pos*(1+1e-10), charQu, charFp, charTri, self.conv)
          prec_val = right_val
      prec = pos
    return li



  def _get_char_abs(self, barre, charQu, charFp, charTri, status):
    """Retourne deux listes des abscisses (relatives) pour les points de calculs d'une courbe de sollicitation
    -> Points singuliers
    -> Discontinuités"""
    #discontinus = []
    if status == 2:
      positions = [i for i in list(charFp.keys())]
      discontinus = [i for i in list(charFp.keys()) if not charFp[i][status] == 0.]
    else:
      positions = [i for i in list(charFp.keys()) if not charFp[i][status] == 0.]
      discontinus = list(positions)
    #for pos in positions:
    #  if not charFp[pos][status] == 0.:
    #    print("ajout", status, charFp[pos])
    #    discontinus.append(pos)
    for pos in charQu:
      if not pos in positions:
        positions.append(pos)
    for pos in charTri:
      if not pos in positions:
        positions.append(pos)
    positions.sort()
    if not 1. in positions:
      positions.append(1.)
    return positions, discontinus

  #  ----------- FONCTIONS D'AFFICHAGE -------------------------



  def GetNodeVal(self, noeud, Char, type):
    """Recherche pour l'affichage les valeurs des sollicitations
    sur les noeuds. Ne doit être utilisée que pour une structure horizontale"""
    maxi = self.GetCombiMax(type, Char)
    resu = {}
    precision = 1e-8
    beamStart, beamEnd = self.struct.BarByNode[noeud]
    if type == 'N':
      soll = 0
    elif type == 'V':
      soll = 1
    elif type == 'M':
      soll = 2

    if len(beamEnd) == 1:
      barre = beamEnd[0]
      if self.conv == 1:
        val = Char.EndBarSol[barre][1][soll]
      else:
        val = -Char.EndBarSol[barre][1][soll]
      resu[1] = val
    if len(beamStart) == 1:
      barre = beamStart[0]
      if self.conv == 1:
        val = -Char.EndBarSol[barre][0][soll]
      else:
        val = Char.EndBarSol[barre][0][soll]
      resu[0] = val
    # suppression valeur
    if len(resu) == 1:
      val = list(resu.values())[0]
      if not (abs(val) > precision and abs(val)*1e8 > maxi):
        return {}
    elif len(resu) == 2:
      val1, val2 = list(resu.values())
      #print(val1, val2, abs(val1-val2))
      if abs(val1-val2) < precision:
        return {}
    return resu

#
# ----------------- Tools -----------------------------
#
  def get_cubic_max(self, a, b, c, d, x0, x1):
    """Retourne le max ou min dans un intervalle donné du polynome de degré 3
    On suppose qu'il n'y a qu'une seule racine dans l'intervalle"""
    def f(a, b, c, d, x):
      return a*x**3+b*x**2+c*x+d
    def fprime(a, b, c, d, x):
      return 3*a*x**2+2*b*x+c
    # éviter tangente quasi nulle en x0 ou x1
    dx = x1 - x0
    x0 = x0 + dx*1e-2
    x1 = x1 - dx*1e-2
    #print(x0, x1, fprime(a, b, c, d, x0)*fprime(a, b, c, d, x1) )
    if fprime(a, b, c, d, x0)*fprime(a, b, c, d, x1) > 0:
      return None
    
    ap, bp, cp = 3*a, 2*b, c
    delta = bp**2-4*ap*cp
    if delta < 0:
      return  None
    r1 = (-bp+delta**0.5)/2/ap
    if r1 > x0 and r1 < x1:
      return  r1, f(a, b, c, d, r1)
    r1 = (-bp-delta**0.5)/2/ap
    if r1 > x0 and r1 < x1:
      return  r1, f(a, b, c, d, r1)
    #print(r1, x0, x1)
    #print("erreur dans get_cubic_max")
    return None


  def get_zero(self, x0, x1, *coefs):
    """Retourne une racine ou None pour le polynome donné par ses coefs"""
    def f(coefs, x):
      """La fonction polynomiale"""
      rank = len(coefs)
      y = 0
      for c in coefs:
        y += c*x**(rank-1)
        rank -= 1
      return y
    def fp(coefs, x):
      """La fonction dérivée"""
      rank = len(coefs)
      y = 0
      for c in coefs[:-1]:
        y += c*(rank-1)*x**(rank-2)
        rank -= 1
      return y
    y0 = f(coefs, x0)
    y1 = f(coefs, x1)
    if y0*y1 > 0:
      return None
    epsi = 1e-4
    #x = (-x0*y1+x1*y0)/(y0-y1)
    x = (x0+x1)/2
# cette méthode pose un pb de divergence et ne trouve pas forcément la valeur dans l'intervalle
    i = 0 # compteur debug
    while 1 :
      i += 1
      y=f(coefs, x)
      yp=fp(coefs, x)
      if yp == 0:
        return None
      new_x = x - y/yp
      if abs(new_x-x) < epsi:
        break
      if i > 40:
        print("debug::get_zero max iterations")
        return None
      x = new_x
    if x < x0 or x > x1+epsi:
      return None
    return x
  
  def _get_control_points2(self, V0, V1, M0, M1, du):
    """Retourne les deux points de controle - Le point de controle est pris sur la tangente à la courbe (à l'origine ou la fin) pour des abcisses qui suivent une progression arithmétique (1/3 de la longueur du segment)"""
    du = du/3
    C1x, C2x = du, 2*du
    C1y = V0*C1x+M0
    C2y = -V1*du+M1
    return (C1x, C1y-M0), (C2x, C2y-M0)

  def _get_linear_coef(self, x1, y1, x2, y2):
    """Retourne les coefficients de la droite y = ax+b"""
    #if x1 == x2:
    a = (y2-y1)/(x2-x1)
    b = y1-a*x1
    if a == 0.:
      return (a, b), None
    r = -b/a
    if r > x1 and r < x2:
      # valeur nulle dans l'intervalle
      return (a, b), r
    return (a, b), None


  def _get_parabolic_coef(self, x1, y1, x2, y2, x3, y3):
    """Retourne les 3 paramètres a, b c de la parabole ou de la droite (si points alignés) passant par les trois points donnés"""
    h31 = (y3-y1)/(x3-x1)
    h21 = (y2-y1)/(x2-x1)
    if abs(h31 - h21) < 1e-5:
      #Points alignés, retourne b, c (droite)
      b = (y3-y1)/(x3-x1)
      c = y1-b*x1
      if y1 == y3:
        r = x1
      else:
        r = -c/b
      if r > x1 and r < x3:
        return (0., b, c), r
      return (0., b, c), None

    a = (h31-h21)/(x3-x2) # y = ax2+bx+c
    b = h21 - a*(x2+x1)
    c = y1 - a*x1*x1 - b*x1
    delta = b**2-4*a*c
    if delta < 0:
      return  (a, b, c), None
# que se passe t il si deux racines dans l'intervale x1, x3? XXX
    r1 = (-b+delta**0.5)/2/a
    if r1 > x1 and r1 < x3:
      return  (a, b, c), r1
    r1 = (-b-delta**0.5)/2/a
    if r1 > x1 and r1 < x3:
      return  (a, b, c), r1
    return  (a, b, c), None

# -----------------------------------------------------------
#          Classe pour les nouvelles études
# -----------------------------------------------------------

class EmptyRdm(R_Structure):
  """Classe Rdm pour une nouvelle étude"""

  class_counter = 0

  def __init__(self, xml, name=None):
    #print("init EmptyRdm")
    self.struct = StructureDrawing(xml)
    self.status = self.struct.status
    self.UP = classPrefs.UserPrefs()
    #super(EmptyRdm, self).__init__(struct)
    EmptyRdm.class_counter += 1
    self.conv = self.GetConv()
    self.Cases = self.GetCasCharge()
    self.CombiCoef = self.GetCombi()
    self.n_cases = len(self.Cases)
    self.n_chars = self.n_cases + len(self.CombiCoef)
    self.XMLNodes = self.struct.XMLNodes
    #if self.status == 0:
    #  return
    xmlnode = list(self.struct.XMLNodes["char"].iter('case'))

    KS = EmptyKStructure(self.struct)
    self.Chars = {}
    for cas in self.Cases:
      Char = CasCharge(cas, xmlnode, self.struct)
      Char.KS = KS
      self.Chars[cas] = Char
    self.bar_values = {}




    self.errors = [("Etude non enregistrée", 0)]
    if name is None:
      self.SetStructName()
    else:
      self.name = name

#  def GetCasCharge(self):
#    return [Const.DEFAULT_CASE]

  def GetG(self, UP=None):
    """Retourne une valeur par défaut de g (9,81)"""
    if UP is None:
      UP = self.UP
    g = UP.get_default_g()
    return g

  def GetConv(self, UP=None):
    """Retourne la convention de signe par défaut"""
    if UP is None:
      UP = self.UP
    conv = UP.get_default_conv()
    return conv

  def GetUnits(self, UP=None):
    """Retourne les unités par défaut"""
    if UP is None:
      UP = self.UP
    try:
      unit_conv = UP.get_default_units()
      if unit_conv == {}:
        raise ValueError
    except (AttributeError, ValueError):
      return Const.default_unit()
    return unit_conv

  def GetStructName(self):
    """Retourne le nom de l'étude"""
    return self.name

  def GetStructPath(self):
    """Retourne le chemin de l'étude"""
    return None

  def SetStructName(self):
    """Définit le nom de l'étude"""
    self.name = "Nouvelle étude %d" % EmptyRdm.class_counter


# -----------------------------------------------------------
#          Classe pour les charges roulantes
# -----------------------------------------------------------


class Moving_Structure(R_Structure):
  """Résolution de la structure pour les charges roulantes"""

  def __init__(self, struct, forces):
    """Classe pour le calcul des lignes d'influence
    Conservation des déplacements imposés"""
    self.struct = struct
    self.conv = self.GetConv()
    self.bar_values = {}
    self.get_abscisses()
    self.struct.l_max = self.get_l_max()
    self.Char = MovingCasCharge(struct, forces)

  def get_l_max(self):
    """Retourne la longueur totale de la poutre droite"""
    barres = self.struct.Barres # pas forcément toutes les barres
    lengths = self.struct.Lengths
    l = 0
    for b in barres:
      l += lengths[b]
    return l
    absc = list(self.struct.positions.keys())
    absc.sort()
    last = absc[-1]
    barre = self.struct.positions[last]
    return last + self.struct.Lengths[barre]

  def get_abscisses(self):
    """Calcule les abscisses cumulées des points des barres"""
    barres = self.struct.Barres # pas forcément toutes les barres
    positions = {}
    for barre in barres:
      N0 = barres[barre][0]
      x = self.struct.Nodes[N0][0]
      positions[x] = barre
    self.struct.positions = positions

  def get_moving_data(self, N, status):
    #status = 5
    Char = self.Char
    struct = self.struct
    l_max = struct.l_max
    barres = struct.Barres # provisoire
    # initialisation env_sup
    env_inf = {}
    env_sup = {}
    m_pas = {}
    m_inter = {}
    for b in barres:
      env_sup[b] = {}
      env_inf[b] = {}
      k = max(1, int(N*struct.Lengths[b]/l_max))
      m_inter[b] = k
      m_pas[b] = struct.Lengths[b]/k
    x = 0
    for b in barres:
      #print("\tbarre=", b)
      n = max(1, int(N*struct.Lengths[b]/l_max))
      #print("n=", n)
      pas = struct.Lengths[b]/n
      u = 0
      for i in range(0, n):
        x += pas
        u += pas
        self.Char.ini(x)
        MatChar = self.Char.GetMatChar()
        self.Char.Solve(struct, Char.KS.InvMatK, MatChar)
        for barre in barres:
          pos = 0
          for j in range(0, m_inter[barre]+1):
            if status == 5 and barre == b and u == pos:
              val1 = self.GetValue(barre, pos*(1+1e-8), self.Char, status)[1]
              try:
                pos_env_sup = env_sup[barre][pos]
                pos_env_inf = env_inf[barre][pos]
                if val1 > pos_env_sup:
                  env_sup[barre][pos] = val1
                elif val1 < pos_env_inf:
                  env_inf[barre][pos] = val1
              except KeyError:
                env_sup[barre][pos] = val1
                env_inf[barre][pos] = val1

            val = self.GetValue(barre, pos, self.Char, status)[1]
        #    print("\t\tpos=", pos, u)
            
            try:
              pos_env_sup = env_sup[barre][pos]
              pos_env_inf = env_inf[barre][pos]
              if val > pos_env_sup:
                env_sup[barre][pos] = val
              elif val < pos_env_inf:
                env_inf[barre][pos] = val
            except KeyError:
              env_sup[barre][pos] = val
              env_inf[barre][pos] = val
            pos += m_pas[barre]
    maxi = -1e10 # provisoire
    mini = 1e10 # provisoire
    for b in env_sup:
      for u in env_sup[b]:
        val = env_sup[b][u]
        if val > maxi:
          maxi = val
        val = env_inf[b][u]
        if val < mini:
          mini = val

    return mini, maxi, env_inf, env_sup


# -----------------------------------------------------------
#          Classe pour les lignes d'influence
# -----------------------------------------------------------

# TODO il faudrait récrire dans cette classe toutes les méthodes gourmandes 
# pour que le calcul des lignes d'influence soit plus rapide (FNod, Resuij, ...)

class Influ_Structure(R_Structure):
  """Résolution de la structure pour les lignes d'influence"""

  def __init__(self, struct):
    """Classe pour le calcul des lignes d'influence
    Conservation des déplacements imposés"""
    self.struct = struct
    self.conv = self.GetConv()
    self.Char = InfluCasCharge(struct)
    self.bar_values = {}
    
  def ValueLigneInf(self, barre_char, x_char, elem_resu, x_resu, status):
    """Retourne la valeur de la ligne d'influence pour l'élément, au point x_resu
    le chargement unitaire étant défini par ailleurs"""
    #print("ValueLigneInf", x_char, elem_resu, barre_char)
    # x_resu: point de calcul sur elem_resu en %
    struct = self.struct
    Char = self.Char
    Char.ini(barre_char, x_char)
    InvMatK = Char.KS.InvMatK
    if InvMatK.size == 0:
      Char._DdlEmpty()
    else:
      matChar = Char.GetMatChar()
      resu = numpy.dot(InvMatK, matChar)
      resu = resu.transpose()[0]
      Char.GetDDLValues(resu)
    Char._GetEndBarSol()
    Char._GetRotationIso()
    # XXX déplacer rotation iso"
    charBarre = {}
    if elem_resu in Char.charBarFp:
      charBarre = Char.charBarFp[elem_resu]
    if status == 1:
      x_resu = x_resu*struct.Lengths[elem_resu]
      return self.TranchantPoint(Char, elem_resu, x_resu, {}, charBarre, {}, self.conv) 
    elif status == 2:
      x_resu = x_resu*struct.Lengths[elem_resu]
      return self.MomentPoint(Char, elem_resu, x_resu, {}, charBarre, {}, self.conv) 
    elif status == 3:
      x_resu = x_resu*struct.Lengths[elem_resu]
      return self.FlechePoint(Char, elem_resu, x_resu)[1]
    elif status == 4:
      Char.GetReac()
      return Char.Reactions[elem_resu]["Fy"]


# mettre de l'ordre dans les critères
  def InfluBarre(self, barre, elem, u, status, is_coef=False):
    """Retourne une liste de valeurs pour le tracé du moment fléchissant
    sur une barre.
    -> Un tuple contenant un seul point pour chaque segment de droite ou discontinuité ((u, soll), )
    -> Un tuple de valeurs contenant les points de controles pour le tracé de la Bézier ((endX, endY), (C1x, C1y), (C2x, C2y), (a, b, c))
    a, b, c, d polynome coefs"""
    l = self.struct.Lengths[barre]
    positions = [1.]
    if barre == elem and not u == 0.:
      positions.insert(0, u)
    li, li2 = [], []
    values = {}
    epsi = 1e-10

    # start point
    xprec = 0.
    yprec = self.ValueLigneInf(barre, xprec, elem, u, status)
    if not yprec == 0.:
      values[0.] = {0: yprec}
    pt0 = (xprec, yprec)
    if not is_coef:
      li.append((pt0, ))
    dyprec = self.ValueLigneInf(barre, xprec+epsi, elem, u, status)
    dyprec = (dyprec-yprec) / epsi / l
    alpha = positions[0]
    x = alpha*l

# ValueLigneInf donne la valeur à droite
    y = self.ValueLigneInf(barre, alpha-1e-12, elem, u, status)
    dy = self.ValueLigneInf(barre, alpha-epsi-1e-12, elem, u, status)
    dy = (y-dy) / epsi / l
    dx = x-xprec
    # C1 C2 dans le repère relatif à yprec
    C1, C2 = self._get_control_points2(dyprec, dy, yprec, y, dx)
    end_pt = (dx, y-yprec)
    
    a, b, c, d = self._GetCubicCoefs(yprec, C1[1]+yprec, C2[1]+yprec, y, xprec, dx)
    if a == 0. and b == 0.:
      if is_coef:
        li2.append((x, (c, d)))
      else:
        li.append((end_pt, (xprec, x)))
    else:
      if is_coef:
        li2.append((x, (a, b, c, d)))
      else:
        li.append((end_pt, C1, C2, (a, b, c, d)))
      resu = self.get_cubic_max(a, b, c, d, xprec, x)
      if not resu is None:
        xm, val = resu
        values[xm/l] = {0: val}
    if not abs(y) < 1e-10:
      values[alpha] = {0: y}

    xprec = x
    yprec = y
    if len(positions) == 2:
      y = self.ValueLigneInf(barre, alpha, elem, u, status)
      if not abs(y-yprec) < epsi:
        discont = (0., -1.)
        li.append((discont, ))
        values.setdefault(alpha, {})[1] = y
      dy = self.ValueLigneInf(barre, alpha+epsi, elem, u, status)
      dy = (dy-y) / epsi / l
      yprec = y
      dyprec = dy
      alpha = positions[1] # 1.
      x = l
      y = self.ValueLigneInf(barre, alpha, elem, u, status)
      dy = self.ValueLigneInf(barre, alpha-epsi, elem, u, status)
      dy = (y-dy) / epsi / l
      dx = x-xprec
      C1, C2 = self._get_control_points2(dyprec, dy, yprec, y, dx)
      a, b, c, d = self._GetCubicCoefs(yprec, C1[1]+yprec, C2[1]+yprec, y, xprec, dx)
      end_pt = (dx, y-yprec)
      if a == 0. and b == 0.:
        if is_coef:
          li2.append((x, (c, d)))
        else:
          li.append((end_pt, (xprec, x)))
      else:
        if is_coef:
          li2.append((x, (a, b, c, d)))
        else:
          li.append((end_pt, C1, C2, (a, b, c, d)))
        resu = self.get_cubic_max(a, b, c, d, xprec, x)
        if not resu is None:
          xm, val = resu
          values[xm/l] = {0: val}
      if not abs(y) < 1e-10:
        values.setdefault(alpha, {})[0] = y
    #print("barre=", barre, values)
    self.bar_values[barre] = self._GetSortedVal(values)
    #self.bar_values[barre] = values
    if is_coef:
      return li2
    return li

  def _GetCubicCoefs(self, yA, yB, yC, yD, x0, l):
    """Retourne les coefficients a, b, c, d de y=ax3+bx2+cx+d à partir des points de controle"""
    #print("_GetCubicCoefs",  yA, yB, yC, yD, x0, l)
    # test cas points alignés
    a1 = yB-yA
    a2 = yD-yC
    if a1 == 0 and abs(a2-a1) < 1e-12:
      return 0., 0., a1, yA
    elif abs((a2-a1)/a1) < 1e-4:
      return 0., 0., a1, yA
    a = (-yA+3*yB-3*yC+yD) / l**3
    b = (3*yA-6*yB+3*yC) / l**2
    c = (-3*yA+3*yB) / l
    d = yA
    if not x0 == 0.:
      b, c, d = b-3*a*x0, c+3*a*x0**2-2*b*x0, d-a*x0**3+b*x0**2-c*x0
    return a, b, c, d



class InfluCasCharge(CasCharge):

  def __init__(self, struct):
    self.struct = struct
    self.charBarQu = {}
    self.charBarFp = {}
    self.charBarTherm = {}
    self.charBarTri = {}
    self.charNode = {}

  def ini(self, barre_char, x_char):
    """Initialise le chargement pour la ligne d'influence"""
    self.charBarFp = {}
    self.charBarFp[barre_char] = {x_char: [0., -1., 0.]}
    self.NodeDeps = {}
    self.KS = KStructure(self.struct) # calcul sans affaissement d'appui

class MovingCasCharge(CasCharge):

  def __init__(self, struct, forces):
    # forces = [(F0, x0=0), (F1, x1), ...]
    self.struct = struct
    self.forces = forces
    self.charBarQu = {}
    self.charBarFp = {}
    self.charBarTherm = {}
    self.charBarTri = {}
    self.charNode = {}


  def ini(self, x0):
    """Initialise un chargement pour la charge roulante"""
    def locate(x, absc, positions, l_max):
      """Retourne la barre et la position d'une force donnée par x compté depuis l'origine des barres"""
      if x > l_max:
        return None
      prec = absc[0]
      for pos in absc[1:]:
        if x <= pos:
          break
        prec = pos
      b0 = positions[prec]
      pos = x-prec
      return pos, b0

    #self.x0 = x0
    struct = self.struct
    absc = list(struct.positions.keys())
    absc.sort()
    self.charBarFp = {}
    u = x0
    for tu in self.forces:
      f, dx = tu
      u += dx
      resu = locate(u, absc, struct.positions, struct.l_max)
      if not resu is None:
       x, barre = resu
       if not barre in self.charBarFp:
         self.charBarFp[barre] = {}
       l = struct.Lengths[barre]
       self.charBarFp[barre][x/l] = [0., -f, 0.]





