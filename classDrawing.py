#!/usr/bin/env python
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

from gi.repository import Gtk, Gdk, GObject, Pango, GdkPixbuf
import math  
import sys
import os
import copy
#import classEditor
import classRdm
import function
import Const
import classPrefs
import classDialog
import cairo
#from time import sleep
import xml.etree.ElementTree as ET

#import time



class MyEntry(Gtk.Entry):
  """Entry à taille modifiable"""

  def __init__(self):
    GObject.GObject.__init__(self)
    self.connect("draw", self.draw_event)

  def draw_event(self, widget, event):
    text = self.get_text()
    n_chars = len(text)
    self.set_width_chars(n_chars)

# functions

def draw_square(cr, x, y, fill=True):
    """Dessine un carré jaune à fond blanc, x et y en pixels (device)"""
    #print("_draw_square")
    cr.save()
    # antialiasing utile si les coordonnées ne sont pas des entiers
    cr.set_antialias(cairo.ANTIALIAS_NONE)
    size = 4
    cr.rectangle(x-size, y-size, 2*size, 2*size)
    cr.fill()
    cr.stroke()
    size = 3
    if not fill:
      cr.restore()
      return
    cr.set_source_rgb(1, 1, 1)
    cr.rectangle(x-size, y-size, 2*size, 2*size)
    cr.fill()
    cr.stroke()
    cr.restore()


def draw_single_soll_text(cr, x, y, text, angle=0, font_size=1, bold=False):
    """Ecrit une valeur caractéristique sur un diagramme de sollicitation
    pt est donné en coordonnées device
    pos : 0 : angle supérieur gauche
    """
    cr.save()
    cr.set_font_size(Const.FONT_SIZE*font_size)
    #  cr.select_font_face(Const.FONT,
    #            cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
    #cr.arc(x, y, 3, 0, 6.29)
    #cr.fill()
    #cr.stroke()
    cr.move_to(x, y)
    cr.rotate(angle)
    cr.rel_move_to( - width / 2 - x_bearing, - height / 2 - y_bearing)
    cr.show_text(text)
    cr.restore()

def get_influ_conv(status, unit_conv):
  """Retourne le facteur de conversion pour les lignes d'influences"""
  if status == 2:
    return unit_conv['F']*unit_conv['L']
  elif status == 3:
    return unit_conv['L']
  return unit_conv['F']

class Singleton(object):
  def __new__(cls, *args, **kwargs):
    if '_inst' not in vars(cls):
      cls._inst = object.__new__(cls, *args, **kwargs)
    return cls._inst

class InfluParams(object):

  #class_counter = 0

  def __init__(self, id):
    self.id = id
    #self.id = InfluParams.class_counter
    #InfluParams.class_counter += 1

  def add(self, args): # mettre un dictionnaire
    for nom, val in args.items():
      setattr(self, nom, val)

class FGColor(Singleton):
  """Classe pour la gestion des couleurs"""

  def __init__(self):
    self._configure_colors()

  def _configure_colors(self):
    """Définit les couleurs du drawing_area
    Les couleurs sont placées dans la propriété diColor"""
    # pixmap colors
    #colormap = Gdk.colormap_get_system() 
    #color = colormap.alloc_color("white", writeable=False, best_match=True)
    #self._white = color
    # cairo colors
    self._colors = {'red': (1, 0, 0),
		'blue': (0, 0, 1),
		'grey': (0.4, 0.4, 0.4),
		'white': (1, 1, 1),
		'orange': (0.8, 0.8, 0.2),
		'black': (0, 0, 0),
		'green': (0, 1, 0)}

  def get_nth_color(self, i):
    """Retourne la couleur de rang i"""
    colors = list(self._colors.keys())
    colors.remove('white')
    n = len(colors)
    return colors[i % n]

  def set_nth_color(self, cr, i): # inutilisée
    """Retourne la couleur de rang i"""
    colors = list(self._colors.keys())
    n = len(colors)
    color = self._colors[colors[i % n]]
    cr.set_source_rgb(color[0], color[1], color[2])

  def set_color_by_name(self, cr, color, alpha=1.):
    try:
      color = self._colors[color]
    except KeyError:
      print("FGColor color name error")
      return
    cr.set_source_rgba(color[0], color[1], color[2], alpha)

  def get_white_color(self,):
    #return Gdk.Color(0.5, 0.5, 1)
    parse, color = Gdk.Color.parse('white')
    return color

  def get_random_color(self):
    pass


class Value(object):
  """Classes de base pour les légendes des courbes"""

  def __init__(self, disc=0, auto=True):
    self.disc = disc
    self.auto = auto # valeur automatique ou user

  def get_position(self):
    """Retourne la position de la légende"""
    return self.x, self.y

  def get_is_selected(self, x_event, y_event, m):
    x, y = self.x, self.y
    if x_event < x-m or x_event > x + m:
      return False
    if y_event < y-m or y_event > y + m:
      return False
    return True



class ReacValue(Value):
  """Classes pour les légendes des réactions d'appuis"""

  def __init__(self, u, name, tu):
    text, x, y, a, disc = tu
    Value.__init__(self)
    self.text = text # utile?
    self.u = u # 0, 1, 2
    self.name = name
    self.x = x
    self.y = y
    self.a = a

  def get_reac_text(self, rdm, unit_conv, unit_name, Char, drawing):
    """Met en évidence une réaction d'appui"""
    barre = self.name
    if drawing.parent is None:
      is_child = False
      texts = ['Fx', 'Fy', 'M']
    else:
      is_child = True
      texts = ['N', 'V', 'M']
    if is_child and drawing.N1[2] == barre:
      pos = 0
    else:
      pos = 1
    Char = rdm.GetCharByNumber(drawing.s_case)
    if self.u == 0:
      if is_child:
        val = Char.EndBarSol[drawing.s_bar][pos][0]
      else:
        val = Char.Reactions[barre]["Fx"] # barre est ici un noeud!!
    elif self.u == 1:
      if is_child:
        val = Char.EndBarSol[drawing.s_bar][pos][1]
      else:
        val = Char.Reactions[barre]["Fy"] # barre est ici un noeud!!
    else:
      if is_child:
        val = Char.EndBarSol[drawing.s_bar][pos][2]
      else:
        val = Char.Reactions[barre]["Mz"] # barre est ici un noeud!!
    val = val/unit_conv
    legend = '%s = %f %s' % (texts[self.u], val, unit_name)
    return legend


class BarreValue(Value):
  """Classes pour les légendes des courbes pour les barres simples"""

  def __init__(self, u, name, tu):
    values, x, y, a, disc, auto = tu
    Value.__init__(self, disc, auto)
    self.values = values
    assert len(values) == 2
    # u : longueur absolue
    self.u = float(u) # convertit type 'numpy.float64'
    self.name = name
    self.x = x
    self.y = y
    self.a = a

  def get_soll_text(self, rdm, unit_conv, unit_name):
    """Met en évidence une légende"""
    u, barre = self.u, self.name
    l = rdm.struct.Lengths[barre]
    if u == 0 or u == l:
      is_node = True
      if u == 0:
        node = rdm.struct.Barres[barre][0]
      else:
        node = rdm.struct.Barres[barre][1]
    else:
      is_node = False
    if is_node:
      legend = "sur %s: %s" % (barre, node)
    else:
      u = function.PrintValue(u, unit_conv, True)
      legend = "sur %s: %s %s" % (barre, u, unit_name)
    return legend



class CurveValue(Value):
  """Classes pour les légendes des courbes pour un arc"""

  def __init__(self, u, name, tu):
    values, x, y, a, disc, auto = tu
    Value.__init__(self, disc, auto)
    self.values = values
    assert len(values) == 2
    self.u = float(u) # longueur absolu par rapport origine arc
    self.name = name
    self.x = x
    self.y = y
    self.a = a

  def get_soll_text(self, rdm, unit_conv, unit_name):
    """Met en évidence une légende"""
    struct = rdm.struct
    Lengths = struct.Lengths
    Arc = struct.Curves[self.name]
    ltot = Arc.get_size(Lengths)

    user_nodes = Arc.user_nodes
    N0, N1 = user_nodes[0].name, user_nodes[-1].name
    if self.u == 0:
      legend = "sur %s: %s" % (self.name, N0)
    elif self.u == ltot:
      legend = "sur %s: %s" % (self.name, N1)
    else:
      pos = function.PrintValue(self.u, unit_conv, True)
      legend = "Position sur %s: %s %s" % (self.name, pos, unit_name)
    return legend

class Node(object):
  """Classes contenant un noeud pour le mapping"""
  def __init__(self, name, coors):
    self.name = name
    self.coors = coors

class MInfo(object):

  class_counter = 0

  def __init__(self):
    self.id = MInfo.class_counter
    MInfo.class_counter += 1

class MText(MInfo):

  def __init__(self, box, text, id=None):
    self.visible = True
    self.box = box
    self.text = text
    if id is None:
      MInfo.__init__(self)
    else:
      self.id = id

class MScale(MInfo):

  def __init__(self, box, id=None):
    self.visible = True
    self.box = box
    if id is None:
      MInfo.__init__(self)
    else:
      self.id = id

class MSeries(MInfo): # les héritages pas utile en l'état

  def __init__(self, box, id=None):
    self.visible = True
    self.box = box
    if id is None:
      MInfo.__init__(self)
    else:
      self.id = id

class MParabola(object):
  """Classes contenant une parabole pour le mapping"""

# simplifier : ldefo, dx ...
  def __init__(self, name, coors):
    self.name = name
    self.coors = coors

  def get_is_selected(self, x_event, y_event, m):
    pt, coefs, geom, bezier = self.coors
    a, b = coefs[1:3]
    x, dx, x1, dx1, angle = geom
    l = x1+dx1
    x0, y0 = pt # origine de la barre
    x_e = (x_event-x0)*math.cos(angle)-(y_event-y0)*math.sin(angle)
    y_e = -(x_event-x0)*math.sin(angle)-(y_event-y0)*math.cos(angle) # inversion signe
    if x_e < x+dx or x_e > x+dx+l:
      return False
    y_chart = a*x_e**2+b*x_e
    if abs(y_chart-y_e) < m:
      return True
    return False

  def redraw(self, cr):
    """Redessine l'arc à partir des données du mapping"""
    x0, y0 = self.coors[0]
    cr.move_to(x0, y0)
    c1x, c1y, c2x, c2y, x1, y1 = self.coors[3]
    cr.rel_curve_to(c1x, c1y, c2x, c2y, x1, y1)
    cr.stroke()
    draw_square(cr, x0, y0)
    draw_square(cr, x0+x1, y0+y1)

class MArc(object):
  """Classes contenant un arc pour le mapping"""
  def __init__(self, name, coors):
    self.name = name
    self.coors = coors

  def get_is_selected(self, x, y, m):
    """Retourne False or True si l'arc est mappé"""
    xc, yc, r, teta1, teta2 = self.coors
    d = ((x-xc)**2 + (y-yc)**2)**0.5
    if abs(d-r) > m:
      return False
    if teta1 == teta2:
      if abs(d-r) < m:
        return True
    a = function.get_vector_angle((xc, -yc), (x, -y))
    if teta1 <= 0 and teta2 > 0:
      if a > teta2 or a < teta2:
        return True
    else:
      if teta2 < a and a < teta1:
        return True
    return False

  def redraw(self, cr):
    """Redessine l'arc à partir des données du mapping"""
    xc, yc, r, teta1, teta2 = self.coors
    if teta1 == teta2:
      cr.arc(xc, yc, r, 0, 6.29)
    else:
      cr.arc(xc, yc, r, -teta1, -teta2)
    cr.stroke()
    draw_square(cr, xc, yc)

class MCurve(object):
  """Classe contenant un segment de courbe"""

  def __init__(self):
    pass

class MCurveDisc(object):
  """Discontinuité du tracé"""

  def __init__(self, x, y):
    self.x, self.y = x, y

  def get_is_selected(self, x_event, y_event, m):
    return False

  def redraw(self, cr):
    """Effectue un déplacement correspondant à la discontinuité"""
    cr.move_to(self.x, self.y)

class MCurveSeg(object):
  """Segment de droite du tracé"""

  def __init__(self, tu):
    self.pt0, self.pt1, pos = tu
    self.l = ((self.pt1[0]-self.pt0[0])**2+(self.pt1[1]-self.pt0[1])**2)**0.5
    self.u0, self.u1 = pos

  def get_is_selected(self, x_event, y_event, m):
    #print("get_is_selected",  x_event, y_event, m)
    pt0, pt1 = self.pt0, self.pt1
    x0, y0 = pt0
    x1, y1 = pt1
    if x1 < x0:
      x0, x1 = x1, x0
      y0, y1 = y1, y0
    dx, dy = x1-x0, y1-y0
    if x_event < x0-1 or x_event > x1+1:
      return False

    #if abs(dx) < 1: # courbe verticale
    #  if y0 < y1:
    #    if y_event > y0 and y_event < y1:
    #      self.is_selected = (x0, y_event, None)
    #      return True
    #  else:
    #    if y_event > y1 and y_event < y0:
    #      self.is_selected = (x0, y_event, None)
    #      return True
    #  return False
    if dx > abs(dy):
      y = dy * (x_event-x0) / dx + y0
      d = abs(y_event-y)
      if d < m:
        self.is_selected = (x_event, y, None)
        return True
    else:
      x = dx * (y_event-y0) / dy + x0
      d = abs(x_event-x)
      if d < m:
        self.is_selected = (x, y_event, None)
        return True
    return False



  def redraw(self, cr):
    x, y = self.pt1
    cr.line_to(x, y)

  def push_hover_value(self, cr, study, barre, drawing, n_case):
    x, y, u = self.is_selected # en px absolu, u = None
    u0, u1 = self.u0, self.u1
    x0, y0 = self.pt0 # origine de la barre
    dl = ((x-x0)**2+(y-y0)**2)**0.5
    u = u0 + dl/self.l*(self.u1-self.u0)
    if u > self.u1:
      u = self.u1
    if u < self.u0:
      u = self.u0
    self.is_selected = (x, y, u)
    angle = function.get_vector_angle(self.pt0, self.pt1)
    if drawing.status == 7:
      rdm = study.rdm
      unit_conv = rdm.struct.units
      Char = rdm.GetCharByNumber(n_case)
      val = rdm.GetValue(barre, u, Char, drawing.status)
      valx, valy = val
      text = function.PrintValue(valy, unit_conv['L'])
    elif drawing.status == 8:
      rdm = study.influ_rdm
      unit_conv = rdm.struct.units
      i_obj = drawing.influ_list[n_case]
      l = rdm.struct.Lengths[barre]
      val = rdm.ValueLigneInf(barre, u/l, i_obj.elem, i_obj.u, i_obj.status)
      influ_unit = get_influ_conv(i_obj.status, unit_conv)
      text = function.PrintValue(val, influ_unit)
      val = (0., val) # provisoire
    elif drawing.status == 6:
      rdm = study.rdm
      unit_conv = rdm.struct.units
      Char = rdm.GetCharByNumber(n_case)
      val = rdm.GetValue(barre, u, Char, drawing.status)
      valx, valy = val
      text = function.PrintValue(valy, unit_conv['F']*unit_conv['L'])
    else:
      rdm = study.rdm
      unit_conv = rdm.struct.units
      Char = rdm.GetCharByNumber(n_case)
      val = rdm.GetValue(barre, u, Char, drawing.status)
      valx, valy = val
      text = function.PrintValue(valy, unit_conv['F'])
    self.text = text
    cr.push_group()
    color = drawing._fg.get_nth_color(n_case)
    drawing._fg.set_color_by_name(cr, color)
    cr.save()
    cr.set_font_size(Const.FONT_SIZE)
    cr.move_to(x, y-10)
    cr.rotate(angle)
    cr.show_text("%s" % text)
    cr.restore()
    drawing._draw_legend_position(cr, rdm.struct, barre, u, val)
    drawing.p_window = cr.pop_group()

class MCurveArc(object):
  """segment de Bezier du tracé"""

  def __init__(self, elem):
    self.x0 = elem[0]
    self.y0 = elem[1]
    self.c0x = elem[2]
    self.c0y = elem[3]
    self.c1x = elem[4]
    self.c1y = elem[5]
    self.x1 = elem[6]
    self.y1 = elem[7]
    self.b0 = elem[8]
    self.b1 = elem[9]
    #print("init=", self.b0, self.b1)

# meme methode que pout les segments
  def get_is_selected(self, x_event, y_event, m):
    #pt0, pt1 = self.pt0, self.pt1
    x0, y0 = self.x0, self.y0
    x1, y1 = self.x1, self.y1
    if x1 < x0:
      x0, x1 = x1, x0
      y0, y1 = y1, y0
    dx, dy = x1-x0, y1-y0
    if x_event < x0 or x_event > x1:
      return False
    y = dy * (x_event-x0) / dx + y0
    d = abs(y_event-y)
    if d < m:
      l0 = (dx**2+dy**2)**0.5
      l = ((x_event-x0)**2+(y-y0)**2)**0.5
      pos = l/l0
      n = self.b1 - self.b0 + 1
      db = int(n*pos)
      b = self.b0 + db
      pos1 = pos*n-db # position sur la barre en relatif
      self.is_selected = (pos1, b, None) # pos1 : par rapport début barre, pos : début arc
      return True
    return False

  def push_hover_value(self, cr, study, arc, drawing, n_case):
    rdm = study.rdm
    struct = rdm.struct
    #unit_conv = rdm.struct.units
    Char = rdm.GetCharByNumber(n_case)
    status = drawing.status
    pos1, b, pos = self.is_selected
    node0 = struct.Barres[b][0]
    angle = struct.Angles[b]
    val, text = rdm.GetArcValue(Char, status, b, pos1)
    #print("val=", val)
    x0, y0 = struct.Nodes[node0]
    X0, Y0 = drawing.x0, drawing.y0
    struct_scale = drawing.struct_scale
    chart_scale = drawing.chart_scale
    l = struct.Lengths[b]
    cr.push_group()
    #print(cr.get_matrix())
    drawing._fg.set_color_by_name(cr, "red")
    cr.save()
    cr.translate(X0 + x0*struct_scale, Y0 - y0*struct_scale)
    cr.rotate(-angle)
    dv = -val[1]*chart_scale

    color = drawing._fg.get_nth_color(n_case)
    drawing._fg.set_color_by_name(cr, color)
    cr.set_font_size(Const.FONT_SIZE)
    cr.move_to(0, dv-10)
    cr.show_text("%s" % text)
    cr.restore()
    drawing._c_draw_legend_position(cr, struct, b, X0, Y0, x0, y0, l*pos1, val[0], val[1], False)
    drawing.p_window = cr.pop_group()

  def redraw(self, cr):
    x0, y0 = self.x0, self.y0
    x1, y1 = self.x1, self.y1
    c0x, c0y = self.c0x, self.c0y
    c1x, c1y = self.c1x, self.c1y
    cr.move_to(x0, y0)
    cr.curve_to(c0x, c0y, c1x, c1y, x1, y1)

class MCurveB(object):
  """segment de Bezier du tracé"""

  def __init__(self, elem):
    self.pt0, self.coefs, self.geom, self.bezier = elem

  def get_is_selected(self, x_event, y_event, m):
    u, dx, x1, dx1, angle = self.geom
    ldefo = x1+dx1
    x0, y0 = self.pt0 # origine de la barre en px
    x_e = (x_event-x0)*math.cos(angle)+(y_event-y0)*math.sin(angle)
    y_e = (x_event-x0)*math.sin(angle)-(y_event-y0)*math.cos(angle) # dans le rep de la barre en px
    if x_e < u+dx or x_e > u+dx+ldefo:
      return False
    y_chart = self.f(x_e-dx, self.coefs)
    if abs(y_chart-y_e) < m:
      x, y = function.Rotation(angle, x_e, y_chart)
      x, y = x+x0, y0-y # repère global en px
      self.is_selected = (x, y, x_e)
      return True
    return False

  def push_hover_value(self, cr, study, barre, drawing, n_case):
    x, y, u = self.is_selected # x, y position sur courbe en px, u position sur intervalle
    u0, du0, u1, du1, angle = self.geom
    #print("resu=", u0, du0, u1, du1, u)
    x0, y0 = self.pt0 # origine de la barre
    struct_scale = drawing.struct_scale
    if struct_scale == 0:
      return
    k = (u-u0-du0)/((u1+du1))
    u0 /= struct_scale
    u1 /= struct_scale
    pos = u0+k*u1
    self.is_selected = (x, y, pos)
    if drawing.status == 7:
      rdm = study.rdm
      unit_conv = rdm.struct.units
      Char = rdm.GetCharByNumber(n_case)
      val = rdm.GetValue(barre, pos, Char, drawing.status)
      valx, valy = val
      text = function.PrintValue(valy, unit_conv['L'])
    elif drawing.status == 8:
      rdm = study.influ_rdm
      unit_conv = rdm.struct.units
      i_obj = drawing.influ_list[n_case]
      l = rdm.struct.Lengths[barre]
      val = rdm.ValueLigneInf(barre, pos/l, i_obj.elem, i_obj.u, i_obj.status)
      influ_unit = get_influ_conv(i_obj.status, unit_conv)
      text = function.PrintValue(val, influ_unit)
      val = (0., val) # provisoire
    elif drawing.status == 6:
      rdm = study.rdm
      unit_conv = rdm.struct.units
      Char = rdm.GetCharByNumber(n_case)
      val = rdm.GetValue(barre, pos, Char, drawing.status)
      valx, valy = val
      text = function.PrintValue(valy, unit_conv['F']*unit_conv['L'])
    else:
      rdm = study.rdm
      unit_conv = rdm.struct.units
      Char = rdm.GetCharByNumber(n_case)
      val = rdm.GetValue(barre, pos, Char, drawing.status)
      valx, valy = val
      text = function.PrintValue(valy, unit_conv['F'])
    self.text = text
    cr.push_group()
    color = drawing._fg.get_nth_color(n_case)
    drawing._fg.set_color_by_name(cr, color)
    cr.save()
    cr.set_font_size(Const.FONT_SIZE)
    cr.move_to(x, y-10)
    cr.rotate(angle)
    cr.show_text("%s" % text)
    cr.restore()
    drawing._draw_legend_position(cr, rdm.struct, barre, pos, val)
    drawing.p_window = cr.pop_group()


  def f(self, x, coefs):
      """La fonction polynomiale"""
      rank = len(coefs)
      y = 0
      for c in coefs:
        y += c*x**(rank-1)
        rank -= 1
      return y

  def redraw(self, cr):
    c1x, c1y, c2x, c2y, x, y = self.bezier
    cr.curve_to(c1x, c1y, c2x, c2y, x, y)

class Barre(object):
  """Classes contenant une barre pour le mapping"""

  def __init__(self, name, coors):
    self.name = name
    x0, y0, x1, y1 = coors
    dx =  x1-x0
    dy =  y1-y0
    # 2 cas selon que la barre est plutot verticale ou horizontale
    if abs(dx) >= abs(dy):
      self.inv = False
      # le sens de parcourt est choisi pour que x augmente
      if dx >= 0:
        self.coors = (x0, y0, dx, dy)
      else:
        self.coors = (x1, y1, -dx, -dy)
    else:
      self.inv = True
      # le sens de parcourt est choisi pour que y augmente
      if dy >= 0:
        self.coors = (x0, y0, dx, dy)
      else:
        self.coors = (x1, y1, -dx, -dy)

  def get_is_selected(self, x, y, m):
    """Retourne False or True si la barre est mappée"""
    x0, y0, deltax, deltay = self.coors
    if not self.inv:
      if x < x0 or x > x0+deltax:
        return False
      if deltax == 0:
        y1 = y0
      else:
        y1 = deltay * (x-x0) / deltax + y0
      d = abs(y-y1)
      if d < m:
        return True
    else:
      if y < y0 or y > y0+deltay:
        return False
      if deltay == 0:
        x1 = x0
      else:
        x1 = deltax * (y-y0) / deltay + x0
      d = abs(x-x1)
      if d < m:
        return True
    return False


  def redraw(self, cr):
    """Redessine la barre à partir des données du mapping"""
    x0, y0, dx, dy = self.coors
    cr.move_to(x0, y0)
    cr.rel_line_to(dx, dy)
    cr.stroke()
    draw_square(cr, x0, y0)
    draw_square(cr, x0+dx, y0+dy)

class AreaMapping(object):
  """Classes contenant les opérations de mapping pour la sélection des objects dans le drawingarea"""

  def __init__(self):
    #print("init AreaMapping")
    self.curves = {}
    self.nodes = {}
    self.bars = {}
    self.box = {} # x, y -> coin Haut Gauche, w, h
    self.curve_values = {}
    self.infos = {}


# ajouter points
  def remove_map(self, drawing_id):
    """Supprime les données du diagramme drawing"""
    try:
      del(self.nodes[drawing_id])
    except KeyError:
      pass
    try:
      del(self.bars[drawing_id])
    except KeyError:
      pass
    try:
      del(self.infos[drawing_id])
    except KeyError:
      pass
    #print('remove self.bars',self.bars)

  def clear(self, drawing_id):
    """Efface certains éléments pour le mapping"""
    try:
      self.curves[drawing_id] = {}
      self.bars[drawing_id] = []
      self.curve_values[drawing_id] = {}
    except KeyError:
      pass


  def set_mapping_arc(self, cr, scale, name, arc, drawing_id, centers):
    """Crée le mapping pour un arc de cercle"""
    center, r, teta1, teta2 = arc.c, arc.r, arc.teta1, arc.teta2
    xc, yc = centers[center]
    yc = -yc
    x_d, y_d = cr.user_to_device(xc, yc)
    Arc = MArc(name, (x_d, y_d, r*scale, teta1, teta2))
    self.bars.setdefault(drawing_id, []).append(Arc)

  def set_mapping_para(self, cr, scale, name, para, drawing_id, node0, node1):
    """Crée le mapping pour une parabole"""
    x0, y0 = node0
    x1, y1 = node1
    C1x, C1y, C2x, C2y = para.bezier
    a, b = para.coefs
    a = a/scale
    l = para.l*scale
    C1x, C1y = cr.user_to_device(x0+C1x, -y0+C1y)
    C2x, C2y = cr.user_to_device(x0+C2x, -y0+C2y)
    x0, y0 = cr.user_to_device(x0, -y0)
    C1x, C1y = C1x-x0, C1y-y0
    C2x, C2y = C2x-x0, C2y-y0
    x1, y1 = cr.user_to_device(x1, -y1)
    #print(cr.device_to_user_distance(1, 1))

    bezier_pts = (C1x, C1y, C2x, C2y, x1-x0, y1-y0)
    Para = MParabola(name, ((x0, y0), (0., a, b, 0.), (0., 0., l, 0., para.a), bezier_pts))
# utilité de tous ces 0 ??
    self.bars.setdefault(drawing_id, []).append(Para)

  def set_mapping_bars(self, drawing_id, nodes, bars, box):
    """Crée le mapping pour une barre utilisateur"""
    di = {}
    for name, coors in nodes.items():
      di[name] = Node(name, coors)
    self.nodes[drawing_id] = di
    for name, coors in bars.items():
      bar = Barre(name, coors)
      self.bars.setdefault(drawing_id, []).append(bar)
    self.set_box(drawing_id, box)

  def set_curve_values(self, drawing, values, n_case, name='bar'):
    """Remplit un dictionnaire {drawing_id: {n_case: {(x, y): Obj}}} de d'instances de classes Value"""
    #print("set_curve_values", n_case, name, values)
    def get_object(name, u, barre, tu):
      if name == "arc":
        return CurveValue(u, barre, tu)
      elif name == "bar":
        return BarreValue(u, barre, tu)
      elif name == "reac":
        return ReacValue(u, barre, tu)
      return None

    drawing_id = drawing.id
    status = drawing.status
    x0, y0, w, h = self.box[drawing_id]
    user_values = drawing.user_values.get(status, {}).get(n_case, {})
    objs = []
    for barre in values:
      are_moved = user_values.get(barre, {})
      for u in values[barre]:
        is_moved = are_moved.get(u, {})
        data = values[barre][u]
        for li in data:
          text, x, y, a, pos = li[0:5]
          if is_moved:
            try:
              dx, dy, hide = is_moved[pos]
              if hide: continue
              li[1] -= dx
              li[2] -= dy
              x -= dx
              y -= dy
            except KeyError:
              pass
          Obj = get_object(name, u, barre, li)
          objs.append(Obj)
          wtext = len(text)*4 # demie largeur
          if x-wtext < x0:
            w += x0 - x+wtext
            x0 = x-wtext
          elif x+wtext > x0+w:
            w = x - x0+wtext
          if y < y0:
            h += y0 - y
            y0 = y-10
          elif y > y0+h:
            h = y - y0 + 32
    self.curve_values.setdefault(drawing_id, {})
    self.curve_values[drawing_id].setdefault(n_case, []).extend(objs)
    self.extend_box(drawing_id, x0, y0)
    self.extend_box(drawing_id, x0+w, y0+h)


  def set_info(self, id, obj):
    """Stocke l'info"""
    #print("set_info", id)
    if not id in self.infos:
      self.infos[id] = {}
    self.infos[id][obj.id] = obj
    

  def set_moved_info(self, id, info_id, box):
    """Position de la boite du contour d'une info"""
    x, y, w, h = box
    self.infos[id][info_id].box = (int(x),  int(y), int(w), int(h)) # coin haut gauche, largeur, hauteur


  def set_box(self, id, box):
    """Position de la boite du contour d'un drawing"""
    x, y, w, h = box
    self.box[id] = (int(x), int(y), int(w), int(h)) # coin haut gauche, width, height

  def extend_box(self, id, x, y, Hm=0, Vm=0):
    """Modifie la taille de la boite pour tenir compte des légendes et autres"""
    x0, y0, w, h = self.box[id]
    x1, y1 = x0+w, y0+h
    change = False
    if x < x0:
      change = True
      x0 = x-Hm
    elif x > x1:
      x1 = x+Hm
      change = True
    if y < y0:
      y0 = y-Vm
      change = True
    elif y > y1:
      y1 = y+Vm
      change = True
      
    if change:
      self.box[id] = (int(x0), int(y0), int(x1-x0), int(y1-y0))

# si degré >= 4, on coupe le tronçon en deux et les coefs a, b, c, d sont stockés deux fois
  def set_curves(self, drawing_id, n_case, barre, points):
    """Contient les informations sur les courbes, redimensionne la boite du contour"""
    #print("set_curves", barre, points)
    if not drawing_id in self.curves:
      self.curves[drawing_id] = {}
    if not n_case in self.curves[drawing_id]:
      self.curves[drawing_id][n_case] = {}
    curves = self.curves[drawing_id][n_case][barre] = []
    x0, y0, w, h = self.box[drawing_id]
    x1, y1 = x0+w, y0+h
    for elem in points:
      if len(elem) == 1:
        x, y = elem[0]
        self.extend_box(drawing_id, x, y, 20, 20)
        curves.append(MCurveDisc(x, y))
      elif len(elem) == 3:
        x, y = elem[1]
        self.extend_box(drawing_id, x, y, 20, 20)
        curves.append(MCurveSeg(elem))
      elif len(elem) == 4:
        bezier = elem[3]
        Cx1, Cy1, Cx2, Cy2, endx, endy = bezier
        #self.extend_box(drawing_id, Cx1, Cy1)
        #self.extend_box(drawing_id, Cx2, Cy2)
# Faudrait caler les dim de la box à partir des valeurs de rdm.bar_values
# à paramétrer en attendant mieux
        self.extend_box(drawing_id, (Cx1+Cx2)/2, (Cy1+Cy2)/2)
        self.extend_box(drawing_id, endx, endy, 20, 20)
        curves.append(MCurveB(elem))
      else:
        print("debug in set_curves", len(elem), elem)

  def set_arc_curves(self, drawing_id, n_case, arc, points):
    """Crée le mapping pour les courbes des arcs"""
    #print("set_arc_curves", arc, points)
    if not drawing_id in self.curves:
      self.curves[drawing_id] = {}
    if not n_case in self.curves[drawing_id]:
      self.curves[drawing_id][n_case] = {}
    curves = self.curves[drawing_id][n_case][arc] = []
    for elem in points:
      for tu in elem:
        curves.append(MCurveArc(tu))
        self.extend_box(drawing_id, tu[6], tu[7])

  def select_curve_values(self, x, y, is_selected):
    """Retourne la légende sélectionnée"""
    if not is_selected:
      return False
    drawing = is_selected[1]
    n_drawing = drawing.id
    if not drawing.status in [3, 4, 5, 6, 7, 8]:
      return False
    try:
      curve_values = self.curve_values[n_drawing]
    except KeyError:
      return False
    delta = 10 # paramétrer
    for n_case, li in curve_values.items():
      for inst in li:
        if inst.get_is_selected(x, y, delta):
          return n_case, inst
    return False

  def get_is_in_drawing(self, x, y, n_drawing):
    """Retourne le numero d'un dessin si on est toujours au dessus d'un dessin
    Attention, les dimensions de box doivent être supérieures a la marge dans select_drawing"""
    x0, y0, w, h = self.box[n_drawing]
    if x < x0 or x > x0+w:
      return False
    if y < y0 or y > y0+h:
      return False
    return (n_drawing, )
    
# faut il pas mieux avoir des entiers pour les coordonnées
  def select_node(self, x, y, n_drawing):
    """Retourne le nom d'un noeud sur lequel on clique
    Doit être lancée avant select_barre"""
    delta = 10 # paramétrer
    nodes = self.nodes[n_drawing]
    for point in nodes.values():
      ptx, pty = point.coors
      if x < ptx-delta or x > ptx+delta:
        continue
      if y < pty-delta or y > pty+delta:
        continue
      return n_drawing, point
    return False

# on pourrait regrouper select_node et select_barre
  def select_barre(self, x, y, n_drawing, m=10):
    """Retourne le numéro du drawing et l'objet Barre au point de coordonnées x, y"""
    barres = self.bars[n_drawing]
    for barre in barres:
      if barre.get_is_selected(x, y, m):
        return n_drawing, barre


  def select_drawing(self, x, y, is_selected):
    """Retourne le numéro du drawing et l'objet Barre au point de coordonnées x, y"""
    if is_selected:
      return False
    m = 20
    bars = self.bars
    for n_drawing in bars:
      is_bar = self.select_barre(x, y, n_drawing, m)
      if is_bar:
        return n_drawing, None # ??? None

    # pas de résultats : on cherche les noeuds
    for n_drawing in bars:
      is_node = self.select_node(x, y, n_drawing)
      if is_node:
        return n_drawing, None
    return False


  def select_infos(self, x_event, y_event, drawings):
    """Retourne vrai ou faux si x_event, y_event correspondent à une info"""
    for drawing in drawings:
      if not drawing.id in self.infos:
        continue
      for id, obj in self.infos[drawing.id].items():
        x, y, w, h = obj.box
        if not obj.visible:
          continue
        if x_event < x or x_event > x+w:
          continue
        if y_event < y or y_event > y+h:
          continue
        return drawing.id, id
    return False

  def select_curve(self, x_event, y_event, is_selected):
    """Retourne un tuple (combinaison, barre) pour la courbe correspondant au point de coordonnées x_event, y_event - Retourne False si aucune courbe
    Les coordonnées sont des pixels"""

    if not is_selected:
      return False
    dmax = 6
    drawing = is_selected[1]
    if not drawing.status in [4, 5, 6, 7, 8]:
      return False
    n_drawing = drawing.id
    #print("select=", n_drawing, drawing.status)
    data = self.curves[n_drawing]
    # test ------------
    #if drawing.status == 8:
    #  assert len(data) == len(drawing.influ_list)
    #else:
    #  assert len(data) == len(drawing.s_cases)
    # fin test --------
    for n_case in data:
      barres = data[n_case]
      for barre in barres:
        curves = barres[barre]
        for obj in curves:
          if obj.get_is_selected(x_event, y_event, dmax):
            return n_case, barre, barres, obj
    return False



  def select_chart_influ(self, x_event, y_event):
    """Retourne un tuple (nom, barre) pour la courbe correspondant au point de coordonnées x_event, y_event - Retourne False si aucune courbe"""
    combis = self.curves.keys()
    for combi in combis:
      barres = list(self.curves[combi].keys())
      for barre in barres:
        points = self.curves[combi][barre]
        for li in points:
          for tu in li:
            if abs(x_event-tu[0]) > 3:
              continue
            if abs(y_event-tu[1]) > 3:
              continue
            return combi, barre
    return False


class Drawing(object):

  class_counter = 0

  def __init__(self, mapping, id_study):
    self.id = Drawing.class_counter
    Drawing.class_counter += 1
    self.id_study = id_study
    self.mapping = mapping
    self.user_values = {} # format : {status: {n_case: {barre:{u: {0: (dxG, dyG, hideG), 1: (dxD, dyD, hideD)]}}}}
    #self.s_cases = []
    self.s_values = []
    self.s_curve = None
    self.s_bar = None
    self._fg = FGColor()
    self.childs = {}
    self.scale_id = None
    self.series_id = None
    self.title_id = None
    self.influ_list = {} # renommer
    self.has_pattern = False
    self.chart_zoom = {}

  def set_status(self, status):
    self.status = status

# attention on teste seulement si la clé existe # defaut True
  def get_menu_options(self):
    """Retourne les options du menu contextuel"""
    options = {}
    options['Node'] = self.options.get('Node', False)
    options['Barre'] = self.options.get('Barre', False)
    options['Axis'] = self.options.get('Axis', False)
    options['Title'] = self.options.get('Title', True)
    options['Save'] = True
    options['Select'] = True
    if not self.status == 0:
      options['Sigma'] = True
      options['Add'] = True
    options['Case'] = True
    if self.status in [4, 5, 6, 7, 8]:
      options['Series'] = self.options.get('Series', False)
    if self.status == 8:
      options['InfluB'] = True
    return options



  def draw_tools(self, study, tab):
    """Dessine la barre d'outils du dessin"""
    layout = tab.layout
    Main = tab._main
    hbox = Gtk.HBox(False, 10)
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_PAGE_SETUP)
    b.set_tooltip_text("Modifier l'échelle")
    b.connect('clicked', tab.on_show_scale_box, self, "struct")
    hbox.pack_start(b, False, False, 0)
    dx = 70
    bdrawings = self.get_bar_drawings()
    if not bdrawings and len(study.rdm.struct.GetBars()) > 1:
      b = Gtk.Button()
      function.add_icon_to_button2(b, Gtk.STOCK_ZOOM_FIT)
      b.set_tooltip_text("Dessin des barres")
      b.connect('clicked', tab.add_bar_drawing, self, study)
      hbox.pack_start(b, False, False, 0)
      dx = 110
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_CLOSE)
    b.set_tooltip_text("Fermer")
    b.connect('clicked', Main.on_del_drawing, self)
    hbox.pack_start(b, False, False, 0)
    hbox.show_all()
    x, y, w, h = self.mapping.box[self.id]
    x = x + 25
    y = y + h - 28
    layout.put(hbox, int(x), int(y))
    return hbox

  def get_is_parent(self):
    """Retourne vrai si le dessin est une instance de BarreDrawing"""
    return True

  def get_is_bar_drawing(self):
    """Retourne vrai si le dessin est une instance de BarreDrawing"""
    return False

  def get_is_sigma_drawing(self):
    """Retourne vrai si le dessin est une instance de SigmaDrawing"""
    return False


  def get_drawing_type(self):
    """Retourne le type de classe du dessin"""
    if self.parent is None:
      return "parent"
    if self.get_is_char_drawing():
      return "char"
    if self.get_is_bar_drawing():
      return "bar"
    if self.get_is_sigma_drawing():
      return "sigma"
    print("debug in get_drawing_type")
    return None

  def get_is_char_drawing(self):
    """Retourne vrai si le dessin est une instance de CharDrawing"""
    return False

  def get_bar_drawings(self):
    """Retourne les identifiants des dessins de barres"""
    li = []
    for key in self.childs:
      d = self.childs[key]
      if d.get_is_bar_drawing():
        li.append(key)
    return li

  def get_char_drawing(self):
    """Retourne l'identifiant du dessin de chargement ou None"""
    for key in self.childs:
      d = self.childs[key]
      if d.get_is_char_drawing():
        return key
    return None


  def set_title_visibility(self, visibility):
    if self.title_id is None:
      return
    obj = self.mapping.infos[self.id][self.title_id]
    obj.visible = visibility

  def set_series_visibility(self, visibility):
    if self.series_id is None:
      return
    obj = self.mapping.infos[self.id][self.series_id]
    obj.visible = visibility


  def set_drawing_prefs(self, prefs, tab, study):
    """Initialise les préférences du dessin"""
    #print("set_drawing_prefs", prefs)
    self.parent = None
    self.options = {'Title': prefs['Title'], 'Barre': prefs['Barre'], 'Node': prefs['Node'], 'Axis': prefs['Axis'], 'Series': prefs['Series']}
    self.set_geometric_prefs(tab, study, prefs)

    if 'values' in prefs: # avant status
      val = prefs['values']
      try:
        di = eval(val)
        if self.test_user_values(di):
          self.user_values = di
      except: # tout type d'erreur ici
        print("Une erreur est survenue dans les préférences du fichier de données")
    if 'status' in prefs:
      val = prefs['status']
      val = val.split(',')
      self.status = int(val[0])
      del(val[0])
      if self.status in [2, 3]:
        try:
          self.s_case = int(val[0])
        except IndexError:
          pass
      elif self.status in [4, 5, 6, 7]:
        self.s_cases = [int(i) for i in val]
      elif self.status == 8:
        for i, elem in enumerate(val):
# purger values des valeurs inutiles qui passent d'une session à l'autre
          elem, u, status, id = elem.split(':') # protéger
          u, status, id = float(u), int(status), int(id)
          Obj = InfluParams(i)
          self.influ_list[Obj.id] = Obj
          Obj.add({"elem": elem, "u": u, "status": status})
          if Obj.id == id:
            continue
          if self.status in self.user_values:
            if id in self.user_values[self.status]:
              self.user_values[self.status][Obj.id] = self.user_values[self.status][id]
              del(self.user_values[self.status][id])
        try:
          self.s_influ = list(self.influ_list.keys())[0]
        except IndexError:
          pass
    else:
      self.set_status(1)
    self._add_info_prefs(prefs)
    if 's_influ_bars' in prefs:
      val = prefs['s_influ_bars']
      self.s_influ_bars = val

  def set_geometric_prefs(self, tab, study, prefs):
    """Attribut les préférences liées à la géométrie et position"""
    tag = True
    if 'x0' in prefs:
      self.x0 = prefs['x0']
    else:
      tag = False
    if 'y0' in prefs:
      self.y0 = prefs['y0']
    else:
      tag = False
    if 'struct_scale' in prefs:
      self.struct_scale = prefs['struct_scale']
    else:
      tag = False
    if tag:
      self.set_dim(study)
    else:
      self.set_all_sizes(tab, study)


  def set_dim(self, study):
    """Calcule la largeur et la hauteur"""
    struct = study.rdm.struct
    struct_w, struct_h = struct.width, struct.height
    self.width = struct_w*self.struct_scale
    self.height = struct_h*self.struct_scale

  def set_all_sizes(self, tab, study):
    """Calcule la taille, l'échelle et la position d'un dessin (structure seule)"""
    size = Const.DRAWING_SIZE
    struct = study.rdm.struct
    margin = Const.AREA_MARGIN
    layout = tab.layout
    #sw_w = int(sw.get_hadjustment().page_size) - 2*margin
    sw_w = int(layout.get_hadjustment().get_page_size()) - 2*margin
    sw_h = int(layout.get_vadjustment().get_page_size()) - 2*margin
    struct_w, struct_h = struct.width, struct.height
    scale = self._get_scale(struct_w, struct_h, sw_w, sw_h)
    if scale is None:
      self.width = size
      self.height = size
    else:
      self.width = scale*struct_w
      self.height = scale*struct_h
    id = study.id
    try:
      self.x0
    except AttributeError:
      self.x0, self.y0 = 100+id*20, 150+id*20
    self.struct_scale = scale

  def zoom_best(self, coef, struct):
    if self.struct_scale is None:
      return
    scale = coef*self.struct_scale
    self.set_zoom(scale)
    self.set_scale(struct)
    self.set_position()

  def set_zoom(self, zoom):
    """Modifie les attributs pour le zoom"""
    max1 = Const.DRAWING_SIZE_MAX
    if zoom == "+":
      coef = 1/0.9
    elif zoom == "-":
      coef = 0.9
    else:
      coef = zoom/self.struct_scale
    if coef > 1:
      w = self.width*coef
      h = self.height*coef
      if w > max1: # limitation
        h = h*max1/w
        w = max1
      if h > max1: # limitation
        w *= max1/h
        h = max1
      self.width = w
      self.height = h
    else:
      self.width = self.width*coef
      self.height = self.height*coef

  def set_position(self):
    """Place le dessin à sa position optimale"""
    m = Const.AREA_MARGIN_MIN
    dx = m - self.x0
    dy = self.height+m - self.y0
    self.x0 = m
    self.y0 = self.height + m

    # déplacement échelle, titre
    if self.id in self.mapping.infos:
      for elem in self.mapping.infos[self.id].values():
        x, y, w, h = elem.box
        x = max(x+dx, m)
        y = y+dy
        elem.box = (x, y, w, h)

  def set_scale(self, struct):
    """Ajuste l'échelle de la structure pour tenir dans la boîte"""
    #print("set_scale dans Drawing",  self.width, self.height)
    struct_w, struct_h = struct.width, struct.height
    self.struct_scale = self._get_scale(struct_w, struct_h, self.width, self.height)
    if self.struct_scale is None:
      return
    self.width = self.struct_scale*struct_w
    self.height = self.struct_scale*struct_h


  def _get_scale(self, struct_w, struct_h, w, h):
    """Retourne l'echelle pour le tracé de la structure"""
    #print("_get_scale", struct_w, struct_h, w, h)
    if struct_w == 0 and struct_h == 0:
      return None
    if w == -1:
      max_drawing = Const.DRAWING_SIZE
    else:
      max_drawing = max(w, h)
    max_struct = max(struct_w, struct_h)
    scale = max_drawing/max_struct
    #if scale > 1:
    #  scale = round(scale, 1)
    return scale


  def get_max_scale2(self, value, study):
    pass


  def get_max_scale(self, value, study):
    """Vérifie si la nouvelle échelle n'est pas trop grande"""
    scale = self.struct_scale
    struct = study.rdm.struct
    width, height = struct.width, struct.height
    struct_w, struct_h = scale*width, scale*height
    coef = value/scale
    max_size = max(struct_w, struct_h)*coef
    if max_size <= 1000:
      return True
    return False


  def update_s_data(self, rdm, barres):
    """Met à jour s_case, s_cases, s_bar, s_curve"""
    self.set_cases_ini(rdm)
    if not self.s_curve in self.s_cases:
      self.s_curve = None
    if not self.s_bar is None and not self.s_bar in barres:
      if len(barres) >= 1:
        self.s_bar = barres[0]
      self.s_bar = None

  def update_drawing_data(self, tag=False):
    """Met à jour la config du dessin par rapport à son parent"""
    pass

  def get_xml_prefs(self, parent):
    """Crée le noeud xml pour les préférences communes aux dessins pour la sauvegarde des préférences"""
    node = ET.SubElement(parent, "drawing")
    self.set_xml_prefs(node)
    return node

  def set_xml_prefs(self, node):
    """Crée les attribues pour les préférences communes aux dessins pour la sauvegarde des préférences"""
    #print("set_xml_prefs", self.id)
    node.set("x0", str(self.x0))
    node.set("y0", str(self.y0))
    node.set("scale", str(self.struct_scale))
    #node.set("w", str(self.width))
    #node.set("h", str(self.height))
    val = [str(self.status)]
    if self.status in [2, 3]:
      val.append(self.s_case)
      val = [str(i) for i in val]
    elif self.status in [4, 5, 6, 7]:
      val.extend(self.s_cases)
      val = [str(i) for i in val]
    elif self.status == 8:
      for obj in self.influ_list.values():
        string = [str(obj.elem), str(obj.u), str(obj.status), str(obj.id)]
        string = ":".join(string)
        val.append(string)
        
    val = ','.join(val)
    node.set("status", val)
    val = self.options['Barre'] and "true" or "false"
    node.set("bar_name", val)
    val = self.options['Node'] and "true" or "false"
    node.set("node_name", val)
    val = self.options['Axis'] and "true" or "false"
    node.set("axis", val)
    val = self.options['Title'] and "true" or "false"
    node.set("show_title", val)
    infos = self.mapping.infos[self.id]
    if not self.title_id is None:
      box = infos[self.title_id].box
      box = [str(i) for i in box]
      box.append(infos[self.title_id].text)
      val = ",".join(box)
      node.set("title", val)
    if not self.scale_id is None:
      box = infos[self.scale_id].box
      box = [str(i) for i in box]
      val = ",".join(box)
      node.set("scale_pos", val)
    if not self.series_id is None:
      box = infos[self.series_id].box
      box = [str(i) for i in box]
      val = self.options['Series'] and "true" or "false"
      box.insert(0, val)
      val = ",".join(box)
      node.set("series", val)
    user_values = self.user_values
    if user_values:
      val = repr(user_values)
      val = val.replace(' ', '')
      node.set("values", val)
    try:
      li = []
      for b in self.s_influ_bars:
        try:
          b + 1 # test b est un entier
          li.append("*%s" % b)
        except TypeError:
          li.append(b)
      val = ",".join(li)
      node.set("influ_bars", val)
    except AttributeError:
      pass


  def test_user_values(self, di):
    """Teste la syntaxe du dictionnaire des valeurs utilisateur"""
    for status in di:
      for case in di[status]:
        for name in di[status][case]:
          for u in di[status][case][name]:
            values = di[status][case][name][u]
            for key in values:
              if not key in [0, 1]:
                return False
              tu = values[key]
              if not isinstance(tu, tuple):
                return False
              if not len(tu) == 3:
                return False
              x, y, tag = tu
              try:
                x+y
              except ValueError:
                return False
              if not isinstance(tu[2], bool):
                return False
    return True
        

  def _add_info_prefs(self, prefs):
    """Ajoute les paramètres pour les pattern de type info"""
    if 'title' in prefs:
      try:
        x, y, w, h, text = prefs['title']
        x, y, w, h = float(x), float(y), float(w), float(h)
        obj = MText((x, y, w, h), text)
        self.mapping.set_info(self.id, obj)
        self.title_id = obj.id
      except ValueError:
        pass
    if 'scale_pos' in prefs:
      try:
        x, y, w, h = prefs['scale_pos']
        x, y, w, h = float(x), float(y), float(w), float(h)
        obj = MScale((x, y, w, h))
        self.mapping.set_info(self.id, obj)
        self.scale_id = obj.id
      except ValueError:
        pass
    if 'series_pos' in prefs:
      try:
        x, y, w, h = prefs['series_pos']
        x, y, w, h = float(x), float(y), float(w), float(h)
        obj = MSeries((x, y, w, h))
        self.series_id = obj.id
        self.mapping.set_info(self.id, obj)
      except ValueError:
        pass

  def delete_value(self, n, legend):
    """Efface une valeur ou la masque si valeur automatique"""
    u, barre, disc, auto = legend.u, legend.name, legend.disc, legend.auto
    if auto:
      try:
        value = self.user_values[self.status][n][barre][u]
        dx, dy, tag = value[disc]
        value[disc] = (dx, dy, True)
      except KeyError:
        self._set_user_values(n, barre, u, disc, hide=True)
    else:
      value = self.user_values[self.status][n][barre]
      del(value[u][disc])
      if len(value[u]) == 0:
        del(value[u])


  def set_hide_value(self, n, legend):
    """Ajoute un élément dans le dictionnaire des valeurs cachées"""
    u, barre, disc = legend.u, legend.name, legend.disc
    self._set_user_values(n, barre, u, disc, hide=True)

  def _set_user_values(self, n, barre, u, disc, x=None, y=None, hide=False):
    """place une valeur dans le dictionnaire des user_values"""
    #print(" _set_user_values", n, barre, u, disc, x, y)
    mv = self.user_values
    if not self.status in mv:
      mv[self.status] = {}
    if not n in mv[self.status]:
      mv[self.status][n] = {}
    di = mv[self.status][n]
    if not barre in di:
      di[barre] = {}
    if not u in di[barre]:
      di[barre][u] = {}
    di2 = di[barre][u]
    if not disc in di2:
      if x is None:
        di2[disc] = (0, 0, hide)
      else:
        di2[disc] = (x, y, hide)
    else:
      x0, y0 = di2[disc][0:2]
      if x is None:
        di2[disc] = (x0, y0, hide)
      else:
        di2[disc] = (x, y, hide) # tester et finir
    #print(self.user_values)

  def _get_user_value(self, n, barre, u, disc, hide):
    """Retourne un sous dictionnaire de user_values si la valeur de u (ou approchée) a été trouvée"""
    #print("_get_user_value", n, barre, u)
    u_v = self.user_values
    if not self.status in u_v:
      return False
    if not n in u_v[self.status]:
      return False
    di = u_v[self.status][n]
    if not barre in di:
      return False
    for pos in di[barre]:
      if pos == 0 and u == 0:
        break
      if abs(u-pos)/pos < 1e-8:
        break
      return False
    di2 = di[barre][pos]
    if not disc in di2:
      return False
    return di[barre], pos

  def restore_values(self, n):
    """Supprime dans le dictionnaire des valeurs cachées les élements pour la courbe n"""
    try:
      values = self.user_values[self.status]
    except KeyError:
      return
    try:
      bars_values = values[n]
    except KeyError:
      return
    for barre in bars_values:
      bar_values = bars_values[barre]
      for u in bar_values:
        for i, disc in enumerate(bar_values[u]):
          dx, dy , hide = bar_values[u][disc]
          if hide is True:
            bar_values[u][i] = (dx, dy, False)


  def get_is_parent(self):
    """Retourne True si le dessin est un dessin parent"""
    if self.parent is None:
      return True
    return False


  def expose_drawing(self, cr, study):
    """Lance le tracé du graphe en fonction de la valeur de status"""
    #print("expose_drawing", cr)
    rdm = study.rdm
    struct = rdm.struct
    status = self.status
    if status == 0:
      self.area_expose_realtime(study, cr)
    elif status == 1:
      self.area_expose_barre(study, cr)
    elif status == 2:
      self.area_expose_char(study, cr)
    elif status == 3:
      self.area_expose_reac(study, cr)
    elif status in [4, 5, 6]:
      self.area_expose_soll(study, cr)
    elif status == 7:
      self.area_expose_defo(study, cr)
    elif status == 8:
      self.area_expose_influ(study, cr)
    elif status == 9:
      self.area_expose_moving(study, cr)
    self.has_pattern = True



# tester s'il faut supprimer les patterns
# XXX ne pas supprimer tous les patterns en fonction du status? à voir
  def del_patterns(self):
    """Supprime tous les patterns du drawing"""
    #print("del_patterns")
    self.has_pattern = False
    return

# remettre ???
    if hasattr(self, 'p_struct'):
      del(self.p_struct)
    self.p_infos = {}
    if hasattr(self, 'p_bind'):
      del(self.p_bind)
    if hasattr(self, 'p_char'):
      del(self.p_char)
    if hasattr(self, 'p_reac'):
      del(self.p_reac)
    if hasattr(self, 'p_window'):
      del(self.p_window)
    if hasattr(self, 'p_barre'):
      del(self.p_barre)
    if hasattr(self, 'p_select'):
      del(self.p_select)

# inutile
  def _push_node_group(self, study, cr, struct_scale):
    self.p_infos = {}
    struct = study.rdm.struct
    cr.push_group()
    self._draw_bars(cr, struct, self.x0, self.y0, struct_scale, color='red', show_name=True, axis=True)
    self._draw_nodes(cr, struct, self.x0, self.y0, struct_scale, 
		symbol=1, color='blue')
    self.p_struct = cr.pop_group()
    self._push_title_group(study, cr)
    self._get_mapping_data(cr, struct, self.x0, self.y0, struct_scale)

  def _push_struct_group(self, study, cr, struct_scale):
    struct = study.rdm.struct
    self.p_infos = {}
    options = self.options
    name = options.get('Barre', False)
    axis = options.get('Axis', False)
    cr.push_group()
    self._draw_bars(cr, struct, self.x0, self.y0, struct_scale, color='grey', show_name=name, axis=axis, width=1)
    self._get_mapping_data(cr, struct, self.x0, self.y0, struct_scale)
    if options.get('Node') or self.status == 0:
      self._draw_nodes(cr, struct, self.x0, self.y0, struct_scale, color='blue')
    self._draw_relax(cr, self.x0, self.y0, struct, struct_scale)
    self.p_struct = cr.pop_group()
    li = self.get_bar_drawings()
# revoir si plusieurs dessin ici et ailleurs
    if li:
      barre = self.childs[li[0]].s_bar
      self._push_selected_barre(cr, struct, barre, 4)

    if self.status == 1:
      message = ("Nombre de barres : %d" % len(struct.GetBars()), 2)
      classDialog.Message().set_message(message)
    self._push_title_group(study, cr)


  def _push_selected_barre(self, cr, struct, barre, width=1, color=None):
    """Dessine une seule barre de la structure"""
    scale = self.struct_scale
    if scale is None:
      return
    if self.status == 0:
      return
    cr.push_group()
    cr.translate(self.x0, self.y0)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.scale(scale, scale)
    cr.set_line_width(width/scale)
    bars = struct.Barres
    nodes = struct.Nodes
    angle = -struct.Angles[barre]
    node1 = bars[barre][0]
    node2 = bars[barre][1]
    x1, y1 = nodes[node1]
    x2, y2 = nodes[node2]
    y1 = -y1
    y2 = -y2
    cr.move_to(x1, y1)
    cr.line_to(x2, y2)
    cr.stroke()
    #cr.restore()
    self.p_barre = cr.pop_group()


  def _push_char_group(self, study, cr):
    """Crée le pattern des chargements"""
    rdm = study.rdm
    struct = rdm.struct
    Nodes = struct.Nodes
    Curves = struct.Curves
    UserNodes = struct.UserNodes
    UserBars = struct.UserBars
    cr.push_group()
    n = self.s_case
    if n is None:
      n = self.s_case = 0

    scale = self.struct_scale
    if scale is None: # pour mode "edition"
      self.p_char = cr.pop_group()
      return
    x0, y0 = self.x0, self.y0
    Char = rdm.GetCharByNumber(n)
    barres = struct.GetBars()
    resu = function.GetCumulChar(barres, Char)
    di = resu[0]
    # attention, qmax obtenu à partir des composantes et pas de la norme contrairement aux autres chargements
    qmax = resu[1]
    for barre, chars in di.items():
      self._draw_char_bar_q(cr, x0, y0, barre, scale, chars,
			qmax, study, color='blue')
    chars = Char.charBarFp
    for barre in chars:
      self._draw_char_bar_fp(cr, x0, y0, barre, study, chars[barre], scale, color="green")
    chars = Char.UserNodesChar
    for noeud in chars:
      if len(Nodes[noeud]) == 0:
        continue
      x, y = Nodes[noeud]
      x, y= x*scale+x0, -y*scale+y0
      self._draw_char_node(cr, x, y, study, chars[noeud], color='red')
    chars = Char.charBarTherm
    for barre in UserBars:
      if not barre in chars:
        continue
      self._draw_char_therm(cr, x0, y0, barre, rdm, scale)
    sbs = struct.SuperBars
    for barre in sbs:
      sb = sbs[barre]
      b0, b1 = sb.b0, sb.b1
      for b in range(b0, b1+1):
        if not b in chars:
          continue
        self._draw_char_therm(cr, x0, y0, b, rdm, scale)

    for name in Curves:
      if not name in Char.ArcChars:
        continue
      arc_chars = Char.ArcChars[name]
      if "pp" in arc_chars:
        arc_char = arc_chars["pp"]
        self._draw_arc_char0(cr, x0, y0, scale, rdm, name, arc_char, color='red')
      if "qu0" in arc_chars:
        arc_char = arc_chars["qu0"]
        self._draw_arc_char0(cr, x0, y0, scale, rdm, name, arc_char, color='blue')
      if "qu1" in arc_chars:
        arc_char = arc_chars["qu1"]
        self._draw_arc_char1(cr, x0, y0, scale, rdm, name, arc_char, color='blue')
      if "qu2" in arc_chars:
        arc_char = arc_chars["qu2"]
        self._draw_arc_char2(cr, x0, y0, scale, rdm, name, arc_char, color='blue')
      if "th" in arc_chars:
        #arc_char = arc_chars["th"]
        self._draw_arc_char_therm(cr, x0, y0, scale, rdm, name)
      if "fp" in arc_chars:
        arc_char = arc_chars["fp"]
        self._draw_arc_char_fp(cr, x0, y0, scale, rdm, name, arc_char)

    self.p_char = cr.pop_group()

  def _push_reac_group(self, study, cr, color="grey"):
    """Dessine tous les chargements d'une combi ou cas spécifié par n"""
    #print(cr.get_matrix())
    rdm = study.rdm
    n = self.s_case
    if n is None:
      #print("debug::_push_char_group")
      n = self.get_first_case(rdm)
    Char = rdm.GetCharByNumber(n)
    maxi = Char.SearchReacMax()[0]
    if maxi is None or maxi == 0.:
      cr.push_group()
      self.p_reac = cr.pop_group()
      self.mapping.set_curve_values(self, {}, self.s_case, "reac")
      message = ("Réactions d'appuis nulles.", 2)
      classDialog.Message().set_message(message)
      return
    struct_scale = self.struct_scale
    x0, y0 = self.x0, self.y0
    unit_conv = rdm.struct.units
    cr.push_group()

    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_font_size(Const.FONT_SIZE)

    message = None
    classDialog.Message().set_message(message)
    legends = {}
    for noeud in Char.Reactions:
      legends[noeud] = {}
      x, y = rdm.struct.Nodes[noeud]
      cr.save()
      cr.translate(x0 + x*struct_scale, y0 - y*struct_scale)
      Fx_sign = 0
      Fx = Char.Reactions[noeud]["Fx"]
      if abs(Fx) / maxi > 1e-8:
        if Fx > 0:
          Fx_sign = 1
          angle = 0
          dx = -5
        else:
          Fx_sign = -1
          angle = math.pi
          dx = 5
        dlegend = 15
        Fx = abs(Fx)
        text = function.PrintValue(Fx, unit_conv['F'])
        Fx = max(Fx*Const.ARROW_SIZE_MAX/maxi, Const.ARROW_SIZE_MIN)
        xlegend, ylegend = self._draw_arrow(cr, dx, 0, Fx,
			angle, mirror=False)
        
        if dx < 0:
          self.mapping.extend_box(self.id, xlegend-dlegend-30, ylegend+15)
          legends[noeud][0] = [[text, xlegend-dlegend, ylegend, 0, 0]]
        else:
          self.mapping.extend_box(self.id, xlegend+30, ylegend+15)
          legends[noeud][0] = [[text, xlegend, ylegend, 0, 0]]

      Fy = Char.Reactions[noeud]["Fy"]
      if abs(Fy) / maxi > 1e-8:
        angle = Fy < 0 and math.pi/2 or -math.pi/2
        mirror = Fy < 0 and True or False
        dy = 5
        Fy = abs(Fy)
        text = function.PrintValue(Fy, unit_conv['F'])
        Fy = max(Fy*Const.ARROW_SIZE_MAX/maxi, Const.ARROW_SIZE_MIN)
        xlegend, ylegend = self._draw_arrow(cr, 0, dy, Fy,
			angle, mirror=mirror)
        self.mapping.extend_box(self.id, xlegend, ylegend+15)
        legends[noeud][1] = [[text, xlegend, ylegend, 0, 0]]
      Mz = Char.Reactions[noeud]["Mz"]
      if abs(Mz) / maxi > 1e-8: # prendre maxi pour M --> [1]
        text = function.PrintValue(Mz, unit_conv['F'])
        if Fx_sign == 0:
          xlegend, ylegend = self._draw_moment(cr, x, -y, rotate=0.78)
          a = 0
        elif Fx_sign == 1:
          xlegend, ylegend = self._draw_moment(cr, x, -y, rotate=1.57)
          a = math.pi/4
        elif Fx_sign == -1:
          a = -math.pi/4
          xlegend, ylegend = self._draw_moment(cr, x, -y)
        self.mapping.extend_box(self.id, xlegend, ylegend+15)
        legends[noeud][2] = [[text, xlegend, ylegend, 0, 0]]
      cr.restore()
    cr.restore()
    self.p_reac = cr.pop_group()

    self.mapping.set_curve_values(self, legends, self.s_case, "reac")

  def _push_bind_group(self, struct, cr):
    """Crée le pattern des appuis"""
    struct_scale = self.struct_scale
    cr.push_group()
    self._draw_bind(cr, self.x0, self.y0, struct, struct_scale)
    self.p_bind = cr.pop_group()

  def _push_soll_group(self, study, cr, maxi):
    """Crée un pattern contenant toutes les courbes des sollicitations"""
    #print("_push_soll_group", maxi)
    rdm = study.rdm
    unit_conv = rdm.struct.units
    struct = rdm.struct
    struct_scale = self.struct_scale
    cr.push_group()

    mode = struct.IsHorizontal() and 1 or 2
    size = mode == 1 and Const.GRAPH_SIZE_MAX or Const.GRAPH_SIZE_MIN
    if maxi == None:
      self.p_curves = cr.pop_group()
      return
    if maxi == 0.:
      chart_scale = 0.
    else:
      chart_scale = size / maxi
    if chart_scale == 0.:
      chart_scale = 1. # evite une cairo invalid matrix
    if self.status in self.chart_zoom:
      chart_scale = chart_scale*self.chart_zoom[self.status]
    self.chart_scale = chart_scale

    s_cases = self.s_cases
    empty = []
    #user_barres = struct.UserBars
    user_barres = struct.GetBars()

    barres = struct.Barres
    for n_case in s_cases:
      color = self._fg.get_nth_color(n_case)
      Char = rdm.GetCharByNumber(n_case)
      max_char = study.get_max(self, Char)
      if max_char < 1e-5: # XXX
        empty.append(Char.name)
      if mode == 1:
        self._draw_ligne_attache1(cr, rdm, Char, struct_scale,
		chart_scale, None, color)

      for barre in user_barres:
        data = self._get_curve_points(rdm, barre, Char)
        x, y = struct.Nodes[barres[barre][0]] # origine barre
        self._draw_single_bar_curve(cr, rdm, barre, data, self.x0, self.y0, x, y, struct_scale, chart_scale, n_case, color=color, mode=mode)
      self._set_soll_values(cr, rdm, struct_scale, chart_scale, n_case, Char)

      for arc in struct.Curves:
        #self._draw_end_bar_debug(cr, rdm, arc, Char, struct_scale, chart_scale)
        data = self._get_bezier_list(cr, rdm, arc, Char, struct_scale, chart_scale)
        self._draw_arc_curve(cr, rdm, arc, data, n_case, color=color, mode=mode)
        self.mapping.set_arc_curves(self.id, n_case, arc, data)
      self._set_curve_values_arc(cr, study, struct_scale, chart_scale, n_case)

    self.p_curves = cr.pop_group()
    if empty:
      text = "Pas de sollicitation dans "
      text += ", ".join(empty)
      message = (text, 2)
      classDialog.Message().set_message(message)


  def _push_series_group(self, study, cr):
    """Crée le pattern pour les légendes des courbes"""
    tag = self.options.get('Series', False)
    series_id = self.series_id
    if not tag:
      #if not series_id is None:
      #  del(self.mapping.infos[self.id][series_id])
      return
    if series_id is None:
      x = self.x0
      y = self.y0
    else:
      x, y = self.mapping.infos[self.id][series_id].box[0:2]
    rdm = study.rdm
    combis = rdm.GetCasesCombis(self.s_cases)
    cr.push_group()
    box_width, box_height = 0, 0
    cr.translate(x, y)
    for i, combi in enumerate(combis):
      n_color = self.s_cases[i]
      color = self._fg.get_nth_color(n_color)
      self._fg.set_color_by_name(cr, color)
      cr.move_to(0, 12*(i+1))
      cr.rel_line_to(50, 0)
      cr.stroke()
      x_bearing, y_bearing, width, height = cr.text_extents(combi)[:4]
      cr.move_to(60, 12*(i+1)+height/2)
      cr.show_text(combi)
      box_height += 12
      if width > box_width:
        box_width = width
    if not box_width == 0:
      box_width += 70
    box = (x, y, int(box_width), int(box_height+12))
    obj = MSeries(box, series_id)
    self.p_infos[obj.id] = cr.pop_group()
    self.mapping.set_info(self.id, obj)
    if series_id is None:
      self.series_id = obj.id

  def _push_defo_group(self, study, cr, maxi, size):
    """Crée un pattern contenant toutes les courbes des sollicitations"""
    rdm = study.rdm
    struct = rdm.struct
    struct_scale = self.struct_scale
    cr.push_group()
    if maxi == None:
      self.p_curves = cr.pop_group()
      return
    if maxi == 0.:
      chart_scale = 0.
    else:
      chart_scale = size / maxi
    mode = struct.IsHorizontal() and 1 or 2
    crit = max(struct.width, struct.height)/1e8
    if chart_scale == 0.:
      chart_scale = 1 # evite une cairo invalid matrix
      #self.p_curves = cr.pop_group()
      #return
    if self.status in self.chart_zoom:
      chart_scale = chart_scale*self.chart_zoom[self.status]
    self.chart_scale = chart_scale
    s_cases = self.s_cases
    empty = []
    user_barres = struct.GetBars()
    barres = struct.Barres
    for n_case in s_cases:
      color = self._fg.get_nth_color(n_case)
      Char = rdm.GetCharByNumber(n_case)
      max_char = study.get_max(self, Char)
      if max_char < crit:
        empty.append(Char.name)
      for barre in user_barres:
        data = self._get_curve_points(rdm, barre, Char)
        #self._print_controls_point(data)
        x, y = struct.Nodes[barres[barre][0]] # origine barre
        self._draw_one_bar_defo(cr, study, barre, data, self.x0, self.y0, x, y, struct_scale, chart_scale, n_case, color=color, mode=mode)

      for arc in struct.Curves:
        #self._draw_end_bar_debug(cr, rdm, arc, Char, struct_scale, chart_scale)
        data = self._get_bezier_list(cr, rdm, arc, Char, struct_scale, chart_scale)
        self._draw_arc_curve(cr, rdm, arc, data, n_case, color=color, mode=mode)
        self.mapping.set_arc_curves(self.id, n_case, arc, data)
      self._set_curve_values_arc(cr, study, struct_scale, chart_scale, n_case)

      self._draw_relax_defo(cr, rdm, struct_scale, chart_scale, Char, color)
      self._draw_bind_dep(cr, rdm, struct_scale, chart_scale, Char, color, 0.5)
      self._set_defo_values(cr, rdm, struct_scale, chart_scale, n_case, Char)
    self.p_curves = cr.pop_group()
    
    if empty:
      text = "Déformée nulle ou très faible dans "
      text += ", ".join(empty)
      message = (text, 2)
    else:
      message = None
    classDialog.Message().set_message(message)


  def _push_influ_group(self, study, cr):
    """Crée un pattern contenant toutes les courbes des sollicitations"""
    #message = ("Réactions d'appuis nulles.", 2)
    #classDialog.Message().set_message(message)
    try:
      rdm = study.influ_rdm
    except AttributeError:
      rdm = study.influ_rdm = classRdm.Influ_Structure(study.rdm.struct)
    struct = rdm.struct
    try:
      bars = self.s_influ_bars
    except AttributeError:
      #bars = struct.UserBars
      bars = struct.GetBars()
    data, values, maxi0 = self._get_influ_data(rdm, bars)
    if maxi0 == 0 or maxi0 < 1e-14:
      chart_scale = 1. # avoid cairo.Error: invalid matrix
    else:
      chart_scale = Const.GRAPH_SIZE_MAX / maxi0
    self.influ_scale = chart_scale
    struct_scale = self.struct_scale
    cr.push_group()
    for obj in self.influ_list.values():
      color = self._fg.get_nth_color(obj.id)
      id = obj.id
      status = obj.status
      self._draw_all_bars_influ(cr, rdm, obj, data[id], struct_scale, chart_scale, color=color)
      self._set_influ_values(cr, rdm, id, status, values[id], struct_scale, chart_scale)
    self.p_curves = cr.pop_group()

# barres inutile
  def _set_curve_values_arc(self, cr, study, struct_scale, chart_scale, n_case, barres=None):
    """Prépare le mapping pour les valeurs d'une courbe correspondant à un arc"""
    rdm = study.rdm
    struct = rdm.struct
    if len(struct.Curves) == 0:
      return
    if self.status == 7:
      maxi = study.get_max(self)
    else:
      maxi = study._get_soll_max()
    if maxi is None:
      return
    crit = maxi / 1e8
    units = struct.units
    Char = rdm.GetCharByNumber(n_case)
    if self.status == 4:
      n_soll = 0
      unit_conv = units['F']
      f = rdm.GetArcSollValues
    elif self.status == 5:
      n_soll = 1
      unit_conv = units['F']
      f = rdm.GetArcSollValues
    elif self.status == 6:
      n_soll = 2
      unit_conv = units['L']*units['F']
      f = rdm.GetArcSollValues
    elif self.status == 7:
      f = rdm.GetArcDefoValues
      n_soll = 2 # inutile
      unit_conv = units['L']
    try:
      user_values = self.user_values[self.status][n_case]
    except KeyError:
      user_values = {}
    di = {}
    for arc in struct.Curves:
      data = f(arc, Char, n_soll, crit)
      di2 = {}
      user_value = {}
      if arc in user_values:
        user_value = user_values[arc]
      self._get_user_values2(rdm, arc, Char, user_value, data)
      for barre in data:
        val, pos = data[barre]
        N0 = struct.Barres[barre][0]
        x, y = struct.Nodes[N0]
        cr.save()
        cr.translate(self.x0 + x*struct_scale, self.y0 - y*struct_scale)
        angle = -struct.Angles[barre]
        if not angle == 0:
          cr.rotate(angle)
        cr.scale(struct_scale, chart_scale)
        dy = self._get_text_pos(val)
        x, y = cr.user_to_device(0., -val+dy/chart_scale)
        di2[pos] = [[(0., val), int(x), int(y), angle, 0, True]]
        cr.restore()
      di[arc] = di2
    self.mapping.set_curve_values(self, di, n_case, 'arc')


  def _set_soll_values(self, cr, rdm, struct_scale, chart_scale, n_case, Char, barres=None):
    """Prépare les données pour les légendes des courbes"""
    #print("_set_soll_values", n_case)
    if not (n_case == self.s_curve or n_case in self.s_values):
      self.mapping.set_curve_values(self, {}, n_case)
      return
    struct = rdm.struct
    units = struct.units
    #if self.status == 6:
    #  unit_conv = units['L']*units['F']
    #else:
    #  unit_conv = units['F']
    self._delete_node_val(rdm)
    if barres is None:
      barres = struct.GetBars()
    try:
      user_values = self.user_values[self.status][n_case]
    except KeyError:
      user_values = {}
    di = {}
    for barre in barres:
      x, y = struct.Nodes[struct.Barres[barre][0]] # origine barre
      di2 = {}
      angle = -struct.Angles[barre]
      l = struct.Lengths[barre]
      cr.save()
      cr.translate(self.x0 + x*struct_scale, self.y0 - y*struct_scale)
      if not angle == 0:
        cr.rotate(angle)
      cr.scale(struct_scale, chart_scale)
      bar_values = rdm.bar_values[barre]
      self._get_user_values(rdm, Char, barre, user_values, bar_values, l)
      for u, data in bar_values.items():
        u = u*l
        di2[u] = []
        for pos, val in data.items():
          dy = self._get_text_pos(val)
          x, y = cr.user_to_device(u, -val+dy/chart_scale)
          if pos == 2: # provisoire
            pos -= 2
            auto = False
          else:
            auto = True
          di2[u].append([(0., val), int(x), int(y), angle, pos, auto])
      cr.restore()
      di[barre] = di2
    self.mapping.set_curve_values(self, di, n_case)

  def _get_user_values(self, rdm, Char, barre, user_values, bar_values, l):
    """Ajoute les valeurs spécifiée par l'utilisateur"""
    #print("id=", self.id, user_values, barre)
    values = user_values.get(barre, {})
    are_deleted = []
    for u_abs in values:
      u = u_abs/l
      if not u in bar_values:
        if len(values[u_abs]) == 2:
          are_deleted.append(u_abs)
          continue
        val = rdm.GetValue(barre, u_abs, Char, self.status)
        if not self.status == 7:
          val = val[1]
        bar_values[u] = {2: val} # provisoire 2 pour marquer les valeurs user
    for val in are_deleted:
      del(values[val]) # suppression valeurs devenues inutiles

  def _get_user_values2(self, rdm, arc, Char, user_values, bar_values):
    """Ajoute les valeurs définies par l'utilisateur à la variable bar_values pour un arc"""
    Arc = rdm.struct.Curves[arc]
    for pos in user_values:
      b, pos1 = Arc.get_bar_and_pos(pos)
      val, text = rdm.GetArcValue(Char, self.status, b, pos1)
      bar_values[b] = (val[1], pos)
     
# todo regrouper avec _set_curve_values
# enlever unit_conv
  def _set_defo_values(self, cr, rdm, struct_scale, chart_scale, n_case, Char):
    """Prépare les données pour les légendes des courbes"""
    #print("_set_defo_vals", rdm.bar_values)
    struct = rdm.struct
    unit_conv = struct.units['L']
    self._delete_node_val(rdm)
    barres = struct.GetBars()
    try:
      user_values = self.user_values[self.status][n_case]
    except KeyError:
      user_values = {}
    di = {}
    for barre in barres:
      x, y = struct.Nodes[struct.Barres[barre][0]] # origine barre
      di2 = {}
      angle = -struct.Angles[barre]
      l = struct.Lengths[barre]
      cr.save()
      cr.translate(self.x0 + x*struct_scale, self.y0 - y*struct_scale)
      if not angle == 0:
        cr.rotate(angle)
      cr.scale(struct_scale, chart_scale)
      bar_values = rdm.bar_values[barre]
      self._get_user_values(rdm, Char, barre, user_values, bar_values, l)
      for u, data in bar_values.items():
        u = u*l
        di2[u] = []
        for pos, val in data.items():
          valx, valy = val
          valx = valx*chart_scale / struct_scale
          dy = self._get_text_pos(valy)
          x, y = cr.user_to_device(u+valx, -valy+dy/chart_scale)
          if pos == 2: # provisoire
            pos -= 2
            auto = False
          else:
            auto = True
          di2[u].append([val, int(x), int(y), angle, pos, auto])
      cr.restore()
      di[barre] = di2
    self.mapping.set_curve_values(self, di, n_case)



  def _push_legends_group(self, cr, struct):
    """Crée un dictionnaire de patterns contenant toutes les valeurs numériques des sollicitations pour chaque combinaison"""
    #print("_push_legends_group")
    if self.status == 3:
      self._push_legends_group2(cr) # provisoire trouver mieux
      return
    self.p_legends = {}
    di = self.mapping.curve_values[self.id]
    if self.status in [4, 5]:
      unit_conv = struct.units['F']
    elif self.status == 6:
      unit_conv = struct.units['F']*struct.units['L']
    elif self.status == 7:
      unit_conv = struct.units['L']
    elif self.status == 8:
      try:
        obj = list(self.influ_list.values())[0]
        status = obj.status
      except IndexError:
        status = 1 # debug
      unit_conv = get_influ_conv(status, struct.units)
    for n, li in di.items():
      cr.push_group()
      for legend in li:
        x, y = legend.x, legend.y
        values, angle = legend.values, legend.a
        text = values[1]
        text = function.PrintValue(text, unit_conv)
        color = self._fg.get_nth_color(n)
        self._fg.set_color_by_name(cr, color)
        draw_single_soll_text(cr, x, y, text, angle)
      self.p_legends[n] = cr.pop_group()

  def _push_legends_group2(self, cr):
    """Crée un dictionnaire de patterns contenant les valeurs des réactions d'appui"""
    #print("_push_legends_group2")
    self.p_legends = {}
    di = self.mapping.curve_values[self.id]
    n = self.s_case
    #assert len(di) == 1
    li = di[n] # di ne contient qu'une seule clé
    cr.push_group()
    for legend in li:
      x, y = legend.x, legend.y
      text, angle = legend.text, legend.a
      #print("x=", x, y, text)
      self._fg.set_color_by_name(cr, 'grey')
      draw_single_soll_text(cr, x, y, text, angle)
    self.p_legends[n] = cr.pop_group() # ne contient qu'un seul pattern





  def _draw_relax_defo(self, cr, rdm, struct_scale, chart_scale, Char, color):
    ddlValue = Char.ddlValue
    for noeud in rdm.struct.IsRelax:
      dx, dy = ddlValue[noeud][0]*chart_scale, -ddlValue[noeud][1]*chart_scale
      x, y = rdm.struct.Nodes[noeud]
      self._draw_one_relax(cr, self.x0+x*struct_scale+dx, -self.y0+y*struct_scale-dy, 1, False, color)

# revoir lancement de cette fonction
  def _draw_bind_dep(self, cr, rdm, struct_scale, ampli, Char, color=None, alpha=1.):
    """Dessine les appuis simples ayant subi un déplacement"""
    struct = rdm.struct
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color, alpha)
    ddlValue = Char.ddlValue
    for noeud, liaison in struct.Liaisons.items():
      dx, dy = ddlValue[noeud][0]*ampli, -ddlValue[noeud][1]*ampli
      delta = (dx**2 + dy**2)**0.5
      if delta < 5:
        continue
      x1, y1 = struct.Nodes[noeud]
      if liaison == 0:
        angle = self._get_clumping_angle(struct, noeud)
        self._draw_clumping(cr, self.x0+dx, self.y0+dy, x1, y1,
			struct_scale, angle)
      elif liaison == 1:
        self._draw_hinge(cr, self.x0+dx, self.y0+dy, x1, y1,
			struct_scale)
      elif liaison == 2:
        teta = 0.
        relax = False
        if noeud in struct.AppuiIncline:
          teta = -struct.AppuiIncline[noeud] 
        if struct.IsRelax.get(noeud) == 1:
          relax = True
        self._draw_simple_support(cr, self.x0+dx, self.y0+dy, x1, y1,
			struct_scale, teta, relax)
      elif liaison == 3:
        self._draw_elastic_support(cr, self.x0+dx, self.y0+dy, x1, y1,
			struct_scale)
    cr.restore()


  def _print_controls_point(self, data):
    for elem in data:
      if len(elem) == 1:
        print("end=", elem)
      else:
        print("end=", elem[0])
        print("\tC1=", elem[1])
        print("\tC2=", elem[2])

# revoir arguments
  def _draw_arc_curve(self, cr, rdm, arc, data, n_case, color=None, width=1, mode=False):
    """Dessine une courbe sur un arc à partir des points de controles donnés dans le repère du device"""
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_line_width(width)
# XXX optimiser mieux x0, y0 si continuité
    for li in data:
      for tu in li:
        x0, y0, c1x, c1y, c2x, c2y, x1, y1 = tu[0:8]
        cr.move_to(x0, y0)
        cr.curve_to(c1x, c1y, c2x, c2y, x1, y1)
        cr.stroke()
    self._draw_ligne_attache3(cr, data, rdm, arc)
    cr.restore()


  def _draw_single_bar_curve(self, cr, rdm, barre, segs, x0, y0, x1, y1, struct_scale, chart_scale, n_case, color=None, width=1, mode=False):
    """Dessine pour une barre une sollicitation données par segs
    sous forme d'une courbe continue"""
    #print("_draw_single_bar_curve", barre, segs)
    unit_conv = rdm.struct.units
    angle = -rdm.struct.Angles[barre]
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_line_width(width)
    cr.save()
    cr.translate(x0 + x1*struct_scale, y0 - y1*struct_scale)
    if not angle == 0:
      cr.rotate(angle)
    cr.scale(struct_scale, chart_scale)
    pt_dashes = []
    mappings = []
    pt0 = cr.user_to_device(0., 0.) # origine de la barre
    n = len(segs)
    for i, data in enumerate(segs):
      dx = data[0][0] # delta x
      dy = -data[0][1] # delta y vers le bas
      if i == 0:
        cr.move_to(0., dy)
        if mode == 2:
          pt_dashes.append((0. , 0., dy))
        x = 0.
        y = dy
        prec = cr.user_to_device(x, y)
        mappings.append((prec, ))
        continue
      if dx == 0.:
        # discontinuité
        cr.rel_move_to(0., dy)
        pt_dashes.append((x , y, y+dy))
        y += dy
        prec = cr.user_to_device(x, y)
        mappings.append((prec, ))
        continue
      current = cr.user_to_device(x+dx, y+dy)
      if len(data) == 2:
        cr.rel_line_to(dx, dy)
        mappings.append((prec, current, data[1]))
      elif len(data) == 4:
        dC1x, dC1y = data[1]
        dC2x, dC2y = data[2]
        a, b, c, d = data[3] # parabolic coefs
        a, b, c, d = a*chart_scale/struct_scale**3, b*chart_scale/struct_scale**2, c*chart_scale/struct_scale, d*chart_scale
        cr.rel_curve_to(dC1x, -dC1y, dC2x, -dC2y, dx, dy)
        C1x, C1y = cr.user_to_device(x+dC1x, y-dC1y)
        C2x, C2y = cr.user_to_device(x+dC2x, y-dC2y)
        bezier_pts = (C1x, C1y, C2x, C2y, current[0], current[1])
# optimiser pt0 présent dans chaque tuple ??
        coefs = (a, b, c, d)
        geom = (x*struct_scale, 0., dx*struct_scale, 0., angle)
        tu = (pt0, coefs, geom, bezier_pts)
        mappings.append(tu)
      else:
        print("debug anomalie dans _draw_single_bar_curve", len(data), data)
      x += dx
      y += dy
      prec = current
      if mode == 2 and i == n-1:
        pt_dashes.append((x , y, 0.))
    cr.restore()
    cr.stroke()
    self._draw_ligne_attache2(cr, x1, y1, struct_scale, chart_scale, angle, pt_dashes)
    cr.restore()
    self.mapping.set_curves(self.id, n_case, barre, mappings)


  def _draw_one_bar_defo(self, cr, study, barre, segs, x0, y0, x1, y1, struct_scale, chart_scale, n_case, color=None, width=1, mode=False):
    """Dessine la déformée pour une barre"""
    #print("_draw_one_bar_defo", barre)
    #self._print_controls_point(data)
    rdm = study.rdm
    unit_conv = rdm.struct.units
    angle = -rdm.struct.Angles[barre]
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_line_width(width)
    cr.save()
    cr.translate(x0 + x1*struct_scale, y0 - y1*struct_scale)
    if not angle == 0:
      cr.rotate(angle)
    # provisoire evite un bug si la longueur de la barre est nulle
    if struct_scale is None:
      struct_scale = 1

    cr.scale(struct_scale, chart_scale)
    ampli = chart_scale / struct_scale
    mappings = []
    pt0 = cr.user_to_device(0., 0.) # origine de la barre
    n = len(segs)
    for i, data in enumerate(segs):
      du = data[0][0] # variation de l'abscisse le long de la barre
      defox = data[0][1]*ampli # déformée dans le sens de la barre (extrémité)
      defoy = -data[0][2] # déformée perpendiculaire (+=vers le bas)
      if i == 0:
        cr.move_to(du+defox, defoy)
        dx = defox
        dy = defoy
        u = du
        prec = cr.user_to_device(du+defox, defoy)
        mappings.append((prec, ))
        continue

      lx = du + defox
      current = cr.user_to_device(u+dx+lx, dy+defoy)
      if len(data) == 1:
        cr.rel_line_to(du+defox, defoy)
        mappings.append((prec, current, (0., du)))
      elif len(data) == 4:
        dC1x, dC1y = data[1]
        dC2x, dC2y = data[2]
        # correction des x des points de controles si raccourcissement ou allongement de la barre 
        dC1x += defox/3
        dC2x += 2*defox/3

        # polynome coefs
        n = len(data[3]) - 1
        coefs = []
        # changement de repère pour tenir compte d'un allongement de la barre
        k = 1+defox/du # (x'=kx et k=(du+defox)/du )
        # !! les coefs du polynome sont donnés dans la barre non déformée
        for j in data[3]:
          j = j*chart_scale/(k*struct_scale)**n
          coefs.append(j)
          n = n - 1
        cr.rel_curve_to(dC1x, -dC1y, dC2x, -dC2y, du+defox, defoy)
        C1x, C1y = cr.user_to_device(u+dx+dC1x, dy-dC1y)
        C2x, C2y = cr.user_to_device(u+dx+dC2x, dy-dC2y)
        bezier_pts = (C1x, C1y, C2x, C2y, current[0], current[1])
        # geom = (u0 non déformée, déplacement origine, longueur déformée, angle)
        geom = (u*struct_scale, dx*struct_scale, du*struct_scale, defox*struct_scale, angle)
        #geom = (u*struct_scale, dx*struct_scale, (du+defox)*struct_scale, angle)
        tu = (pt0, coefs, geom, bezier_pts)
        mappings.append(tu)
      else:
        print("debug anomalie dans _draw_one_bar_defo")
      u += du
      dx += defox
      dy += defoy
      prec = current
    cr.restore()
    cr.stroke()
    cr.restore()
    self.mapping.set_curves(self.id, n_case, barre, mappings)


  def _delete_node_val(self, rdm):
    """Supprime les valeurs en double sur les noeuds"""
    def get_is_in_list(val, li):
      eps = 1e-6
      for elem in li:
        if abs(val-elem) < eps:
          return True
      return False

    struct = rdm.struct
    bar_values = rdm.bar_values
    
    #print("bar_values", bar_values)
    barre_by_node = struct.BarByNode
    for noeud, tu in barre_by_node.items():
      data = []
      for barre in tu[0]:
        if not barre in bar_values:
          continue
        values = bar_values[barre]
        if not 0. in values:
          continue
        if not 0 in values[0.]:
          continue
        val = values[0.][0]
        #print("+++", barre, val, data)
        if get_is_in_list(val, data):
          del(bar_values[barre][0.])
        else:
          data.append(val)
      for barre in tu[1]:
        if not barre in bar_values:
          continue
        values = bar_values[barre]
        if not 1. in values:
          continue
        val = values[1.][0]
        if get_is_in_list(val, data):
          del(bar_values[barre][1.])
        else:
          data.append(val)

  def _get_text_pos(self, value):
    """Retourne le décalage en px d'un texte suivant le signe de value dans le repère de la barre"""
    h = 12
    return value >= 0 and -0.8 * h or 1.15 * h


  def get_interpolation_bars(self, rdm, arc):
    """Retourne une liste de tuple contenant les barres sur lesquelles sont interpolées les courbes - Chaque tuple correspond à une courbe continue"""
    #print("get_interpolation_bars", arc)
    struct = rdm.struct
    Arc = struct.Curves[arc]
    user_nodes = Arc.user_nodes
    start, end = Arc.b0, Arc.b1
    da = struct.Angles[start+1] - struct.Angles[start]
    b = start
    li_barres = []
    for Node in user_nodes[1:]:
      end_bar = Node.end
      n_bars = end_bar-b+1
      a = abs(da)*n_bars
      n_inter = max(2, int(round(a/0.4)),  int(round(float(n_bars)/8))) # parameter : 0,5 radian -> influe sur la précision du tracé ou toutes les 8 barres
      if n_inter > n_bars:
        print("debug in get_interpolation_bars")
        n_inter = n_bars
      li2 = [b]
      pas = float(n_bars)/n_inter
      for i in range(n_inter-1):
        b += pas
        li2.append(int(b))
      if not b == end_bar:
        li2.append(end_bar)
      b = end_bar+1
      li_barres.append(tuple(li2))
    return li_barres, start, end

  def _get_bezier_list(self, cr, rdm, arc, Char, struct_scale, chart_scale):
    """Retourne une liste de points de controle pour le tracé d'une courbe sur un arc
    Format: [[(x0, y0, c0x, c0y, c1x, c1y, x1, y1), ()], [()]] -> les sous-listes correspondent aux tronçons entre user_nodes"""
    #print("_get_bezier_list", arc)
    struct = rdm.struct
    X0, Y0 = self.x0, self.y0
    if self.status == 4:
      n_soll = 0
      f = self._get_device_point
    elif self.status == 5:
      n_soll = 1
      f = self._get_device_point
    elif self.status == 6:
      n_soll = 2
      f = self._get_device_point
    elif self.status == 7:
      n_soll = None
      f = self._get_device_point2
    li_barres, start, end = self.get_interpolation_bars(rdm, arc)
    #print("liBarres=", li_barres)
    pt_device = {}
    for tu in li_barres:
      n = len(tu)
      for j, b in enumerate(tu):
        if b == start and j == 0:
          xd0, yd0 = f(cr, X0, Y0, struct, Char, arc, b, struct_scale, chart_scale, n_soll, 0)
          xd1, yd1 = f(cr, X0, Y0, struct, Char, arc, b+1, struct_scale, chart_scale, n_soll, 2)
        elif j == 0:
          xd0, yd0 = f(cr, X0, Y0, struct, Char, arc, b, struct_scale, chart_scale, n_soll, 0, average_angle=True)
          xd1, yd1 = f(cr, X0, Y0, struct, Char, arc, b+1, struct_scale, chart_scale, n_soll, 2)
        elif b == end and j == n-1:
          xd0, yd0 = f(cr, X0, Y0, struct, Char, arc, b, struct_scale, chart_scale, n_soll, 2)
          xd1, yd1 = f(cr, X0, Y0, struct, Char, arc, b, struct_scale, chart_scale, n_soll, 1)
        elif j == n-1:
          xd0, yd0 = f(cr, X0, Y0, struct, Char, arc, b, struct_scale, chart_scale, n_soll, 2)
          xd1, yd1 = f(cr, X0, Y0, struct, Char, arc, b, struct_scale, chart_scale, n_soll, 1, average_angle=True)
        else:
          xd0, yd0 = f(cr, X0, Y0, struct, Char, arc, b, struct_scale, chart_scale, n_soll, 2)
          xd1, yd1 = f(cr, X0, Y0, struct, Char, arc, b+1, struct_scale, chart_scale, n_soll, 2)
        pt_device[b] = (xd0, yd0, xd1, yd1)

    li = []
    #print("li_barres=", li_barres)
    for tu1 in li_barres:
      n = len(tu1)
      li2 = []
      for i in range(n-1):
        b, next_b = tu1[i:i+2]
        #print("barre=", b, next_b)
        xd0_0, yd0_0, xd0_1, yd0_1 = pt_device[b]
        xd1_0, yd1_0, xd1_1, yd1_1 = pt_device[next_b]
        d_corde = ((xd0_0-xd1_0)**2+(yd0_0-yd1_0)**2)**0.5
        a_corde = -function.get_vector_angle((xd0_0, yd0_0), (xd1_0, yd1_0))
        if i == 0: # on prend la pente avec la barre suivante pour éviter effet escalier sur effort tranchant
          xd1_0, yd1_0 = f(cr, X0, Y0, struct, Char, arc, b+1, struct_scale, chart_scale, n_soll, 0)
          dx0, dy0 = xd1_0-xd0_0, yd1_0-yd0_0
          a0 = -function.get_vector_angle((xd0_0, yd0_0), (xd1_0, yd1_0))
          coef = d_corde/3/math.cos( a0-a_corde)
          d0 = (dx0**2 + dy0**2)**0.5
          C0xprec, C0yprec = xd0_0 + dx0*coef/d0, yd0_0 + dy0*coef/d0
          xdprec, ydprec = xd0_0, yd0_0
          b0, b1 = b, next_b-1
          continue
        dx0, dy0 = xd0_1-xd0_0, yd0_1-yd0_0
        d0 = (dx0**2 + dy0**2)**0.5
        a0 = -function.get_vector_angle((xd0_0, yd0_0), (xd0_1, yd0_1))
        coef = d_corde/3/math.cos( a0-a_corde)
        C0x, C0y = xd0_0 - dx0*coef/d0, yd0_0 - dy0*coef/d0
        tu = (xdprec, ydprec, C0xprec, C0yprec, C0x, C0y, xd0_0, yd0_0, b0, b1)
        li2.append(tu)
        b0, b1 = b, next_b-1
       
        C0xprec, C0yprec = xd0_0 + dx0*coef/d0, yd0_0 + dy0*coef/d0
        xdprec, ydprec = xd0_0, yd0_0
      # cloture dernier segment
      # on calcule la dernière pente à partir de la valeur 1 de l'avant dernière barre (à cause de la forme discontinue de V sur un arc)
      xd1_0, yd1_0 = f(cr, X0, Y0, struct, Char, arc, next_b-1, struct_scale, chart_scale, n_soll, 1)
      a1 = -function.get_vector_angle((xd1_0, yd1_0), (xd1_1, yd1_1))
      coef = d_corde/3/math.cos( a1-a_corde)
      dx0, dy0 = xd1_1-xd1_0, yd1_1-yd1_0
      d1 = (dx0**2 + dy0**2)**0.5
      C0x, C0y = xd1_1 - dx0*coef/d1, yd1_1 - dy0*coef/d1
      tu = (xdprec, ydprec, C0xprec, C0yprec, C0x, C0y, xd1_1, yd1_1, b0, b1+1)
      li2.append(tu)
      li.append(li2)
    return li

  def _draw_end_bar_debug(self, cr, rdm, arc, Char, struct_scale, chart_scale):
    """Dessine les valeurs exactes des sollicitation ou deplacements sur les barres de l'arc"""
    #return
    struct = rdm.struct
    Arc = struct.Curves[arc]
    X0, Y0 = self.x0, self.y0
    cr.save()
    if self.status == 4:
      n_soll = 0
      f = self._get_device_point
    elif self.status == 5:
      n_soll = 1
      f = self._get_device_point
    elif self.status == 6:
      n_soll = 2
      f = self._get_device_point
    elif self.status == 7:
      n_soll = None
      f = self._get_device_point2
    b0, b1 = Arc.b0, Arc.b1
    for barre in range(b0, b1+1):
      # valeur au début
      xd0, yd0 = f(cr, X0, Y0, struct, Char, arc, barre, struct_scale, chart_scale, n_soll, 0)
      self._fg.set_color_by_name(cr, "red")
      cr.arc(xd0, yd0, 0.5, 0, 6.29)
      cr.stroke()
      # valeur à la fin
      self._fg.set_color_by_name(cr, "grey")
      xd0, yd0 = f(cr, X0, Y0, struct, Char, arc, barre, struct_scale, chart_scale, n_soll, 1)
      cr.arc(xd0, yd0, 0.5, 0, 6.29)
      cr.stroke()
    cr.restore()

  def _get_device_point(self, cr, X0, Y0, struct, Char, arc, barre, struct_scale, chart_scale, n_soll, position, average_angle=False):
    """Retourne les coordonnées d'un point (d'un arc) du tracé d'une sollicitation dans le repère du device"""
    if position == 0: # arc start
      if average_angle:
        angle = -(struct.Angles[barre-1]+struct.Angles[barre])/2
      else:
        angle = -struct.Angles[barre]
      soll = Char.EndBarSol[barre][0][n_soll]
      pos = 0
    elif position == 1: # end arc
      # inversion des signes par rapport RDM pour repère info
      soll = -Char.EndBarSol[barre][1][n_soll]
      if average_angle:
        angle = -(struct.Angles[barre+1]+struct.Angles[barre])/2
      else:
        angle = -struct.Angles[barre]
      #angle = -struct.Angles[barre]
      pos = 1
    elif position == 2: # current
      angle = -(struct.Angles[barre-1]+struct.Angles[barre])/2
      # réellement utile que pour N et V
      soll = (-Char.EndBarSol[barre-1][1][n_soll]+Char.EndBarSol[barre][0][n_soll])/2
      pos = 0
    node = struct.Barres[barre][pos]
    x0, y0 = struct.Nodes[node]
    cr.save()
    cr.translate(X0 + x0*struct_scale, Y0 - y0*struct_scale)
    if not angle == 0:
      cr.rotate(angle)
    cr.scale(chart_scale, chart_scale)
    xd, yd = cr.user_to_device(0., soll)
    cr.restore()
    return xd, yd

  def _get_device_point2(self, cr, X0, Y0, struct, Char, arc, barre, struct_scale, chart_scale, n_soll, pos, average_angle=False):
    """Retourne les coordonnées d'un point du tracé de la déformée dans le repère du device"""
    if not pos == 1:
      pos = 0
    node = struct.Barres[barre][pos]
    x0, y0 = struct.Nodes[node]
    defx, defy, w = Char.ddlValue[node]
    cr.save()
    cr.translate(X0 + x0*struct_scale, Y0 - y0*struct_scale)
    cr.scale(chart_scale, chart_scale)
    # inversion des signes par rapport RDM pour repère info
    xd, yd = cr.user_to_device(defx, -defy)
    cr.restore()
    return xd, yd

# sauvegarde : calcul d'une bézier en interpolant les temps t1 et t2
  def _get_control_points(self, tu):
    """Retourne les points de controle pour la bézier passant par les 4 points donnés dans tu"""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = tu
    d1 = ((x0-x1)**2+(y0-y1)**2)**0.5
    d2 = ((x1-x2)**2+(y1-y2)**2)**0.5
    d3 = ((x2-x3)**2+(y2-y3)**2)**0.5
    d = d1 + d2 + d3
    t1, t2 = d1/d, (d1 + d2)/d
    #print("t=", t1, t2)
    #t1, t2 = 0.32, 0.68
    a1, a2, a3 = 3*t1*(1-t1)**2, 3*t1**2*(1-t1), x0*(1-t1)**3 + x3*t1**3
    a4 =  y0*(1-t1)**3 + y3*t1**3
    b1, b2, b3 = 3*t2*(1-t2)**2, 3*t2**2*(1-t2), x0*(1-t2)**3 + x3*t2**3
    b4 =  y0*(1-t2)**3 + y3*t2**3
    den = a2*b1 - b2*a1
    c1x = (b1*x1 - a1*x2 + b3*a1 - a3*b1) / den
    c0x = (x1 - a2*c1x - a3) / a1
    c1y = (b1*y1 - a1*y2 + b4*a1 - a4*b1) / den
    c0y = (y1 - a2*c1y - a4) / a1
    #print("controls=", (x0, y0), (c0x, c0y), (c1x, c1y), (x3, y3))
    return (x0, y0), (c0x, c0y), (c1x, c1y), (x3, y3)

  def _get_curve_points(self, rdm, barre, Char):
    """Calcule les sollicitations en fonction du status
    pour une barre donnée - Retourne une liste de liste de valeurs (pour tenir compte des discontinuités)"""
    if self.status == 4:
      points = rdm.ForceBarre(barre, Char, 0)
    elif self.status == 5:
      points = rdm.ForceBarre(barre, Char, 1)
    elif self.status == 6:
      points = rdm.MomentBarre(barre, Char)
    elif self.status == 7:
      points = rdm.DefoBarre(barre, Char)
    return points


  def _draw_ligne_attache1(self, cr, rdm, Char, struct_scale, chart_scale, nodes=None, color=None, width=1):
    """Dessine les lignes d'attaches des sollicitations sur les noeuds
    si les valeurs à droite et à gauche sont différentes pour toutes les barres
    Ne doit être appelée que si les barres sont horizontales"""
    #print("drawing::_draw_ligne_attache1")
    # pas de ligne d'attache si une barre présente un angle de 180°
    if self.status == 4:
      type = 'N'
    elif self.status == 5:
      type = 'V'
    elif self.status == 6:
      type = 'M'
    cr.save()
    cr.set_line_width(width)
    cr.set_antialias(cairo.ANTIALIAS_NONE)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    px = max(cr.device_to_user_distance(1, 1))
    cr.set_dash([9 * px], 0)
    cr.save()
    cr.translate(self.x0, self.y0)
    cr.scale(struct_scale, chart_scale) # attention : non uniforme
    if nodes is None:
      nodes = rdm.struct.Nodes
    names = list(nodes.keys())
    abscisses = [i[0] for i in nodes.values()]
    # trier les noeuds par x croissant
    names = function.tri_abscisse_croissante(names, abscisses)
    n = len(nodes)
    for i, name in enumerate(names):
      #print(i, name)
      pt = nodes[name]
      di = rdm.GetNodeVal(name, Char, type)
      #print("di=", di)
      nb = len(di)
      if nb == 0:
        continue
      if i == 0:
        if 0 in di:  
          soll1 = di[0]
          cr.move_to(pt[0], pt[1]-soll1)
          cr.rel_line_to(0, soll1)
      elif i == n-1:
        if 1 in di:  
          soll2 = di[1]
          cr.move_to(pt[0], pt[1])
          cr.rel_line_to(0, -soll2)
      else:
        if nb == 2:
          soll1 = di[0]
          soll2 = di[1]
          cr.move_to(pt[0], pt[1]-soll1)
          cr.rel_line_to(0, soll1-soll2)

    cr.restore()
    cr.stroke()
    cr.restore()

  def _draw_ligne_attache2(self, cr, x0, y0, struct_scale, chart_scale, angle, pt_dashes):
    """dessin des lignes d'attache à l'intérieur d'une barre"""
    #print("_draw_ligne_attache2", pt_dashes)
    cr.save()
    cr.set_antialias(cairo.ANTIALIAS_NONE)
    cr.set_line_width(1) # dash width = 1
    px = max(cr.device_to_user_distance(1, 1))
    cr.set_dash([9 * px], 0)
    cr.save()
    cr.translate(self.x0 + x0*struct_scale, self.y0 - y0*struct_scale)
    if not angle == 0:
      cr.rotate(angle)
    cr.scale(struct_scale, chart_scale)
    for tu in pt_dashes:
      cr.move_to(tu[0], tu[1])
      cr.line_to(tu[0], tu[2])
    cr.restore()
    cr.stroke()
    cr.restore()

  def _draw_ligne_attache3(self, cr, data, rdm, arc):
    """dessin des lignes d'attache pour les arcs"""
    #print("_draw_ligne_attache3", data)
    struct = rdm.struct
    user_nodes = struct.Curves[arc].user_nodes
    N0, N1 = user_nodes[0].name, user_nodes[-1].name
    nodes = self.mapping.nodes[self.id]
    xprec, yprec = nodes[N0].coors
    cr.save()
    cr.set_dash([9], 0)
    cr.set_line_width(1) # dash width = 1
    #xprec, yprec = data[0][-1][6:]
    for tu in data:
      cr.move_to(xprec, yprec)
      x, y = tu[0][0:2]
      cr.line_to(x, y)
      cr.stroke()
      xprec, yprec = tu[-1][6:8]
    x, y = nodes[N1].coors
    cr.move_to(xprec, yprec)
    cr.line_to(x, y)
    cr.stroke()
    cr.restore()

  def paint_info(self, cr, info_id, alpha=1):
    """Dessine le pattern de l'info donnée par id"""
    cr.set_source(self.p_infos[info_id])
    cr.paint_with_alpha(alpha)


  def paint_drawing(self, cr, alpha=1.):
    """Dessine la structure pour tous les patterns"""
    #print("paint_drawing", self.status)
    cr.save()
    cr.set_source(self.p_struct)
    cr.paint_with_alpha(alpha)

    for p in self.p_infos.values():
      cr.set_source(p)
      cr.paint_with_alpha(alpha)

    status = self.status

    if status == 0:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
    elif status == 1:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
    elif status == 2:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
    elif status == 3:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha*0.5)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_reac)
      cr.paint_with_alpha(alpha)
      for p in self.p_legends.values():
        cr.set_source(p)
        cr.paint_with_alpha(alpha)
    else:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha*0.3)
      cr.set_source(self.p_curves)
      cr.paint_with_alpha(alpha)
      for p in self.p_legends.values():
        cr.set_source(p)
        cr.paint_with_alpha(alpha)

#    if hasattr(self, "p_window"):
#        cr.set_source(self.p_window)
#        cr.paint_with_alpha(alpha)


    if hasattr(self, "p_select"):
      cr.set_source(self.p_select)
      cr.paint_with_alpha(alpha)
    if hasattr(self, "p_barre"):
      cr.set_source(self.p_barre)
      cr.paint_with_alpha(1.)
    cr.restore()

  def paint_drawing2(self, cr, n_case, alpha=1.):
    """Dessine la structure à partir des patterns - Ne dessine que les valeurs numériques de la courbe donnée par n_case"""
    cr.save()
    cr.set_source(self.p_struct)
    cr.paint_with_alpha(alpha)
    status = self.status

    for p in self.p_infos.values():
      cr.set_source(p)
      cr.paint_with_alpha(alpha)
    if status == 0:
      pass
    elif status == 1:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
    elif status == 2:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
    elif status == 3:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha*0.5)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_reac)
      cr.paint_with_alpha(alpha)
    else:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha*0.3)
      cr.set_source(self.p_curves)
      cr.paint_with_alpha(alpha*0.5)
      cr.set_source(self.p_legends[n_case])
      cr.paint_with_alpha(alpha)

    cr.restore()

  def paint_value(self, cr, alpha=1):
    """Peint une légende sur une courbe"""
    cr.save()
    if hasattr(self, "p_window"):
      cr.set_source(self.p_window)
      cr.paint_with_alpha(alpha)
    cr.restore()

# inutile
  def paint_drawing3(self, cr, alpha=1.):
    """Dessine la structure pour tous les patterns"""
    #print("paint_drawing", self.status)
    cr.save()
    cr.set_source(self.p_struct)
    cr.paint_with_alpha(alpha)

    status = self.status

    if status == 0:
      pass
    elif status == 1:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
    elif status == 2:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
    elif status == 3:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha*0.5)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_reac)
      cr.paint_with_alpha(alpha)
      for p in self.p_legends.values():
        cr.set_source(p)
        cr.paint_with_alpha(alpha)
    else:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha*0.3)
      cr.set_source(self.p_curves)
      cr.paint_with_alpha(alpha)
      for p in self.p_legends.values():
        cr.set_source(p)
        cr.paint_with_alpha(alpha)
    if hasattr(self, "p_select"):
      cr.set_source(self.p_select)
      cr.paint_with_alpha(alpha)
    if hasattr(self, "p_barre"):
      cr.set_source(self.p_barre)
      cr.paint_with_alpha(1.)
    cr.restore()


  def paint_drawing4(self, cr, alpha=1.):
    """Dessine tous les patterns sauf le pattern des legendes des courbes"""
    cr.save()
    cr.set_source(self.p_struct)
    cr.paint_with_alpha(alpha)
    status = self.status
    if status == 0:
      pass
    elif status == 1:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
    elif status == 2:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
    elif status == 3:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha*0.5)
      cr.set_source(self.p_char)
      cr.paint_with_alpha(alpha)
      cr.set_source(self.p_reac)
      cr.paint_with_alpha(alpha)
      for p in self.p_legends.values():
        cr.set_source(p)
        cr.paint_with_alpha(alpha)
    elif status in [4, 5, 6, 7, 8]:
      cr.set_source(self.p_bind)
      cr.paint_with_alpha(alpha*0.3)
      cr.set_source(self.p_curves)
      cr.paint_with_alpha(alpha)
      for p in self.p_legends.values():
        cr.set_source(p)
        cr.paint_with_alpha(alpha)
    cr.restore()

  def area_expose_realtime(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    try:
      struct_scale = self.struct_scale
    except TypeError:
      struct_scale = None
    if not len(struct.NodeNotLinked) == 0: 
      message = ("Certains noeuds ne sont pas reliés à une barre.", 0)
    else:
      message = ("Nombre de noeuds : %d" % len(struct.UserNodes), 2)
    classDialog.Message().set_message(message)
    #self._push_node_group(study, cr, struct_scale)
    self._push_struct_group(study, cr, struct_scale)
    self._push_scale_group(study, cr, 1., struct_scale)
    self._push_bind_group(struct, cr)
    self._push_char_group(study, cr)
# provisoire pas de pattern p_barre
    cr.push_group()
    self.p_barre = cr.pop_group()


  def area_expose_barre(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    try:
      struct_scale = self.struct_scale
    except TypeError:
      struct_scale = None
    if not len(struct.NodeNotLinked) == 0 or struct_scale is None:
      self.status = 0 # changement de status
      self.area_expose_realtime(study, cr)
      return
    self._push_struct_group(study, cr, struct_scale)
    self._push_scale_group(study, cr, 1., struct_scale)
    self._push_bind_group(struct, cr)

  def area_expose_char(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    struct_scale = self.struct_scale
    #if not hasattr(self, 'p_struct'):
    self._push_struct_group(study, cr, struct_scale)
    #if not hasattr(self, 'p_bind'):
    self._push_bind_group(struct, cr)
    self._push_char_group(study, cr)
    self._push_scale_group(study, cr, 1., struct_scale)

  def area_expose_reac(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    struct_scale = self.struct_scale
    #if not hasattr(self, 'p_struct'):
    self._push_struct_group(study, cr, struct_scale)
    #if not hasattr(self, 'p_bind'):
    self._push_bind_group(struct, cr)
    #if not hasattr(self, 'p_char'):
    self._push_char_group(study, cr)
    self._push_reac_group(study, cr)
    self._push_legends_group2(cr)
    self._push_scale_group(study, cr, 1., struct_scale)

  def area_expose_soll(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    struct_scale = self.struct_scale
    maxi = study.get_max(self)
    mode = struct.IsHorizontal() and 1 or 2
    size = mode == 1 and Const.GRAPH_SIZE_MAX or Const.GRAPH_SIZE_MIN
    #if not hasattr(self, 'p_struct'):
    self._push_struct_group(study, cr, struct_scale)
    #if not hasattr(self, 'p_bind'):
    self._push_bind_group(struct, cr)
    self._push_soll_group(study, cr, maxi)
    self._push_series_group(study, cr)
    self._push_scale_group(study, cr, maxi, size)
    self._push_legends_group(cr, struct)


  def area_expose_defo(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    struct_scale = self.struct_scale
    maxi = study.get_max(self)
    size = Const.DEFO_MAX
    #if not hasattr(self, 'p_struct'):
    self._push_struct_group(study, cr, struct_scale)
    #if not hasattr(self, 'p_bind'):
    self._push_bind_group(struct, cr)
    self._push_defo_group(study, cr, maxi, size)
    self._push_legends_group(cr, struct)
    self._push_scale_group(study, cr, maxi, size)
    self._push_series_group(study, cr)

  def area_expose_moving(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    struct_scale = self.struct_scale
    #if not hasattr(self, 'p_struct'):
    self._push_struct_group(study, cr, struct_scale)
    #if not hasattr(self, 'p_bind'):
    self._push_bind_group(struct, cr)
    self._push_moving_group(study, cr)
    self._push_legends_group(cr, struct)

  def _push_moving_group(self, study, cr):
    struct = study.rdm.struct
    barres = struct.Barres # provisoire
    forces = ((2, 0), ) # mettre virgule si une seule valeur
    m_rdm = classRdm.Moving_Structure(struct, forces)
    N = 101 # position convoi
    mini, maxi, env_inf, env_sup = m_rdm.get_moving_data(N, 5)
    # maximum
    maxi0 = max(abs(mini), abs(maxi)) # protéger valeur nulle
    chart_scale = Const.GRAPH_SIZE_MAX / maxi0
    struct_scale = self.struct_scale
    for b in env_sup:
      x, y = struct.Nodes[barres[b][0]] # origine barre
      angle = -struct.Angles[b]
      cr.save()
      cr.translate(self.x0 + x*struct_scale, self.y0 - y*struct_scale)
      if not angle == 0:
        cr.rotate(angle)
      cr.scale(struct_scale, chart_scale)
      self._fg.set_color_by_name(cr, "blue")
      for u in env_sup[b]:
        v = env_sup[b][u]
        cr.save()
        cr.translate(u, -v)
        cr.scale(1./struct_scale, 1./chart_scale)
        cr.arc(0, 0, 0.3, 0, 6.29)
        cr.stroke()
        cr.restore()
      self._fg.set_color_by_name(cr, "red")
      for u in env_inf[b]:
        v = env_inf[b][u]
        cr.save()
        cr.translate(u, -v)
        cr.scale(1./struct_scale, 1./chart_scale)
        cr.arc(0, 0, 0.3, 0, 6.29)
        cr.stroke()
        cr.restore()
      cr.restore()

    #print("max=", maxi, mini)
    cr.push_group()




    self.p_curves = cr.pop_group()

  def area_expose_influ(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    struct_scale = self.struct_scale
    status = None
    i = 0
    #mettre test ici pour voir si obj.elem existe
    for obj in self.influ_list.values():
      # test existence obj.elem
      if obj.status == 4:
        if not obj.elem in struct.Nodes:
          obj.elem = list(struct.Nodes.keys())[0] #XXX suppose existence noeud
      else:
        if not obj.elem in struct.Barres:
          try:
            b = int(obj.elem)
            if not b in struct.Barres:
              raise ValueError
            obj.elem = b
          except ValueError:
            obj.elem = list(struct.Barres.keys())[0] #XXX suppose existence barre
      # test status multiple
      if i == 0:
        status = obj.status
        i += 1
        continue
      if not status == obj.status:
        status = None # plusieurs status différents
        break
      status = obj.status
      i += 1
    #if not hasattr(self, 'p_struct'):
    self._push_struct_group(study, cr, struct_scale)
    #if not hasattr(self, 'p_bind'):
    self._push_bind_group(struct, cr)
    self._push_influ_group(study, cr)
    self._push_legends_group(cr, struct)
    if status is None:
      self._push_scale_group(study, cr)
    else:
      self._push_scale_group(study, cr, 1., self.influ_scale, status)

  def _push_title_group(self, study, cr):
    """Crée le pattern pour le titre du dessin"""
    #print("_push_title_group", self.title_id)
    title_id = self.title_id
    tag = self.options.get('Title', True)
    if not tag:
      return
    cr.push_group()
    cr.set_font_size(Const.FONT_SIZE)
    texts = ["Mode ébauche", "Structure", "Chargement", "Liaisons", "N", "V", "M", "Déformée", "Influence", "Mobile"]
    if title_id is None:
      text = '%s (%s)' % (study.name, texts[self.status])
      text2 = study.name
      x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
      x = self.x0+50
      y = self.y0-40
      box = (x, y, int(width+8), int(height+12))
      obj = MText(box, text2, title_id)
      self.title_id = obj.id
    else:
      obj = self.mapping.infos[self.id][title_id]
      text = '%s (%s)' % (obj.text, texts[self.status])
      x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
      x, y, w, h = obj.box
      box = (x, y, int(width+8), int(height+12))
      obj.box = box
    cr.translate(x, y)
    cr.move_to(4, height+5)
    cr.show_text(text)
    self.p_infos[obj.id] = cr.pop_group()
    self.mapping.set_info(self.id, obj)


# revoir user_size/device_size
  def _push_scale_group(self, study, cr, user_size=None, device_size=None, influ_status=None):
    """Crée le pattern pour l'échelle des longueurs ou des graphes"""
    scale_id = self.scale_id
    if scale_id is None:
      x, y, w, h = self.mapping.box[self.id]
      x, y = x+10, y+20
      h = 25
    else:
      x, y, w, h = self.mapping.infos[self.id][scale_id].box
      x += 4
    if user_size is None or device_size == None:
      return
    cr.push_group()
    try:
      zoom = self.chart_zoom[self.status]
    except KeyError:
      zoom = 1
    w, h = self._draw_scale(study, cr, x, y+h, user_size/zoom/device_size, influ_status)
    box = (x-4, y, int(w+8), int(h))
    obj = MScale(box, scale_id)
    self.p_infos[obj.id] = cr.pop_group()
    self.mapping.set_info(self.id, obj)
    if scale_id is None:
      self.scale_id = obj.id


# revoir simplifier
  def _draw_nodes(self, cr, struct, x0, y0, scale=1, color='blue', width=1, name=True, symbol=1):
    """Dessine les noeuds spécifiés dans le dictionnaire nodes
    x, y spécifient la translation
    symbol = 0 : aucun
    symbol = 1 : all except liaison and relax
    symbol = 2 : all
    """
    nodes = struct.Nodes
    nodes_name = list(struct.UserNodes)
    not_linked = struct.NodeNotLinked
    centers = struct.Centers
    nodes_name.extend(list(centers.keys()))
    if name == False and symbol == 0:
      return
    if symbol == 1:
      size = 4
    else:
      size = 8
    cr.save()
    cr.translate(x0, y0)
    if scale is None:
      scale = 1
    cr.scale(scale, scale)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_line_width(width/scale)
    for node in nodes_name:
      try:
        if node in nodes:
          xi, yi = nodes[node]
        else:
          xi, yi = centers[node]
      except ValueError:
        continue
      yi = -yi
      if name:
        self._draw_node_name(cr, xi, yi, node, scale)
      if symbol == 1:
        if node in struct.Liaisons:
          continue
        relax = struct.IsRelax.get(node, 0)
        if relax == 1:
          continue
        cr.save()
        # dessin fond blanc circulaire
        cr.set_source_rgb(1, 1, 1)
        cr.arc(xi, yi, size/scale, 0, 6.29)
        cr.fill()
        cr.stroke()
        cr.restore()
        self._draw_cross(cr, xi, yi, scale)

    if symbol == 2:
      cr.save()
      self._fg.set_color_by_name(cr, "red")
      for node in not_linked:
        try:
          xi, yi = not_linked[node]
        except ValueError:
          continue
        yi = -yi
        if name:
          self._draw_node_name(cr, xi, yi, node, scale)
        cr.save()
        # dessin fond blanc circulaire
        cr.set_source_rgb(1, 1, 1)
        cr.arc(xi, yi, size/scale, 0, 6.29)
        cr.fill()
        cr.stroke()
        cr.restore()
        self._draw_cross(cr, xi, yi, scale)
      cr.restore()
    cr.restore()


  def _draw_bars(self, cr, struct, x0, y0, scale=1, color=None, width=1, show_name=True, axis=False):
    """Dessine les barres, x, y spécifient la translation"""
    if scale is None:
      return
    cr.save()
    cr.translate(x0, y0)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.scale(scale, scale)
    cr.set_line_width(width/scale)
    names = struct.UserBars
    # test ------ dessin de toutes les barres -----
    #names = struct.Barres.keys()
    # fin test -------
    bars = struct.Barres
    nodes = struct.Nodes
    Lengths = struct.Lengths
    arcs = struct.Curves
    superbars = struct.SuperBars
    for name in arcs:
      arc = arcs[name]
      arc.draw(cr, struct)
    for name in superbars:
      bar = superbars[name]
      b0, b1 = bar.b0, bar.b1
      angle = -struct.Angles[b0]
      N0 = bars[b0][0]
      N1 = bars[b1][1]
      x0, y0 = nodes[N0]
      x1, y1 = nodes[N1]
      xm, ym = (x0+x1) / 2., -(y0+y1) / 2.
      bar.draw(cr, struct)
      if show_name:
        self._draw_bar_name(cr, xm, ym, name, angle, scale)
      if axis:
        self._draw_axis(cr, xm, ym, angle, scale)
    for bar in names:
      angle = -struct.Angles[bar]
      l = Lengths[bar]
      if l == 0:
        continue
      node1 = bars[bar][0]
      node2 = bars[bar][1]
      x1, y1 = nodes[node1]
      x2, y2 = nodes[node2]
      y1 = -y1
      y2 = -y2
      cr.move_to(x1, y1)
      cr.line_to(x2, y2)
      xm, ym = (x1+x2) / 2., (y1+y2) / 2.
      if show_name:
        self._draw_bar_name(cr, xm, ym, bar, angle, scale)
      if axis:
        self._draw_axis(cr, xm, ym, angle, scale)

      cr.stroke()
    cr.restore()
# revoir x0 et self.x0
# renommer
  def _get_mapping_data(self, cr, struct, x0, y0, scale):
    """Calcule les points et barres pour le mapping"""
    #print("_get_mapping_data", scale)
    mapping = self.mapping
    names = struct.GetBars()
    bars = struct.Barres
    nodes = struct.Nodes
    not_linked = struct.NodeNotLinked
    m_points, m_bars = {}, {}
    m = 50
    if scale is None:
      try:
        name = list(not_linked.keys())[0]
        m_points[name] = (self.x0, self.y0)
      except IndexError:
        pass
        #m_points = {}
      w, h = 2*m, 2*m
      box = (self.x0-m, self.y0-h+m, w, h)
      mapping.set_mapping_bars(self.id, m_points, m_bars, box)
      return
    cr.save()
    cr.translate(x0, y0)
    cr.scale(scale, scale)
    for bar in names:
      node1 = bars[bar][0]
      node2 = bars[bar][1]
      try:
        x1, y1 = nodes[node1]
        x2, y2 = nodes[node2]
      except ValueError: # undifinied points
        continue
      y1 = -y1
      y2 = -y2
      x1_d, y1_d = cr.user_to_device(x1, y1)
      x2_d, y2_d = cr.user_to_device(x2, y2)
      m_bars[bar] = (x1_d, y1_d, x2_d, y2_d)
      if not node1 in m_points:
        m_points[node1] = (x1_d, y1_d)
      if not node2 in m_points:
        m_points[node2] = (x2_d, y2_d)
    for node in not_linked:
      try:
        x, y = not_linked[node]
      except ValueError:
        continue
      y = -y
      x_d, y_d = cr.user_to_device(x, y)
      m_points[node] = (x_d, y_d)

    arcs = struct.Curves
    centers = struct.Centers
    for name in arcs:
      arc = arcs[name]
      li_nodes = arc.user_nodes
      for Node in li_nodes:
        node = Node.name
        x, y = nodes[node]
        y = -y
        if not node in m_points:
          x_d, y_d = cr.user_to_device(x, y)
          m_points[node] = (x_d, y_d)
      if isinstance(arc, classRdm.Parabola):
        N0 = li_nodes[0].name
        N1 = li_nodes[-1].name
        mapping.set_mapping_para(cr, scale, name, arc, self.id, nodes[N0], nodes[N1])
      elif isinstance(arc, classRdm.Arc):
        mapping.set_mapping_arc(cr, scale, name, arc, self.id, centers)

    cr.restore()
    w_struct, h_struct = struct.width*scale, struct.height*scale
    if h_struct == 0: # horizontal
      w, h = w_struct+2*m, 3.2*m
      x, y = self.x0-m, self.y0-h+1.5*m
    else:
      w, h = w_struct+2.2*m, h_struct+2*m
      x, y = self.x0-m, self.y0-h+m
    box = (x, y, w, h)
    mapping.set_mapping_bars(self.id, m_points, m_bars, box)

  def _draw_scale(self, study, cr, x, y, scale, influ_status=None):
    """Calcule le format de l'échelle et effectue son tracé
    """
    rdm = study.rdm
    unit_conv = rdm.struct.units
    if self.status in [0, 1, 2, 3, 7]:
      unit_name = study.get_unit_name('L')
      unit = unit_conv['L']
    elif self.status in [4, 5]:
      unit_name = study.get_unit_name('F')
      unit = unit_conv['F']
    elif self.status == 6:
      unit_F = study.get_unit_name('F')
      unit_L = study.get_unit_name('L')
      unit_name = '%s.%s' % (unit_F, unit_L)
      unit = unit_conv['L']*unit_conv['F']
    elif self.status == 8:
      if influ_status == 2:
        unit_F = study.get_unit_name('F')
        unit_L = study.get_unit_name('L')
        unit_name = '%s.%s' % (unit_F, unit_L)
        unit = unit_conv['L']*unit_conv['F']
      elif influ_status == 3:
        unit_name = study.get_unit_name('L')
        unit = unit_conv['L']
      else:
        unit_name = study.get_unit_name('F')
        unit = unit_conv['F']
    SCALE = Const.SCALE # 100 px
    u = scale*SCALE/unit
    if u < 1e-12: # vérifier critère XXX
      return 0, 0
    exp = int(math.log(u, 10))
    u0 = float('1e%s' % (exp-1))
    long = u0/u
    if long > 1:
      print("debug::_draw_scale -> ne devrait pas être > 1")
    if long < 0.02:
      long *= 50
      u0 *= 50
    if long < 0.05:
      long *= 20
      u0 *= 20
    elif long < 0.1:
      long *= 10
      u0 *= 10
    elif long < 0.2:
      long *= 5
      u0 *= 5
    elif long < 0.4:
      long *= 2
      u0 *= 2
    long *= SCALE
    value = function.PrintValue(u0, 1, True)
    text = '%s %s' % (value, unit_name)

    cr.save()
    cr.set_line_width(3)
    cr.set_font_size(Const.FONT_SIZE)
    self._fg.set_color_by_name(cr, "grey")
    cr.translate(x, y)
    cr.move_to(0, 0)
    cr.rel_line_to(long, 0)
    cr.stroke()
    x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
    cr.move_to(long/2-width/2, -8)
    cr.show_text(text)
    cr.restore()
    return long, 25


  def _draw_axis(self, cr, x, y, angle, scale):
    """Dessine le repère sur la barre"""
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.move_to(0, -5/scale)
    cr.rel_line_to(12/scale, 0)
    cr.stroke()
    cr.move_to(0, -5/scale)
    cr.rel_line_to(0, -12/scale)
    cr.stroke()
    cr.restore()

  def _draw_relax(self, cr, x0, y0, struct, scale, color=None):
    if scale is None:
      return
    try:
      relaxed = struct.IsRelax
    except AttributeError:
      relaxed = {}
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x0, y0)
    cr.scale(scale, scale)
    # relaxation sur les noeuds
    for noeud in relaxed:
      if not relaxed.get(noeud) == 1:
        continue
      x, y = struct.Nodes[noeud]
      self._draw_one_relax(cr, x, y, scale, False)
    cr.restore()

    # relaxation sur les barres
    barre_name = list(struct.UserBars)
    barres = struct.Barres
    arcs = struct.Curves
    # ajout barres des arcs
    for name in arcs:
      arc = arcs[name]
      name0, name1 = arc.b0, arc.b1
      r0 = barres[name0][2]
      r1 = barres[name1][3]
      if r0 == 1:
        barre_name.append(name0)
      if r1 == 1:
        barre_name.append(name1)
    for barre in barre_name:
      angle = -struct.Angles[barre]
      pt1, pt2, rel1, rel2 = barres[barre]
      if rel1 == 1 and not pt1 in relaxed:
        x1, y1 = struct.Nodes[pt1]
        cr.save()
        cr.translate(x0+x1*scale, y0-y1*scale)
        cr.scale(scale, scale)
        cr.rotate(angle)
        self._draw_one_relax(cr, 12/scale, 0, scale, False)
        cr.restore()
      if rel2 == 1 and not pt2 in relaxed:
        x2, y2 = struct.Nodes[pt2]
        cr.save()
        cr.translate(x0+x2*scale, y0-y2*scale)
        cr.scale(scale, scale)
        cr.rotate(angle)
        self._draw_one_relax(cr, -12/scale, 0, scale, False)
        cr.restore()

    # rotules élastiques
    try:
      rotules = struct.RotuleElast
    except AttributeError:
      rotules = {}
    for noeud in rotules:
      n_barre = struct.BarByNode.get(noeud, 2)
      x, y = struct.Nodes[noeud]
      if len(n_barre) >= 3:
        barre = rotules[noeud][0]
        pt1, pt2, rel1, rel2 = struct.Barres[barre]
        if pt1 == noeud:
          delta = 12/scale
        else:
          delta = -12/scale
        angle = -struct.Angles[barre]
        cr.save()
        cr.translate(x0+x*scale, y0-y*scale)
        cr.scale(scale, scale)
        cr.rotate(angle)
        self._draw_one_relax(cr, delta, 0, scale, True)
        cr.restore()
      else:
        cr.save()
        cr.translate(x0, y0)
        cr.scale(scale, scale)
        self._draw_one_relax(cr, x, y, scale, True)
        cr.restore()



  def _draw_one_relax(self, cr, x, y, scale, fill=True, color=None):
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.arc(x, -y, 6/scale, 0, 2*math.pi)
    cr.fill()
    cr.stroke()
    cr.restore()
    if fill:
      return

    # white bg
    cr.save()
    cr.set_source_rgb(1, 1, 1)
    cr.arc(x, -y, 5/scale, 0, 2*math.pi)
    #print(max(cr.user_to_device_distance(1, 1)))
    cr.fill()
    cr.stroke()
    cr.restore()



  def _draw_node_name(self, cr, x, y, name, scale, angle=0):
    """Ecrit le nom du noeud"""
    cr.save()
    cr.translate(x+15/scale, y+20/scale)
    if angle:
      cr.rotate(angle)
    cr.set_font_size(Const.FONT_SIZE/scale)
    cr.move_to(0, 0)
    cr.show_text(name)
    cr.stroke()
    cr.restore()

  def _draw_bar_name(self, cr, x, y, name, angle, scale):
    """Ecrit le nom du noeud"""
    #if isinstance(name, int): # XXX debug
    #  return
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    #h = 12. / scale
    cr.set_font_size(Const.FONT_SIZE/scale)
    x_bearing, y_bearing, width, height = cr.text_extents(name)[:4]
    cr.move_to(- width / 2, 2*height)
    cr.show_text(name)
    cr.restore()

  def _draw_bind(self, cr, x0, y0, struct, struct_scale, color=None):
    """Méthode de tracé de l'ensemble des liaisons de la structure"""
    if struct_scale is None:
      return
    if color is None:
      color = 'blue'
    try:
      liaisons = struct.Liaisons
    except AttributeError:
      return
    for noeud, liaison in liaisons.items(): 
      try:
        pt = struct.Nodes[noeud]
      except KeyError:
        continue
      try:
        x, y = pt
      except ValueError:
        continue
      _color = color
      if not self.status == 8 and noeud in struct.NodeDeps:
        _color = "red"
      if liaison == 0:
        angle = self._get_clumping_angle(struct, noeud)
        self._draw_clumping(cr, x0, y0, x, y, struct_scale, angle, _color)
      elif liaison == 1:
        if struct.IsRelax.get(noeud) == 1:
          y = y - 6/struct_scale
        self._draw_hinge(cr, x0, y0, x, y, struct_scale, _color)
      elif liaison == 2:
        teta = 0.
        relax = False
        if noeud in struct.AppuiIncline:
          teta = -struct.AppuiIncline[noeud]
        if struct.IsRelax.get(noeud) == 1:
          relax = True
        self._draw_simple_support(cr, x0, y0, x, y, struct_scale, teta, relax, _color)
      elif liaison == 3:
        self._draw_elastic_support(cr, x0, y0, x, y, struct_scale, _color)

  def _get_clumping_angle(self, struct, noeud):
    """Calcule l'angle de la barre dont l'une des extrémité est un encastrement
    retourne un angle"""
    li = struct.BarByNode[noeud]
    for elem in li:
      if len(elem) == 0:
        continue
      barre = elem[0]
      break
    alpha = struct.Angles[barre]
    if alpha < 0:
      alpha += 3.14
    return -alpha + math.pi / 2

  def _draw_clumping(self, cr, x0, y0, x, y, scale, angle=0, color=None):
    """Dessin d'un encastrement"""
    x = x * scale
    y = -y * scale
    cr.save()
    cr.set_line_width(1)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x0 + x, y0 + y)
    cr.rotate(angle) 
    cr.move_to(-10, 0)
    cr.rel_line_to(21, 0)
    cr.stroke()

    for i in range(5):
      cr.move_to(-9+5*i, 0)
      cr.rel_line_to(10, 10)
      cr.stroke()
    cr.restore()

  def _draw_simple_support(self, cr, x0, y0, x, y, scale, angle=0, relax=False, color=None):
    """Dessin d'un appui simple"""
    if relax:
      x = x - 6/scale*math.sin(angle)
      y = y - 6/scale*math.cos(angle)
    x = x * scale
    y = -y * scale
    cr.save()
    cr.set_line_width(1)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x0+x, y0+y)
    cr.rotate(angle)
    cr.move_to(0, 0)
    cr.rel_line_to(-7, 12)
    cr.rel_line_to(14, 0)
    cr.close_path()
    cr.stroke()

    cr.arc(-4, 15, 3, 0, 2*math.pi)
    cr.stroke()
    cr.arc(4, 15, 3, 0, 2*math.pi)
    cr.stroke()

    cr.move_to(-11, +18)
    cr.rel_line_to(22, 0)
    cr.stroke()

    for i in range(6):
      cr.move_to(-9+4*i, 18)
      cr.rel_line_to(-5, 5)
      cr.stroke()
    cr.restore()

  def _draw_hinge(self, cr, x0, y0, x, y, scale, color=None):
    """Dessin d'une articulation"""
    x = x * scale
    y = -y * scale
    cr.save()
    cr.set_line_width(1)
    cr.translate(x0 + x, y0 + y)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.move_to(0, 0)
    cr.rel_line_to(-10, 18)
    cr.rel_line_to(20, 0)
    cr.close_path()
    cr.stroke()
    for i in range(6):
      cr.move_to(-9+4*i, 18)
      cr.rel_line_to(-5, 5)
      cr.stroke()
    cr.restore()

  def _draw_elastic_support(self, cr, x0, y0, x, y, scale, color=None):
    """Dessine les appuis élastiques"""

    def one(cr, x, y):
      cr.move_to(x, y)
      cr.rel_curve_to(5, 5, 15, 4, 20, -2)
      cr.stroke()

    x = x * scale
    y = -y * scale
    cr.save()
    cr.set_line_width(1)
    cr.translate(x0 + x, y0 + y)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    for i in range(5):
      one(cr, -10, 4*i+4)
    cr.restore()

  def _draw_cross(self, cr, x, y, factor):
    size = 4./factor
    cr.move_to(x-size, y-size)
    cr.rel_line_to(2*size, 2*size)
    cr.stroke()
    cr.move_to(x+size, y-size)
    cr.rel_line_to(-2*size, 2*size)
    cr.stroke()




# ------------------- DESSIN DU CHARGEMENT -------------------------

  def _draw_char_therm(self, cr, x0, y0, barre, rdm, struct_scale, nodes=None, size=15):
    """Fonction de dessin du chargement thermique"""
    size = size/struct_scale
    angleBarre = -rdm.struct.Angles[barre]
    l = rdm.struct.Lengths[barre]
    if nodes is None:
      nodes = rdm.struct.Nodes
    x, y = nodes[rdm.struct.Barres[barre][0]]
    cr.save()
    #cr.set_line_width(1/struct_scale)
    cr.translate(x0 + x*struct_scale, y0 - y*struct_scale)
    cr.rotate(angleBarre)
    cr.scale(struct_scale, struct_scale)
    cr.translate(l/2, -0.666*size)
    self._draw_sun(cr, size)
    cr.restore()


  def _draw_arc_char_therm(self, cr, x0, y0, struct_scale, rdm, name, size=15):
    """Dessine le chargement thermique sur un arc"""
    size = size/struct_scale
    struct = rdm.struct
    nodes = struct.Nodes
    arc = struct.Curves[name]
    cr.save()
    if isinstance(arc, classRdm.Parabola):
      user_nodes = arc.user_nodes
      l, f = arc.l, arc.f
      N0 = user_nodes[0].name
      x, y = nodes[N0]
      angle = -arc.a
      cr.translate(x0 + x*struct_scale, y0 - y*struct_scale)
      cr.rotate(angle)
      cr.scale(struct_scale, struct_scale)
      cr.translate(l/2, -0.666*size-f)
    else:
      C = arc.c
      teta1, teta2 = arc.teta1, arc.teta2
      dteta = teta1-teta2
      if dteta <= 0:
        dteta += 6.29
      x, y = struct.Centers[C]
      cr.translate(x0 + x*struct_scale, y0 - y*struct_scale)
      cr.rotate(-dteta/2)
      cr.scale(struct_scale, struct_scale)
      cr.translate(arc.r+0.666*size, 0)
    self._draw_sun(cr, size)
    cr.restore()

  def _draw_arc_char_fp(self, cr, X0, Y0, struct_scale, rdm, name, arc_char, size=15):
    """Dessine une charge ponctuelle sur un arc"""
    arrow_size = Const.ARROW_SIZE_MAX
    values = arc_char.values
    struct = rdm.struct
    unit_conv = struct.units
    Arc = struct.Curves[name]
    l_arc = Arc.get_size()
    barres = struct.Barres
    nodes = struct.Nodes
    angles = struct.Angles
    # recherche maxi
    maxi = 0
    for b, du, fpx, fpy, mz in values.values():
      norme = fpx**2+fpy**2
      if norme > maxi:
        maxi = norme
    maxi = maxi**0.5
    legends = []
    cr.save()
    cr.translate(X0 , Y0)
    e = 3
    for alpha in values:
      b, du, fpx, fpy, mz = values[alpha]
      norme = (fpx**2+fpy**2)**0.5
      N0 = barres[b][0]
      a = angles[b]
      x0, y0 = nodes[N0]
      N1 = barres[b][1]
      x1, y1 = nodes[N1]
      dx, dy = du*(x1-x0), du*(y1-y0)
      if not norme == 0:
        ex, ey = -e*math.sin(a), -e*math.cos(a)
        size = max(arrow_size*norme/maxi, arrow_size/2)
        translate = fpy >= 0 and True or False
        angle = function.get_vector_angle((0, 0), (fpx, fpy))
        text = function.PrintValue(norme, unit_conv['F'])
        xlegend, ylegend = self._draw_arrow3(cr, (x0+dx)*struct_scale+ex , -(y0+dy)*struct_scale+ey, size, angle, translate=translate, width=3, end_device_coors=True, color='green')
        legends.append((xlegend, ylegend-15, text))
      if not mz == 0:
        xlegend, ylegend = self._draw_moment(cr, (x0+dx)*struct_scale , -(y0+dy)*struct_scale, radius=20, end=3.1, middle=True, color='green')
        text = function.PrintValue(mz, unit_conv['F'])
        legends.append((xlegend, ylegend, text))
    #print(cr.get_matrix())
    cr.restore()
    cr.save()
    cr.set_font_size(Const.FONT_SIZE)
    #print(cr.get_font_matrix())
    for tu in legends:
      xd, yd, text = tu
      self.mapping.extend_box(self.id, xd, yd-25)
      self._draw_arrow_legend(cr, text, xd, yd, color='green') 
    cr.restore()

  def _draw_arc_char0(self, cr, X0, Y0, struct_scale, rdm, name, arc_char, color=None):
    """Dessin d'une charge linéique sur un arc (type poids propre)"""
    #print("_draw_arc_char0")
    arrow_size = Const.ARROW_SIZE_MAX
    struct = rdm.struct
    unit_conv = struct.units
    Arc = struct.Curves[name]
    l_arc = Arc.get_size()
    barres = struct.Barres
    angles = struct.Angles
    lengths = struct.Lengths
    points = arc_char.points
    values = arc_char.values
    maxi = 0
    for qx0, qy0, qx1, qy1 in values.values():
      norme = qx0**2+qy0**2
      if norme > maxi:
        maxi = norme
      norme = qx1**2+qy1**2
      if norme > maxi:
        maxi = norme
    maxi = maxi**0.5
    if maxi < 1e-8: # XXX
      return
    arc_barres = arc_char.barres
    if 0. in arc_barres:
      n = 1
    else:
      n = 2
    texts_coors, texts = [], []
    prec_pos = points[n-1]
    prec_b, prec_u = arc_barres[prec_pos]
    #print(cr.get_matrix())
    cr.save()
    cr.set_line_width(1)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    #print( "arc_barres=", arc_barres)
    for pos in points[n:]:
      if not pos in arc_barres:
        break
      b, u = arc_barres[pos]
      qx0, qy0 = values[prec_pos][2:]
      qx1, qy1 = values[pos][0:2]
      if b == prec_b:
        l = u-prec_u
      else:
        l = lengths[prec_b]-prec_u + u
        for barre in range(prec_b+1, b):
          l += lengths[barre]
      n_arrows = int(l*struct_scale / 30)
      if n_arrows == 0:
        pas = l+10 # évite de tracer deux flèches trop proches
      else:
        pas = l/n_arrows

      N0 = barres[prec_b][0]
      x0, y0 = struct.Nodes[N0]
      a = angles[prec_b]
      x = x0+prec_u*math.cos(a)
      y = y0+prec_u*math.sin(a)
      translate = qy0 >= 0 and True or False
      norme0 = (qx0**2+qy0**2)**0.5
      norme1 = (qx1**2+qy1**2)**0.5
      if norme0 == 0 and norme1 == 0:
        prec_pos = pos
        prec_b, prec_u = b, u
        continue
      if norme0 == norme1:
        text0 = function.PrintValue(norme0, unit_conv['F'])
        texts.append(text0)
        texts_size = 1
      else:
        text0 = function.PrintValue(norme0, unit_conv['F'])
        text1 = function.PrintValue(norme1, unit_conv['F'])
        texts.append(text0)
        texts.append(text1)
        texts_size = 2
      angle = function.get_vector_angle((0, 0), (qx0, qy0))
      size0 = arrow_size*norme0/maxi
      size1 = arrow_size*norme1/maxi
      cr.save()
      cr.translate(X0 , Y0)
      device = self._draw_arrow3(cr, x*struct_scale , -y*struct_scale-2, size0, angle, translate=translate, width=3, end_device_coors=True)
      if texts_size == 2 and not device is None:
        xd, yd = device
        texts_coors.append((xd, yd, prec_b))
      s = l = lengths[prec_b]-prec_u
      l0 = (pos-prec_pos)*l_arc
      mid_b = int((prec_b+b)/2)
      for barre in range(prec_b+1, b+1):
        dl = lengths[barre]
        if barre == mid_b and texts_size == 1:
          if not device is None:
            xd, yd = device
            texts_coors.append((xd, yd, barre))
        if s+dl+1e-10 <= pas:
          s += dl
          l += dl
          continue
        qx = qx0 + (qx1-qx0)/l0*l
        qy = qy0 + (qy1-qy0)/l0*l
        norme = (qx**2+qy**2)**0.5
        size = arrow_size*norme/maxi
        angle = function.get_vector_angle((0, 0), (qx, qy))
        translate = qy >= 0 and True or False
        du = pas-s
        if du < 0:
          print("Unexpected pas in _draw_arc_char0")
          du = 0
        N0 = barres[barre][0]
        x0, y0 = struct.Nodes[N0]
        a = angles[barre]
        x = x0+du*math.cos(a)
        y = y0+du*math.sin(a)
        device = self._draw_arrow3(cr, x*struct_scale , -y*struct_scale-2, size, angle, translate=translate, width=3, end_device_coors=True)
        s = dl-du
        l += dl
      cr.restore()
      prec_pos = pos
      prec_b, prec_u = b, u
      if texts_size == 2:
        if not device is None:
          xd, yd = device
          texts_coors.append((xd, yd, barre))
    cr.restore()
    i = 0
    for xd, yd, barre in texts_coors:
      a = -angles[barre]
      text = texts[i]
      self._draw_arrow_legend(cr, text, xd, yd, angle=a, decalage=10, color=color)
      i += 1


  def _draw_arc_char1(self, cr, X0, Y0, struct_scale, rdm, arc, arc_char, color=None):
    """Dessin d'une charge projetée sur un arc"""
    arrow_size = Const.ARROW_SIZE_MAX
    struct = rdm.struct
    unit_conv = struct.units
    barres = struct.Barres
    nodes = struct.Nodes
    angles = struct.Angles
    points = arc_char.points
    values = arc_char.values
    maxi = 0
    for qx0, qy0, qx1, qy1 in values.values():
      norme = qx0**2+qy0**2
      if norme > maxi:
        maxi = norme
      norme = qx1**2+qy1**2
      if norme > maxi:
        maxi = norme
    maxi = maxi**0.5
    if maxi < 1e-8: # XXX
      return
    arc_barres = arc_char.barres
    if 0. in arc_barres:
      n = 1
    else:
      n = 2
    texts_coors, texts = [], []
    prec_pos = points[n-1]
    prec_b, prec_u = arc_barres[prec_pos]
    cr.save()
    cr.set_line_width(1)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    for pos in points[n:]:
      if not pos in arc_barres:
        break
      b, u = arc_barres[pos]
      qx0, qy0 = values[prec_pos][2:]
      qx1, qy1 = values[pos][0:2]
      norme0 = (qx0**2+qy0**2)**0.5
      norme1 = (qx1**2+qy1**2)**0.5
      if norme0 == 0 and norme1 == 0:
        prec_pos = pos
        prec_b, prec_u = b, u
        continue
      if norme0 == norme1:
        text0 = function.PrintValue(norme0, unit_conv['F'])
        texts.append(text0)
        texts_size = 1
      else:
        text0 = function.PrintValue(norme0, unit_conv['F'])
        text1 = function.PrintValue(norme1, unit_conv['F'])
        texts.append(text0)
        texts.append(text1)
        texts_size = 2
      N0 = barres[prec_b][0]
      N1 = barres[b][0]
      x0, y0 = nodes[N0]
      a0 = angles[prec_b]
      x0 += prec_u*math.cos(a0)
      a1 = angles[b]
      x1, y1 = nodes[N1]
      x1 += u*math.cos(a1)
      x0, y0 = x0*struct_scale, y0*struct_scale
      x1, y1 = x1*struct_scale, y1*struct_scale
      if b - prec_b > 8:
        middle = int((prec_b + b)/2)
        xm, ym = nodes[middle]
        xm, ym = xm*struct_scale, ym*struct_scale
      else:
        xm, ym = x1, y1
      cr.save()
      cr.translate(X0 + x0, Y0 - y0)
      l = x1-x0
      n_arrows = int(l / 20)
      if n_arrows == 0:
        pas = l
      else:
        pas = l/n_arrows
      if y1 >= y0 or ym >= y0:
        dy = max(y1-y0, ym-y0)
        dy = -dy-arrow_size
      else:
        dy = -arrow_size
      translate = qy0 >= 0 and True or False
      norme0 = (qx0**2+qy0**2)**0.5
      norme1 = (qx1**2+qy1**2)**0.5
      text = function.PrintValue(norme0, unit_conv['F'])
      a0 = function.get_vector_angle((0, 0), (qx0, qy0))
      a1 = function.get_vector_angle((0, 0), (qx1, qy1))
      s = 0
      mid = int(n_arrows/2)
      for i in range(n_arrows+1):
        size = norme0 + (norme1-norme0)/l*s
        size = size*arrow_size/maxi
        a = a0 + (a1-a0)/l*s
        x, y = self._draw_arrow3(cr, s, dy, size, a, translate=translate, width=3, end_device_coors=True)

        if (i == 0 or i == n_arrows) and texts_size == 2:
          texts_coors.append((x, y))
        elif i == mid and texts_size == 1:
          texts_coors.append((x, y))
        s += pas
      cr.set_antialias(cairo.ANTIALIAS_NONE)
      cr.move_to(0, dy)
      cr.rel_line_to(l, 0)
      cr.stroke()
      #cr.arc(0, dy, 2, 0, 2*math.pi)
      #cr.stroke()
      xd, yd = cr.user_to_device(l/2, 0)
      cr.restore()
      self.mapping.extend_box(self.id, x, y-25)
      prec_pos = pos
      prec_b, prec_u = b, u
    cr.restore()
    i = 0
    for xd, yd in texts_coors:
      text = texts[i]
      self._draw_arrow_legend(cr, text, xd, yd-15, color=color) 
      i += 1

  def _draw_arc_char2(self, cr, X0, Y0, struct_scale, rdm, name, arc_char, color=None):
    """Dessin d'une charge radiale sur un arc"""
    arrow_size = Const.ARROW_SIZE_MAX
    struct = rdm.struct
    unit_conv = struct.units
    Arc = struct.Curves[name]
    l_arc = Arc.get_size()
    barres = struct.Barres
    angles = struct.Angles
    lengths = struct.Lengths
    points = arc_char.points
    values = arc_char.values
    maxi = 0
    for qx0, q0, qx1, q1 in values.values():
      if abs(q0) > maxi:
        maxi = abs(q0)
      if abs(q1) > maxi:
        maxi = abs(q1)
    if maxi < 1e-8: # XXX
      return
    arc_barres = arc_char.barres
    if 0. in arc_barres:
      n = 1
    else:
      n = 2
    texts_coors, texts = [], []
    prec_pos = points[n-1]
    prec_b, prec_u = arc_barres[prec_pos]
    cr.save()
    cr.set_line_width(1)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    for pos in points[n:]:
      if not pos in arc_barres:
        break
      b, u = arc_barres[pos]
      qx0, q0 = values[prec_pos][2:]
      qx1, q1 = values[pos][0:2]
      # qx0, qx1 nuls !!
      if q0 == 0 and q1 == 0:
        prec_pos = pos
        prec_b, prec_u = b, u
        continue
      if q0 == q1:
        text0 = function.PrintValue(q0, unit_conv['F'])
        texts.append(text0)
        texts_size = 1
      else:
        text0 = function.PrintValue(q0, unit_conv['F'])
        text1 = function.PrintValue(q1, unit_conv['F'])
        texts.append(text0)
        texts.append(text1)
        texts_size = 2
      N0 = barres[prec_b][0]
      if prec_b == b:
        l = u-prec_u
      else:
        l = lengths[prec_b]-prec_u + u
        for barre in range(prec_b+1, b):
          l += lengths[barre]
      n_arrows = int(l*struct_scale / 30)
      if n_arrows == 0:
        pas = l+10 # évite de tracer deux flèches trop proches
      else:
        pas = l/n_arrows
      N0 = barres[prec_b][0]
      x0, y0 = struct.Nodes[N0]
      cr.save()
      cr.translate(X0 + x0, Y0 - y0)
      a = angles[prec_b]
      x =  x0+prec_u*math.cos(a)
      y =  y0+prec_u*math.sin(a)
      translate = q0 >= 0 and True or False
      if q0 < 0:
        da = -1.5707
      else:
        da = 1.5707
      q = abs(arrow_size*q0/maxi)
      device = self._draw_arrow3(cr, x*struct_scale , -y*struct_scale, q, a+da, translate=translate, width=3, end_device_coors=True)
      if texts_size == 2 and not device is None:
        xd, yd = device
        texts_coors.append((xd, yd, prec_b))
      s = l = lengths[prec_b]-prec_u
      l0 = (pos-prec_pos)*l_arc
      mid_b = int((prec_b+b)/2)
      for barre in range(prec_b+1, b+1):
        dl = lengths[barre]
        if barre == mid_b and texts_size == 1:
          if not device is None:
            xd, yd = device
            texts_coors.append((xd, yd, barre))
        if s+dl+1e-10 <= pas: # évite un pb numérique
          s += dl
          l += dl
          continue
        du = pas-s
        if du < 0:
          print("Unexpected pas in _draw_arc_char2")
          du = 0
        N0 = barres[barre][0]
        x0, y0 = struct.Nodes[N0]
        a = angles[barre] # prendre moyenne??
        x = x0+du*math.cos(a)
        y = y0+du*math.sin(a)
        q = q0 + (q1-q0)/l0*l
        translate = q >= 0 and True or False
        if q < 0:
          da = -1.5707
        else:
          da = 1.5707
        q = abs(arrow_size*q/maxi)
        device = self._draw_arrow3(cr, x*struct_scale , -y*struct_scale, q, a+da, translate=translate, width=3, end_device_coors=True)
        s = dl-du
        l += dl
      cr.restore()
      prec_pos = pos
      prec_b, prec_u = b, u
      if texts_size == 2:
        if not device is None:
          xd, yd = device
          texts_coors.append((xd, yd, barre))
    cr.restore()
    i = 0
    for xd, yd, barre in texts_coors:
      a = -angles[barre]
      text = texts[i]
      self._draw_arrow_legend(cr, text, xd, yd, angle=a, decalage=10, color=color)
      i += 1



# déplacer
  def _draw_arrow3(self, cr, x, y, size, angle=0, translate=False, width=3, color=None, end_device_coors=False):
    """Dessin d'une flèche au point x, y : si translate, la base de la flèche est positionnée en x, y, sinon pointe flèche en x, y"""
    if angle is None:
      return


    #cr.save()
    #cr.arc(x, y, 2, 0, 2*math.pi)
    #cr.stroke()
    #pt = cr.user_to_device(-size, 0)
    #cr.restore()
    #return pt


    cr.save()
    cr.set_line_width(width)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x, y)
    if not angle == 0:
      cr.rotate(-angle)
    if translate:
      cr.translate(size, 0)
    # axis
    cr.move_to(-size, 0)
    cr.rel_line_to(size-1, 0)
    cr.stroke()
    # arrow
    if size > 9:
      cr.move_to(0, 0)
      cr.rel_line_to(-9, -7)
      cr.rel_line_to(0, 14)
      cr.close_path()
      cr.fill()
      cr.stroke()
    if not end_device_coors:
      cr.restore()
      return
    if translate:
      pt = cr.user_to_device(0, 0)
      cr.restore()
      return pt
    pt = cr.user_to_device(-size, 0)
    cr.restore()
    return pt


  def _draw_char_bar_fp(self, cr, x0, y0, barre, study, char, struct_scale, nodes=None, color=None):
    """Dessine le chargement de type force dur les barres"""
    rdm = study.rdm
    unit_conv = rdm.struct.units
    angleBarre = -rdm.struct.Angles[barre]
    l = rdm.struct.Lengths[barre]
    if nodes is None:
      nodes = rdm.struct.Nodes
    x, y = nodes[rdm.struct.Barres[barre][0]]
    if char == {}:
      return
    cr.save()
    cr.set_font_size(Const.FONT_SIZE)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.save()
    cr.translate(x0 + x*struct_scale, y0 - y*struct_scale)
    cr.rotate(angleBarre)
    #cr.scale(struct_scale, struct_scale)
    arrow_size = Const.ARROW_SIZE_MAX

    legends = []
    for alpha, char in char.items():
      u = alpha*l*struct_scale
      fpu = char[0]
      fpv = char[1]
      mirror = fpv >= 0 and True or False
      dy = -5 # décalage de l'axe de la barre
     
      mz = char[2]
      norme = (fpu**2+fpv**2)**0.5
      if not norme == 0:
        angle = -function.get_vector_angle((0, 0), char)
        text = function.PrintValue(norme, unit_conv['F'])
        xlegend, ylegend = self._draw_arrow(cr, u, dy, arrow_size,
		angle, mirror=mirror)
        legends.append((xlegend, ylegend, text))
      if not mz == 0:
        xlegend, ylegend = self._draw_moment(cr, u, 0, radius=20, end=3.1, middle=True)
        text = function.PrintValue(mz, unit_conv['F'])
        legends.append((xlegend, ylegend, text))

    cr.restore()
    for tu in legends:
      xd, yd, text = tu
      self.mapping.extend_box(self.id, xd, yd-25)
      self._draw_arrow_legend(cr, text, xd, yd, color=color) 
    cr.restore()

  def _draw_char_node(self, cr, x, y, study, char, color=None):
    """Dessine le chargement de type force dur les barres"""
    rdm = study.rdm
    unit_conv = rdm.struct.units
    cr.save()
    cr.set_font_size(Const.FONT_SIZE)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.save()
    cr.translate(x, y)
    #print(cr.user_to_device(0, 0))
    #cr.scale(struct_scale, struct_scale)

    fx = char[0]
    fy = char[1]
    mirror = fy >= 0 and True or False
   
    mz = char[2]
    norme = (fx**2+fy**2)**0.5
    arrow_size = Const.ARROW_SIZE_MAX
    legends = []
    if not norme == 0:
      angle = -function.get_vector_angle((0, 0), (fx, fy))

      dx, dy = -5 * math.cos(angle), -5 * math.sin(angle)
      if mirror:
        dx, dy = -dx, -dy
      # décalage de l'axe de la barre
      text = function.PrintValue(norme, unit_conv['F'])
      xlegend, ylegend = self._draw_arrow(cr, dx, dy, arrow_size,
			angle, mirror=mirror)
      legends.append((xlegend, ylegend, text))
    if not mz == 0:
      text = function.PrintValue(mz, unit_conv['F'])
      xlegend, ylegend = self._draw_moment(cr, 0, 0, radius=20, end=3.1, middle=True)
      legends.append((xlegend, ylegend, text))
    cr.restore()
    for tu in legends:
      xd, yd, text = tu
      self.mapping.extend_box(self.id, xd, yd-25)
      self._draw_arrow_legend(cr, text, xd, yd, color=color) 
    cr.restore()



# enlever struct_scale XXX

# bug avec les charges triangulaires dans le cas d'un changement d'unité de longueur. Pour ces dernières les valeurs sont données en N et non pas en N/m pour les charges qu. 

  def _draw_char_bar_q(self, cr, x0, y0, barre, struct_scale, chars, qmax, study, nodes=None, color=None):
    """Dessine le chargement de type force qu sur la barre"""
    crit = 1e-8
    rdm = study.rdm
    unit_conv = rdm.struct.units
    dim = Const.ARROW_SIZE_MAX # paramètre longueur flèche 
    angleBarre = -rdm.struct.Angles[barre]
    l = rdm.struct.Lengths[barre]
    if nodes is None:
      nodes = rdm.struct.Nodes
    x, y = nodes[rdm.struct.Barres[barre][0]]

    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x0 + x*struct_scale, y0 - y*struct_scale)
    cr.rotate(angleBarre)
    cr.scale(struct_scale, struct_scale)
    # longueur de la barre en px
    l_px = l * struct_scale
    # arrow width = 0.5px * dim (paramétrable)
    arrow_scale = dim / struct_scale
    # nombre de flèche sur la barre
    n_arrows = int(l_px / (0.5 * dim * 1.5)) + 1
    dy = -5/struct_scale # décalage de l'axe de la barre

    a0 = 0
    li = list(chars.keys())
    li.sort()
    for i, a1 in enumerate(li):
      tu = chars[a1]
      if i == 0:
        qu_prec, qv_prec = tu[1]
        a0 = a1
        continue
      qu, qv = tu[0]
      #print("a1=", a1, qv, qv_prec)
      dqu = qu-qu_prec
      dqv = qv-qv_prec
      if abs(qv) < crit and abs(qu) < crit and abs(dqv) < crit \
			and abs(dqu) < crit:
        qu_prec, qv_prec = tu[1]
        a0 = a1
        continue
      # si qv et qv_prec de signe différent, chercher point nul
      brisure = False
      if qv*qv_prec < 0:
        brisure = True
        x_bris = -qv_prec*(a1-a0)/(qv-qv_prec)+a0

      # nombre de flèches par intervale
      n = int((a1-a0)*n_arrows)
      # écartement entre flèche
      delta_x = (a1-a0)/(n+1)

      for j in range(n+2):
        pas = a0 + j*delta_x
        qx = qu_prec + dqu/(n+1)*j
        qy = qv_prec + dqv/(n+1)*j
        # hauteur de flèche variable
        height = (qx**2+qy**2)**0.5 / qmax
        if height < crit:
          height = 0
        mirror = qy >= 0 and True or False
        # attention l'angle peut varier pour chaque flèche si qu diff 0
        angle = function.get_vector_angle((0, 0), (qx, qy))
        if angle is None:
          angle = 0 # evite un bug
        angle  = -angle
        if mirror:
          angle += math.pi
        self._draw_arrow2(cr, pas*l, dy, struct_scale, 
		arrow_scale, angle, mirror=mirror, height=height, width=1)
        if j == 0:
          text1 = function.PrintValue(height*qmax, unit_conv['F']/unit_conv['L'])
          pt1 = (pas*l, dy, height, angle)
        elif j == n+1:
          text2 = function.PrintValue(height*qmax, unit_conv['F']/unit_conv['L'])
          pt2 = (pas*l, dy, height, angle)
      # dessin ligne attache et de la légende
      if brisure:
        pt3 = (x_bris*l, dy, 0, 0)
        texts = ((text1, 0), )
        self._draw_qu_attache(cr, pt1, pt3, struct_scale, 
		arrow_scale, texts=texts)
        texts = ((text2, 1), )
        self._draw_qu_attache(cr, pt3, pt2, struct_scale, 
		arrow_scale, texts=texts)
      else:
        if text1 == text2:
          texts = ((text1, 2), )
        else:
          texts = ((text1, 0), (text2,1))
        self._draw_qu_attache(cr, pt1, pt2, struct_scale, 
		arrow_scale, texts=texts)
      a0 = a1
      qu_prec, qv_prec = tu[1]

    cr.restore()

  def _draw_qu_attache(self, cr, pt1, pt2, struct_scale, arrow_scale, texts=None, color=None):
    """Dessin de la ligne d'attache d'une charge qu et de sa légende
    height : hauteur de la flèche entre 0!! et 1"""
    def show_text(x1, x2, y, height1, height2, angle1, angle2, text, pos):
      if pos == 0:
        x = x1
        height = height1
        angle = angle1
      elif pos == 1:
        x = x2
        height = height2
        angle = angle2
      else:
        x = (x1+x2)/2
        angle = (angle1+angle2)/2
        height = height2
      cr.save()
      cr.translate(x, y)
      cr.rotate(angle)
      cr.move_to(height, 0)
      pt = cr.user_to_device(height, 0)
      cr.save()
      cr.rotate(-angle)
      x_bearing, y_bearing, w, h = cr.text_extents(text)[:4]
      cr.rel_move_to(-w/2, -h)
      cr.show_text(text)
      cr.restore()
      cr.restore()
      return pt

    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)

    cr.save()
    cr.set_line_width(1/struct_scale)
    x1, y, height1, angle1 = pt1
    cr.translate(x1, y)
    cr.rotate(angle1)
    height1 = -height1*arrow_scale
    cr.move_to(height1, 0)
    cr.restore()

    cr.save()
    cr.set_line_width(1/struct_scale)
    x2, y, height2, angle2 = pt2
    cr.translate(x2, y)
    cr.rotate(angle2)
    height2 = -height2*arrow_scale
    cr.line_to(height2, 0)
    cr.stroke()
    cr.restore()

    if texts:
      cr.set_font_size(Const.FONT_SIZE/struct_scale)
      
      if len(texts) == 1:
        text, pos = texts[0]
        xd, yd = show_text(x1, x2, y, height1, height2, angle1, angle2, text, pos)
        self.mapping.extend_box(self.id, xd, yd-25)
      else:
        text1, pos1 = texts[0]
        xd, yd = show_text(x1, x2, y, height1, height2, angle1, angle2, text1, pos1)
        self.mapping.extend_box(self.id, xd, yd-25)
        text2, pos2 = texts[1]
        xd, yd = show_text(x1, x2, y, height1, height2, angle1, angle2, text2, pos2)
        self.mapping.extend_box(self.id, xd, yd-25)

    cr.restore()

  def _draw_arrow(self, cr, x, y, height, angle=0, mirror=False, width=3, color=None):
    """Dessin d'une flèche
    height : hauteur de la flèche entre 0!! et 1"""
    if mirror:
      angle2 = math.pi
      angle += math.pi
    else:
      angle2 = 0
    cr.save()
    cr.set_line_width(width)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x, y)
    if not angle == 0:
      cr.rotate(angle)

    # rotation en mirroir par rapport au centre de la flèche
    cr.save()
    cr.translate(-height/2, 0)
    cr.rotate(angle2)
    # axis
    cr.move_to(-height/2, 0)
    cr.rel_line_to(height-5, 0)
    cr.stroke()

    # point pour la ligne d'attache
    if mirror:
      pt = cr.user_to_device(height, 0)
    else:
      pt = cr.user_to_device(-height, 0)
    # arrow
    cr.move_to(height/2, 0)
    cr.rel_line_to(-9, -7)
    cr.rel_line_to(0, 14)
    cr.close_path()
    cr.fill()
    cr.stroke()
    cr.restore()
    cr.restore()
    return pt

  def _draw_arrow_legend(self, cr, text, x, y, angle=0, decalage=0, color=None):
    """Ecrit une légende à la position x, y du device"""
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x, y)
    x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
    if angle:
      cr.rotate(angle)
    cr.move_to(-width / 2 - x_bearing, -decalage-height / 2 - y_bearing)
    cr.show_text(text)
    cr.restore()


  def _draw_arrow2(self, cr, x, y, struct_scale, arrow_scale, angle=0, mirror=False, height=1., width=3, color=None):
    """Dessin d'une flèche
    height : hauteur de la flèche entre 0!! et 1"""
    if height == 0:
      return
    if mirror:
      angle2 = math.pi
      #angle += math.pi
    else:
      angle2 = 0
    cr.save()
    cr.set_line_width(width/arrow_scale/struct_scale)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x, y)
    if not angle == 0:
      cr.rotate(angle)
    cr.scale(arrow_scale, arrow_scale)

    # rotation en miroir par rapport au centre de la flèche
    cr.save()
    cr.translate(-height/2, 0)
    cr.rotate(angle2)

    cr.move_to(-height/2, 0)
    cr.rel_line_to(height, 0)
    cr.stroke()
    # height isn't enought long
    if height <= 0.15:
      cr.restore()
      cr.restore()
      return

    cr.move_to(height/2, 0)


    cr.rel_line_to(-0.15, -0.1)
    cr.rel_line_to(0, 0.2)
    cr.close_path()
    cr.fill()
    cr.stroke()
    cr.restore()
    cr.restore()


  def _draw_moment(self, cr, x, y, start=0.1, end=1.4, radius=25, rotate=0, middle=False, color=None):
    """Dessin d'une flèche de moment - start=axe horiz, tourne sens anti-trigo"""
    cr.save()
    cr.set_line_width(2)
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(x, y)
    if rotate:
      cr.rotate(rotate)
    # middle point
    if middle:
      cr.arc(0, 0, 2, 0, 2*math.pi)
      cr.fill()
      cr.stroke()
    x_top = radius*math.cos(start)
    y_top = radius*math.sin(start)
    angle_d = (start+end)/2
    x_d = radius*math.cos(angle_d)+15
    y_d = radius*math.sin(angle_d)+15
    x_d, y_d = cr.user_to_device(x_d, y_d)
    cr.arc(0, y_top, radius, start, end)
    cr.stroke()
    cr.move_to(x_top, y_top)
    #cr.move_to(radius, 0)
    #d = radius/4
    d = 7
    #print("d=", d, radius)
    cr.rel_line_to(d, d)
    cr.rel_line_to(-2*d, 0)
    cr.close_path()
    cr.fill()
    cr.stroke()
    #a = angle/2
    #x_u = 1.8*radius*math.cos(a)
    #y_u = 1.8*radius*math.sin(a)
    cr.restore()
    return x_d, y_d

  def draw_circle(self, cr, x, y, angle, scale, u):
    cr.save()
    cr.set_line_width(1/scale)
    cr.translate(x, y)
    cr.scale(scale, scale)
    cr.rotate(angle)
    cr.arc(u, 0, 3/scale, 0, 6.29)
    cr.fill()
    cr.stroke()
    cr.restore()

  def _draw_sun(self, cr, size):
    """Dessine un soleil au point 0, 0 du context cr"""
    cr.set_source_rgba(1, 1, 0, 0.6)
    cr.arc(0, 0, 0.4*size, 0, 6.29)
    cr.fill()
    cr.set_line_width(0.333*size)
    a = 0.3
    cr.rotate(a)
    n = 6
    pas = 6.29/n
    for i in range(n):
      cr.rotate(pas)
      cr.move_to(0.533*size, 0)
      cr.rel_line_to(size, 0)
    cr.stroke()


  # ------------ combinaisons --------------------

  def get_combi_view(self, rdm, is_info=False):
    #print("get_combi_view", is_info)
    status = self.status
    if is_info:
      if self.s_case is None:
        self._set_s_case(rdm)
      view = self._get_combi_view2(rdm, True)
    elif status == 0:
      view = self._get_combi_view2(rdm, False)
    elif status in [1, 8]:
      view = None
    elif status == 2:
      view = self._get_combi_view2(rdm)
    elif status == 3:
      view = self._get_combi_view2(rdm, False)
    else:
      view = self._get_combi_view1(rdm)
    return view

  def copy_selected_objects(self, sibling):
    """Copie les objets selectionnés"""
    self.s_curve = sibling.s_curve
    self.s_cases = copy.copy(sibling.s_cases)
    self.s_case = sibling.s_case


  def set_cases_ini(self, rdm):
    """Initialise les cas et combinaisons actifs"""
    self._set_s_case(rdm)
    self._set_s_cases(rdm)

  def _set_s_cases(self, rdm):
    """Détermine l'attribut s_cases en fonction des erreurs de l'étude"""
    #print("_set_s_cases")
    try:
      s_cases = self.s_cases
    except AttributeError:
      self.s_cases = s_cases = []
    try:
      n_cases = rdm.n_cases
      n_chars = rdm.n_chars
    except AttributeError:
      n_cases = 0
      n_chars = 0
    try:
      errorcases = rdm.char_error
      is_finish = True
    except AttributeError:
      errorcases = []
      #print("debug::set_s_cases cas inattendu")
      is_finish = False
    combi_error = False
    if len(errorcases) > 0:
      combi_error = True
    if is_finish and len(s_cases) == 0:
      n0 = self.get_first_case(rdm)
      if n0 is None:
        self.s_cases = []
        return
      self.s_curve = n0
      s_cases.append(n0)
    elif is_finish:
      new = []
      for i in range(n_chars):
        cas = i
        if not i in s_cases:
          continue
        if cas in errorcases:
          continue
        if combi_error and cas >= n_cases:
          continue
        new.append(i)
    
      s_cases = new
      if len(s_cases) == 0:
        n0 = self.get_first_case(rdm)
        if n0 is None:
          self.s_cases = []
          return
        s_cases.append(n0)
      self.s_cases = s_cases
      if self.s_curve is None:
        try:
          self.s_curve = s_cases[0]
        except IndexError:
          pass
    #print("s_cases=", self.s_cases)


  def _get_combi_view1(self, rdm):
    """Retourne une vue de l'état des boutons des combinaisons du type [(0/1 inactif/actif, 0/1 insensible/sensible)] # attention doit être un tuple
    Mode checkbutton"""
    s_cases = self.s_cases
    try:
      n_cases = rdm.n_cases
      n_chars = rdm.n_chars
    except AttributeError:
      n_cases = 0
      n_chars = 0
    try:
      errorcases = rdm.char_error
    except AttributeError:
      errorcases = []
    view = []
    for i in range(n_cases):
      if i in s_cases:
        view.append((1, 1))
        continue
      if i in errorcases:
        view.append((0, 0))
        continue
      view.append((0, 1))
    sens = 1
    if errorcases:
      sens = 0
    for i in range(n_cases, n_chars):
      if sens == 0:
        view.append((0, 0))
      elif i in s_cases:
        view.append((1, 1))
      else:
        view.append((0, 1))
    return view


  def get_first_case(self, rdm):
    """Détermine l'indice du premier cas non erroné"""
    errorcases = rdm.char_error
    n_cases = rdm.n_cases
    if len(errorcases) == 0:
      #try:
      if not self.s_case is None:
        return self.s_case
      #except AttributeError:
      return 0
    for i in range(n_cases):
      if not i in errorcases:
        return i
    return None

  def _set_s_case(self, rdm):
    """Détermine l'attribut s_case en fonction des erreurs de l'étude"""
    try:
      n_cases = rdm.n_cases
      n_chars = rdm.n_chars
    except AttributeError:
      n_cases = 0
      n_chars = 0
    #default = None
    try:
      default = self.s_case
      if default is None:
        default = 0
    except AttributeError:
      default = 0
    if default >= n_chars:
      default = 0
    try:
      errorcases = rdm.char_error
    except AttributeError:
      errorcases = []
    n_errors = len(errorcases)
    if n_errors == n_cases:
      default = None
    self.s_case = default

  def _get_combi_view2(self, rdm, show_all=True):
    """Retourne une vue de l'état des boutons des combinaisons du type [(0/1 inactif/actif, 0/1 insensible/sensible)] # attention doit être un tuple
    Mode radiobutton"""
    try:
      n_cases = rdm.n_cases
      n_chars = rdm.n_chars
    except AttributeError:
      n_cases = 0
      n_chars = 0
    try:
      errorcases = rdm.char_error
    except AttributeError:
      errorcases = []

    n_errors = len(errorcases)
    combi_error = False
    if n_errors > 0:
      combi_error = True
    s_case = self.s_case
# tester
    if self.status == 0:
      combi_error = True
    if self.status == 2: 
      show_all = True # on montre les chargements
    if s_case is None:
      s_case = self.s_case = 0

    if show_all:
      errorcases = []
      combi_error = False
    if s_case is None:
      return [(0, 0)]*n_chars

    if s_case in errorcases:
      for i in range(n_cases):
        if not i in errorcases:
          s_case = i
          break

    view = [(0, 1)]*n_chars
    view[s_case] = (1, 1)

    if not show_all:
      for i in range(n_chars):
        if i in errorcases or (combi_error and i >= n_cases):
          view[i] = (0, 0)
    return view

# Dessin des mapping

  def _draw_selected_barre(self, cr, barre):
    """Met en valeur une barre sélectionnée pendant un survol"""
    barre.redraw(cr)

  def _draw_legend_position(self, cr, struct, name, u, values):
    """Dessine le repérage d'une valeur sur une courbe"""
    #print("_draw_legend_position")
    du, dv = values
    x0, y0 = self.x0, self.y0
    if name in struct.Curves:
      Arc = struct.Curves[name]
      barre, u = Arc.get_bar_and_pos(u)
      u *= struct.Lengths[barre]
      show_pos = False
    else:
      barre = name
      show_pos = True
    x, y = struct.Nodes[struct.Barres[barre][0]] 
    self._c_draw_legend_position(cr, struct, barre, x0, y0, x, y, u, du, dv, show_pos)

  def _c_draw_legend_position(self, cr, struct, barre, x0, y0, x, y, u, du, dv, show_pos=False):
    """Dessine le repérage d'une valeur sur une courbe, partie commune aux classes"""
    angle = -struct.Angles[barre]
    struct_scale = self.struct_scale
    if self.status == 8:
      chart_scale = self.influ_scale
    else:
      chart_scale = self.chart_scale
    cr.save()
    self._fg.set_color_by_name(cr, "red")
    cr.set_font_size(Const.FONT_SIZE*0.8)
    cr.translate(x0 + x*struct_scale, y0 - y*struct_scale)
    if not angle == 0:
      cr.rotate(angle)
    cr.scale(struct_scale, struct_scale)
    du = du*chart_scale/struct_scale
    dv = dv*chart_scale/struct_scale
    cr.translate(u+du, -dv)
    cr.arc(0, 0, 3./struct_scale, 0, 6.29)
    cr.fill()
    cr.stroke()

    cr.translate(-du, dv)
    cr.arc(0, 0, 3./struct_scale, 0, 6.29)
    cr.fill()
    cr.stroke()

    cr.set_line_width(1./struct_scale)
    cr.move_to(0, 0)
    cr.rel_line_to(du, -dv)
    cr.stroke()
    # cotation
    if show_pos:
      cr.set_line_width(2./struct_scale)
      cr.move_to(0, 0)
      cr.rel_line_to(-u, 0)
      cr.stroke()
      cr.move_to(-u/2, 15/struct_scale)
      cr.save()
      cr.scale(1./struct_scale, 1./struct_scale)
      text = function.PrintValue(u, struct.units['L'])
      cr.show_text(text)
      cr.restore()
    cr.restore()


# -------------- DESSIN DES LIGNES D'INFLUENCE -------------

  def _set_influ_values(self, cr, rdm, id, status, values, struct_scale, chart_scale):
    """Prépare les données pour les légendes des courbes d'influence"""
    struct = rdm.struct
    units = struct.units

    if status == 3:
      unit_conv = units['L']
    else:
      unit_conv = units['F']
    self._delete_node_val(rdm)
    #try:
    #  user_values = self.user_values[self.status][id]
    #except KeyError:
    #  user_values = {}

    PrintValue = function.PrintValue
    di = {}
    for barre, data in values.items():
      di2 = {}
      x, y = struct.Nodes[struct.Barres[barre][0]] # origine barre
      angle = -struct.Angles[barre]
      l = struct.Lengths[barre]
      cr.save()
      cr.translate(self.x0 + x*struct_scale, self.y0 - y*struct_scale)
      if not angle == 0:
        cr.rotate(angle)
      cr.scale(struct_scale, chart_scale)
      for u, elem in data.items():
        u = u*l
        di2[u] = []
        for pos, val in elem.items():
          text = PrintValue(val, unit_conv)
          dy = self._get_text_pos(val)
          x, y = cr.user_to_device(u, -val+dy/chart_scale)
          if pos == 2: # provisoire
            pos -= 2
            auto = False
          else:
            auto = True
          di2[u].append([(0., val), int(x), int(y), angle, pos, auto])
      cr.restore()
      di[barre] = di2
    self.mapping.set_curve_values(self, di, id)

# attention, bars peut être un dictionnaire ou une liste : pas cohérent
  def _get_influ_data(self, rdm, bars):
    """Calcule les données pour toutes les lignes d'influence afin de pouvoir en déduire le maximum. Retourne les béziers, les valeurs caractéristiques et le maxi"""
    data = {}
    values = {}
    maxi0 = 0
    try:
      user_values = self.user_values[self.status]
    except KeyError:
      user_values = {}
    for obj in self.influ_list.values():
      id = obj.id
      try:
        c_user_values = user_values[id]
      except KeyError:
        c_user_values = {}
      data[id] = {}
      status = obj.status
      elem = obj.elem
      u = obj.u
      for barre in bars:
        points = rdm.InfluBarre(barre, elem, u, status)
        data[id][barre] = points
      values[id] = copy.copy(rdm.bar_values) # !! effet de bord

      for barre in c_user_values:
        are_deleted = []
        for pos in c_user_values[barre]:
          if not barre in values[id]:
            continue
          if not pos in values[id][barre]:
            if len(c_user_values[barre][pos]) == 2:
              are_deleted.append(pos)
              continue
            l = rdm.struct.Lengths[barre]
            val = rdm.ValueLigneInf(barre, pos/l, elem, u, status)
            values[id][barre][pos/l] = {2: val}
        for val in are_deleted:
          del(c_user_values[barre][val]) # suppression valeurs devenues inutiles

      for di in rdm.bar_values.values():
        for tu in di.values():
          for val in tu.values():
            if abs(val) > maxi0:
              maxi0 = abs(val)
    return data, values, maxi0

  def _draw_all_bars_influ(self, cr, rdm, obj, data, struct_scale, chart_scale, color=None):
    """Lance le tracé pour une ligne d'influence"""
    struct = rdm.struct
    id = obj.id
    status = obj.status
    elem = obj.elem
    u = obj.u
    for barre, points in data.items():
      x, y = struct.Nodes[struct.Barres[barre][0]] # origine barre
      self._draw_single_bar_curve(cr, rdm, barre, points, self.x0, self.y0, x, y, struct_scale, chart_scale, id, color=color, mode=2)
    if not status == 4:
      self._draw_influ_position(cr, rdm, elem, u, color)

  def get_influ_message(self, study, n):
    """Retourne le message concernant la ligne d'influence"""
    rdm = study.rdm
    struct = rdm.struct
    texts = {1: "d'effort tranchant", 2: "du moment fléchissant", 3: "de la déformée", 4: "de réaction d'appui"} 
    for obj in self.influ_list.values():
      if obj.id == n:
        break
    unit_L = study.get_unit_name('L')
    status = obj.status
    elem = obj.elem
    if status == 4:
      text = "Ligne d'influence %s au noeud %s" % (texts[status], elem)
    else:
      u = obj.u
      l = struct.Lengths[elem]
      u = function.PrintValue(u*l, struct.units['L'])
      text = "Ligne d'influence %s sur %s (x=%s %s)" % (texts[status], elem, u, unit_L)
    return (text, 3)


  def _draw_influ_position(self, cr, rdm, barre, u, color=None):
    """Dessine la position de la référence de la ligne d'influence"""
    pt1name = rdm.struct.Barres[barre][0]
    x1, y1 = rdm.struct.Nodes[pt1name]
    angle = -rdm.struct.Angles[barre]
    l = rdm.struct.Lengths[barre]
    scale = self.struct_scale

    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    width = 1
    cr.set_line_width(width/scale)
    cr.translate(self.x0+x1*scale, self.y0-y1*scale)
    cr.scale(scale, scale)
    cr.rotate(angle)
    cr.arc(u*l, 0, 4/scale, 0, 6.29)
    cr.fill()
    cr.stroke()
    cr.restore()

# inutilisée (servait pour l'affichage d'une valeur sur LI)
  def push_w4_group(self, rdm, cr, barre, x):
    """x en %"""
    struct = rdm.struct
    try:
      obj = self.influ_list[self.s_influ]
    except IndexError:
      return
    n_charts = len(self.influ_list)
    if n_charts == 0:
      return
    elem = obj.elem
    u = obj.u
    status = obj.status
    val = rdm.ValueLigneInf(barre, x, elem, u, rdm.struct.InvMatK, status)
    ampli = obj.ampli
    if val is None:
      return
    color = self._fg.get_nth_color(self.s_influ)
    x = x*rdm.struct.Lengths[barre]
    value = {barre: {x: (val, )}}
    cr.push_group()
    self.draw_value_influ(cr, rdm, value, ampli, mark=True, color=color)
    self.p_window = cr.pop_group()


class ChildDrawing(Drawing):

  def get_bar_drawings(self):
    """Retourne les identifiants des dessins de barres"""
    return []

  def get_char_drawing(self):
    """Retourne l'identifiant du dessin de chargement ou None"""
    return None

  def get_is_parent(self):
    """Retourne vrai si le dessin est une instance de BarreDrawing"""
    return False



class CharDrawing(ChildDrawing):
  """Classe ne permettant de faire qu'un affichage du chargement"""

  def __init__(self, mapping, id_study, parent):
    self.parent = parent
    Drawing.__init__(self, mapping, id_study)
    parent.childs[self.id] = self
    self.s_case = parent.s_curve

  def get_menu_options(self):
    """Retourne les options du menu contextuel"""
    return {}

  def set_drawing_prefs(self, prefs, tab, study):
    """Initialise les préférences du dessin"""
    self.options = self.parent.options
    self.status = 2
    self.options['Sync'] = True
    self.set_geometric_prefs(tab, study, prefs)
    self._add_info_prefs(prefs)

# à finir ?
  def set_dim(self, study):
    """Calcule la largeur et la hauteur"""
    pass

  def set_all_sizes(self, tab, study):
    """Calcule la taille, l'échelle et la position d'un dessin (structure seule)"""
    # tout est calculé dans expose_drawing
    print("finir set_all_sizes")

  def get_is_char_drawing(self):
    """Retourne vrai si le dessin est une instance de CharDrawing"""
    return True

  def update_s_data(self, rdm, barres):
    """Met à jour s_case, s_cases, s_bar, s_curve pour le CharDrawing"""
    if self.parent.s_curve is None:
      return False
    if not self.s_case in self.parent.s_cases:
      return False
    self.s_case = parent.s_curve

  def update_drawing_data(self, tag=False):
    """Met à jour la config du dessin par rapport à son parent"""
    self.s_case = self.parent.s_curve

  def get_xml_prefs(self, parent):
    """Crée le noeud xml pour les préférences communes aux dessins pour la sauvegarde des préférences"""
    node = ET.SubElement(parent, "c_child")
    self.set_xml_prefs(node)
    return node

  def _push_title_group(self, study, cr):
    """Crée le pattern pour le titre du dessin"""
    title_id = self.title_id
    case_name = study.rdm.GetCharByNumber(self.s_case).name
    tag = self.options.get('Title', True)
    if not tag:
      return
    cr.push_group()
    cr.set_font_size(Const.FONT_SIZE)
    if title_id is None:
      text = '%s : %s' % (study.name, case_name)
      text2 = study.name
      x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
      x = self.x0+50
      y = self.y0-40
      box = (x, y, int(width+8), int(height+12))
      obj = MText(box, text2, title_id)
      self.title_id = obj.id
    else:
      obj = self.mapping.infos[self.id][title_id]
      text = '%s : %s' % (obj.text, case_name)
      x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
      x, y, w, h = obj.box
      box = (x, y, int(width+8), int(height+12))
      obj.box = box
    cr.translate(x, y)
    cr.move_to(4, height+5)
    cr.show_text(text)
    self.p_infos[obj.id] = cr.pop_group()
    self.mapping.set_info(self.id, obj)


  def draw_tools(self, study, tab):
    """Dessine la barre d'outils du dessin"""
    layout = tab.layout
    Main = tab._main
    hbox = Gtk.HBox(False, 10)
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_PAGE_SETUP)
    b.set_tooltip_text("Modifier l'échelle")
    b.connect('clicked', tab.on_show_scale_box, self, "struct")
    hbox.pack_start(b, False, False, 0)
    dx = 70
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_CLOSE)
    b.set_tooltip_text("Fermer")
    b.connect('clicked', Main.on_del_drawing, self)
    hbox.pack_start(b, False, False, 0)
    hbox.show_all()
    x, y, w, h = self.mapping.box[self.id]
    x = x + 25
    y = y + h - 28
    layout.put(hbox, int(x), int(y))
    return hbox


class BarreDrawing(ChildDrawing):

  def __init__(self, mapping, id_study, parent):
    self.parent = parent
    Drawing.__init__(self, mapping, id_study)
    parent.childs[self.id] = self

  def get_menu_options(self):
    """Retourne les options du menu contextuel"""
    options = super(BarreDrawing, self).get_menu_options()
    del(options["Add"])
    options['Sync'] = self.options.get('Sync', True)
    return options

  def get_is_bar_drawing(self):
    """Retourne vrai si le dessin est une instance de BarreDrawing"""
    return True

  def set_drawing_prefs(self, prefs, tab, study):
    """Initialise les préférences du dessin"""
    self.options = self.parent.options
    self.s_case = None
    self.s_cases = []
    self.s_curve = None
    self.s_bar = prefs['bar']
    self.options['Sync'] = True
    self.set_geometric_prefs(tab, study, prefs)
    if 'values' in prefs: # avant status
      val = prefs['values']
      try:
        self.user_values = eval(val)
      except SyntaxError:
        pass
    if 'status' in prefs:
      val = prefs['status']
      val = val.split(',')
      self.status = int(val[0])
      if self.status in [2, 3]:
        try:
          self.s_case = int(val[1])
        except IndexError:
          pass
      else:
        self.s_cases = [int(i) for i in val[1:]]
    else:
      self.set_status(self.parent.status)
    self._add_info_prefs(prefs)

  def set_status(self, status):
    if status == 0:
      self.status = 1
      return
    self.status = status

  def set_dim(self, study):
    """Calcule la largeur et la hauteur"""
    #print("set_dim dans Barre Drawing")
    size = Const.DRAWING_SIZE
    struct = study.rdm.struct
    l = struct.Lengths[self.s_bar]
    angle = struct.Angles[self.s_bar]
    self.width = max(l*self.struct_scale*math.cos(angle), size)
    self.height = max(l*self.struct_scale*math.sin(angle), size)

  def set_all_sizes(self, tab, study):
    """Calcule la taille, l'échelle et la position d'un dessin (structure seule)"""
    #print("set_all_sizes in Barre Drawing")
    size = Const.DRAWING_SIZE
    struct = study.rdm.struct
    sw = tab.sw
    sw_w = int(sw.get_hadjustment().get_page_size())
    sw_h = int(sw.get_vadjustment().get_page_size())
    l = struct.Lengths[self.s_bar]
    if l == 0:
      self.struct_scale = None
      self.width = self.height = size
    else:
      self.struct_scale = size / l
      angle = struct.Angles[self.s_bar]
      self.width = l*self.struct_scale*math.cos(angle)
      self.height = l*self.struct_scale*math.sin(angle)

    self.x0 = int(sw_w/2) # milieu de la fenetre
    self.y0 = int(sw_h/2+50)

  def set_scale(self, struct):
    """Ajuste léchelle de la structure pour tenir dans la boîte"""
    #print("set_scale dans Barre Drawing")
    l = struct.Lengths[self.s_bar]
    angle = struct.Angles[self.s_bar]
    w, h = abs(l*math.cos(angle)), abs(l*math.sin(angle))
    self.struct_scale = self._get_scale(w, h, self.width, self.height)

  def set_position(self):
    """Place le dessin à sa position optimale"""
    m = Const.AREA_MARGIN_MIN
    dx = self.width/2 + m - self.x0
    dy = self.height+m - self.y0
    self.x0 = self.width/2+m
    self.y0 = self.height + m
    # déplacement échelle, titre
    if self.id in self.mapping.infos:
      for elem in self.mapping.infos[self.id].values():
        x, y, w, h = elem.box
        x = max(x+dx, m)
        y = y+dy
        elem.box = (x, y, w, h)

  def zoom_best(self, coef, struct):
    if self.struct_scale is None:
      return
    self.set_position()

  def set_zoom(self, zoom):
    """Modifie les attributs pour le zoom"""
    max1 = Const.DRAWING_SIZE_MED
    if zoom == "+":
      coef = 1/0.9
    elif zoom == "-":
      coef = 0.9
    else:
      return # on évite de changer le zoom (a tester)
    if coef > 1:
      w = self.width*coef
      h = self.height*coef
      if h > max1: # limitation
        h = max1
        w = w/h*max1
      if w > max1: # limitation
        w = max1
        h = h/w*max1
      self.width = w
      self.height = h
    else:
      self.width = self.width*coef
      self.height = self.height*coef


  def update_s_data(self, rdm, barres):
    """Met à jour s_case, s_cases, s_bar, s_curve dans BarreDrawing"""
    self.s_cases = self.parent.s_cases
    if not self.s_case in self.s_cases:
      try:
        self.s_case = self.s_cases[0]
      except IndexError:
        return False
    if not self.s_curve is None and not self.s_curve in self.s_cases:
      self.s_curve = self.s_case
    if not self.s_bar is None and not self.s_bar in barres:
      if len(barres) >= 2:
# problème d'echelle si on renomme la barre active -> car basculement sur la première barre
        self.s_bar = barres[0]
      else:
        return False

  def update_drawing_data(self, change_parent=False):
    """Met à jour la config du dessin par rapport à son parent"""
    sync = self.options['Sync']
    parent = self.parent
    if sync:
      if change_parent:
        parent.del_patterns()
        parent.s_cases = self.s_cases
        parent.s_case = self.s_case
        parent.status = self.status
      else:
        self.s_cases = parent.s_cases
        self.s_case = parent.s_case
        self.status = parent.status


  def get_xml_prefs(self, parent):
    """Crée le noeud xml pour les préférences communes aux dessins pour la sauvegarde des préférences"""
    node = ET.SubElement(parent, "b_child")
    self.set_xml_prefs(node)
    node.set("bar", str(self.s_bar))
    return node

  def draw_tools(self, study, tab):
    """Dessine la barre d'outils du dessin"""
    layout = tab.layout
    Main = tab._main
    hbox = Gtk.HBox(False, 10)
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_MEDIA_FORWARD)
    b.set_tooltip_text("Barre suivante")
    b.connect('clicked', tab.on_select_next, self, study)
    hbox.pack_start(b, False, False, 0)
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_MEDIA_REWIND)
    b.set_tooltip_text("Barre précédente")
    b.connect('clicked', tab.on_select_back, self, study)
    hbox.pack_start(b, False, False, 0)
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_CLOSE)
    b.set_tooltip_text("Fermer")
    b.connect('clicked', Main.on_del_drawing, self)
    hbox.pack_start(b, False, False, 0)
    hbox.show_all()
    x, y, w, h = self.mapping.box[self.id]
    x = x + 25
    y = y + h - 28
    layout.put(hbox, int(x), int(y))
    return hbox


  def area_expose_realtime(self, study, cr):
    self.status = 1 # évite un bug avec l'absence du pattern p_char pour drawing.paint
    self.area_expose_barre(study, cr)

  def area_expose_barre(self, study, cr):
    self.mapping.clear(self.id)
    struct = study.rdm.struct
    struct_scale = self.struct_scale
    self._push_struct_group(study, cr, struct_scale)
    self._push_bind_group(struct, cr)
    self._push_scale_group(study, cr, 1., struct_scale)



  def area_expose_influ(self, study, cr):
    print("Ligne d'influence non supportée pour le mode par barre")
    self.status = 1
    self.area_expose_barre(study, cr)

  def _push_error_group(self, cr):
    """Dessine une croix si le dessin présente une impossibilité de tracé"""
    cr.push_group()
    cr.set_source_rgba(1, 0, 0, 0.6)
    cr.set_line_width(10)
    x0, y0 = self.x0, self.y0
    w, h = self.width, self.height
    m = 25
    cr.translate(x0 , y0)
    cr.move_to(-w/2+m, h/2-m)
    cr.rel_line_to(w-2*m, -h+2*m)
    cr.stroke()
    cr.move_to(-w/2+m, -h/2+m)
    cr.rel_line_to(w-2*m, h-2*m)
    cr.stroke()
    self.p_struct = cr.pop_group()


  def _push_struct_group(self, study, cr, struct_scale):
    struct = study.rdm.struct
    self.p_infos = {}
    options = self.options
    barre = self.s_bar
    try:
      a = -struct.Angles[barre]
      l =  struct.Lengths[barre]
    except KeyError:
      self._push_error_group(cr)
      self._draw_cross(cr, self.x0, self.y0, 1)
      self._push_title_group(study, cr)
      w, h = self.width, self.height
      box = (self.x0-w/2, self.y0-h/2, w, h)
      self.mapping.set_mapping_bars(self.id, {'e': (self.x0, self.y0)}, {}, box)
      return
    cr.push_group()    
    self._draw_one_bar(cr, struct, struct_scale, barre, fill=True)
    x1, y1, node1 = self.N1
    x2, y2, node2 = self.N2

    if self.status in [2, 3]:
      self._draw_section(cr, struct, x1, y1, barre, color='grey')
      self._draw_section(cr, struct, x2, y2, barre, end=True, color='grey')
    else:
      self._draw_cross(cr, x1, y1, 1)
      self._draw_cross(cr, x2, y2, 1)
    self.p_struct = cr.pop_group()
    drawing = self.parent
    drawing._push_selected_barre(cr, struct, barre, 4)
    self._push_title_group(study, cr)



  def _push_bind_group(self, struct, cr):
    cr.push_group()
    self.p_bind = cr.pop_group()


  def _push_char_group(self, study, cr):
    """Crée le pattern des chargements"""
    rdm = study.rdm
    struct = rdm.struct
    cr.push_group()
    n = self.s_case
    barre = self.s_bar
    if n is None:
      print("debug::_push_char_group")
      n = self.s_case = 0

    scale = self.struct_scale
    x0, y0 = self.x0, self.y0
    N1 = struct.Barres[barre][0]
    N2 = struct.Barres[barre][1]
    x1, y1 = struct.Nodes[N1] # origine barre
    x2, y2 = struct.Nodes[N2] # fin barre
    dx, dy = -(x2-x1)/2, -(y2-y1)/2
    nodes = {N1: (dx, dy), N2: (-dx, -dy)}
    Char = rdm.GetCharByNumber(n)
    resu = function.GetCumulChar(rdm.struct.Barres, Char)
    di = resu[0]
    # attention, qmax obtenu à partir des composantes et pas de la norme contrairement aux autres chargements
    qmax = resu[1]
    if barre in di:
      chars = di[barre]
      self._draw_char_bar_q(cr, x0, y0, barre, scale, chars,
			qmax, study, nodes, color='blue')
    chars = Char.charBarFp
    if barre in chars:
      self._draw_char_bar_fp(cr, x0, y0, barre, study, chars[barre], scale, nodes, color="green")
    chars = Char.charBarTherm
    if barre in chars:
      self._draw_char_therm(cr, x0, y0, barre, rdm, scale, nodes)
    # décalage dans le repère du device
    self.p_char = cr.pop_group()

  def _push_reac_group(self, study, cr, color="grey"):
    struct_scale = self.struct_scale
    x1, y1, node1 = self.N1
    x2, y2, node2 = self.N2
    n = self.s_case
    barre = self.s_bar
    rdm = study.rdm
    Char = rdm.GetCharByNumber(n)
    cr.push_group()
    self._draw_start_action(cr, study, Char, barre, x1, y1)
    self._draw_end_action(cr, study, Char, barre, x2, y2)
    self.p_reac = cr.pop_group()

  def _push_soll_group(self, study, cr, maxi):
    barre = self.s_bar
    rdm = study.rdm
    struct = rdm.struct
    struct_scale = self.struct_scale
    cr.push_group()
    mode = struct.IsHorizontal() and 1 or 2
    size = mode == 1 and Const.GRAPH_SIZE_MAX or Const.GRAPH_SIZE_MIN
# Attention, changer size va changer la courbe et donner un pb avec draw_scale
    #size  = Const.GRAPH_SIZE_MIN
    if maxi == None:
      self.p_curves = cr.pop_group() # main pattern
      return
    if maxi == 0.:
      chart_scale = 0.
    else:
      chart_scale = size / maxi
    if self.status in self.chart_zoom:
      chart_scale = chart_scale*self.chart_zoom[self.status]
    self.chart_scale = chart_scale
    N1 = struct.Barres[barre][0]
    N2 = struct.Barres[barre][1]
    x1, y1 = struct.Nodes[N1] # origine barre
    x2, y2 = struct.Nodes[N2] # fin barre
    dx, dy = -(x2-x1)/2, -(y2-y1)/2
    nodes = {N1: (dx, 0), N2: (-dx, 0)}
    if chart_scale == 0.:
      chart_scale = 1. # evite une cairo invalid matrix
    chart_scale = chart_scale

    s_cases = self.s_cases
    for n_case in s_cases:
      color = self._fg.get_nth_color(n_case)
      Char = rdm.GetCharByNumber(n_case)

      data = self._get_curve_points(rdm, barre, Char)
      self._draw_single_bar_curve(cr, rdm, barre, data, self.x0, self.y0, dx, dy, struct_scale, chart_scale, n_case, color=color, mode=2)
      self._set_soll_values(cr, rdm, dx, dy, struct_scale, chart_scale, 
		n_case, Char, barre)
    self.p_curves = cr.pop_group()

  def _push_defo_group(self, study, cr, maxi, size):
    barre = self.s_bar
    rdm = study.rdm
    struct = rdm.struct
    struct_scale = self.struct_scale
    cr.push_group()
    mode = struct.IsHorizontal() and 1 or 2
    if maxi == None:
      self.p_curves = cr.pop_group() # main pattern
      return
    if maxi == 0.:
      chart_scale = 0.
    else:
      chart_scale = size / maxi

    self.chart_scale = chart_scale
    N1 = struct.Barres[barre][0]
    N2 = struct.Barres[barre][1]
    x1, y1 = struct.Nodes[N1] # origine barre
    x2, y2 = struct.Nodes[N2] # fin barre
    dx, dy = -(x2-x1)/2, -(y2-y1)/2
    nodes = {N1: (dx, 0), N2: (-dx, 0)}
    if chart_scale == 0.:
      chart_scale = 1. # evite une cairo invalid matrix
    if self.status in self.chart_zoom:
      chart_scale = chart_scale*self.chart_zoom[self.status]
    self.chart_scale = chart_scale

    s_cases = self.s_cases
    for n_case in s_cases:
      color = self._fg.get_nth_color(n_case)
      Char = rdm.GetCharByNumber(n_case)
      data = self._get_curve_points(rdm, barre, Char)
      self._draw_one_bar_defo(cr, study, barre, data, self.x0, self.y0, dx, dy, struct_scale, chart_scale, n_case, color=color, mode=mode)
      self._set_defo_values(cr, rdm, dx, dy, struct_scale, chart_scale, 
		n_case, Char, barre)

    self.p_curves = cr.pop_group()

  def _draw_legend_position(self, cr, struct, barre, u, values):
    """Dessine le repérage d'une valeur sur une courbe"""
    du, dv = values
    N1 = struct.Barres[barre][0]
    N2 = struct.Barres[barre][1]
    x1, y1 = struct.Nodes[N1] # origine barre
    x2, y2 = struct.Nodes[N2] # fin barre
    dx, dy = -(x2-x1)/2, -(y2-y1)/2
    x, y = dx, dy
    x0, y0 = self.x0, self.y0
    self._c_draw_legend_position(cr, struct, barre, x0, y0, x, y, u, du, dv)


  def _set_soll_values(self, cr, rdm, x1, y1, struct_scale, chart_scale, n_case, Char, barre):
    """Prépare les données pour les légendes des courbes"""
    if not (n_case == self.s_curve or n_case in self.s_values):
      self.mapping.set_curve_values(self, {}, n_case)
      return
    struct = rdm.struct
    units = struct.units
    #if self.status == 6:
    #  unit_conv = units['L']*units['F']
    #else:
    #  unit_conv = units['F']
    angle = -struct.Angles[barre]
    l = struct.Lengths[barre]
    cr.save()
    cr.translate(self.x0 + x1*struct_scale, self.y0 - y1*struct_scale)
    if not angle == 0:
      cr.rotate(angle)
    cr.scale(struct_scale, chart_scale)
    try:
      user_values = self.user_values[self.status][n_case]
    except KeyError:
      user_values = {}

    di = {barre: {}}
    bar_values = rdm.bar_values[barre]
    self._get_user_values(rdm, Char, barre, user_values, bar_values, l)
    for u, data in bar_values.items():
      u = u*l
      di[barre][u] = []
      for pos, val in data.items():
        #text = function.PrintValue(val, unit_conv)
        dy = self._get_text_pos(val)
        x, y = cr.user_to_device(u, -val+dy/chart_scale)
        if pos == 2: # provisoire
          pos -= 2
          auto = False
        else:
          auto = True
        di[barre][u].append([(0., val), int(x), int(y), angle, pos, auto])
    cr.restore()
    self.mapping.set_curve_values(self, di, n_case)

  def _set_defo_values(self, cr, rdm, x1, y1, struct_scale, chart_scale, n_case,Char, barre):
    """Prépare les données pour les légendes des courbes"""
    struct = rdm.struct
    unit_conv = struct.units['L']
    self._delete_node_val(rdm)
    angle = -struct.Angles[barre]
    l = struct.Lengths[barre]
    cr.save()
    cr.translate(self.x0 + x1*struct_scale, self.y0 - y1*struct_scale)
    if not angle == 0:
      cr.rotate(angle)
    cr.scale(struct_scale, chart_scale)
    try:
      user_values = self.user_values[self.status][n_case]
    except KeyError:
      user_values = {}
    di = {barre: {}}
    bar_values = rdm.bar_values[barre]
    self._get_user_values(rdm, Char, barre, user_values, bar_values, l)
    for u, data in bar_values.items():
      u = u*l
      di[barre][u] = []
      for pos, val in data.items():
        valx = val[0]*chart_scale / struct_scale
        valy = val[1]
        text = function.PrintValue(valy, unit_conv)
        dy = self._get_text_pos(valy)
        x, y = cr.user_to_device(u+valx, -valy+dy/chart_scale)
        if pos == 2: # provisoire
          pos -= 2
          auto = False
        else:
          auto = True
        di[barre][u].append([val, int(x), int(y), angle, pos, auto])
    cr.restore()
    self.mapping.set_curve_values(self, di, n_case)



  def _draw_one_bar(self, cr, struct, scale, barre, width=1, color=None, fill=False):
    """Dessine une seule barre de la structure à partir du milieu de celle-ci pour le mode par barre"""
    angle = -struct.Angles[barre]
    l = struct.Lengths[barre]
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.translate(self.x0 , self.y0)
    if not angle == 0:
      cr.rotate(angle)
    cr.scale(scale, scale)
    cr.set_line_width(width / scale)

    cr.move_to(-l/2, 0)
    cr.line_to(l/2, 0)
    cr.stroke()

    # mapping
    m_points = {}
    node1 = struct.Barres[barre][0]
    node2 = struct.Barres[barre][1]
    x1, y1 = cr.user_to_device(-l/2, 0)
    self.N1 = (x1, y1, node1)
    m_points[node1] = (x1, y1)
    x2, y2 = cr.user_to_device(l/2, 0)
    self.N2 = (x2, y2, node2)
    m_points[node2] = (x2, y2)
    m_bars = {barre: (x1, y1, x2, y2)}
    if fill:
      m = 50
      w, h = abs(x2-x1)+2*m, abs(y2-y1)+2*m
      box = (min(x1, x2)-m, min(y1, y2)-m, w, h)
      self.mapping.set_mapping_bars(self.id, m_points, m_bars, box)
    options = self.options
    if options.get('Barre'):
      name = struct.GetBarreName(self.s_bar)
      self._draw_bar_name(cr, 0, 0, name, 0, scale)
    if options.get('Node'):
      self._draw_node_name(cr, -l/2, 0, node1, scale, -angle)
      self._draw_node_name(cr, l/2, 0, node2, scale, -angle)
    if options.get('Axis'):
      self._draw_axis(cr, 0, 0, 0, scale)
    cr.restore()
    #return N1, N2

  def _draw_start_action(self, cr, study, Char, barre, x, y, color=None):
    #print("_draw_start_action")
    rdm = study.rdm
    unit_conv = rdm.struct.units
    angleBarre = -rdm.struct.Angles[barre]

    maxi = study._get_soll_max()
    if maxi is None:
      return
    crit = maxi / 1e8
    try:
      N = Char.EndBarSol[barre][0][0]
      V = Char.EndBarSol[barre][0][1]
      M = Char.EndBarSol[barre][0][2]
    except AttributeError:
      self.mapping.set_curve_values(self, {}, self.s_case, "reac")
      return
    node1 = self.N1[2]
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_font_size(Const.FONT_SIZE)
    cr.save()
    cr.translate(x, y)
    cr.rotate(angleBarre)

    dx = -10
    dy = 5
    legends = {node1: {}}
    if abs(N) > crit:
      mirror = N < 0 and True or False
      angle = N < 0 and math.pi or 0
      N = abs(N)
      text = function.PrintValue(N, unit_conv['F'])
      N = max(N*Const.ARROW_SIZE_MAX/maxi, Const.ARROW_SIZE_MIN)
      xlegend, ylegend = self._draw_arrow(cr, dx, 0, N,
		angle=angle, mirror=mirror)
      legends[node1][0] = [[text, xlegend-20, ylegend, 0, 0]]
      self.mapping.extend_box(self.id, xlegend-40, ylegend+25)

    if abs(V) > crit:
      angle = V < 0 and math.pi/2 or -math.pi/2
      mirror = V < 0 and True or False
      V = abs(V)
      text = function.PrintValue(V, unit_conv['F'])
      V = max(V*Const.ARROW_SIZE_MAX/maxi, Const.ARROW_SIZE_MIN)
      xlegend, ylegend = self._draw_arrow(cr, dx, dy, V,
		angle=angle, mirror=mirror)
      legends[node1][1] = [[text, xlegend, ylegend, 0, 0]]
      self.mapping.extend_box(self.id, xlegend, ylegend+25)

    if abs(M) > crit:
      text = function.PrintValue(M, unit_conv['F'])
      xlegend, ylegend = self._draw_moment(cr, dx, 0, start=0.3, 
		end=1.2, rotate=1.57, radius=25, middle=False, color='red')
      legends[node1][2] = [[text, xlegend, ylegend, 0, 0]]
      self.mapping.extend_box(self.id, xlegend, ylegend+25)
    cr.restore()
    cr.restore()
    self.mapping.set_curve_values(self, legends, self.s_case, "reac")


  def _draw_end_action(self, cr, study, Char, barre, x, y, color=None):
    rdm = study.rdm
    unit_conv = rdm.struct.units
    angleBarre = -rdm.struct.Angles[barre]
    maxi = study._get_soll_max()
    if maxi is None:
      return
    crit = maxi / 1e8
    try:
      N = Char.EndBarSol[barre][1][0]
      V = Char.EndBarSol[barre][1][1]
      M = Char.EndBarSol[barre][1][2]
    except AttributeError:
      self.mapping.set_curve_values(self, {}, self.s_case, "reac")
      return
    node2 = self.N2[2]

    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_font_size(Const.FONT_SIZE)
    cr.save()
    cr.translate(x, y)
    cr.rotate(angleBarre)

    dx = 10
    dy = 5
    legends = {node2: {}}
    if abs(N) > crit:
      mirror = N > 0 and True or False
      angle = N < 0 and math.pi or 0
      N = abs(N)
      text = function.PrintValue(N, unit_conv['F'])
      N = max(N*Const.ARROW_SIZE_MAX/maxi, Const.ARROW_SIZE_MIN)
      xlegend, ylegend = self._draw_arrow(cr, dx, 0, N,
		angle=angle, mirror=mirror)
      legends[node2][0] = [[text, xlegend+10, ylegend, 0, 0]]
      self.mapping.extend_box(self.id, xlegend+40, ylegend+25)

    if abs(V) > crit:
      angle = V < 0 and math.pi/2 or -math.pi/2
      mirror = V < 0 and True or False
      V = abs(V)
      text = function.PrintValue(V, unit_conv['F'])
      V = max(V*Const.ARROW_SIZE_MAX/maxi, Const.ARROW_SIZE_MIN)
      xlegend, ylegend = self._draw_arrow(cr, dx, dy, V,
		angle=angle, mirror=mirror)
      legends[node2][1] = [[text, xlegend, ylegend, 0, 0]]
      self.mapping.extend_box(self.id, xlegend, ylegend+25)

    if abs(M) > crit:
      text = function.PrintValue(M, unit_conv['F'])
      xlegend, ylegend = self._draw_moment(cr, dx, 0, start=0.3, 
		end=1.2, radius=25, middle=False, color='red')
      legends[node2][2] = [[text, xlegend, ylegend, 0, 0]]
      self.mapping.extend_box(self.id, xlegend+25, ylegend+25)

    cr.restore()
    cr.restore()
    self.mapping.set_curve_values(self, legends, self.s_case, "reac")


  def _draw_section(self, cr, struct, x, y, barre, end=False, color=None):
    """Dessine une extrémité de barre : x, y sont les décalages par rapport au milieu de la barre."""
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_line_width(2)
    angle = -struct.Angles[barre]
    if end:
      angle += math.pi
    cr.translate(x, y)
    cr.rotate(angle)
    h = 20
    l = 15
    cr.move_to(l, -h)
    cr.rel_line_to(-l, 0)
    cr.rel_line_to(0, 2*h)
    cr.rel_line_to(l, 0)
    cr.stroke()
    cr.set_line_width(1)
    for i in range(3):
      cr.move_to(l, h*(-0.8+2.*i/3))
      cr.rel_line_to(-l, 4)
      cr.stroke()
    cr.restore()

  def draw_new_bar(self, tab, struct, new):
    """Redessine le diagramme d'une barre"""
    self.s_bar = new
    self.set_scale(struct)
    self.del_patterns()
    #tab.del_surface()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()

class SigmaDrawing(ChildDrawing):

  def __init__(self, mapping, id_study, parent):
    self.parent = parent
    self.id_study = id_study
    self.id = Drawing.class_counter
    Drawing.class_counter += 1
    self.childs = {}
    parent.childs[self.id] = self
    self.mapping = mapping
    self.title_id = None
    self.chart_scale = None
    self.chart_zoom = {}
    self.has_pattern = False

  def set_status(self, status):
    """Blocage du status pour ce type de dessin"""
    self.status = 2
    
  def get_menu_options(self):
    """Retourne les options du menu contextuel"""
    options = {}
    options['Title'] = self.options.get('Title', True)
    options['Save'] = True
    options['Select'] = True
    options['Sigma'] = True
    options['Case'] = True
    return options

  def set_drawing_prefs(self, prefs, tab, study):
    """Initialise les préférences du dessin"""
    self.options = {'Title': True, 'Sync': False}
    self.status = 2 # laisser
    self.s_bar = prefs['bar']
    if 'u' in prefs:
      self.u = prefs['u']
    else:
      self.u = 0.5
    if 's_case' in prefs:
      self.s_case = prefs['s_case']
    else:
      self.s_case = 0 # tester

    if 'struct_scale' in prefs:
      self.struct_scale = prefs['struct_scale']
    if 'chart_scale' in prefs:
      self.chart_scale = prefs['chart_scale']
    else:
      self.chart_scale = None
    self.set_geometric_prefs(tab, study, prefs)
    self._add_info_prefs(prefs)


  def set_dim(self, study):
    """Calcule la largeur et la hauteur"""
    struct = study.rdm.struct
    self.H = H = struct.GetH(self.s_bar)
    self.v = v = struct.Getv(self.s_bar)
    if self.H is None or self.v is None:
      return
    self.height = H*self.struct_scale
    self.set_height(struct)
    self.set_width(study.rdm)

  def set_all_sizes(self, tab, study):
    """Calcule la taille, l'échelle et la position d'un dessin (structure seule)"""
    rdm = study.rdm
    struct = rdm.struct
    size = Const.SIGMA_SIZE_MAX
    self.H = H = struct.GetH(self.s_bar)
    self.v = v = struct.Getv(self.s_bar)
    if self.H is None or self.v is None:
      return
    try:
      self.struct_scale
    except AttributeError:
      self.struct_scale = size / H
    self.height = H*self.struct_scale
    self.set_height(rdm.struct)
    self.set_width(rdm)

  def set_width(self, rdm):
    """Calcule la largeur du dessin à partir des valeurs des contraintes normales"""
    size = Const.SIGMA_SIZE_MAX
    if self.status in self.chart_zoom:
      zoom = self.chart_zoom[self.status]
    else:
      zoom = 1
    self.sig_inf, self.sig_sup = self.get_sigma(rdm)
    s1, s2 = self.sig_inf, self.sig_sup
    maxi = max(abs(s1), abs(s2))
    if maxi == 0:
      chart_scale = 1
      self.width = size
      dx1 = dx2 = size/2
    else:
      chart_scale = size / 2 / maxi*zoom
      if maxi*chart_scale > size:
        chart_scale = size/maxi
      elif maxi*chart_scale < size/10:
        chart_scale = size/10/maxi
      dx1, dx2 = self.get_axe_x(s1, s2, chart_scale)
      self.width = dx1+dx2 # largeur du dessin en px
    self.chart_scale = chart_scale
    self.dec_x = -dx1

  def set_height(self, struct):
    """Vérifie la hauteur du dessin des contraintes"""
    size = Const.SIGMA_SIZE_MAX
    if self.height > 3*size:
      self.height = 3*size
      self.struct_scale = self.height / self.H
    elif self.height < 0.5*size:
      self.height = int(0.5*size)
      self.struct_scale = self.height / self.H
    self.dec_y = (self.H-self.v)*self.struct_scale


  def zoom_best(self, coef, struct):
    if self.struct_scale is None:
      return
    self.set_position()

  def set_zoom(self, zoom):
    """Modifie les attributs pour le zoom"""
    max1 = 3*Const.SIGMA_SIZE_MAX
    if zoom == "+":
      coef = 1/0.9
    elif zoom == "-":
      coef = 0.9
    else:
      coef = zoom/self.struct_scale
    if coef > 1:
      h = float(self.height*coef)
      if h > max1: # limitation
        h = max1
      self.height = int(h)
    else:
      self.height = int(self.height*coef)

  def set_scale(self, struct):
    """Ajuste l'échelle de la structure pour tenir dans la boîte"""
    self.struct_scale = abs(self.height / self.H)
    self.set_height(struct)

  def set_position(self):
    """Place le dessin à sa position optimale"""
    m = Const.AREA_MARGIN_MIN
    dx = self.width/2 + m - self.x0
    dy = 0
    self.x0 = self.width/2 + m
    if self.y0 < self.height:
      dy = self.height+m - self.y0
      self.y0 = self.height+m
    # déplacement échelle, titre
    if self.id in self.mapping.infos:
      for elem in self.mapping.infos[self.id].values():
        x, y, w, h = elem.box
        x = max(x+dx, m)
        y = y+dy
        elem.box = (x, y, w, h)


  def update_s_data(self, rdm, barres):
    """Met à jour s_case, s_cases, s_bar, s_curve dans SigmaDrawing"""
    #if not self.s_case in self.parent.s_cases:
    #  try:
    #    self.s_case = self.parent.s_cases[0]
    #  except IndexError:
    #    return False
    if not self.s_bar is None and not self.s_bar in barres:
      if len(barres) >= 1:
        self.s_bar = barres[0]
        self.chart_scale = None
        self.struct_scale = None
      else:
        return False

  def get_is_sigma_drawing(self):
    """Retourne vrai si le dessin est une instance de SigmaDrawing"""
    return True

  def get_xml_prefs(self, parent):
    """Crée le noeud xml pour les préférences communes aux dessins pour la sauvegarde des préférences"""
    if self.chart_scale is None or self.struct_scale is None:
      return None
    node = ET.SubElement(parent, "sigma_child")
    self.set_xml_prefs(node)
    return node

  def set_xml_prefs(self, node):
    """Crée les attribues pour les préférences communes aux dessins pour la sauvegarde des préférences"""
    node.set("x0", str(self.x0))
    node.set("y0", str(self.y0))
    node.set("chart_scale", str(self.chart_scale))
    node.set("struct_scale", str(self.struct_scale))
    node.set("u", str(self.u))
    node.set("bar", str(self.s_bar))
    node.set("s_case", str(self.s_case))
    val = self.options['Title'] and "true" or "false"
    node.set("show_title", val)
    infos = self.mapping.infos[self.id]
    if not self.title_id is None:
      box = infos[self.title_id].box
      box = [str(i) for i in box]
      box.append(infos[self.title_id].text)
      val = ",".join(box)
      node.set("title", val)

  def get_combi_view(self, rdm, is_info=False):
    """Retourne la vue des boutons des cas et combinaisons"""
    return self._get_combi_view2(rdm, False)


  def expose_drawing(self, cr, study):
    """Lance la création des pattern"""
    rdm = study.rdm
    struct = rdm.struct
    units = struct.units
    unit_C = study.get_unit_name('C')
    self.p_infos = {}
    if self.H is None or self.v is None:
      self._draw_error_chart(cr, study, unit_C, Const.SIGMA_SIZE_MAX)
      self.has_pattern = True
      return
    
    if self.struct_scale is None:
      self.set_scale(struct)
    self.set_width(rdm)
    s1, s2 = self.sig_inf, self.sig_sup
    if s1 is None or s2 is None:
      self._draw_error_chart(cr, study, unit_C, Const.SIGMA_SIZE_MAX)
      self.has_pattern = True
      return

    self.mapping.clear(self.id)
    self._push_chart_group(cr, self.dec_x, self.dec_y, units['C'], unit_C)
    self._push_title_group(study, cr)
    self.has_pattern = True

  def _push_title_group(self, study, cr):
    """Crée le pattern pour le titre du dessin"""
    struct = study.rdm.struct
    title_id = self.title_id
    tag = self.options.get('Title', True)
    if not tag:
      return
    cr.push_group()
    cr.set_font_size(Const.FONT_SIZE)
    name = struct.GetBarreName(self.s_bar)
    if name is None:
      name = "?"
    if title_id is None:
      text = '%s (sur %s u=%s)' % (study.name, name, self.u)
      text2 = study.name
      x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
      x = self.x0+50
      y = self.y0-40
      box = (x, y, int(width+8), int(height+12))
      obj = MText(box, text2, title_id)
      self.title_id = obj.id
    else:
      obj = self.mapping.infos[self.id][title_id]
      text = '%s (sur %s u=%s)' % (obj.text, name, self.u)
      x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
      x, y, w, h = obj.box
      box = (x, y, int(width+8), int(height+12))
      obj.box = box
    cr.translate(x, y)
    cr.move_to(4, height+5)
    cr.show_text(text)
    self.p_infos[obj.id] = cr.pop_group()
    self.mapping.set_info(self.id, obj)

  def _draw_error_chart(self, cr, study, unit_C, size):
    """Dessine le graphe en cas d'erreur dans les données"""
    self.width = size
    self.height = size
    self.mapping.clear(self.id)
    self._push_error_group(cr, unit_C)
    self._push_title_group(study, cr)

  def _push_error_group(self, cr, unit_C):
    """Crée les pattern pour le graphe non disponible"""
    self.chart_scale = None
    self.struct_scale = None
    x_axe1 = self.x0 -self.width/2
    y_axe1 = self.y0
    x_axe2 = self.x0
    y_axe2 = self.y0 + self.height/2
    self._get_mapping_data(x_axe1, y_axe1, x_axe2, y_axe2)
    cr.push_group()
    cr.set_font_size(Const.FONT_SIZE)
    self._draw_axis(cr, x_axe1, y_axe1, x_axe2, y_axe2, unit_C)
    surface = cairo.ImageSurface.create_from_png("glade/process-stop.png")
    cr.set_source_surface(surface, self.x0, self.y0)
    cr.paint()
    self.p_struct = cr.pop_group()

  def _push_chart_group(self, cr, dec_x, dec_y, factor_C, unit_C):
    """Gère l'ensemble des fonctions du tracé des contraintes"""
    x_axe1 = self.x0 + dec_x
    y_axe1 = self.y0
    x_axe2 = self.x0
    y_axe2 = self.y0 + dec_y
    self._get_mapping_data(x_axe1, y_axe1, x_axe2, y_axe2)
    cr.push_group()
    cr.set_font_size(Const.FONT_SIZE)
    self._draw_axis(cr, x_axe1, y_axe1, x_axe2, y_axe2, unit_C)
    self._draw_sigma(cr, dec_y, factor_C)
    self.p_struct = cr.pop_group()

  def _draw_axis(self, cr, x_axe1, y_axe1, x_axe2, y_axe2, unit_C):
    """Dessine les axes du repère et leur légende"""
    self._draw_one_axis(cr, x_axe1, y_axe1, self.width, 0.)
    self._draw_one_axis(cr, x_axe2, y_axe2, self.height, -math.pi/2)
    cr.move_to(x_axe1+self.width-30, self.y0-10)
    cr.show_text('\u03C3 (%s)' % unit_C)
    cr.move_to(x_axe2-10, y_axe2-self.height-10)
    cr.show_text('y')

  def _draw_one_axis(self, cr, x, y, size, angle):
    """Dessine un axe de centre x, y avec flèche"""
    cr.save()
    cr.translate(x, y)
    cr.rotate(angle)
    cr.set_line_width(1)
    a = 6 # arrow
    cr.move_to(0, 0)
    cr.rel_line_to(size, 0)
    cr.stroke()
    cr.move_to(size-a, -a)
    cr.rel_line_to(a+1, a)
    cr.rel_line_to(-a-1, a)
    cr.close_path()
    cr.fill()
    cr.stroke()
    cr.restore()

  def _draw_sigma(self, cr, dec_y, factor_C):
    """Dessine les flèches de contrainte"""
    if self.chart_scale is None or math.isinf(self.chart_scale):
      return
    x_axe, y_axe = self.x0, self.y0
    H, v = self.H, self.v # caractéristiques section droite
    s1, s2 = self.sig_inf, self.sig_sup
    cr.save()
    cr.set_source_rgb(1, 0, 0)
    y = v
    n = 8 # n arrows
    dy = H / n
    struct_scale = self.struct_scale
    chart_scale = self.chart_scale
    sig0 = s2*chart_scale
    for i in range(n+1):
      dsig = (s1-s2)*i*dy/H*chart_scale
      sig = dsig+sig0
      self._draw_arrow(cr, x_axe, sig, y_axe-y*struct_scale)
      y -= dy
    self._draw_attache(cr, dec_y)
    self._draw_values(cr, dec_y, factor_C)
    cr.restore()

  def _draw_values(self, cr, dec_y, factor_C):
    """Dessine les textes des valeurs des contraintes"""
    chart_scale = self.chart_scale
    s1, s2 = self.sig_inf, self.sig_sup
    text1 = function.PrintValue(s1, factor_C)
    text2 = function.PrintValue(s2, factor_C)
    cr.save()
    cr.translate(self.x0, self.y0+dec_y)
    x_bearing, y_bearing, width, height = cr.text_extents(text1)[:4]
    dx = s1 > 0 and 1 or -width
    cr.move_to(s1*chart_scale+dx, 20)
    cr.show_text(text1)
    cr.restore()
    cr.save()
    cr.translate(self.x0, self.y0-self.height+dec_y)
    x_bearing, y_bearing, width, height = cr.text_extents(text2)[:4]
    dx = s2 > 0 and 1 or -width
    cr.move_to(s2*chart_scale+dx, -20+height)
    cr.show_text(text2)
    cr.restore()

    sG = ((self.H-self.v)*s2+self.v*s1) / self.H
    if abs(sG) > max(abs(s1), abs(s2))/1e4:
      textG = function.PrintValue(sG, factor_C)
      cr.save()
      cr.translate(self.x0, self.y0)
      x_bearing, y_bearing, width, height = cr.text_extents(textG)[:4]
      dx = sG > 0 and 1 or -1.5*width
      cr.move_to(sG*chart_scale+dx, -5)
      cr.show_text(textG)
      cr.restore()


  def _draw_attache(self, cr, dec_y):
    """Dessine la ligne qui relie sigma sup et inf"""
    chart_scale = self.chart_scale
    s1, s2 = self.sig_inf, self.sig_sup
    H, v = self.H, self.v # caractéristiques section droite
    cr.save()
    cr.set_line_width(1)
    px = max(cr.device_to_user_distance(1, 1))
    cr.set_dash([3 * px], 0)
    cr.translate(self.x0, self.y0 + dec_y)
    cr.move_to(s1*chart_scale, 0)
    cr.line_to(s2*chart_scale, -self.height)
    cr.stroke()
    cr.restore()


  def _draw_arrow(self, cr, x0, sig, y):
    """Dessine une flèche de contrainte"""
    #print("_draw_arrow", x0, sig, y)
    if abs(sig) < 2:
      return
    cr.save()
    cr.set_line_width(1)
    cr.translate(x0, y)
    dx = sig < 0 and -2 or 2
    cr.move_to(dx, 0)
    cr.rel_line_to(sig-2*dx, 0)
    cr.stroke()

    if abs(sig) <= 5:
      cr.restore()
      return

    if sig > 0:
      d = 5
    else:
      d = -5
    # arrow
    cr.move_to(sig-dx, 0)
    cr.rel_line_to(-d, -d)
    cr.rel_line_to(0, 2*d)
    cr.close_path()
    cr.fill()
    cr.stroke()
    cr.restore()

  def paint_drawing(self, cr, alpha=1.):
    cr.save()
    cr.set_source(self.p_struct)
    cr.paint_with_alpha(alpha)
    for p in self.p_infos.values():
      cr.set_source(p)
      cr.paint_with_alpha(alpha)
    if hasattr(self, "p_select"):
      cr.set_source(self.p_select)
      cr.paint_with_alpha(alpha)
    cr.restore()

  def paint_drawing4(self, cr, alpha=1.):
    """Dessine tous les patterns sauf le pattern des legendes des courbes"""
    cr.save()
    cr.set_source(self.p_struct)
    cr.paint_with_alpha(alpha)
    cr.restore()


  def get_axe_x(self, s1, s2, scale):
    """Retourne les largeurs du graphe côté négatif et positif"""
    mini = 50
    #scale = self.chart_scale
    if s1 == 0 and s2 == 0:
      return mini, mini
    if s1*s2 < 0:
      if s1 < 0:
        dx1 = -s1*scale
        dx2 = s2*scale
      else:
        dx1 = -s2*scale
        dx2 = s1*scale
    elif s1 < 0: # s1 et s2 < 0
      dx1 = -(min(s1, s2))*scale
      dx2 = mini
    else: # s1 et s2 > 0
      dx1 = mini
      dx2 = max(s1, s2)*scale
    return max(dx1, mini), max(dx2, mini)


  def get_sigma(self, rdm):
    """Retourne les valeurs des contraintes""" 
    Char = rdm.GetCharByNumber(self.s_case)

    return rdm.GetSigma(Char, self.u, self.s_bar)

  def _get_mapping_data(self, x1_d, y1_d, x2_d, y2_d):
    """Calcule les points et barres pour le mapping"""
    mapping = self.mapping
    margin = 30
    mapping.nodes[self.id] = {}
    bar = Barre("X", (x1_d, y1_d, x1_d+self.width, y1_d))
    mapping.bars.setdefault(self.id, []).append(bar)
    bar = Barre("Y", (x2_d, y2_d, x2_d, y2_d-self.height))
    mapping.bars[self.id].append(bar)
    mapping.set_box(self.id, (x1_d-1.5*margin, y2_d-self.height-margin, self.width+3*margin, self.height+2.6*margin))

  def get_max_scale(self, value, study):
    """Vérifie si la nouvelle échelle des y n'est pas trop grande"""
    size = Const.SIGMA_SIZE_MAX*4
    scale = self.struct_scale
    w, h = self.width, self.height
    coef = value/scale
    max_size = max(w, h)*coef
    if max_size <= size:
      return True
    return False

  def dim_chart_scale(self, size):
    """Redimensionne l'échelle du graphe si trop grande ou trop petite"""
    if self.chart_scale is None:
      return
    s1, s2 = self.sig_inf, self.sig_sup
    if s1 == 0 and s2 == 0:
      return
    maxi = max(abs(s1), abs(s2))
    if maxi*self.chart_scale > size:
      self.chart_scale = size/maxi
    elif maxi*self.chart_scale < size/10:
      self.chart_scale = size/10/maxi
    
  def get_max_scale2(self, value, study):
    """Vérifie si la nouvelle échelle des contraintes n'est pas trop grande"""
    size = Const.SIGMA_SIZE_MAX
    s1, s2 = self.sig_inf, self.sig_sup
    scale = self.chart_scale
    maxi = max(abs(s1), abs(s2))*scale
    coef = value/scale
    if maxi <= size:
      return True
    return False

  def draw_tools(self, study, tab):
    """Dessine la barre d'outils du dessin"""
    layout = tab.layout
    Main = tab._main
    hbox = Gtk.HBox(False, 10)
    if not self.chart_scale is None and not self.struct_scale is None:
      b = Gtk.Button()
      function.add_icon_to_button2(b, Gtk.STOCK_GO_FORWARD)
      b.set_tooltip_text("Modifier l'échelle des contraintes")
      b.connect('clicked', tab.on_show_scale_box, self, "chart")
      hbox.pack_start(b, False, False, 0)
      b = Gtk.Button()
      function.add_icon_to_button2(b, Gtk.STOCK_GO_UP)
      b.set_tooltip_text("Modifier l'échelle des y")
      b.connect('clicked', tab.on_show_scale_box, self, "struct")
      hbox.pack_start(b, False, False, 0)
      b = Gtk.Button()
      function.add_icon_to_button2(b, Gtk.STOCK_PAGE_SETUP)
      b.set_tooltip_text("Modifier la position")
      b.connect('clicked', tab.on_show_scale_box, self, "pos")
      hbox.pack_start(b, False, False, 0)
      if len(study.rdm.struct.GetBars()) > 1:
        b = Gtk.Button()
        function.add_icon_to_button2(b, Gtk.STOCK_MEDIA_FORWARD)
        b.set_tooltip_text("Barre suivante")
        b.connect('clicked', tab.on_select_next, self, study)
        hbox.pack_start(b, False, False, 0)
        b = Gtk.Button()
        function.add_icon_to_button2(b, Gtk.STOCK_MEDIA_REWIND)
        b.set_tooltip_text("Barre précédente")
        b.connect('clicked', tab.on_select_back, self, study)
        hbox.pack_start(b, False, False, 0)
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_CLOSE)
    b.set_tooltip_text("Fermer")
    b.connect('clicked', Main.on_del_drawing, self)
    hbox.pack_start(b, False, False, 0)
    hbox.show_all()
    x, y, w, h = self.mapping.box[self.id]
    x = x + 25
    y = y + h - 28
    layout.put(hbox, int(x), int(y))
    return hbox

  def draw_new_bar(self, tab, struct, new):
    """Redessine le diagramme d'une barre"""
    self.s_bar = new
    self.del_patterns()
    #tab.del_surface()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()



# ----------------------------------------------------------------
# ----------------------------------------------------------------
# ----------------------------------------------------------------

class Study(object):

  class_counter = 0

  def __init__(self, path):
    self.id = Study.class_counter
    Study.class_counter += 1
    self.path = path
    self.name = os.path.basename(path)[:-4]
    self._add_rdm(path)
      #affichage des erreurs dans le terminal
      #self.rdm.PrintErrorConsole()

  def __del__(self):
    pass
    #Study.class_counter -= 1

  def _add_rdm(self, path):
    """Ajoute un dessin dans une étude"""
    structure = classRdm.StructureFile(path)
    self.rdm = classRdm.R_Structure(structure)

  def get_max(self, drawing, Char=None):
    """Retourne le maximum des sollicitations de l'ensemble des chargements ou d'un chargement si précisé"""
    #print("get_max")
    status = drawing.status
    di = {4: 'N', 5: 'V', 6: 'M', 7: 'u'}
    s_cases = drawing.s_cases
    n_cases = len(s_cases)
    if n_cases == 0:
      return None
    if Char is None:
      return self.rdm.GetCombiMax(di[status])
    return self.rdm.GetCombiMax(di[status], Char)


  def _get_soll_max(self):
    """Retourne le maximum des sollicitations N, V, M toutes combinaisons ou cas confondus"""
    #print("get_max_all_status")
    maxi = 0.
    for mode in ['N', 'V', 'M']:
      val = self.rdm.GetCombiMax(mode)
      if val > maxi:
        maxi = val
    return maxi


  def _get_max_max(self): # dépréciée
    """Retourne le maximum toute combinaison confondue"""
    #print("classDrawing::_get_max_max", self.status)
    if self.status == 4:
      maxi = self.rdm.CaseMax['N']['__all__']
    elif self.status == 5:
      maxi = self.rdm.CaseMax['V']['__all__']
    elif self.status == 6:
      maxi = self.rdm.CaseMax['M']['__all__']
    elif self.status == 7:
      maxi = self.rdm.CaseMax['u']['__all__']
    else:
      print("Error::classDrawing status error")
      return 0
    return maxi

  def get_unit_name(self, key):
    """Retourne le nom d'une unité"""
    value = self.rdm.struct.units[key]
    units = Const.UNITS[key]
    for name, elem in units.items():
      if value == elem:
        return name
    units = Const.UNITS2[key]
    for name, elem in units.items():
      if value == elem:
        return name
    print("Undefined unit in classDrawing::get_unit_name")
    return "(?)"


class EmptyStudy(Study):
  class_counter = 0

  def __init__(self):
    self.id = Study.class_counter
    Study.class_counter += 1
    EmptyStudy.class_counter += 1
    self.path = None
    self.name = "Nouvelle étude %d" % EmptyStudy.class_counter
    self._add_rdm(None)

  def _add_rdm(self, path=None):
    string = Const.XML % (Const.SITE_URL, Const.VERSION)
    xml = ET.ElementTree(ET.fromstring(string))
    self.rdm = classRdm.EmptyRdm(xml)

#-------------------------------------------------
#
#      ONGLET DE LA FENETRE DE DESSIN
#
#-------------------------------------------------

class Tab(object):

  def __init__(self, main_app):
    # initialisation de l'objet
    self.studies = main_app.studies
    self._main = main_app
    self._fg = FGColor()
    self.mapping = AreaMapping()
    self.drawings = {}
    self.active_drawing = None
    self.is_selected = False
    self.status = 0
    self._ini_layout()


# inutile?
  def get_parent_drawings(self):
    """Retourne la liste des dessins parents"""
    resu = []
    for d in self.drawings.values():
      if d.parent is None:
        resu.append(d)
    return resu

  def add_drawing(self, sibling, study):
    """Ajoute un diagramme dans un onglet à partit du drawing sibling"""
    print("add_drawing")
    id_study = sibling.id_study
    prefs = copy.copy(sibling.options)
    prefs["x0"] = sibling.x0
    prefs["y0"] = sibling.y0 + 50
    prefs["struct_scale"] = sibling.struct_scale
    drawing = Drawing(self.mapping, id_study)
    drawing.set_drawing_prefs(prefs, self, study)
    drawing.copy_selected_objects(sibling)
    self.drawings[drawing.id] = drawing
    self.active_drawing = drawing
    #self.del_surface()
    self.configure_event(self.layout)
    self.remove_tools_box()
    self.layout.queue_draw() # déclenche draw_event

  def add_bar_drawing(self, widget, sibling, study):
    if self.is_selected and self.is_selected[0] == "entry":
      return
    rdm = study.rdm
    barre = sibling.s_bar
    if barre is None:
      barre = rdm.struct.FirstBarre()
    if barre is None:
      return # pas de zoom pour les arcs
    id_study = study.id
    prefs = copy.copy(sibling.options)
    prefs['bar'] = barre
    drawing = BarreDrawing(self.mapping, id_study, sibling)
    drawing.set_drawing_prefs(prefs, self, study)
    drawing.copy_selected_objects(sibling)
    drawing.s_bar = barre
    self.drawings[drawing.id] = drawing
    self.active_drawing = drawing
    self.remove_tools_box()
    self.remove_entry_box()
    #self.del_surface()
    self.configure_event(self.layout)
    self.layout.queue_draw()


  def add_char_drawing(self, sibling):
    """Ajoute un dessin de type CharDrawing"""
    id_study = sibling.id_study
    prefs = {}
    prefs["x0"] = sibling.x0
    prefs["y0"] = sibling.y0 + 150
    prefs["struct_scale"] = sibling.struct_scale
    drawing = CharDrawing(self.mapping, id_study, sibling)
    drawing.set_drawing_prefs(prefs, self, None)
    self.drawings[drawing.id] = drawing
    #self.del_surface()
    self.configure_event(self.layout)
    self.remove_tools_box()
    self.layout.queue_draw() # déclenche draw_event

  def add_sigma_drawing(self, sibling, study):
    """Ajoute un dessin de type SigmaDrawing"""
    id_study = sibling.id_study
    rdm = study.rdm
    barre = sibling.s_bar
    if barre is None:
#finir pour les arcs
      barre = rdm.struct.FirstBarre()
    if barre is None:
      return # pas de zoom pour les arcs
    prefs = {'bar': barre}
    if sibling.get_is_sigma_drawing():
      prefs["struct_scale"] = sibling.struct_scale
      prefs["chart_scale"] = sibling.chart_scale
    prefs["x0"] = sibling.x0 + 50
    prefs["y0"] = sibling.y0 + 100
    prefs["s_case"] = sibling.s_case
    drawing = SigmaDrawing(self.mapping, id_study, sibling)
    drawing.set_drawing_prefs(prefs, self, study)
    self.drawings[drawing.id] = drawing
    #self.del_surface()
    self.configure_event(self.layout)
    self.remove_tools_box()
    self.layout.queue_draw() # déclenche draw_event

# inutile
  def get_drawing_by_id_study(self):
    """Retourne un dictionnaire de liste des drawings pour chaque id_study"""
    di = {}
    for drawing in self.drawings.values():
      id_study = drawing.id_study
      di.setdefault(id_study, []).append(drawing)
    return di

  def _get_first_drawing(self):
    """Retourne un drawing"""
    try:
      return list(self.drawings.values())[0]
    except IndexError:
      #print("_get_first_drawing::debug drawing is None")
      return None

  def _remove_study(self, id):
    """Supprime une étude si aucun drawing n'en dépend"""
    for drawing in self.drawings.values():
      if drawing.id_study == id:
        return
    del(self.studies[id])

  def remove_drawings_by_study(self, drawing):
    """Supprime tous les dessins de l'étude donnée"""
    self.is_selected = False
    id_study = drawing.id_study
    drawings = self.drawings
    for drawing in drawings.values():
      id = drawing.id_study
      if not id == id_study:
        continue
      del(self.drawings[drawing.id])
      self.mapping.remove_map(drawing.id)
    self._remove_study(id_study)
    self.active_drawing = self._get_first_drawing()
    #self.del_surface()
    self.remove_tools_box()
    self.remove_entry_box()
    self.configure_event(self.layout)
    self.layout.queue_draw() # déclenche draw_event

  def remove_drawing(self, drawing):
    """Supprime un drawing"""
    is_changed = False
    if drawing is self.active_drawing:
      is_changed = True
    self.is_selected = False
    for key in drawing.childs:
      is_changed = True
      self.mapping.remove_map(key)
      del(self.drawings[key])
    drawing_id = drawing.id
    id_study = drawing.id_study
    if not drawing.parent is None:
      parent = drawing.parent
      del(parent.childs[drawing_id])
      parent.del_patterns()
    del(self.drawings[drawing_id])
    self.mapping.remove_map(drawing_id)
    self._remove_study(id_study)
    if is_changed:
      self.active_drawing = self._get_first_drawing()

    #self.del_surface()
    self.remove_tools_box()
    self.remove_entry_box()
    self.configure_event(self.layout)
    self.layout.queue_draw() # déclenche draw_event

  def add_empty_study(self, prefs, x, y):
    """Ajoute une nouvelle étude"""
    study = EmptyStudy()
    id = study.id
    if x:
      prefs['x0'], prefs['y0'] = int(x), int(y)
    drawing = Drawing(self.mapping, id)
    drawing.set_drawing_prefs(prefs, self, study)
    drawing.s_case = None
    self.studies[id] = study
    self.drawings[drawing.id] = drawing
    self.active_drawing = drawing
    return study, drawing

  def add_study(self, path, options):
    """Ajoute une étude"""
    study = Study(path)
    id = study.id
    if study.rdm.status == -1: # xml error
      return study, None
    prefs = self.get_drawings_prefs(study.rdm.struct, options)
    drawings = []
    for pref in prefs:
      drawing = Drawing(self.mapping, id)
      drawing.set_drawing_prefs(pref, self, study)
      drawing.set_cases_ini(study.rdm)
      self.drawings[drawing.id] = drawing
      drawings.append(drawing)
      if 'b_child' in pref:
        bdrawing = BarreDrawing(self.mapping, id, drawing)
        bdrawing.set_drawing_prefs(pref['b_child'], self, study)
        self.drawings[bdrawing.id] = bdrawing
      if 'c_child' in pref:
        cdrawing = CharDrawing(self.mapping, id, drawing)
        cdrawing.set_drawing_prefs(pref['c_child'], self, study)
        self.drawings[cdrawing.id] = cdrawing
      if 'sigma_child' in pref:
        for i, elem in enumerate(pref['sigma_child']):
          sdrawing = SigmaDrawing(self.mapping, id, drawing)
          sdrawing.set_drawing_prefs(pref['sigma_child'][i], self, study)
          self.drawings[sdrawing.id] = sdrawing
    self.studies[id] = study
    # ajout de l'attribut pour les lignes d'influence
    for drawing in drawings:
      if drawing.status == 8:
        study.influ_rdm = classRdm.Influ_Structure(study.rdm.struct)
        break
    try:
      self.active_drawing = drawings[0]
    except IndexError:
      self.active_drawing = None
    return study, drawings

  def _set_option_prefs(self, xml, di, options):
    """Récupère les préférences relatives à l'affichage du nom des barres, noeuds ... """
    #try:
    val = xml.get("show_title")
    if val is None:
      di['Title'] = options['Title']
    elif val == "true":
      val = True
      di['Title'] = val
    else:
      val = False
      di['Title'] = val
    val = xml.get("bar_name")
    if val is None:
      di['Barre'] = options['Barre']
    elif val == "true":
      val = True
      di['Barre'] = val
    else:
      val = False
      di['Barre'] = val
    val = xml.get("node_name")
    if val is None:
      di['Node'] = options['Node']
    elif val == "true":
      val = True
      di['Node'] = val
    else:
      val = False
      di['Node'] = val
    val = xml.get("axis")
    if val is None:
      di['Axis'] = options['Axis']
    elif val == "true":
      val = True
      di['Axis'] = val
    else:
      val = False
      di['Axis'] = val
    val = xml.get("series")
    if val is None:
      di['Series'] = options['Series']
    else:
      option = val.split(',')[0]
      if option == "true":
        option = True
      else:
        option = False
      di['Series'] = option



  def get_drawings_prefs(self, struct, options):
    """Lit les préférences du ou des dessins dans le fichier xml"""
    prefs = []
    XML = struct.XML
    default = {'Title': options['Title'], 'Barre': options['Barre'], 'Node': options['Node'], 'Axis': options['Axis'], 'Series': options['Series']}
    elem = XML.find('draw')
    if elem is None:
      prefs.append(default)
      return prefs
    nodes = elem.iter('drawing')
    for xml in nodes:
      di = {}
      self._set_option_prefs(xml, di, options)
      try:
        di['x0'] = float(xml.get("x0"))
        di['y0'] = float(xml.get("y0"))
        scale = float(xml.get("scale"))
        if not scale:
          raise ValueError
        di['struct_scale'] =scale
      except (TypeError, ValueError):
        pass
      status = xml.get("status")
      if not status is None:
        di['status'] = status
      values = xml.get("values")
      if not values is None:
        di['values'] = values
      val = xml.get("title")
      if not val is None:
        val = val.split(',')
        di['title'] = val
      val = xml.get("scale_pos")
      if not val is None:
        val = val.split(',')
        di['scale_pos'] = val
      val = xml.get("series")
      if not val is None:
        val = val.split(',')
        del(val[0])
        di['series_pos'] = val
      val = xml.get("influ_bars")
      if not val is None:
        val = val.split(',')
        for i, elem in enumerate(val):
          if elem[0] == '*': # Conversion en entier pour les super barres
            elem = int(elem[1:])
            val[i] = elem
        di['s_influ_bars'] = val
      childs = xml.iter('b_child')
      #if len(childs) == 1:
      for child in childs:
        #child = childs[0]
        di1 = {}
        error = False
        try:
          di1['x0'] = float(child.get("x0"))
          di1['y0'] = float(child.get("y0"))
          scale = float(xml.get("scale"))
          if not scale:
            raise ValueError
          di1['struct_scale'] =scale
          #di1['struct_scale'] = float(child.get("scale"))
        except (TypeError, ValueError):
          error = True
        val = child.get("status")
        if not val is None:
          di1['status'] = val
        val = child.get("bar")
        if not val is None:
          if val in struct.UserBars:
            di1['bar'] = val
          else:
            try:
              val = int(val)
              if not val in struct.Barres:
                error = True
              di1['bar'] = val
            except ValueError:
              error = True
        val = child.get("title")
        if not val is None:
          val = val.split(',')
          di1['title'] = val
        val = child.get("scale_pos")
        if not val is None:
          val = val.split(',')
          di1['scale_pos'] = val
        self._set_option_prefs(xml, di1, options)

        values = child.get("values")
        if not values is None:
          di1['values'] = values
        if not error:
          di['b_child'] = di1
      childs = xml.iter('c_child')
      for child in childs:
      #if len(childs) == 1:
        #child = childs[0]
        di1 = {}
        error = False
        try:
          di1['x0'] = float(child.get("x0"))
          di1['y0'] = float(child.get("y0"))
          scale = float(xml.get("scale"))
          if not scale:
            raise ValueError
          di1['struct_scale'] =scale
          #di1['struct_scale'] = float(child.get("scale"))
        except (TypeError, ValueError):
          error = True
        val = child.get("title")
        if not val is None:
          val = val.split(',')
          di1['title'] = val
        val = child.get("scale_pos")
        if not val is None:
          val = val.split(',')
          di1['scale_pos'] = val
        val = child.get("series")
        if not val is None:
          val = val.split(',')
          di1['series_pos'] = val
        self._set_option_prefs(xml, di1, options)
        if not error:
          di['c_child'] = di1

      childs = xml.iter('sigma_child')
      for child in childs:
        di1 = {}
        error = False
        try:
          di1['x0'] = float(child.get("x0"))
          di1['y0'] = float(child.get("y0"))
          di1['u'] = float(child.get("u"))
          di1['chart_scale'] = float(child.get("chart_scale"))
          di1['struct_scale'] = float(child.get("struct_scale"))
          di1['s_case'] = int(child.get("s_case"))
        except (TypeError, ValueError):
          error = True
        val = child.get("bar")
        if not val is None:
          if val in struct.UserBars:
            di1['bar'] = val
          else:
            try:
              val = int(val)
              if not val in struct.Barres:
                error = True
              di1['bar'] = val
            except ValueError:
              error = True
        val = child.get("title")
        if not val is None:
          val = val.split(',')
          di1['title'] = val
        self._set_option_prefs(xml, di1, options)
        if not error:
          di.setdefault('sigma_child', []).append(di1)

      prefs.append(di)
    if len(prefs) == 0:
      prefs.append(default)
    return prefs


  def _ini_layout(self):
    """Crée le layout pour le dessin et les boutons du dessin"""
    self.area_w = self.area_h = None
    sw = self.sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    layout = self.layout = Gtk.Layout()
    layout.modify_bg(Gtk.StateType.NORMAL, self._fg.get_white_color()) # keep
    layout.set_events(Gdk.EventMask.POINTER_MOTION_MASK # enlever ???
		| Gdk.EventMask.BUTTON_PRESS_MASK
		| Gdk.EventMask.BUTTON_RELEASE_MASK
		| Gdk.EventMask.KEY_PRESS_MASK
		| Gdk.EventMask.LEAVE_NOTIFY_MASK
		| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    sw.add(layout)
    sw.show_all()

  def _get_unit(self):
    """Retourne l'unité"""
    unit = self.unit_conv['F']
    if unit == 1: text = 'N'
    elif unit == 10: text = 'daN'
    elif unit == 1000: text = 'kN'
    return text


  # -------- Méthodes liées aux évènements

  def draw_event(self, layout, cr):
    """Fonction de tracé lors d'un signal de type 'draw'"""
    #print("draw_event")
    sw = self.sw
    hadj = sw.get_hadjustment()
    dx = int(hadj.get_value()) # int <- évite une pixelisation avec flottant
    vadj = sw.get_vadjustment()
    dy = int(vadj.get_value())
    cr.set_source_surface(self.surface, -dx, -dy)
    cr.paint()
    return False


   
# le dessin se fait en deux étapes:
# D'abord on dessine sur une source en mémoire dans la méthode configure_event
# puis on dessin de la source sur le widget dans draw_event


# voir principe dessin sur
# http://developer.gnome.org/gtk3/3.0/gtk-getting-started.html

  def configure_event(self, widget, event=None):
    """Fonction de configuration du drawing_area"""
    #print("classDrawing::configure_event layout=", widget.get_size())
    w_alloc = widget.get_allocated_width()
    h_alloc = widget.get_allocated_height()
    w, h = widget.get_size()
    if self.area_w is None:
      widget.set_size(w_alloc, h_alloc)
      self.area_w, self.area_h = w_alloc, h_alloc
      self.set_surface(w_alloc, h_alloc)
      return

    if self.area_w > w or self.area_h > h:
      #print("\tallocation new", self.area_w, self.area_h, w, h)
      self.area_w = max(self.area_w, w)
      self.area_h = max(self.area_h, h)
      widget.set_size(self.area_w, self.area_h)
      self.configure_event(widget)
      return

    if w < w_alloc or h < h_alloc: # passage fullscreen
      #print("passage fullscreen")
      w, h = max(w, w_alloc), max(h, h_alloc)
      w, h = min(w, 2000), min(h, 2000) # size limitation
      widget.set_size(w, h)
      self.area_w, self.area_h = w, h
      return

    self.set_surface(w, h)
    cr = cairo.Context(self.surface)

    drawings = self.drawings
    active = self.active_drawing
    n_drawing = len(drawings)
    studies = self.studies
    ids = list(drawings.keys())
    ids.sort(reverse=True)
    for id in ids: # on parcours en sens des id décroissants pour dessiner 
      # à coup sûr le p_barre
      drawing = drawings[id]
      study = studies[drawing.id_study]
      if not drawing.has_pattern:
        drawing.expose_drawing(cr, study)
      if n_drawing > 1:
        tag = drawing is active
        self.draw_is_selected(cr, drawing, tag)
      drawing.paint_drawing(cr)
    return True



  def paint_drawings(self):
    """Génère un nouveau tracé, si new_pattern : régénère le pattern correspondant"""
    drawings = self.drawings
    a_d = self.active_drawing
    study = self.studies[a_d.id_study]
    self.set_surface(self.area_w, self.area_h)
    cr = cairo.Context(self.surface)

    n_drawing = len(self.drawings)
    ids = list(drawings.keys())
    ids.sort(reverse=True)
    for id in ids: # on parcours en sens des id décroissants pour dessiner 
      # à coup sûr le p_barre
      drawing = drawings[id]
      tag = drawing is a_d and n_drawing > 1
      self.draw_is_selected(cr, drawing, tag)
      drawing.paint_drawing(cr)
    self.layout.queue_draw()

  def do_new_drawing(self, new_pattern):
    """Génère un nouveau tracé, si new_pattern : régénère le pattern correspondant"""
    drawings = self.drawings
    a_d = self.active_drawing
    study = self.studies[a_d.id_study]
# XXX voir utilité
    self.set_surface(self.area_w, self.area_h)
    cr = cairo.Context(self.surface)
    if new_pattern:
      affected_ids = [a_d.id]
      affected_ids.extend(a_d.childs)
      if not a_d.parent is None:
        affected_ids.append(a_d.parent.id)
      for key in affected_ids:
        d = drawings[key]
        d.update_drawing_data(d is a_d) # revoir
        d.del_patterns()
      for key in affected_ids:
        d = drawings[key]
        d.expose_drawing(cr, study)

      # vérification de la nouvelle taille
      x0, y0, w, h = a_d.mapping.box[a_d.id]
      if x0 < 0:
        area_w = x0 + w
        x0 = 0
      else:
        area_w = w
      if y0 < 0:
        area_h = y0 + h
        y0 = 0
      else:
        area_h = h
      has_changed = False
      if self.area_w < area_w:
        self.area_w = int(area_w)
        has_changed = True
      if self.area_h < area_h:
        self.area_h = int(area_h)
        has_changed = True
      if has_changed:
        a_d.del_patterns() # on force un nouveau expose_drawing
        self.layout.set_size(self.area_w, self.area_h)
        return
    n_drawing = len(self.drawings)
    if n_drawing > 1:
      ids = list(drawings.keys())
      ids.sort(reverse=True)
      for id in ids: # on parcours en sens des id décroissants pour dessiner 
      # à coup sûr le p_barre
        drawing = drawings[id]
        tag = drawing is a_d
        self.draw_is_selected(cr, drawing, tag)
    self.paint_all_struct(cr, a_d)
    #a_d.paint_drawing(cr)
    self.layout.queue_draw()


  def do_new_drawing2(self, study, drawing):
    """Tracé en temps réel depuis l'éditeur"""
    #print("do_new_drawing2", new_pattern)
    # Rectangle à mettre à jour:
    m = 100
    size = Const.DRAWING_SIZE
    w0, h0 = drawing.width, drawing.height
    x0, y0 = drawing.x0, drawing.y0
    struct = study.rdm.struct
    struct_w, struct_h = struct.width, struct.height
    drawing.set_scale(struct)
    #print("scale=", drawing.struct_scale)
    #repositionner en x0, y0 dans certains cas
    if y0-h0 < m:
      drawing.y0 = h0 + m
    w0 = max(w0, size)
    h0 = max(h0, size)
    y0 = drawing.y0 - h0
    # dessin
    self.set_surface(self.area_w, self.area_h)
    cr = cairo.Context(self.surface)
    drawing.expose_drawing(cr, study)
    for key in drawing.childs:
      d = drawing.childs[key]
      xi, yi = d.x0, d.y0
      wi, hi = d.width, d.height
      x0, y0, w0, h0 = self.get_union_2boxes(x0, y0, w0, h0, xi, yi, wi, hi)
      d.expose_drawing(cr, study)
    self.paint_all_struct(cr)
    x0 = max(x0-m, 0)
    y0 = max(y0-m, 0)
    self.layout.queue_draw_area(x0, y0, w0+2*m, h0+2*m)

  def get_union_2boxes(self, x0, y0, w0, h0, x1, y1, w1, h1):
    """Retourne les dimensions de l'union de deux boites"""
    x = min(x0, x1)
    y = min(y0, y1)
    w = max(x0+w0, x1+w1) - x
    h = max(y0+h0, y1+h1) - y
    return x, y, w, h

  def draw_is_selected(self, cr, drawing, is_active):
    """Dessine le repère indiquant quelle est le dessin actif"""
    if is_active:
      cr.push_group()
      surface = cairo.ImageSurface.create_from_png("glade/default.png")
      x, y, w, h = self.mapping.box[drawing.id]
      cr.set_source_surface(surface, x+5, y+h-22)
      cr.paint()
      drawing.p_select = cr.pop_group()
    else:
      try:
        del(drawing.p_select)
      except AttributeError:
        pass

  def get_layout_size(self, drawings):
    """Retourne la taille la fenetre graphique en fonction de la taille des dessins - drawings doit être une liste"""
    #print("get_layout_size")
    margin = Const.AREA_MARGIN_MIN
    w = h = 0
    for drawing in drawings:
      x = drawing.x0 + drawing.width
      if x > w:
        w = x
      y = drawing.y0
      if y > h:
        h = y
      if y - drawing.height < 0:
        drawing.y0 -= y - drawing.height
    w += margin
    h += margin
    self.area_w = int(max(self.area_w, w))
    self.area_h = int(max(self.area_h, h))


  def _draw_box(self, cr, x, y, w, h):
    """Dessine le contour d'un dessin"""
    #print(" _draw_box", x, y, w, h)
    cr.save()
    cr.set_line_width(1)
    cr.set_antialias(cairo.ANTIALIAS_NONE)
    self._fg.set_color_by_name(cr, 'blue')
    px = max(cr.device_to_user_distance(1, 1))
    cr.set_dash([2 * px], 0)
    cr.move_to(x, y)
    cr.rel_line_to(w, 0)
    cr.rel_line_to(0, h)
    cr.rel_line_to(-w, 0)
    cr.rel_line_to(0, -h)
    cr.stroke()
    draw_square(cr, x, y)
    draw_square(cr, x+w, y)
    draw_square(cr, x, y+h)
    draw_square(cr, x+w, y+h)
    cr.restore()

  def _paint_serie(self, alpha=1):
    cr.set_source(self.p_serie)
    cr.paint_with_alpha(alpha)

  def _paint_moving_info(self, cr, moving_drawing, info_id, x=0, y=0, alpha=1.):
    for drawing in self.drawings.values():
      if drawing is moving_drawing:
        cr.save()
        cr.translate(x, y)
        drawing.paint_info(cr, info_id, alpha)
        cr.restore()
        drawing.paint_drawing4(cr, 1.)
      else:
        drawing.paint_drawing(cr, alpha)
 
  def _paint_moving_struct(self, cr, moving_drawing, x=0, y=0, alpha=1.):
    """Redessine toutes les structures, y compris celle en mouvement de DND"""
    for drawing in self.drawings.values():
      if drawing is moving_drawing:
        cr.save()
        cr.translate(x, y)
        drawing.paint_drawing(cr, 1.)
        cr.restore()
      else:
        cr.save()
        drawing.paint_drawing(cr, alpha)
        cr.restore()


  def paint_all_struct(self, cr, selected_drawing=None, alpha=1.):
    """Redessine toutes les structures, y compris celle en mouvement de DND"""
    for drawing in self.drawings.values():
      cr.save()
      if drawing is selected_drawing:
        drawing.paint_drawing(cr, 1.)
      else:
        drawing.paint_drawing(cr, alpha)
      cr.restore()

  def paint_all_struct2(self, cr, selected_drawing=None, n_case=None, alpha=1.):
    """Dessine la structure avec seulement les valeurs numériques pour la courbe donnée par n_case"""
    for drawing in self.drawings.values():
      cr.save()
      if drawing is selected_drawing:
        drawing.paint_drawing2(cr, n_case, 1.)
      else:
        drawing.paint_drawing(cr, alpha)
      cr.restore()

# -------- FONCTIONS DES EVENEMENTS DE L'AREA -------------

  def _get_struct_info(self):
    """Retourne les informations en fonction de l'objet sélectionné: noeud ou barre"""
    type, drawing, node = self.is_selected
    if type == 'node':
      text = self._area_node_info(node, drawing)
      return text
    if type == 'bar':
      text = self._area_barre_info(node, drawing)
      return text
    return None

  def _area_barre_info(self, barre, drawing):
    """Retourne les informations sur la barre choisie"""
    barre = barre.name
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    struct = study.rdm.struct
    #crit = 1e-10
    crit = max(struct.width, struct.height)/1e8
    unit_L = study.get_unit_name('L')
    unit_S = study.get_unit_name('S')
    unit_I = study.get_unit_name('I')
    name = struct.GetBarreName(barre)
    l = struct.GetLength(barre)
    if l is None:
      return ("Non disponible", 0)
    if l < crit:
      l = 0
    s = struct.GetSection(barre)
    if s is None:
      return ("Non disponible", 0)
    if s < crit/1e4:
      s = 0
    i = struct.GetMQua(barre)
    if i is None:
      return ("Non disponible", 0)
    if i < crit/1e8:
      i = 0
    a = struct.GetAngle(barre)
    if a is None:
      return ("Non disponible", 0)
    if abs(a) < crit:
      a = 0
    text = "%s : l = %s %s, S = %s %s, Igz = %s %s, Angle = %s°" % (name,
		function.PrintValue(l, struct.units['L']), unit_L,
		function.PrintValue(s, struct.units['S']), unit_S,
		function.PrintValue(i, struct.units['I']), unit_I,
		function.PrintValue(a))
    return (text, 2)

  def _area_node_info(self, noeud, drawing):
    """Retourne les informations sur le noeud choisi"""
    #crit = 1e-10
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    struct = rdm.struct
    crit = max(struct.width, struct.height)/1e8
    try:
      x = struct.Nodes[noeud.name][0]
    except KeyError:
      x = struct.NodeNotLinked[noeud.name][0]
    if abs(x) < crit:
      x = 0
    try:
      y = struct.Nodes[noeud.name][1]
    except KeyError:
      y = struct.NodeNotLinked[noeud.name][1]
    if abs(y) < crit:
      y = 0
    unit_L = study.get_unit_name('L')
    text = "%s : %s %s, %s %s" % (noeud.name,
	function.PrintValue(x, rdm.struct.units['L']), unit_L,
	function.PrintValue(y, rdm.struct.units['L']), unit_L)
    return (text, 2)

  def _draw_selected_node(self, cr, node):
    """Met en valeur un noeud sélectionné pendant un survol"""
    x, y = node.coors
    #print(cr.get_antialias())
    draw_square(cr, x, y)


  def _draw_selected_value(self, cr, legend, drawing):
    """Dessine les détails pour la légende sélectionnée"""
    id_study = drawing.id_study
    status = drawing.status
    study = self.studies[id_study]
    rdm = study.rdm
    struct = rdm.struct
    unit_conv = rdm.struct.units['F']
    dx, dy = 42, 4
    x, y = legend.get_position()
    cr.save()
    self._fg.set_color_by_name(cr, 'blue')
    if status == 3:
      Char = rdm.GetCharByNumber(drawing.s_case)
      unit_name = study.get_unit_name('F')
      text = legend.get_reac_text(rdm, unit_conv, unit_name, Char, drawing)
    else:
      unit_name = study.get_unit_name('L')
      unit_conv = rdm.struct.units['L']
      text = legend.get_soll_text(rdm, unit_conv, unit_name)
    draw_square(cr, x, y)
    x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]
    cr.save()
    cr.set_source_rgba(1, 1, 1, 0.8)
    xi = x+dx
    yi = y+dy
    if xi+width+20 > self.area_w:
      xi = self.area_w-width-20
      yi = yi -20
    cr.rectangle(xi-10, yi-1.5*height, width+20, 2*height)
    cr.fill()
    cr.stroke()
    cr.restore()
    self._fg.set_color_by_name(cr, 'red')
    cr.move_to(xi, yi)
    cr.show_text(text)
    cr.restore()
    if not status == 3:
      drawing._draw_legend_position(cr, struct, legend.name, legend.u, legend.values)


  def _draw_selected_chart(self, cr, data, color=None):
    """Dessine la courbe des sollicitations définie par "data" pour "drawing" """
    cr.save()
    if not color is None:
      self._fg.set_color_by_name(cr, color)
    cr.set_line_width(2)
    # dessin des lignes
    for elem in data.values():
      for obj in elem:
        obj.redraw(cr)
    cr.stroke()
    cr.restore()


  def get_message(self):
    """Retourne les messages lors de clics sur les objets"""
    #print("get_message")
    is_selected = self.is_selected
    if is_selected is False: 
      return None
    drawing = is_selected[1]
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    if is_selected[0] == 'node' or is_selected[0] == 'bar':
      text = self._get_struct_info()
      return text
    if is_selected[0] == 'curve':
      n = is_selected[2]
      return self.get_char_message(rdm, n)
    return None


# déplacer de la classe Tab ??
  def get_char_message(self, rdm, n):
    """Retourne le message concernant le chargement actif"""
    if n is None:
      return None
    name = rdm.GetCharNameByNumber(n)
    n_cases = rdm.n_cases
    if n < n_cases:
      return ("Cas: %s" % name, 3)
    coefs = rdm.CombiCoef
    cas = coefs[name]
    li = list(cas.keys())
    li.sort()
    string = ''
    for val in li:
      coef = cas[val]
      if float(coef) == 0.:
        continue
      string += ' %sx%s +' % (coef, val)
    string = string[:-1]
    return ("Combinaison: %s (%s)" % (name, string), 3)

  def on_show_value_box(self, drawing, n_case, legend):
    """Affiche la boite de dialogue pour la position d'une valeur de courbe"""
    if self.is_selected and self.is_selected[0] == 'entry':
      return
    hbox = Gtk.HBox(False, 10)
    entry = MyEntry()
    x, y = legend.get_position()
    entry.set_text(str(legend.u)) # crée un arrondi!!!
    entry.set_tooltip_text("Modifier la position sur la barre")
    entry.modify_base(Gtk.StateType.NORMAL, Gdk.color_parse("#cac9c8"))
    entry.modify_font(Pango.FontDescription("sans 14"))
    entry.connect('event', self.on_pos_change, n_case, legend)
    entry.set_has_frame(False)

    hbox.pack_start(entry, False, False, 0)
    hbox.show_all()

    self.is_selected = ('entry', drawing, entry)
    self.layout.put(hbox, int(x), int(y))
    self.scale_box = hbox
    entry.grab_focus() # après show()
    entry.set_position(-1) # curseur a la fin

  def on_show_title_box(self, drawing):
    """Affiche la boite de dialogue pour le titre d'un dessin"""
    if self.is_selected and self.is_selected[0] == 'entry':
      return
    #print("on_show_title_box")
    hbox = Gtk.HBox(False, 10)
    entry = MyEntry()
    obj = drawing.mapping.infos[drawing.id][drawing.title_id]
    x, y = obj.box[0:2]
    entry.set_text(obj.text)
    entry.set_tooltip_text("Modifier le titre")
    entry.modify_base(Gtk.StateType.NORMAL, Gdk.color_parse("#cac9c8"))
    entry.modify_font(Pango.FontDescription("sans 14"))
    entry.connect('event', self.on_title_change)
    entry.set_has_frame(False)

    hbox.pack_start(entry, False, False, 0)
    hbox.show_all()

    self.is_selected = ('entry', drawing, entry)
    self.layout.put(hbox, int(x), int(y))
    self.scale_box = hbox
    entry.grab_focus() # après show()
    entry.set_position(-1) # curseur a la fin
    # on efface le titre correspondant
    del(drawing.p_infos[obj.id])
    #self.del_surface()
    self.configure_event(self.layout)
    self.layout.queue_draw()

  def on_show_scale_box(self, widget, drawing, tag):
    """Affiche la boite de dialogue pour l'échelle d'un dessin"""
    if self.is_selected and self.is_selected[0] == 'entry':
      return
    if drawing.struct_scale is None:
      return
    if tag == "struct":
      value = drawing.struct_scale
    elif tag == "chart":
      value = drawing.chart_scale
    elif tag == "pos":
      value = drawing.u
    hbox = Gtk.HBox(False, 10)
    entry = MyEntry()
    text = str(value)
    entry.set_text(text)
    entry.modify_font(Pango.FontDescription("sans 14"))
    entry.set_tooltip_text("Modifier l'échelle")
    entry.modify_base(Gtk.StateType.NORMAL, Gdk.color_parse("#cac9c8"))
    entry.connect('event', self.on_scale_change, tag)
    #entry.set_width_chars(n_chars)
    entry.set_has_frame(False)

    hbox.pack_start(entry, False, False, 0)
    hbox.show_all()
    self.is_selected = ('entry', drawing, entry)

    x0, y0, w, h = drawing.mapping.box[drawing.id]
    x = x0 + w -200
    y = y0 + h - 80
    self.layout.put(hbox, int(x), int(y))
    self.scale_box = hbox
    entry.grab_focus() # après show()
    entry.set_position(-1) # curseur a la fin

  def on_select_next(self, widget, drawing, study):
    """Changement de barre en avant"""
    rdm = study.rdm
    struct = rdm.struct
    Barres = struct.GetBars()
    #cmp = function.compare
    #Barres.sort(cmp)
    barre = drawing.s_bar
    try:
      new = Barres[Barres.index(barre) + 1]
    except (IndexError, ValueError):
      new = Barres[0]
    drawing.draw_new_bar(self, struct, new)

  def on_select_back(self, widget, drawing, study):
    """Changement de barre en arrière"""
    rdm = study.rdm
    struct = rdm.struct
    Barres = struct.GetBars()
    #cmp = function.compare
    #Barres.sort(cmp)
    barre = drawing.s_bar
    try:
      new = Barres[Barres.index(barre) - 1]
    except (IndexError, ValueError):
      new = Barres[0]
    drawing.draw_new_bar(self, struct, new)



  def start_dnd(self, area, event, is_press):
    """Action liée à un mouvement du pointeur"""
    #print("start_dnd", is_press)
    if event.is_hint:
      (ptr_window, x, y, mask) = event.window.get_pointer()
      #x, y, state = event.window.get_pointer()
    else:
      # for Windows
      x = event.x
      y = event.y
      #state = event.get_state()
    if is_press:
      x0, y0 = is_press
      dx = x-x0
      dy = y-y0
      cr = cairo.Context(self.surface)
      if not self.is_selected:
        return
      if self.is_selected[0] == 'entry':
        return
      if not dx and not dy:
        return
      if self.is_selected[0] == 'info':
        drawing = self.is_selected[1]
        info_id = self.is_selected[2]
        self.set_surface(self.area_w, self.area_h)
        cr = cairo.Context(self.surface)
        x, y, w, h = self.mapping.infos[drawing.id][info_id].box
        dx_prec, dy_prec = self.motion
        self._paint_moving_info(cr, drawing, info_id, dx, dy, 0.5)
        rect = (int(min(x+dx, x+dx_prec))-5, int(min(y+dy_prec, y+dy))-5, int(max(w, w+dx_prec-dx))+10, int(max(h, h+dy_prec-dy))+10)
        self.motion = (dx, dy)
        Rect = Gdk.Rectangle()
        Rect.x, Rect.y, Rect.width, Rect.height = rect
        area.get_window().invalidate_rect(Rect, True)
        #self.draw_event(area)
      elif self.is_selected[0] == 'value':
        drawing, n_case, legend = self.is_selected[1:]
        barre = legend.name
        u = legend.u
        status = drawing.status
        drawing.user_values.setdefault(status, {})
        drawing.user_values[status].setdefault(n_case, {})
        moved = drawing.user_values[status][n_case].setdefault(barre, {})
        dx = float(legend.x - x)
        dy = float(legend.y - y)
        dx_prec, dy_prec = self.motion
        try:
          di = moved[u]
          if legend.disc in di:
            coors = di[legend.disc]
            di[legend.disc] = (coors[0]+dx, coors[1]+dy, False)
          else:
            di[legend.disc] = (dx, dy, False)
        except KeyError:
          moved[u] = {legend.disc: (dx, dy)}
        legend.x = x
        legend.y = y
        # on refait le pattern des légendes pour le drawing
        self.set_surface(self.area_w, self.area_h)
        cr = cairo.Context(self.surface)
        study = self.studies[drawing.id_study]
        drawing._push_legends_group(cr, study.rdm.struct)
        self.paint_all_struct(cr, drawing, alpha=0.6)
        w, h = 80, 40 # paramétrer mieux?
        rect = (int(min(x+dx, x+dx_prec))-40, int(min(y+dy_prec, y+dy))-20, int(max(w, w+dx_prec-dx)), int(max(h, h+dy_prec-dy)))
        self.motion = (dx, dy)
        #self.draw_event(area)
        Rect = Gdk.Rectangle()
        Rect.x, Rect.y, Rect.width, Rect.height = rect
        area.get_window().invalidate_rect(Rect, True)
      elif self.is_selected[0] == 'draw':
        drawing = self.is_selected[1]
        self.set_surface(self.area_w, self.area_h)
        cr = cairo.Context(self.surface)
        self._paint_moving_struct(cr, drawing, dx, dy, 0.5)
        x, y, w, h = self.mapping.box[drawing.id]
        dx_prec, dy_prec = self.motion
        if drawing.id in drawing.mapping.infos:
          for elem in drawing.mapping.infos[drawing.id].values():
            xi, yi, wi, hi = elem.box
            xm = min(xi, x)
            ym = min(yi, y)
            w = max(x+w, xi+wi)-xm
            h = max(y+h, yi+hi)-ym
            x, y = xm, ym
        rect = (int(min(x+dx, x+dx_prec))-3, int(min(y+dy_prec, y+dy))-3, int(max(w, w+dx_prec-dx))+6, int(max(h, h+dy_prec-dy))+6)
        self.motion = (dx, dy)
        Rect = Gdk.Rectangle()
        Rect.x, Rect.y, Rect.width, Rect.height = rect
        area.get_window().invalidate_rect(Rect, True)
    else:
      self.layout_motion_event(area, event)
    return True


  def finish_dnd(self, event, is_press):
    """Actions liées à la fin du drag and drop dans le area"""
    #print("finish_dnd")
    if not self.is_selected:
      return
    if not is_press:
      return
    cr = cairo.Context(self.surface)
    x0, y0 = is_press
    x1, y1 = event.x, event.y
    dx = x1-x0
    dy = y1-y0
    dx, dy = int(dx), int(dy)
    if not dx and not dy:
      #self.is_selected = False # supprimé le 21/9/2012
      #self.layout.window.set_cursor(None)
      return
    # on encre la légende
    if self.is_selected[0] == 'info':
      drawing = self.is_selected[1]
      info_id = self.is_selected[2]
      x, y, w, h = self.mapping.infos[drawing.id][info_id].box
      x = x + dx
      y = y + dy
      self.mapping.set_moved_info(drawing.id, info_id, (x, y, w, h))
      drawing.del_patterns()
      w_min, h_min = x + w, y + h
      if w_min > self.area_w and dx > 0:
        self.area_w = int(x + w)
      if h_min > self.area_h and dy > 0:
        self.area_h = int(y + h)
      self.configure_event(self.layout)
      self.layout.queue_draw()
    elif self.is_selected[0] == 'value':
      drawing, n_case, legend = self.is_selected[1:]
      x, y = legend.x, legend.y
      w, h = 25, 8 # il faudrait revoir entièrement les dimensions de la box pour pouvoir en réduire aussi la taille
      self.mapping.extend_box(drawing.id, x-w, y-h)
      self.mapping.extend_box(drawing.id, x+w, y+h)
    elif self.is_selected[0] == 'draw':
      drawing = self.is_selected[1]
      b_x, b_y, b_w, b_h = self.mapping.box[drawing.id]
      w_min = b_x + b_w + dx
      h_min = b_y + b_h + dy
      drawing.x0 += dx
      drawing.y0 += dy
      if drawing.id in drawing.mapping.infos:
        for elem in drawing.mapping.infos[drawing.id].values():
          x, y, w, h = elem.box
          x += dx
          y += dy
          elem.box = (x, y, w, h)
      drawing.del_patterns()
      is_resize = False
      # ne réduit jamais la taille de l'area
      if w_min > self.area_w and dx > 0:
        self.area_w += dx
        is_resize = True
      if h_min > self.area_h and dy > 0:
        self.area_h += dy
        is_resize = True
      if is_resize:
        self.layout.set_size(self.area_w, self.area_h)
      else:
        self.configure_event(self.layout)
        self.layout.queue_draw()
      self.remove_tools_box()
      self._draw_tools(drawing)
    watch = Gdk.Cursor.new(Gdk.CursorType.ARROW)
    self.layout.get_root_window().set_cursor(watch)

# inutilisée
  def move_tools_box(self, x, y):
    """Déplace la boite des boutons"""
    if not hasattr(self, "tools_box"):
      return
    self.layout.move(self.tools_box, int(x), int(y))

  def remove_tools_box(self):
    """Supprime les boutons sur le Layout"""
    if self._main.key_press:
      return
    if not hasattr(self, "tools_box"):
      return
    self.layout.remove(self.tools_box)
    del(self.tools_box)

  def remove_entry_box(self):
    """Supprime la boite de dialogue de l'échelle sur le Layout"""
    if not hasattr(self, "scale_box"):
      return
    self.layout.remove(self.scale_box)
    del(self.scale_box)

# génère configure_event
  def _draw_tools(self, drawing):
    """Ajoute le menu sur le Layout"""
    #print("_draw_tools")
    if hasattr(self, "tools_box"):
      return
    study = self.studies[drawing.id_study]
    self.tools_box = drawing.draw_tools(study, self)


  def on_pos_change(self, widget, event, n_case, legend):
    """Evènement sur l'Entry de modification de la position d'une légende"""
    exit = False
    must_save = False
    #if event.type == Gdk.EventType.EXPOSE:
    #  text = widget.get_text()
    #  layout = widget.get_layout()
    #  w, h = layout.get_pixel_size()
    #  w0, h0 = widget.size_request()
    #  if not w + 20 == w0:
    #    widget.set_size_request(w+20, h)
    if event.type == Gdk.EventType.KEY_PRESS:
      drawing = self.is_selected[1]
      key = Gdk.keyval_name (event.keyval)
      if key == "Return":
        try:
          u = float(widget.get_text())
          must_save = True
        except ValueError:
          pass
        exit = True
      elif key == "Escape":
        exit = True
    elif event.type == Gdk.EventType.DESTROY:
      drawing = self.is_selected[1]
      try:
        u = float(widget.get_text())
        must_save = True
      except ValueError:
        pass
      exit = True
    if must_save:
        if abs(u - legend.u) > 1e-8:
          #print("%.12f %.12f" % (u, legend.u))
          resu = drawing._get_user_value(n_case, legend.name, legend.u, legend.disc, True)
          if resu:
            di, pos = resu
            tu = di[pos][legend.disc]
            del(di[pos][legend.disc])
            if len(di[pos]) == 0:
              del(di[pos])
            di[u] = {0: tu}
          else:
            drawing._set_user_values(n_case, legend.name, u, legend.disc, 0, 0)



    if exit:
      #self.del_surface()
      drawing.del_patterns()
      self.remove_tools_box()
      self.remove_entry_box()
      self.is_selected = ('draw', drawing)
      self.configure_event(self.layout)
      self.layout.queue_draw()



  def on_title_change(self, widget, event):
    """Gère les événement clavier pour le titre du dessin"""
    #print("on_title_change", event.type)
    exit = False
    #if event.type == Gdk.EventType.EXPOSE:
    #  text = widget.get_text()
    #  layout = widget.get_layout()
    #  w, h = layout.get_pixel_size()
    #  w0, h0 = widget.size_request()
    #  if not w + 20 == w0:
    #    widget.set_size_request(w+20, h)
    if event.type == Gdk.EventType.KEY_PRESS:
      drawing = self.is_selected[1]
      obj = drawing.mapping.infos[drawing.id][drawing.title_id]
      key = Gdk.keyval_name (event.keyval)
      if key == "Return":
        obj.text = widget.get_text()
        exit = True
      elif key == "Escape":
        exit = True
    elif event.type == Gdk.EventType.DESTROY:
      drawing = self.is_selected[1]
      obj = drawing.mapping.infos[drawing.id][drawing.title_id]
      obj.text = widget.get_text()
      exit = True
    if exit:
      #self.del_surface()
      drawing.del_patterns()
      self.remove_tools_box()
      self.remove_entry_box()
      self.is_selected = ('draw', drawing)
      self.configure_event(self.layout)
      self.layout.queue_draw()



# le layout emet des configure_event !!!!
  def on_scale_change(self, widget, event, tag):
    """Gère les événement clavier pour le menu de l'echelle"""
    if event.type == Gdk.EventType.KEY_PRESS:
      drawing = self.is_selected[1]
      study = self.studies[drawing.id_study]
      key = Gdk.keyval_name (event.keyval)
      text = widget.get_text().replace(',', '.')
      if key == "Return":
        try:
          value = float(text)
        except ValueError:
          value = None
        if not value is None:
          if tag == "struct":
            if drawing.get_max_scale(value, study):
              drawing.set_zoom(value)
              drawing.struct_scale = value
              #drawing.set_scale(study.rdm.struct)
              drawing.del_patterns()
              self.get_layout_size([drawing])
              self.configure_event(self.layout)
              self.layout.queue_draw()
            else:
              self._main.message.set_message(("Taille de dessin trop grande", 1))
          elif tag == "chart":
            if drawing.get_max_scale2(value, study):
              scale = drawing.chart_scale
              coef = value/scale
              drawing.chart_zoom[drawing.status] = coef
              #self.del_surface()
              drawing.del_patterns()
              self.configure_event(self.layout)
              self.layout.queue_draw()
          elif tag == "pos":
            if value >= 0. and value <= 1.:
              drawing.u = value
              #self.del_surface()
              drawing.del_patterns()
              self.configure_event(self.layout)
              self.layout.queue_draw()
        self.remove_tools_box()
        self.remove_entry_box()
        self.is_selected = ('draw', drawing)
      elif key == "Escape":
        self.remove_tools_box()
        self.remove_entry_box()
        self.is_selected = ('draw', drawing)

  
  def layout_motion_event(self, area, event):
    """Gère les fonctionnalités lors d'un évènement de survol du Layout"""
    x_event, y_event = event.x, event.y
    #print("layout_motion_event", x_event, y_event, self.is_selected)

    # test -----------------
    #drawings = self.drawings
    #mappings = self.mapping.bars
    #assert len(drawings) == len(mappings)
    #for id in drawings:
    #  if not id in mappings:
    #    raise
    # fin test

    if self.is_selected and self.is_selected[0] == "entry":
      watch = Gdk.Cursor.new(Gdk.CursorType.ARROW)
      area.get_root_window().set_cursor(watch)
      return
    area.grab_focus()
    watch = Gdk.Cursor.new(Gdk.CursorType.HAND1)
    if self.is_selected:
      drawings = [self.is_selected[1]]
    else:
      drawings = self.drawings.values()
    data = self.mapping.select_infos(x_event, y_event, drawings)
    if not data is False:
      drawing_id, info_id = data
      drawing = self.drawings[drawing_id]
      area.get_root_window().set_cursor(watch)
      self.set_surface(self.area_w, self.area_h)
      cr = cairo.Context(self.surface)
      self.paint_all_struct(cr, drawing, alpha=0.6)
      self.is_selected = ('info', drawing, info_id)
      x, y, w, h = self.mapping.infos[drawing_id][info_id].box
      self._draw_box(cr, x, y, w, h)
      area.queue_draw()
      return

    data = self.mapping.select_curve_values(x_event, y_event, self.is_selected)
    if not data is False:
      n_case, legend = data
      #print(legend.auto)
      drawing = self.is_selected[1]
      area.get_root_window().set_cursor(watch)
      self.is_selected = ('value', drawing, n_case, legend)
      self.set_surface(self.area_w, self.area_h)
      cr = cairo.Context(self.surface)
        # revoir pour ne pas tout redessiner
      self.paint_all_struct(cr, drawing, alpha=0.6)
      self._draw_selected_value(cr, legend, drawing)
      area.queue_draw()
      return

    chart = self.mapping.select_curve(x_event, y_event, self.is_selected)
    if chart:
      n_case, barre, points = chart[0], chart[1], chart[2]
      drawing = self.is_selected[1]
      area.get_root_window().set_cursor(watch)
      self.set_surface(self.area_w, self.area_h)
      cr = cairo.Context(self.surface)
      obj = chart[3]
      study = self.studies[drawing.id_study]
      obj.push_hover_value(cr, study, barre, drawing, n_case)
      self.paint_all_struct2(cr, drawing, n_case, alpha=0.6)
      x, y, w, h = self.mapping.box[drawing.id]
      self._draw_box(cr, x, y, w, h)
      self._draw_selected_chart(cr, points, 'orange')
      drawing.paint_value(cr)
      self.is_selected = ('curve', drawing, n_case, barre, obj)
      area.queue_draw()
      return

    if not self.is_selected is False:
      id = self.is_selected[1].id
      data = self.mapping.select_node(x_event, y_event, id)
      if data:
        point = data[1]
        drawing = self.is_selected[1]
        area.get_root_window().set_cursor(watch)
        self.set_surface(self.area_w, self.area_h)
        cr = cairo.Context(self.surface)
        self.paint_all_struct(cr, drawing, alpha=0.6)
        x, y, w, h = self.mapping.box[drawing.id]
        self._draw_box(cr, x, y, w, h)
        #self._draw_box(cr, drawing)
        self._draw_selected_node(cr, point)
        area.queue_draw()
        self.is_selected = ('node', drawing, point)
        return
      data = self.mapping.select_barre(x_event, y_event, id)
      if data:
        barre = data[1]
        drawing = self.is_selected[1]
        area.get_root_window().set_cursor(watch)
        self.set_surface(self.area_w, self.area_h)
        cr = cairo.Context(self.surface)
        self.paint_all_struct(cr, drawing, alpha=0.6)
        x, y, w, h = self.mapping.box[drawing.id]
        self._draw_box(cr, x, y, w, h)
        drawing._draw_selected_barre(cr, barre)
        self.is_selected = ('bar', drawing, barre)
        area.queue_draw()
        return
    data = self.mapping.select_drawing(x_event, y_event, self.is_selected)
    if data:
      drawing = self.drawings[data[0]]
      area.get_root_window().set_cursor(watch)
      if self.is_selected:
        type_prec, prec = self.is_selected[0:2]
        if type_prec == 'draw' and prec is drawing:
          # nothing to do
          return
      self.set_surface(self.area_w, self.area_h)
      cr = cairo.Context(self.surface)
      self.paint_all_struct(cr, drawing, alpha=0.6)
      x, y, w, h = self.mapping.box[drawing.id]
      self._draw_box(cr, x, y, w, h)
      self.is_selected = ('draw', drawing)
      self._draw_tools(drawing)
      area.queue_draw()
      return
    if not self.is_selected is False:
      id = self.is_selected[1].id
      data = self.mapping.get_is_in_drawing(x_event, y_event, id)
      if data:
        area.get_root_window().set_cursor(watch)
        drawing = self.drawings[data[0]]
        type_prec, prec = self.is_selected[0:2]
        if type_prec == 'draw' and prec is drawing:
          # nothing to do
          return
        self.set_surface(self.area_w, self.area_h)
        cr = cairo.Context(self.surface)
        self.paint_all_struct(cr, drawing, alpha=0.6)
        x, y, w, h = self.mapping.box[drawing.id]
        self._draw_box(cr, x, y, w, h)
        self.is_selected = ('draw', drawing)
        self._draw_tools(drawing) #bug: empèche affichage box au premier survol
        area.queue_draw()
        return

    if not self.is_selected is False:
      self.set_surface(self.area_w, self.area_h)
      cr = cairo.Context(self.surface)
      self.paint_all_struct(cr, None, alpha=1.)
      self.layout.queue_draw()
    self.is_selected = False
    self.remove_tools_box()
    watch = Gdk.Cursor.new(Gdk.CursorType.ARROW)
    area.get_root_window().set_cursor(watch)



  # ------------------ METHODES DE DESSIN À PARTIR DU PATTERN ------------------

# not supported
  def draw_jpg_file(self, file):
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, self.area_w, self.area_h)
    cr = cairo.Context(surface)
    drawings = self.drawings
    studies = self.studies

    for drawing in drawings.values():
      study = studies[drawing.id_study]
      drawing.del_patterns() # force un nouveau tracé pour éviter d'avoir des images bitmap de certain pattern
      drawing.expose_drawing(cr, study)
      self._main.window.queue_draw()
      drawing.paint_drawing(cr)
    width, height = self.area_w, self.area_h
# not implemented yet!!!!!!!!!
    pixbuf = GdkPixbuf.Pixbuf.new_from_data(surface.get_data(), GdkPixbuf.Colorspace.RGB, True, 8, width, height, surface.get_stride())
    surface.finish()


  def draw_svg_file(self, file):
    """Lance le tracé du graphe en fonction de la valeur de status
    Attention, tous les éléments dessinés à partir d'un patern sont dessinés en bitmap"""
    surface = cairo.SVGSurface(file, self.area_w, self.area_h)
    cr = cairo.Context(surface)
    drawings = self.drawings
    studies = self.studies

    for drawing in drawings.values():
      study = studies[drawing.id_study]
      drawing.del_patterns() # force un nouveau tracé pour éviter d'avoir des images bitmap de certain pattern
      drawing.expose_drawing(cr, study)
      self._main.window.queue_draw()
      drawing.paint_drawing(cr)

    surface.finish()

  def draw_png_file(self, file):
    """Lance le tracé du graphe en fonction de la valeur de status
    Attention, tous les éléments dessinés à partir d'un patern sont dessinés en bitmap"""
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, self.area_w, self.area_h)
    cr = cairo.Context(surface)
    self.draw_surface_bg(cr)
    drawings = self.drawings
    studies = self.studies

    for drawing in drawings.values():
      study = studies[drawing.id_study]
      drawing.expose_drawing(cr, study)
      #while Gtk.events_pending():
      #    Gtk.main_iteration(False)
      self._main.window.queue_draw()
      drawing.paint_drawing(cr)

    surface.write_to_png(file)
    surface.finish()

# inutile
  def get_drawings_size(self):
    """Retourne la boite contenant l'ensemble des drawings"""
    for i, box in enumerate(self.mapping.box.values()):
      x, y, w, h = box
      if i == 0:
        x0, y0, x1, y1 = x, y, x+w, y+h
      if x < x0:
        x0 = x
      if x+w > x1:
        x1 = x+w
      if y < y0:
        y0 = y
      if y+h > y1:
        y1 = y+h
    w = x1 - x0
    h = y1 - y0
    return x0, y0, w, h




# -------------DESSINS LÉGENDES ET ECHELLES ------------------


# ------------------ OUTILS -------------------------------------

# inutile
  def _get_max_fp(self, rdm): # inutilisée si toutes les forces fp ont meme longueur
    """recherche de la charge fp maxi
    Retourne la norme"""
    fpmax = 0
    for barre in rdm.struct.Barres:
      if not barre in rdm.charBarFp:
        continue
      dichar = rdm.charBarFp[barre]
      for alpha, char in dichar.items():
        fpu = char[0]
        fpv = char[1]
        fp = (fpu**2 + fpv**2)**0.5
        if fp > fpmax:
          fpmax = fp
    return fpmax




# inutilisée
  def _pix_opacify(self, cr, w, h):
    """Dessine un rectangle blanc semi-transparent sur la pixmap"""
    cr.save()
    cr.set_source_rgba(1, 1, 1, 0.8)
    cr.rectangle(0, 0, w, h)
    cr.fill()
    cr.stroke()
    cr.restore()



  def draw_surface_bg(self, cr):
    """initialise un fond blanc dans la surface"""
    #print("draw_surface_bg")
    cr.save()
    self._fg.set_color_by_name(cr, "white")
    cr.rectangle(0, 0, self.area_w, self.area_h)
    cr.fill()
    #cr.stroke()
    cr.restore()

  def set_surface(self, w, h):
    """initialise la surface et le context. cr doit être appelé après cette méthode"""
    #print("set_surface", w, h)
    self.del_surface()
    self.surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    cr = cairo.Context(self.surface)
    self.draw_surface_bg(cr)

  def del_surface(self):
    """Supprime la Surface de dessin"""
    #print("del_surface")
    try:
      self.surface.finish()
      del(self.surface)
    except AttributeError:
      #print("debug::del_surface impossible -> la surface n'existe pas")
      pass



