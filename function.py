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

# ----------- FONCTIONS UTILES -------------------------------

import math
import re
from gi.repository import Gtk

def indent(elem, level=0):
    """Indentation du xml pour le module etree"""
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# fonctionne pour la classe editor à partir des instances de Nodes
def Str2NodeCoors2(node, prec_nodes):
    """Convertit la chaine de caractères "content" en coordonnées absolues
    prec_nodes est la liste des noeuds déjà définis
    prec_node est le noeud précédemment défini"""
    #print "function", content
    x, y = 0., 0.
    if node.s_x == '' or node.s_y == '':
      return False

    if not node.rel is None:
      for elem in prec_nodes:
        if elem.name == node.rel:
          try:
            x, y = elem.x, elem.y
            if x is None:
              return False
            break
          except AttributeError: # test inutile car attribut vaut None par défaut
            return False
        
    if node.pol:
      try:
        teta = float(node.s_y)*math.pi/180
        r = float(node.s_x)
      except ValueError:
        return False
      x += r*math.cos(teta)
      y += r*math.sin(teta)
    else:
      try:
        x += float(node.s_x)
        y += float(node.s_y)
      except ValueError:
        return False
    return x, y

# fonctionne pour la classe rdm à partir d'un dictionnaire
def Str2NodeCoors(content, prec_nodes, prec_node=None, unit=1):
    """Convertit la chaine de caractères "content" en coordonnées absolues
    prec_nodes est le dictionnaire des noeuds déjà définis
    prec_node est le noeud précédemment défini"""
    #print "function", content
    if content is None:
      return False
    x, y = 0., 0.
    if content[0] == "@": 
      pos = content.find(",")
      noeud_relatif = content[1:pos]
      if noeud_relatif == "" and prec_node is None:
        #print "Erreur inattendue dans Str2NodeCoors O", content
        return False
      elif not noeud_relatif in prec_nodes:
        #print "Erreur inattendue dans Str2NodeCoors", content
        return False
      x = prec_nodes[noeud_relatif][0]
      y = prec_nodes[noeud_relatif][1]
        
      content = content[pos+1:]
    #recherche des coordonnées polaires
    pos1 = content.find("<")
    if  pos1 >= 0: 
      if not content.find(",") == -1: 
        return False
      try:
        teta = float(content[pos1+1:])*math.pi/180
        r = float(content[:pos1])
      except ValueError:
        return False
      x += r*math.cos(teta)*unit
      y += r*math.sin(teta)*unit
    else:
      coors = content.split(",")
      if not len(coors) == 2:
        return False
      try:
        x += float(coors[0])*unit
        y += float(coors[1])*unit
      except ValueError:
        return False
    return x, y

# inutile
def GetBoxSize(nodes, box=[]):
    """Retourne un tuple xmin, ymin, xmax, ymax du contour de la structure
    Si box est donnée, nodes est comparé à box"""
    if len(nodes) == 0:
      return box
    if not box == []:
      xmin, ymin, xmax, ymax = box[0], box[1], box[2], box[3] 
    i = 0
    for node in nodes:
      coors = nodes[node]
      if i == 0 and box == []:
        xmax = xmin = coors[0]
        ymax = ymin = coors[1]
      i = i+1
      if coors[0] < xmin:
        xmin = coors[0]
      elif  coors[0] > xmax:
        xmax = coors[0]
      if coors[1] < ymin:
        ymin = coors[1]
      elif  coors[1] > ymax:
        ymax = coors[1]
    return xmin, ymin, xmax, ymax
# inutile
def translate_nodes(box, nodes):
    """Recadrage des points si originie différente de 0, 0"""
    if box == []:
      return
    x0, y0 = box[0], box[1]
    if not x0 == 0 or not y0 == 0:
      for node in nodes:
        x = nodes[node][0]
        x -= x0
        y = nodes[node][1]
        y -= y0
        nodes[node] = (x, y)


def get_vector_size(pt1, pt2):
  """Retourne la longueur d'une barre"""
  return math.sqrt((pt2[0]-pt1[0])**2+(pt2[1]-pt1[1])**2)

# en double avec classRdm
def Rotation(a, x, y):
  """x, y étant les coordonnées d'un point dans un repère 1, retourne les coordonnées du point dans le repère 2 obtenu par rotation d'angle a"""
  x1 = x*math.cos(a) + y*math.sin(a)
  y1 = -x*math.sin(a) + y*math.cos(a)
  return x1, y1



# voir différence avec fonction suivante XXX
def get_vector_angle(pt1, pt2):
    """Retourne l'angle d'une barre par rapport à l'axe X
    compris entre -pi et pi"""
    x1, y1 = pt1
    x2, y2 = pt2[0:2] # revoir à cause des chargements ponctuels
    return math.atan2(y2-y1, x2-x1)



    if x2 == x1:
      if y1 == y2:
        return None
      if y2 > y1:
        return math.pi/2 
      return -math.pi/2
    if y2 == y1:
      if x1 == x2:
        return None
      if x2 >= x1:
        return 0.
      return math.pi
    if y2-y1 <= 0 and x2-x1 <= 0 :
      return math.atan((y2-y1)/(x2-x1)) - math.pi
    if y2-y1>0 and x2-x1 <= 0:
      return math.atan((y2-y1)/(x2-x1)) + math.pi
    return math.atan((y2-y1)/(x2-x1))


#Retourne l'angle d'un segment donné par pt1, pt2 par rapport a l'axe X
# dans le repère informatique
def AngleSegment(pt1, pt2):
  x1, y1 = pt1
  x2, y2 = pt2[0:2] # revoir à cause des chargements ponctuels
  return math.atan2(y2-y1, x2-x1)


  if pt2[0] == pt1[0]:
    if pt2[1] > pt1[1]:
      return -math.pi/2
    return math.pi/2
  if pt2[1] == pt1[1]:
    if pt2[0] >= pt1[0]:
      return 0.
    return math.pi
  if pt2[1]-pt1[1] <= 0 and pt2[0]-pt1[0] <= 0:
    return math.atan(-float(pt2[1]-pt1[1])/float(pt2[0]-pt1[0]))+math.pi
  if pt2[1]-pt1[1] >= 0 and pt2[0]-pt1[0] <= 0:
    return math.atan(-float(pt2[1]-pt1[1])/float(pt2[0]-pt1[0]))+math.pi
  return math.atan(-float(pt2[1]-pt1[1])/float(pt2[0]-pt1[0]))

# Effectue la rotation d'un point (x,y) par rapport à un centre de rotation
# et pour un angle alpha
# retourne un tuple d'entier ou de flottant
def PointRotate(centerX, centerY, x, y, alpha, arrondi=True):
  if alpha == 0:
    if not arrondi: return (x, y)
    return (int(round(x)), int(round(y)))
  teta = AngleSegment([centerX, centerY], [x, y])
  D = ((x-centerX)**2+(y-centerY)**2)**0.5
  deltax = D*(-math.cos(teta)+math.cos(teta+alpha))
  deltay = D*(-math.sin(teta)+math.sin(teta+alpha))
  x, y = x + deltax, y-deltay
  if not arrondi: return (x, y)
  return (int(round(x)), int(round(y)))

def DeleteEndingZero(x):
  #x = float(x)
  # nombres décimaux
  if not x.find('.') == -1:
    p = re.compile('[0]+$')
    x = p.sub('', x)
    p = re.compile('\.$')
    x = p.sub('', x)
  return x

def TestDeleteEndingZero():
  # test déplacer
  assert DeleteRe('1000') == '1000'
  assert DeleteRe('1000.0') == '1000'
  assert DeleteRe('1000.00') == '1000'
  assert DeleteRe('-1000.01') == '-1000.01'
  assert DeleteRe('0.010') == '0.01'
  assert DeleteRe('0.10') == '0.1'
  assert DeleteRe('0.01') == '0.01'
  assert DeleteRe('0.11') == '0.11'

def PrintValue(x, unit=1, delete_end=False):
  """Formate une valeur numérique"""
  x = x / unit
  if abs(x) == 0:
    strx = '0'
  elif abs(x) >= 1e6:
    strx = "%.2E" % x
  elif abs(x) >= 1000:
    strx = "%.0f" % x
  elif abs(x) >= 10:
    strx = "%.1f" % x
  elif abs(x) >= 1:
    strx = "%.2f" % x
  elif abs(x) >= 1e-1:
    strx = "%.3f" % x
  elif abs(x) >= 1e-2:
    strx = "%.4f" % x
  elif abs(x) >= 1e-3:
    strx = "%.5f" % x
  else:
    delete_end = False
    strx = "%.2E" % x
  if delete_end:
    strx = DeleteEndingZero(strx)
  return strx

def tri_abscisse_croissante(li_node, li_x):
    """Trie li_point suivant les abscisses croissantes contenues dans li_x"""
    # on doit pouvoir faire plus simple
    li_x.sort()
    li = []
    for i in li_x:
      name = li_node[li_x.index(i)]
      li.append(name)
    return li


# Projection d'un vecteur du repère local vers le repère global
# vec est exprimé dans le repère local
# retourne vec dans le repère du DC
# inutilisée
def projL2G(vec, teta):
    x = float(vec[0])*math.cos(teta)-float(vec[1])*math.sin(teta)
    y = -float(vec[0])*math.sin(teta)-float(vec[1])*math.cos(teta)
    if len(vec) == 2:
      return [x, y]
    return [x, y, vec[2]]

# -----------------------------------------------------------------------

# méthode relative aux dictionnaires

def sortedDictValues(adict):
  """Retourne la liste des items d'un dict classé en fonction des clés"""
  return map(adict.get, keys)

def sortedDictKeys(adict):
  """Retourne la liste des clés d'un dict classé en fonction des clés"""
  keys = list(adict.keys())
  keys.sort()
  return keys

def return_key(di, val, verbose=False):
  """Retourne la clé d'un dictionnaire
  en correspondance avec la valeur val"""
  for key, elem in di.items():
    #print type(val), type(elem)
    #assert type(val) == type(elem)
    if val == elem:
      return key 
  if verbose:
    print("Function::error in return_key")
  return None

# XXX ne fonctionne pas comme attendu, à revoir
def compare(x, y):
  """fonction de tri pour trier des barres ou des noeuds de format B1 B2 ..."""
  i1 = x[0]
  i2 = y[0]
  if i1 == i2:
    try:
      x = int(x[1:]) # comparer B1 et B10
      y = int(y[1:])
    except ValueError:
      pass
  if x > y:
    print("compare jamais????")
    return 1
  elif x == y:
    return 0
  else:  #x < y
    return -1
# inutilisée
def compare2(tu1, tu2):
  """fonction de tri pour trier des tuples par la première valeur"""
  x = tu1[0]
  y = tu2[0]
  if x > y:
    return 1
  elif x == y:
    return 0
  else:  #x < y
    return -1

# --- Fonctions de dessin ------------------------



def draw_text(drawable, gc, pangolayout, x, y, string):
    """Dessine une ecriture: x, y sont le milieu de la boite  """
    width = len(string)*8
    height = 8 # 16/2
    pangolayout.set_text(string)
    drawable.draw_layout(gc, x-width/2, y-height, pangolayout)

def draw_one_cross(drawable, gc, x, y, fgcolor=None, bgcolor=None):
    """Dessine un point en forme de croix sur un carré blanc"""
    size = 8
    prev_color = gc.foreground
    if bgcolor:
      gc.foreground = bgcolor
      drawable.draw_rectangle(gc, True, x-size/2-1 , y-size/2-1, size+3, size+3)
    if fgcolor is None:
      fgcolor = prev_color
    gc.foreground = fgcolor
    drawable.draw_line(gc, x-size/2, y-size/2, x+size/2, y+size/2)
    drawable.draw_line(gc, x-size/2, y+size/2, x+size/2, y-size/2)
    gc.foreground = prev_color

# inutile
def update_combo_list(combobox, elem_list, elem_selected="", active_first=False):
    """Insére les noeuds dans un combobox
    Si node_selected n'est pas vide, node_selected est le noeud activé
    Si active_first, le premier élément est activé
    Le combo doit être précédemment vidé si nécessaire"""
    for val in elem_list:
      combobox.append_text(val)
    if active_first:
      combobox.set_active(0)
      return
    if elem_selected == "": return # ajout 4 sept 2008
    try:
      index = elem_list.index(elem_selected)
      combobox.set_active(index)
    except:
        pass

# ne fonctionne pas pour renommer une valeur active, active_val doit être dans les éléments du combo
def fill_elem_combo(combo, values, active_val=''):
  """Vide puis remplit le combo avec les valeurs values
  Active la valeur précédemment active, active active_val si donnée, aucune sinon"""
  #print "function::fill_elem_combo", values, active_val
  model = combo.get_model()
  index = combo.get_active()
  if not index == -1:
    active_val = model[index][0]
    try:
      index = values.index(active_val)
    except ValueError:
      index = -1
  elif active_val:
    try:
      index = values.index(active_val)
    except ValueError:
      index = -1
  model.clear() # utile??
  for val in values:
    combo.append_text(val)
  combo.set_active(index)

# inutilisée
def get_elem_combo(combobox):
  """Retoune la liste des éléments d'un combo"""
  model = combobox.get_model()
  li = []
  for elem in model:
    li.append(elem[0])
  return li
  

# sauvegarde
def change_elem_combo_sauv(combobox, old, new):
  """Remplace le texte old par new dans le combobox, y compris la valeur active"""
  model = combobox.get_model()
  for elem in model:
    val = elem[0]
    if val == old:
      elem[0] = new
      break

# TODO généraliser cette fonction
def change_elem_combo2(combo, n, new):
  """Remplace le texte à la position n par new dans le combobox, y compris la valeur active"""
  model = combo.get_model()
  model[n][0] = new
  return combo.get_active_text()

def change_elem_combo(combobox, old, new, exclude_first=True):
  """Remplace le texte old par new dans le combobox, y compris la valeur active sauf pour le premier élément qui est vide"""
  model = combobox.get_model()
  for i, elem in enumerate(model):
    if i == 0 and exclude_first:
      continue
    val = elem[0]
    if val == old:
      elem[0] = new
      break

# Fonctions pour le chargement

def GetCumulChar(barres, Char):
    """Retourne le chargement point par point sur les barres et le maxi"""
    #print "charTri",self.charBarTri
    maxi = 0
    di = {}
    for barre in barres:
      resu = GetCumulCharBarre(barre, Char)
      if resu == {}:
        continue
      di[barre] = resu[0]
      maxi_b = resu[1]
      if maxi_b > maxi:
        maxi = maxi_b
    return di, maxi

def GetCumulCharBarre(barre, Char):
    """Retourne les valeurs des charges uniformes et triangulaires cumulées pour une barre
    Format {0: ((qxD,qYD), ), a2: ((qxG,qyG), (qxD,qyD)), 1: ((qxG,qyG), )}
    Attention aux valeurs extremes 0 et 1 à revoir"""
    di = {}
    maxi = 0
    char_tri = Char.charBarTri.get(barre, {})
    char_qu = Char.charBarQu.get(barre, {})
    li_a = list(char_qu.keys())
    for a in list(char_tri.keys()):
      if a in li_a:
        continue
      li_a.append(a)
    if li_a == []:
      return {}
    li_a.append(0.)
    li_a.sort()

    for a in li_a:
      deltax, deltay = 0., 0.
      qxD, qyD = 0., 0.
      for u, char in char_tri.items():
        if u < a:
          continue
        if u > a:
          qxD += a/u*char[0]
          qyD += a/u*char[1]
        elif u == a:
          deltax = char[0]
          deltay = char[1]
      qxG = qxD + deltax
      qyG = qyD + deltay
      for u, char in char_qu.items():
        if u < a:
          continue
        if u > a:
          qxD += char[0]
          qxG += char[0]
          qyD += char[1]
          qyG += char[1]
        elif u == a:
          qxG += char[0]
          qyG += char[1]
      di[a] = ((qxG, qyG), (qxD, qyD))
      qmax = max(abs(qxG), abs(qyG), abs(qxD), abs(qyD))
      if qmax > maxi:
        maxi = qmax
    return di, maxi

def add_icon_to_button(button, id):
    """Fonction pour ajouter un bouton fermer dans l'onglet du notebook"""
    #création d'une boite horizontale
    iconBox = Gtk.HBox(False, 0)
    #Création d'une image vide
    image = Gtk.Image()
    #On récupère l'icone du bouton "fermer"
    image.set_from_stock(id, Gtk.IconSize.MENU)
    #On enlève le relief au bouton (donné en attribut)
    Gtk.Button.set_relief(button, Gtk.ReliefStyle.NONE)
    #On récupère les propriétés du bouton
    settings = Gtk.Widget.get_settings(button)
    #On affecte à w et h les dimensions
    w, h = Gtk.icon_size_lookup_for_settings(settings, Gtk.IconSize.MENU)[1:]
    #On modifie ces dimensions
    Gtk.Widget.set_size_request(button, w + 8, h + 8)
    image.show()
    #On met l'image dans la boite
    iconBox.pack_start(image, True, False, 0)
    #On ajoute la boite dans le bouton
    button.add(iconBox)
    iconBox.show()

def add_icon_to_button2(button, id, size=None):
    """Fonction pour ajouter un bouton fermer dans l'onglet du notebook"""
    #création d'une boite horizontale
    if size is None:
      size = Gtk.IconSize.MENU
    elif size == "+":
      size = Gtk.IconSize.DIALOG
    iconBox = Gtk.HBox(False, 0)
    #Création d'une image vide
    image = Gtk.Image()
    #On récupère l'icone du bouton "fermer"
    image.set_from_stock(id, size)
    #On enlève le relief au bouton (donné en attribut)
    Gtk.Button.set_relief(button, Gtk.ReliefStyle.NONE)
    #On récupère les propriétés du bouton
    #settings = Gtk.Widget.get_settings(button)
    #On affecte à w et h les dimensions
    #(w, h) = Gtk.icon_size_lookup_for_settings(settings, Gtk.IconSize.MENU)
    #On modifie ces dimensions
    #Gtk.Widget.set_size_request(button, w + 8, h + 8)
    image.show()
    #On met l'image dans la boite
    iconBox.pack_start(image, True, False, 0)
    #On ajoute la boite dans le bouton
    button.add(iconBox)
    iconBox.show()



# --------- Tools -------------------------

def debug_get_props(widget):
    for pspec in widget.props:
      print(pspec)
      try: print(widget.get_property(pspec.name))
      except: pass


# fonctionnement : print_api([])
def print_api(element):
  methods = [el for el in dir(element) if not el.startswith('_')]
  for meth in methods:
    print(meth)
    try:
      print(getattr(element, meth).__doc__)
    except:
      print("Error")

def debug_get_props(widget):
    for pspec in widget.props:
      print(pspec)
      try: print(widget.get_property(pspec.name))
      except: pass



