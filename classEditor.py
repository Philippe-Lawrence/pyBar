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

import os
import sys
from gi.repository import Pango, GObject, Gtk, Gdk, GLib

import xml.etree.ElementTree as ET
from function import *
from time import sleep
import Const
import classDialog
import classProfilManager
import classPrefs
import classSectionEditor
import classSection
import copy
import file_tools
import function

screen = Gdk.Screen.get_default()
css_provider = Gtk.CssProvider()
css_provider.load_from_path('gtk-widgets.css')
context = Gtk.StyleContext()
context.add_provider_for_screen(screen, css_provider,
                                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def Rotation(a, x, y):
  """x, y étant les coordonnées d'un point dans un repère 1, retourne les coordonnées du point dans le repère 2 obtenu par rotation d'angle a"""
  x1 = x*math.cos(a) + y*math.sin(a)
  y1 = -x*math.sin(a) + y*math.cos(a)
  return x1, y1

class MyError(Exception):
  """Surcharge de la classe d'erreur"""

  #def __init__(self, value):
  #  self.value = value

  def __str__(self):
    return repr(self.value)

# inutile
class DataEntry(Gtk.Entry):

  def __init__(self):
    super(DataEntry,self).__init__()

  def get_text(self):
    print(super(DataEntry, self).get_text().replace(",", "."))
    return super(DataEntry, self).get_text().replace(",", ".")

class MyEntry(Gtk.Entry):
  """Entry à taille modifiable"""

  def __init__(self):
    GObject.GObject.__init__(self)
    self.connect("draw", self.draw_event)

  def draw_event(self, widget, event):
    text = self.get_text()
    n_chars = len(text)
    self.set_width_chars(n_chars+1)

class AbstractNode(object):
  """Classe abstraite pour les noeuds"""

  class_counter = 0

  def update_preceding_combo(self, old, new):
    """Actualise le combo des noeuds précédents - Ne fait rien"""
    pass

  def fill_preceding_node(self, combobox, li):
    """Remplit le combo des noeuds avec des nouvelles valeurs - Ne fait rien"""
    pass

  def update_arc_name(self, barres, old_name, new_name):
    """Actualise le combo du nom de l'arc pour un noeud - Ne fait rien"""
    pass

  def set_xml(self, parent):
    """Crée les attributs nécessaires à la structure xml pour un noeud - Ne fait rien"""
    pass

  def update_tooltip_L(self, unit_L, unit_F=None):
    """Actualise les tooltips des longueurs suite à un changement d'unité pour un noeud - Ne fait rien"""
    pass

  def add_combo_item(self, elem):
    """Ajoute un arc dans le combo des arcs - Ne fait rien"""
    pass

  def remove_combo_items(self, barres):
    """Supprime des arcs dans le combo des arcs - Ne fait rien"""
    pass

# non utilisé
  def on_copy(self, widget, Main):
    """Action de copier l'élement - finir"""
    Main.set_is_changed()

  def on_delete(self, widget, args):
    """Action de suppression d'un noeud depuis le CM"""
    Main, node_id = args
    box = Main.data_box['noeud']
    nodes = Main.data_editor.nodes
    are_deleted = []
    old_nodes = Main.data_editor.get_all_nodes()
    for i, node in enumerate(nodes):
      if not node.id == node_id:
        continue
      box.remove(node.hbox.get_parent())
      are_deleted.append(node.name)
      del(nodes[i])
      Main.set_is_changed(True)
      Main.data_editor.size_changed = True
      break
    Main._fill_preceding_node(i)
    # modification de la page contenant des combobox avec des noeuds
    Main.remove_liaison2(are_deleted)
    Main.remove_nodes_combos(old_nodes, are_deleted)
    Main._remove_combo_char_items(are_deleted)

class ArcNode(AbstractNode):
  """Classe pour un noeud d'arc"""

  def __init__(self, data):
    self.id = AbstractNode.class_counter
    AbstractNode.class_counter += 1
    content = data['d']
    self.name = data['id']
    self.arc = data['name']
    d = data['d']
    try:
      self.d = float(d) # compris entre 0 et 1
    except ValueError:
      self.d = None
    try:
      pos_on_curve = data['pos_on_curve']
      if pos_on_curve == 'true':
        self.pos_on_curve = 1
      else:
        self.pos_on_curve = 0
    except KeyError:
      self.pos_on_curve = 1
    if 'rel' in data:
      if data["rel"] == 1:
        self.rel = True
      elif data["rel"] == "0":
        self.rel = False
      else:
        self.rel = False
    else:
      self.rel = False
    self.x = None
    self.y = None
    if 'liaison' in data : self.liaison = data['liaison'].split(',')

  def set_content_from_widgets(self, relative_node=None):
    """Modifie les attributs à partir de la lecture des widgets pour un noeud d'arc"""
    widgets = self.hbox.get_children()
    self.arc = widgets[3].get_active_text()
    entry = widgets[4]
    try:
      self.d = float(entry.get_text().replace(',', '.'))
      if self.d <= 0 or self.d >= 1:
        raise ValueError
    except ValueError:
      self.d = None
    #self.rel = widgets[5].get_active()

  def set_xml(self, parent):
    """Crée les attributs nécessaires à la structure xml pour un noeud d'arc"""
    if self.arc is None:
      return
    node = ET.SubElement(parent, "arc", {"id": self.name})
    d = self.d
    if self.d is None:
      d = ""
    node.set("d", str(d))
    node.set("name", self.arc)
    node.set("r", self.rel and "1" or "0")
    node.set("pos_on_curve", self.pos_on_curve and "true" or "false")
    try:
      node.set("liaison", ",".join(self.liaison))
    except AttributeError:
      pass
    return node

  def update_arc_name(self, barres, old_name, new_name):
    """Actualise le combo du nom de l'arc pour un noeud d'arc"""
    widgets = self.hbox.get_children()
    if self.arc == old_name:
      self.arc = new_name
    combobox = widgets[3]
    function.change_elem_combo(combobox, old_name, new_name, False)

  def update_coors(self, modified_nodes, data_editor):
    """Actualise les coordonnées du noeud d'arc"""
    self.set_coors_label(data_editor)
    return self.name

  def set_coors_label(self, data_editor):
    """Raffraichit l'affichage des coordonnées dans une ligne de noeud d'arc"""
    #print ("set_coors_label", self.name, self.arc)
    widgets = self.hbox.get_children()
    label = widgets[5]
    try:
      if self.arc == False or self.arc is None:
        raise MyError
      arc = data_editor.get_barre(self.arc)
      resu = arc.get_coors(data_editor, self.d)
      if resu is None:
        raise MyError
      x, y = resu

    except MyError:
      label.set_text("%s = (-,-)" % self.name)
      self.x = None
      self.y = None
      return
    label.set_text("%s = (%s,%s)" % (self.name, function.PrintValue(x),
		function.PrintValue(y)))
    self.x = x
    self.y = y

  def update_numeric_L(self, factor):
    """Actualise les valeurs numériques après changement unité de longueur pour un noeud ArcNode"""
    pass


  def add_hbox(self, Main):
    """Crée la hbox pour un noeud d'arc pour la page des noeuds"""
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    image = Gtk.Image()
    file1 = self.get_img_file()
    image.set_from_file("glade/%s" % file1)
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    #entry.set_width_chars(10)
    entry.set_width_chars(10)
    entry.set_text(self.name)
    entry.set_tooltip_text("Nom")
    entry.connect("changed", self.update_node_name, Main, self.id)
    hbox.pack_start(entry, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(90, 30)
    arcs = Main.data_editor.get_arcs2()
    function.fill_elem_combo(combobox, arcs, self.arc)
    id1 = combobox.connect('changed', self.update_arc, Main)
    combobox.set_tooltip_text('Choix de l\'arc')
    hbox.pack_start(combobox, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    #entry.set_width_chars(10)
    d = self.d
    if self.d is None:
      d = ""
    entry.set_text(str(d))
    entry.set_tooltip_text("Position relative entre 0 et 1")
    id2 = entry.connect('changed', Main.update_nodes, self)
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label()
    hbox.pack_start(label, False, False, 20)
    self.hbox = hbox
    self.set_coors_label(Main.data_editor)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    self.ids = (id1, id2)
    return eventbox

  def get_img_file(self):
    """Retourne le nom du fichier en fonction des relaxations"""
    if self.rel == 0:
      return "noeud2_0.png"
    return "noeud2_1.png"

  def _update_relax(self, widget, Main):
    """Modification de la relaxation du noeud d'arc"""
    self.rel = widget.get_active()
    file1 = self.get_img_file()
    widgets = self.hbox.get_children()
    image = widgets[0]
    image.set_from_file("glade/%s" % file1)
    Main.set_is_changed(True)

  def update_arc(self, widget, Main):
    """Mise à jour de l'arc de rattachement d'un noeud d'arc"""
    tag = self.arc
    self.arc = widget.get_active_text()
    ed = Main.data_editor
    barres = ed.barres
    if tag is False: # ajout du noeud dans les combo des barres
      for barre in barres:
        barre.add_node_combo(ed, self)
    else:
      defined = []
      for barre in barres:
        widgets = barre.hbox.get_children()
        combo1 = widgets[3]
        combo2 = widgets[4]
        model = combo1.get_model()
        nodes = [i[0] for i in model]
        if self.arc in defined:
          if not self.name in nodes:
            barre.add_node_combo(ed, self, force=True)
        else:
          if self.name in nodes:
            barre.remove_nodes_combo([self.name])
        defined.append(barre.name)
    self.set_coors_label(Main.data_editor)
    Main.set_is_changed(True)

  def update_node_name(self, widget, Main, id):
    """Mise à jour du nom d'un noeud pour un noeud d'arc"""
    new = widget.get_text()
    old = self.name
    if new == old:
      return None
    self.name = new
    Main.set_is_changed(True)
    # actualise les combobox des noeuds précédents
    nodes = Main.data_editor.nodes
    #node_names = Main.data_editor.get_all_nodes()
    #n = node_names.index(new)
    n = 0
    for node in nodes:
      if node.id == id:
        break
      n += 1
    next_nodes = nodes[n+1:]
    self._update_preceding_node(next_nodes, old, new)
    # modification des combos des noeuds dans toutes mes pages
    Main._update_node_list(self, n)
    # actualise les instances Nodes
    self.set_content_from_widgets()
    self.set_coors_label(Main.data_editor)

  def _update_preceding_node(self, nodes, old, new):
    """Actualise le combo des noeuds relatifs pour tous les noeuds donnés"""
    for node in nodes:
      node.update_preceding_combo(old, new)

  def add_combo_item(self, elem):
    """Ajoute un arc dans le combo des arcs"""
    combo = self.hbox.get_children()[3]
    combo.append_text(elem)

  def remove_combo_items(self, deleted):
    """Supprime des arcs dans le combo des noeuds d'arcs"""
    combo = self.hbox.get_children()[3]
    model = combo.get_model()
    nodes = [i[0] for i in model]
    indices = []
    for node in deleted:
      if node in nodes:
        indices.append(nodes.index(node))
    for pos in reversed(indices):
      combo.remove(pos)

  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'un noeud d'arc"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        arcs = Main.data_editor.get_arcs()
        menu1 = Gtk.Menu()
        if self.arc in arcs:
          pass
        menuitem1 = Gtk.CheckMenuItem(label="Relaxer", active=self.rel)
        menuitem1.connect("activate", self._update_relax, Main)
        menu1.append(menuitem1)
        menuitem2 = Gtk.MenuItem(label="Supprimer")
        menuitem2.connect("activate", self.on_delete, (Main, self.id))
        menu1.append(menuitem2)
        menuitem3 = Gtk.CheckMenuItem(label="Position relative à la corde", active=self.pos_on_curve)
        menuitem3.connect("activate", self.update_type_coor, Main)
        menu1.append(menuitem3)
        menu1.show_all()
        menu1.popup_at_pointer(event)
        return True # bloque la propagation du signal
    return False

  def update_type_coor(self, widget, Main):
    """Choisi le type de coordonnées (par rapport à la corde ou sur l'arc)"""
    #print ("update_type_coor")
    self.pos_on_curve = widget.get_active()
    Main.set_is_changed(True)


class Node(AbstractNode):
  """Classe contenant pour un noeud simple"""

  def __init__(self, name, content):
    self.id = AbstractNode.class_counter
    AbstractNode.class_counter += 1
    self.name = name
    self.arc = None # None si sans objet (segment), False si pas encore défini
    self.x = None
    self.y = None
    self.set_content_from_string(content['d'])
    if 'liaison' in content : 
      self.liaison = content['liaison'].split(',')

  def set_content_from_string(self, content):
    """Crée les attribut de l'instance en fonction de la chaine de caractère"""
    self.rel = None
    if content.find("<") > 0:
      self.pol = True
    else:
      self.pol = False
    if content[0] == "@":
      pos = content.find(",")
      self.rel = content[1:pos]
      content = content[pos+1:]
    string = ","
    if self.pol:
      string = "<"
    self.s_x, self.s_y = content.split(string)

  def set_content_from_widgets(self, relative_node=None):
    """Modifie les attributs à partir de la lecture des widgets pour un noeud simple"""
    widgets = self.hbox.get_children()
    entry = widgets[2]
    node_name = entry.get_text()
    if relative_node is None:
      combobox = widgets[3]
      relative_node = combobox.get_active_text()
      if relative_node == "":
        relative_node = None
    self.rel = relative_node
    entry = widgets[4]
    self.s_x = entry.get_text().replace(',', '.')
    entry = widgets[5]
    self.s_y = entry.get_text().replace(',', '.')
    self.pol = [False, True][widgets[6].get_active()]


  def set_xml(self, parent):
    """Crée les attributs nécessaires à la structure xml pour un noeud simple"""
    node = ET.SubElement(parent, "node", {"id": self.name})
    string = ''
    if not self.rel is None:
      string += "@%s," % self.rel
    string += "%s" % self.s_x
    if self.pol:
      string += "<"
    else:
      string += ","
    string += "%s" % self.s_y
    node.set("d", string)
    try:
      #assert(isinstance(self.liaison, list))
      node.set("liaison", ",".join(self.liaison))
    except AttributeError:
      pass

  def update_preceding_combo(self, old, new):
    """Actualise le combo des noeuds précédents pour un noeud simple"""
    combobox = self.hbox.get_children()[3]
    function.change_elem_combo(combobox, old, new)
    if self.rel == old:
      self.rel = new

  def fill_preceding_node(self, combobox, li):
    """Remplit le combo des noeuds avec des nouvelles valeurs"""
    function.fill_elem_combo(combobox, li)

  def update_coors(self, modified_nodes, data_editor):
    """Actualise les coordonnées du noeud simple"""
    combobox = self.hbox.get_children()[3]
    relative_node = combobox.get_active_text()
    if relative_node is None or not relative_node in modified_nodes:
      return None # pas de noeud relatif ou noeud different de celui modifié
    self.set_coors_label(data_editor)
    return self.name

  def set_coors_label(self, data_editor):
    """Raffraichit l'affichage des coordonnées dans une ligne de noeud simple"""
    widgets = self.hbox.get_children()
    nodes = data_editor.nodes
    coors = function.Str2NodeCoors2(self, nodes)
    label = widgets[7]
    if coors:
      label.set_text("%s = (%s,%s)" % (self.name, function.PrintValue(coors[0]),
		function.PrintValue(coors[1])))
      self.x = coors[0]
      self.y = coors[1]
    else:
      label.set_text("%s = (-,-)" % self.name)
      try:
        self.x = None
        self.y = None
      except AttributeError:
        pass



  def update_numeric_L(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de longueur pour un noeud Node"""
    widgets = self.hbox.get_children()
    is_pol = [False, True][widgets[6].get_active()]
    entry = widgets[4]
    entry.handler_block(self.ids[1])
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    entry.handler_unblock(self.ids[1])
    entry = widgets[5]
    entry.handler_block(self.ids[2])
    if not is_pol:
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass
    entry.handler_unblock(self.ids[2])
    self.set_content_from_widgets(self.rel)


  def add_hbox(self, Main):
    """Crée la hbox d'un noeud simple de la page des noeuds"""
    node_name = self.name
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    #unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    image = Gtk.Image()
    image.set_from_file("glade/noeud1.png")
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(node_name)
    entry.set_tooltip_text("Nom")
    entry.connect("changed", self.update_node_name, Main, self.id)
    hbox.pack_start(entry, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(60, 30)
    pos = Main.data_editor.nodes.index(self)
    nodes = Main.data_editor.nodes[0:pos]
    li = ['']
    for val in nodes:
      li.append(val.name)
    if self.rel is None:
      rel = ''
    else:
      rel = self.rel
    function.fill_elem_combo(combobox, li, rel)
    if pos == 0:
      combobox.set_sensitive(False)
    combobox.set_tooltip_text("Définir le noeud par rapport à un noeud précédent")
    id1 = combobox.connect('changed', Main.update_nodes, self)
    hbox.pack_start(combobox, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(self.s_x)
    id2 = entry.connect('changed', Main.update_nodes, self)
    hbox.pack_start(entry, False, False, 0)

    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(self.s_y)
    id3 = entry.connect('changed', Main.update_nodes, self)
    hbox.pack_start(entry, False, False, 0)
    self.ids = (id1, id2, id3)
    button = Gtk.CheckButton(label="Polaire")
    if self.pol:
      button.set_active(True)
    button.connect('clicked', self.update_node2, Main)
    hbox.pack_start(button, False, False, 0)

    label = Gtk.Label()
    hbox.pack_start(label, False, False, 20)
    self.hbox = hbox
    self.set_coors_label(Main.data_editor)
    self.update_tooltip_L(unit_L)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox


  def update_tooltip_L(self, unit_L):
    """Actualise les tooltips des longueurs suite à un changement d'unité pour un noeud simple"""
    widgets = self.hbox.get_children()
    is_pol = [False, True][widgets[6].get_active()]
    entry1 = widgets[4]
    entry2 = widgets[5]
    if is_pol:
      string1 = 'Distance en %s' % unit_L
      string2 = 'Angle en degré'
    else:
      string1 = 'Coordonnée suivant X en %s' % unit_L
      string2 = 'Coordonnée suivant Y en %s' % unit_L
    entry1.set_tooltip_text(string1)
    entry2.set_tooltip_text(string2)

  def update_node2(self, widget, Main):
    """Changement du type de coordonnées polaire ou cartésienne.
    Actualise les tooltip pour un noeud donné"""
    self.pol = [False, True][widget.get_active()]
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    self.update_tooltip_L(unit_L)
    Main.set_is_changed(True)


  def update_node_name(self, widget, Main, id):
    """Mise à jour du nom d'un noeud pour un noeud simple"""
    new = widget.get_text()
    old = self.name
    if new == old:
      return None
    self.name = new
    Main.set_is_changed(True)
    # actualise les combobox des noeuds précédents
    nodes = Main.data_editor.nodes
    n = 0
    for node in nodes:
      if node.id == id:
        break
      n += 1

    next_nodes = nodes[n+1:]
    self._update_preceding_node(next_nodes, old, new)
    # modification de la page des barres
    Main._update_node_list(self, n)
    # actualise les instances Nodes
    self.set_content_from_widgets()
    self.set_coors_label(Main.data_editor)

  def _update_preceding_node(self, nodes, old, new):
    """Actualise le combo des noeuds relatifs pour tous les noeuds donnés"""
    for node in nodes:
      node.update_preceding_combo(old, new)

  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'un noeud"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        menu1 = Gtk.Menu()
        menuitem1 = Gtk.MenuItem(label="Supprimer")
        menuitem1.connect("activate", self.on_delete, (Main, self.id))
        menu1.append(menuitem1)
        menu1.show_all()
        menu1.popup_at_pointer(event)
        return True # bloque la propagation du signal
    return False


class AbstractBar(object):
  """Classe abstraite pour les barres"""

  class_counter = 0


  def get_nodes(self, barres, nodes):
    """Retourne la liste des noms des noeuds pour la barre"""
    b_pos = barres.index(self) # tester ou mettre self.pos???
    barres = barres[:b_pos]
    barres = [b.name for b in barres]
    mynodes = []
    for node in nodes:
      if node.arc is None:
        mynodes.append(node.name)
        continue
      if not node.arc in barres:
        break
      mynodes.append(node.name)
    return mynodes

  def set_content(self, data_editor):
    """Calcule les attributs de l'objet"""
    #print("set_content pas défini pour la classe")
    pass

  def set_empty_nodes(self, data_editor):
    """calcul des coordonnées des points qui dépendent de l'arc"""
    nodes = data_editor.nodes
    for node in nodes:
      try:
        if node.arc == self.name:
          if node.x is None:
            resu = self.get_coors(data_editor, node.d)
            if not resu is None:
              node.x, node.y = resu
      except AttributeError:
        pass

  def add_node_combo(self, ed, node, force=False):
    """Ajoute un noeud aux combo des barres"""
    print("debug add_node_combo")

  def remove_nodes_combo(self, deleted_nodes):
    """Supprime les noeuds du combo des noeuds"""
    widgets = self.hbox.get_children()
    combo1 = widgets[3]
    combo2 = widgets[4]
    model = combo1.get_model()
    nodes = [i[0] for i in model]
    indices = []
    for node in deleted_nodes:
      if node in nodes:
        indices.append(nodes.index(node))
    for pos in reversed(indices):
      combo1.remove(pos)
      combo2.remove(pos)

  def update_numeric_F(self, factor):
    pass

  def update_tooltip_F(self, factor):
    pass

  def rename_node_combo(self, de, Node, n):
    """Renomme un noeud dans la liste des noeuds des combo"""
    print("rename_node_combo::debug")

  def set_length(self, nodes):
    """Attribut la longueur de l'élément"""
    self.l = None

  def _update_relaxs(self, widget, Main):
    if self.R0 == 1 and self.R1 == 1:
      self.R0, self.R1 = 0, 0
    elif self.R0 == 0 and self.R1 == 0:
      self.R0, self.R1 = 1, 1
    file1 = self.get_img_file()
    widgets = self.hbox.get_children()
    image = widgets[0]
    image.set_from_file("glade/%s" % file1)
    Main.set_is_changed(True)

  def _update_relax(self, widget, Main):
    """Modification de la relaxation d'extremité d'une barre"""
    r = widget.get_name()
    if r == "R0":
      self.R0 = [0, 1][widget.get_active()]
    elif r == "R1":
      self.R1 = [0, 1][widget.get_active()]
    file1 = self.get_img_file()
    widgets = self.hbox.get_children()
    image = widgets[0]
    image.set_from_file("glade/%s" % file1)
    Main.set_is_changed(True)

  def _update_combo(self, combo, Main, n):
    """Actualisation d'un combo de noeud"""
    node_name = combo.get_active_text()
    if node_name is None:
      node_name = ''
    self.set_node(Main.data_editor, node_name, n)
    self.set_content(Main.data_editor)
    self.set_length(Main.data_editor.nodes)
    Main.set_is_changed(True)
    Main.update_bars_combo(self.name)


  def update_numeric_L(self, factor):
    pass

  def update_tooltip_L(self, unit_L):
    """Actualise les tooltips des longueurs suite à un changement d'unité dans une barre - Ne fait rien"""
    pass

  def on_move_up(self, widget, barre, Main):
    """Déplace la ligne vers le haut"""
    n = Main.data_editor.get_barre_pos(barre)
    if n == 0:
      return
    barres = Main.data_editor.barres
    barres[n], barres[n-1] = barres[n-1], barres[n]
    eventbox = barre.hbox.get_parent()
    box = eventbox.get_parent()
    box.reorder_child(eventbox, n-1)
    for i in range(n-1, len(barres)):
      b = barres[i]
      b.update_combos(Main)
    Main.set_is_changed()


  def on_move_down(self, widget, barre, Main):
    """Déplace la ligne vers le bas"""
    n = Main.data_editor.get_barre_pos(barre)
    barres = Main.data_editor.barres
    if n == len(barres)-1:
      return
    barres[n], barres[n+1] = barres[n+1], barres[n]
    eventbox = barre.hbox.get_parent()
    box = eventbox.get_parent()
    box.reorder_child(eventbox, n+1)
    for i in range(n-1, len(barres)):
      b = barres[i]
      b.update_combos(Main)
    Main.set_is_changed()

  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'une barre"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        try:
          self.k0
          k0 = 1
        except AttributeError:
         k0 = 0
        try:
          self.k1
          k1 = 1
        except AttributeError:
          k1 = 0
        menu1 = Gtk.Menu()
        menuitem = Gtk.CheckMenuItem(label="Relaxer l\'origine", active=self.R0)
        menuitem.set_name('R0')
        menuitem.connect("activate", self._update_relax, Main)
        menu1.append(menuitem)
        menuitem = Gtk.CheckMenuItem(label="Relaxer l\'extrémité", active=self.R1)
        menuitem.set_name('R1')
        menuitem.connect("activate", self._update_relax, Main)
        menu1.append(menuitem)
        if isinstance(self, Barre):
          if self.R0==1 and self.R1==1:
            menuitem = Gtk.MenuItem(label="Supprimer les relaxations")
            #menuitem.set_name('R1')
            menuitem.connect("activate", self._update_relaxs, Main)
            menu1.append(menuitem)
            is_sensitive = True
          elif self.R0==0 and self.R1==0:
            menuitem = Gtk.MenuItem(label="Tout relaxer")
            #menuitem.set_name('R1')
            menuitem.connect("activate", self._update_relaxs, Main)
            menu1.append(menuitem)
            is_sensitive = False
          else:
            is_sensitive = False
          if self.mode == 0:
            active1 = 0
            active2 = 0
          elif self.mode == 1:
            active1 = 1
            active2 = 0
          elif self.mode == -1:
            active1 = 0
            active2 = 1
          menuitem3 = Gtk.CheckMenuItem(label="Traction seulement", active=active1)
          menuitem3.set_sensitive(is_sensitive)
          menuitem3.connect("activate", self.set_one_way, Main, "N+")
          menu1.append(menuitem3)
          menuitem4 = Gtk.CheckMenuItem(label="Compression seulement", active=active2)
          menuitem4.set_sensitive(is_sensitive)
          menuitem4.connect("activate", self.set_one_way, Main, "N-")
          menu1.append(menuitem4)

        menuitem5 = Gtk.CheckMenuItem(label="Rotation élastique de l\'origine", active=(k0 == 1 and True or False))
        menuitem5.set_name('k0')
        menuitem5.connect("activate", self.update_k_widget, Main)
        menu1.append(menuitem5)
        menuitem6 = Gtk.CheckMenuItem(label="Rotation élastique de l\'extrémité", active=(k1 == 1 and True or False))
        menuitem6.set_name('k1')
        menuitem6.connect("activate", self.update_k_widget, Main)
        menu1.append(menuitem6)

        menuitem7 = Gtk.MenuItem(label="Supprimer")
        menuitem7.connect("activate", self.on_delete, (Main, self.id))
        menu1.append(menuitem7)

        menu1.show_all()
        menu1.popup_at_pointer(event)
        return True # bloque la propagation du signal
    return False

  def on_delete(self, widget, args):
    """Action de suppression d'une barre depuis le CM"""
    Main, b_id = args
    box = Main.data_box['barre']
    barres = Main.data_editor.barres
    for i, b in enumerate(barres):
      if not b.id == b_id:
        continue
      box.remove(b.hbox.get_parent())
      #are_deleted.append(node.name)
      del(barres[i])
      Main.data_editor.size_changed = True
      Main.set_is_changed(True)
      break
    Main.set_is_changed()
    Main.data_editor.get_barres_by_node()
    nodes = Main.data_editor.nodes
    for node in nodes:
      node.remove_combo_items([b.name])


  def update_k_widget(self, widget, Main):
    pass
    # chargement


class Arc(AbstractBar):
  """Classe pour une barre de type arc"""

  def __init__(self, args, data_editor):
    for nom, val in args.items():
      setattr(self, nom, val)
    self.id = AbstractBar.class_counter
    AbstractBar.class_counter += 1
    self.set_content(data_editor)
    self.set_empty_nodes(data_editor)
    #self.set_length(data_editor.nodes)

  def set_xml(self, parent):
    """Crée les attributs nécessaires à la structure xml pour un arc"""
    node = ET.SubElement(parent, "arc", {"id": self.name})
    node.set("start", self.N0)
    node.set("end", self.N1)
    node.set("center", self.c)
    node.set("r0", str(self.R0))
    node.set("r1", str(self.R1))
    return node

  def set_node(self, data_editor, node_name, n):
    """Modifie un noeud dans une ligne d'arc"""
    if n == 0:
      self.N0 = node_name
      self.set_content(data_editor)
    elif n == 1:
      self.N1 = node_name
      self.set_content(data_editor)
    elif n == 2:
      self.c = node_name
      self.set_content(data_editor)
    else:
      print("debug:: unexpected in set_node")

  def set_content(self, data_editor):
    """Calcule les attributs de l'objet de type Arc"""
    #print("set_content in class Arc")
    factor_L = data_editor.unit_conv['L']
    self.l = None
    try:
      N0_name, N1_name, C_name = self.N0, self.N1, self.c
    except AttributeError:
      return
    nodes = data_editor.nodes
    node_names = data_editor.get_all_nodes()
    try:
      C_inst = nodes[node_names.index(C_name)]
      N0_inst = nodes[node_names.index(N0_name)]
      N1_inst = nodes[node_names.index(N1_name)]
    except ValueError:
      self.teta1 = None
      self.teta2 = None
      self.r = None
      return
    try:
      xc, yc = C_inst.x, C_inst.y
      x0, y0 = N0_inst.x, N0_inst.y
      x1, y1 = N1_inst.x, N1_inst.y
    except AttributeError:
      self.teta1 = None
      self.teta2 = None
      self.r = None
      return
    self.teta1 = function.get_vector_angle((xc, yc), (x0, y0))
    #print "teta1=", self.teta1
    if self.teta1 is None:
      self.teta2 = None
      self.r = None
      return
    self.teta2 = function.get_vector_angle((xc, yc), (x1, y1))
    #print "teta2=", self.teta2
    if self.teta2 is None:
      self.teta1 = None
      self.r = None
      return
    if abs(self.teta1 - self.teta2) < 1e-6:
      print("test Arc:: set_content")
      #self.teta1 = None
      #self.teta2 = None
      #self.r = None
      #return
    r0 = ((xc-x0)**2+(yc-y0)**2)**0.5
    r1 = ((xc-x1)**2+(yc-y1)**2)**0.5
    if r0 == 0:
      self.r = None
    elif abs(r1-r0)/r0 > 1e-5:
      self.r = None
    else:
      self.r = r0*factor_L # toujours en mètre
      alpha = self.teta1-self.teta2
      if alpha <= 0:
        alpha += 2*math.pi
      self.l = alpha*self.r

  def get_coors(self, data_editor, d):
    """Retourne les coordonnées du point appartenant à un arc"""
    nodes = data_editor.nodes
    #print "get_coors"
    factor_L = data_editor.unit_conv['L']
    if self.r is None:
      return None
    r = self.r/factor_L
    try:
      N0_name, N1_name, C_name = self.N0, self.N1, self.c
    except AttributeError:
      return None
    node_names = data_editor.get_all_nodes()
    C_inst = nodes[node_names.index(C_name)]
    N0_inst = nodes[node_names.index(N0_name)]
    N1_inst = nodes[node_names.index(N1_name)]
    try:
      xc, yc = C_inst.x, C_inst.y
      x0, y0 = N0_inst.x, N0_inst.y
      x1, y1 = N1_inst.x, N1_inst.y
    except AttributeError:
      return None
    try:
      xc*yc*x0*y0*x1*y1 # test valeur None ???
    except TypeError:
      return None
    teta1, teta2 = self.teta1, self.teta2
    if teta1 is None or teta2 is None:
      return None
    dteta = teta1-teta2
    if dteta <= 0:
      dteta += 2*math.pi
    if teta1 < 0:
      teta1 += 2*math.pi
    if d is None:
      return None
    a = teta1 - d*dteta
    x, y = r*math.cos(a)+xc, r*math.sin(a)+yc
    return x, y


  def add_hbox(self, Main):
    """Crée la hbox de la page des barres pour un arc"""
    name = self.name
    barres = Main.data_editor.barres
    nodes = self.get_nodes(barres, Main.data_editor.nodes)
    c = self.c
    N0, N1 = self.N0, self.N1
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=6)
    image = Gtk.Image()
    file1 = self.get_img_file()
    image.set_from_file("glade/%s" % file1)
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_tooltip_text('Nom')
    entry.set_text(name)
    entry.connect("changed", self.update_bar_name, Main)
    hbox.pack_start(entry, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, N0)
    combobox.connect('changed', self._update_combo, Main, 0)
    combobox.set_tooltip_text('Origine')
    hbox.pack_start(combobox, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_tooltip_text('Fin')
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, N1)
    combobox.connect('changed', self._update_combo, Main, 1)
    hbox.pack_start(combobox, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_tooltip_text('Centre')
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, c)
    combobox.connect('changed', self._update_combo, Main, 2)
    hbox.pack_start(combobox, False, False, 0)
    up_b = Gtk.Button.new_from_icon_name('go-up', Gtk.IconSize.MENU)
    up_b.set_relief(Gtk.ReliefStyle.NONE)
    up_b.connect('clicked', self.on_move_up, self, Main)
    hbox.pack_start(up_b, False, False, 0)
    down_b = Gtk.Button.new_from_icon_name('go-down', Gtk.IconSize.MENU)
    down_b.set_relief(Gtk.ReliefStyle.NONE)
    down_b.connect('clicked', self.on_move_down, self, Main)
    hbox.pack_start(down_b, False, False, 0)
    self.hbox = hbox
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def get_img_file(self):
    """Retourne le nom du fichier en fonction des relaxations"""
    if self.R0 == 0:
      if self.R1 == 0:
        return "arc00.png"
      return "arc01.png"
    if self.R1 == 0:
      return "arc10.png"
    return "arc11.png"


  def update_combos(self, Main):
    """Remplit les combo des noeuds pour un arc"""
    nodes = self.get_nodes( Main.data_editor.barres, Main.data_editor.nodes)
    widgets = self.hbox.get_children()
    combobox = widgets[3]
    function.fill_elem_combo(combobox, nodes, self.N0)
    combobox = widgets[4]
    function.fill_elem_combo(combobox, nodes, self.N1)
    combobox = widgets[5]
    function.fill_elem_combo(combobox, nodes, self.c)

  def get_is_arc(self):
    """Retourne vrai pour un arc"""
    return True

  def update_bar_name(self, widget, Main):
    """Modification du nom d'un arc"""
    new_name = widget.get_text()
    old_name = self.name
    self.name = new_name
    Main.update_bar_names(self, old_name, new_name)
    Main.update_combo_arc(old_name, new_name)
    Main.set_is_changed()


  def remove_nodes_combo(self, deleted_nodes):
    """Supprime les noeuds du combo des noeuds d'arc"""
    widgets = self.hbox.get_children()
    combo1 = widgets[3]
    combo2 = widgets[4]
    combo3 = widgets[5]
    model = combo1.get_model()
    nodes = [i[0] for i in model]
    indices = []
    for node in deleted_nodes:
      if node in nodes:
        indices.append(nodes.index(node))
    for pos in indices:
      combo1.remove(pos)
      combo2.remove(pos)
      combo3.remove(pos)

  def add_node_combo(self, ed, node, force=False):
    """Ajoute un noeud aux combo d'un arc"""
    if not force:
      if node.arc is False: # noeud d'arc mais pas encore défini
        return
      elif not node.arc is None:
        barres = ed.barres
        b_pos = barres.index(self) # tester ou mettre self.pos???
        barres = barres[:b_pos]
        barres = [b.name for b in barres]
        if not node.arc in barres: # l'arc n'est pas encore défini
          return
    node_name = node.name
    combo = self.hbox.get_children()[3]
    combo.append_text(node_name)
    combo = self.hbox.get_children()[4]
    combo.append_text(node_name)
    combo = self.hbox.get_children()[5]
    combo.append_text(node_name)

  def rename_node_combo(self, de, Node, n):
    """Renomme un noeud dans la liste des noeuds des combo d'un arc"""
    try:
      arc = Node.arc
    except AttributeError:
      arc = None
    if not arc is None and self.name == arc:
      return
    nodes = de.nodes
    pos = -1
    for i in range(n):
      try:
        arc = nodes[i].arc
        if arc == self.name:
          n -= 1
          continue
      except AttributeError:
        pass
    new = Node.name
    widgets = self.hbox.get_children()
    combo = widgets[3]
    self.N0 = function.change_elem_combo2(combo, n, new)
    combo = widgets[4]
    self.N1 = function.change_elem_combo2(combo, n, new)
    combo = widgets[5]
    self.c = function.change_elem_combo2(combo, n, new)

class Parabola(AbstractBar):
  """Classe pour une barre de type parabole"""

  def __init__(self, args, data_editor):
    self.id = AbstractBar.class_counter
    AbstractBar.class_counter += 1
    nodes = data_editor.nodes
    for nom, val in args.items():
      setattr(self, nom, val)
    try:
      self.f = float(self.f)
    except ValueError:
      self.f = 0
    self.set_content(data_editor)
    self.set_length(None)
    self.set_empty_nodes(data_editor)

  def set_length(self, nodes):
    """Attribut la longueur de l'élément d'une parabole"""
    if self.c is None or self.c == 0:
      self.l = None
      #print("erreur dans  set_length")
      return
    f = abs(self.f)
    if f == 0:
      self.l = None
      return
    k = (self.c**2+16*f)**0.5
    self.l = k/2+self.c**2/8/f*math.log((4*f+k)/self.c)

  def set_content(self, data_editor):
    #print("set_content parabole")
    nodes = data_editor.nodes
    node_names = [val.name for val in nodes]
    try:
      N0 = nodes[node_names.index(self.N0)]
      N1 = nodes[node_names.index(self.N1)]
    except ValueError:
      self.c = None
      self.a = None
      return
    try:
      self.c = function.get_vector_size((N0.x, N0.y), (N1.x, N1.y))
      self.a = function.get_vector_angle((N0.x, N0.y), (N1.x, N1.y))
    except TypeError:
      self.c = None
      self.a = None


  def set_node(self, data_editor, node_name, n):
    """Modifie les noeuds de parabole"""
    #print "set_node::parabole"
    if n == 0:
      self.N0 = node_name
      self.set_length(data_editor.nodes)
    elif n == 1:
      self.N1 = node_name
      self.set_length(data_editor.nodes)
    else:
      print("debug:: unexpected in set_node")


  def get_coors(self, data_editor, d):
    """Retourne les coordonnées du point appartenant à une parabole"""
    #print ("get_parabola_coors", self.N0, self.N1)
    factor_L = data_editor.unit_conv['L']
    nodes = data_editor.nodes
    try:
      N0_name, N1_name = self.N0, self.N1
    except AttributeError:
      return None
    node_names = data_editor.get_all_nodes()
    try:
      N0_inst = nodes[node_names.index(N0_name)]
    except ValueError:
      return None
    try:
      x0, y0 = N0_inst.x, N0_inst.y
    except AttributeError:
      return None
    if x0 is None:
      return None
    a, corde, f = self.a, self.c, self.f
    #print(a, corde, f, d)
    if d is None or corde is None:
      return None
    u = d*corde
    if corde == 0.:
      return None
    v = 4*f*u*(1-u/corde)/corde
    if not a == 0:
       u, v = Rotation(-a, u, v)
    return x0+u, y0+v


  def set_xml(self, parent):
    """Crée les attributs nécessaires à la structure xml pour une parabole"""
    node = ET.SubElement(parent, "parabola", {"id": self.name})
    node.set("start", self.N0)
    node.set("end", self.N1)
    node.set("f", str(self.f))
    node.set("r0", str(self.R0))
    node.set("r1", str(self.R1))
    return node

  def add_hbox(self, Main):
    """Retourne une nouvelle ligne (hbox) dans l'onglet des barres pour une barre de type parabole"""
    barres = Main.data_editor.barres
    nodes = self.get_nodes(barres, Main.data_editor.nodes)
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    name = self.name
    f = self.f
    N0, N1 = self.N0, self.N1
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=6)
    image = Gtk.Image()
    file1 = self.get_img_file()
    image.set_from_file("glade/%s" % file1)
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_tooltip_text('Nom')
    entry.set_text(name)
    entry.connect("changed", self.update_bar_name, Main)
    hbox.pack_start(entry, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, N0)
    combobox.connect('changed', self._update_combo, Main, 0)
    combobox.set_tooltip_text('Origine')
    hbox.pack_start(combobox, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_tooltip_text('Fin')
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, N1)
    combobox.connect('changed', self._update_combo, Main, 1)
    hbox.pack_start(combobox, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(str(f))
    entry.connect("changed", self._update_f, Main)
    hbox.pack_start(entry, False, False, 0)
    up_b = Gtk.Button.new_from_icon_name('go-up', Gtk.IconSize.MENU)
    up_b.set_relief(Gtk.ReliefStyle.NONE)
    up_b.connect('clicked', self.on_move_up, self, Main)
    hbox.pack_start(up_b, False, False, 0)
    down_b = Gtk.Button.new_from_icon_name('go-down', Gtk.IconSize.MENU)
    down_b.set_relief(Gtk.ReliefStyle.NONE)
    down_b.connect('clicked', self.on_move_down, self, Main)
    hbox.pack_start(down_b, False, False, 0)

    self.hbox = hbox
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    self.update_tooltip_L(unit_L)
    return eventbox

  def get_img_file(self):
    """Retourne le nom du fichier en fonction des relaxations"""
    if self.R0 == 0:
      if self.R1 == 0:
        return "parabola00.png"
      return "parabola01.png"
    if self.R1 == 0:
      return "parabola10.png"
    return "parabola11.png"

  def update_combos(self, Main):
    """Remplit les combo des noeuds pour une parabole"""
    nodes = self.get_nodes( Main.data_editor.barres, Main.data_editor.nodes)
    widgets = self.hbox.get_children()
    combobox = widgets[3]
    function.fill_elem_combo(combobox, nodes, self.N0)
    combobox = widgets[4]
    function.fill_elem_combo(combobox, nodes, self.N1)

  def get_is_arc(self):
    """Retourne vrai pour une parabole"""
    return True

  def update_bar_name(self, widget, Main):
    """Modification du nom d'une parabole"""
    new_name = widget.get_text()
    old_name = self.name
    self.name = new_name
    Main.update_bar_names(self, old_name, new_name)
    Main.update_combo_arc(old_name, new_name)
    Main.set_is_changed()

  def _update_f(self, widget, Main):
    """Gestionnaire des évènements liés à une modification de la flèche d'une parabole"""
    f = widget.get_text()
    try:
      f = float(f.replace(',', '.'))
    except ValueError:
      f = 0
    self.f = f
    Main.update_bars_combo(self.name)
    self.set_content(Main.data_editor)
    Main.set_is_changed(True)

  def rename_node_combo(self, de, Node, n):
    """Renomme un noeud dans la liste des noeuds des combo d'une parabole"""
    try:
      arc = Node.arc
    except AttributeError:
      arc = None
    if not arc is None and self.name == arc:
      return
    nodes = de.nodes
    new = Node.name
    widgets = self.hbox.get_children()
    combo = widgets[3]
    self.N0 = function.change_elem_combo2(combo, n, new)
    combo = widgets[4]
    self.N1 = function.change_elem_combo2(combo, n, new)

  def update_numeric_L(self, factor):
    self.f *= factor
    widget = self.hbox.get_children()[5]
    widget.set_text(str(self.f))

  def add_node_combo(self, ed, node, force=False):
    """Ajoute un noeud aux combo d'une parabole"""
    if not force:
      if node.arc is False: # noeud d'arc mais pas encore défini
        return
      elif not node.arc is None:
        barres = ed.barres
        b_pos = barres.index(self) # tester ou mettre self.pos???
        barres = barres[:b_pos]
        barres = [b.name for b in barres]
        if not node.arc in barres: # l'arc n'est pas encore défini
          return
    node_name = node.name
    combo = self.hbox.get_children()[3]
    combo.append_text(node_name)
    combo = self.hbox.get_children()[4]
    combo.append_text(node_name)

  def update_tooltip_L(self, unit_L):
    """Actualise les tooltips des longueurs suite à un changement d'unité pour une parabole"""
    entry = self.hbox.get_children()[7]
    entry.set_tooltip_text('Flèche en %s' % unit_L)

class Barre(AbstractBar):
  """Classe pour une barre de type segment"""

  def __init__(self, content, nodes):
    self.id = AbstractBar.class_counter
    AbstractBar.class_counter += 1
    self.name = content['name']
    self.boxes = {}
    self.N0 = content['start']
    self.N1 = content['end']
    self.R0 = content['r0']
    self.R1 = content['r1']
    if "k0" in content:
      self.k0 = content["k0"]
    if "k1" in content:
      self.k1 = content["k1"]
    self.set_length(nodes)
    if "mode" in content:
      self.mode = content['mode']
    else:
      self.mode = 0


  def set_node(self, data_editor, node_name, n):
    """Modifie un noeud dans une ligne de barre """
    if n == 0:
      self.N0 = node_name
    elif n == 1:
      self.N1 = node_name
    else:
      print("debug:: unexpected in set_node")

  def set_xml(self, parent):
    """Crée les attributs nécessaires à la structure xml pour une barre"""
    #node = XML.createElement("barre")
    node = ET.SubElement(parent, "barre", {"id": self.name})
    node.set("start", self.N0)
    node.set("end", self.N1)
    node.set("r0", str(self.R0))
    node.set("r1", str(self.R1))
    if not self.mode == 0:
      node.set("mode", str(self.mode))
    try:
      node.set("k0", self.k0)
    except AttributeError:
      pass
    try:
      node.set("k1", self.k1)
    except AttributeError:
      pass
    return node

  def set_length(self, nodes):
    """Attribut la longueur de l'élément"""
    node_names = [val.name for val in nodes]
    try:
      N0 = nodes[node_names.index(self.N0)]
      N1 = nodes[node_names.index(self.N1)]
    except ValueError:
      self.l = None
      return
    try:
      self.l = function.get_vector_size((N0.x, N0.y), (N1.x, N1.y))
    except TypeError:
      self.l = None


  def add_hbox(self, Main):
    """Retourne une nouvelle ligne (hbox) dans l'onglet des barres pour une barre de type segment"""

    units = Main.data_editor.get_units()
    unit = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    barres = Main.data_editor.barres
    nodes = self.get_nodes(barres, Main.data_editor.nodes)
    N1, N2 = "", ""
    barre_name = self.name
    N1 = self.N0
    N2 = self.N1
    eventbox = Gtk.EventBox()
    self.hbox = hbox = Gtk.HBox(homogeneous=False, spacing=6)
    image = Gtk.Image()
    file1 = self.get_img_file()
    image.set_from_file("glade/%s" % file1)
    hbox.pack_start(image, False, False, 0)

    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    entry.set_tooltip_text('Nom')
    entry.set_text(barre_name)
    entry.set_width_chars(10)
    entry.connect("changed", self.update_bar_name, Main)
    hbox.pack_start(entry, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, N1)
    combobox.connect('changed', self._update_combo, Main, 0)
    combobox.set_tooltip_text('Origine')
    hbox.pack_start(combobox, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_tooltip_text('Fin')
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, N2)
    combobox.connect('changed', self._update_combo, Main, 1)
    hbox.pack_start(combobox, False, False, 0)
    up_b = Gtk.Button.new_from_icon_name('go-up', Gtk.IconSize.MENU)
    up_b.set_relief(Gtk.ReliefStyle.NONE)
    up_b.connect('clicked', self.on_move_up, self, Main)
    hbox.pack_start(up_b, False, False, 0)
    down_b = Gtk.Button.new_from_icon_name('go-down', Gtk.IconSize.MENU)
    down_b.set_relief(Gtk.ReliefStyle.NONE)
    down_b.connect('clicked', self.on_move_down, self, Main)
    hbox.pack_start(down_b, False, False, 0)

    try:
      k0 = self.k0
    except AttributeError:
      k0 = False
    if not k0 is False:
      k_box = self._get_k_box(Main, "k0")
      hbox.pack_start(k_box, False, False, 0)
    try:
      k1 = self.k1
    except AttributeError:
      k1 = False
    if not k1 is False:
      k_box = self._get_k_box(Main, "k1")
      hbox.pack_start(k_box, False, False, 0)
    self.update_tooltip_F(unit)

    eventbox.add(hbox)
    eventbox.connect("event", self.onCMenu, Main)
    eventbox.show_all()
    return eventbox

  def _get_k_box(self, Main, name):
    """Ajoute la zone de saisie pour les raideurs élastiques"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="%s=" % name)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_placeholder_text('Option')
    if name == "k0":
      entry.set_name("k0")
      entry.set_text(self.k0)
    elif name == "k1":
      entry.set_name("k1")
      entry.set_text(self.k1)
    entry.connect('changed', self.update_k, Main)
    hbox.pack_start(entry, False, False, 0)
    self.boxes[name] = hbox
    return hbox

  def update_k(self, widget, Main):
    """Met à jour la pivot élastique"""
    new = widget.get_text()
    name = widget.get_name()
    if name == "k0":
      old = self.k0
      if new == old:
        return None
      self.k0 = new.replace(',', '.')
    elif name == "k1":
      old = self.k1
      if new == old:
        return None
      self.k1 = new.replace(',', '.')
    Main.set_is_changed()

  def update_numeric_F(self, factor):
    """Actualise les valeurs numériques pour les pivots élastiques"""
    if "k0" in self.boxes:
      entry = self.boxes["k0"].get_children()[1]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass
    if "k1" in self.boxes:
      entry = self.boxes["k1"].get_children()[1]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass


  def update_tooltip_F(self, unit):
    """Actualise les tooltips pour les liaisons élastiques"""
    if "k0" in self.boxes:
      string = "Raideur élastique en rotation de l'origine\n(%s / rad)" % unit
      self.boxes['k0'].get_children()[1].set_tooltip_markup(string)
    if "k1" in self.boxes:
      string = "Raideur élastique en rotation de l'extrémité\n(%s / rad)" % unit
      self.boxes['k1'].get_children()[1].set_tooltip_markup(string)

  def update_k_widget(self, widget, Main):
    """Ajoute ou supprime la boite pour la raideur k pour une action depuis le CM"""
    units = Main.data_editor.get_units()
    unit = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    if widget.get_name() == "k0":
      if widget.get_active():
        self.k0 = "0"
        k_box = self._get_k_box(Main, "k0")
        k_box.show_all()
        self.hbox.pack_start(k_box, False, False, 0)
        self.update_tooltip_F(unit)
        if "k1" in self.boxes:
          self.hbox.reorder_child(k_box, 7)
      else:
        self.hbox.remove(self.boxes['k0'])
        del(self.k0)
    elif widget.get_name() == "k1":
      if widget.get_active():
        self.k1 = "0"
        k_box = self._get_k_box(Main, "k1")
        k_box.show_all()
        self.hbox.pack_start(k_box, False, False, 0)
        self.update_tooltip_F(unit)
      else:
        self.hbox.remove(self.boxes['k1'])
        del(self.k1)
    Main.set_is_changed(True)

  def get_img_file(self):
    """Retourne le nom du fichier en fonction des relaxations"""
    if self.R0 == 0:
      if self.R1 == 0:
        return "segment00.png"
      return "segment01.png"
    if self.R1 == 0:
      return "segment10.png"
    return "segment11.png"


  def update_combos(self, Main):
    """Remplit les combo des noeuds pour un segment"""
    nodes = self.get_nodes( Main.data_editor.barres, Main.data_editor.nodes)
    widgets = self.hbox.get_children()
    combobox = widgets[3]
    function.fill_elem_combo(combobox, nodes, self.N0)
    combobox = widgets[4]
    function.fill_elem_combo(combobox, nodes, self.N1)

  def update_bar_name(self, widget, Main):
    """Modification du nom d'une barre"""
    new_name = widget.get_text()
    old_name = self.name
    self.name = new_name
    Main.update_bar_names(self, old_name, new_name)
    Main.set_is_changed(True)


  def get_is_arc(self):
    """Retourne faux pour un segment"""
    return False


  def remove_nodes_combo(self, deleted_nodes):
    """Supprime les noeuds du combo des noeuds d'un segment"""
    widgets = self.hbox.get_children()
    combo1 = widgets[3]
    combo2 = widgets[4]
    model = combo1.get_model()
    nodes = [i[0] for i in model]
    indices = []
    for node in deleted_nodes:
      if node in nodes:
        indices.append(nodes.index(node))
    for pos in reversed(indices):
      combo1.remove(pos)
      combo2.remove(pos)

  def rename_node_combo(self, de, Node, n):
    """Renomme un noeud dans la liste des noeuds des combo d'une barre"""
    new = Node.name
    widgets = self.hbox.get_children()
    combo = widgets[3]
    self.N0 = function.change_elem_combo2(combo, n, new)
    combo = widgets[4]
    self.N1 = function.change_elem_combo2(combo, n, new)

  def add_node_combo(self, ed, node, force=False):
    """Ajoute un noeud aux combo d'une barre"""
    if not force:
      if node.arc is False: # noeud d'arc mais pas encore défini
        return
      elif not node.arc is None:
        barres = ed.barres
        b_pos = barres.index(self) # tester ou mettre self.pos???
        barres = barres[:b_pos]
        barres = [b.name for b in barres]
        if not node.arc in barres: # l'arc n'est pas encore défini
          return
    node_name = node.name
    combo = self.hbox.get_children()[3]
    combo.append_text(node_name)
    combo = self.hbox.get_children()[4]
    combo.append_text(node_name)

  def set_one_way(self, widget, Main, mode):
    """Configure le mode compression seul ou traction seule"""
    tag = widget.get_active()
    if mode == "N+":
      if tag:
        self.mode = 1
      else:
        self.mode = 0
    elif mode == "N-":
      if tag:
        self.mode = -1
      else:
        self.mode = 0
    Main.set_is_changed()

class MBarre(AbstractBar):
  """Classe pour une barre de type barre à noeud multiple"""

  def __init__(self, args, data_editor):
    self.id = AbstractBar.class_counter
    AbstractBar.class_counter += 1
    for nom, val in args.items():
      setattr(self, nom, val)
    self.set_length(data_editor.nodes)
    self.set_empty_nodes(data_editor)

  def set_xml(self, parent):
    """Crée les attributs nécessaires à la structure xml pour une mbarre"""
    node = ET.SubElement(parent, "mbarre", {"id": self.name})
    node.set("id", self.name)
    node.set("start", self.N0)
    node.set("end", self.N1)
    node.set("r0", str(self.R0))
    node.set("r1", str(self.R1))
    return node

  def set_node(self, data_editor, node_name, n):
    """Modifie un noeud dans une ligne de barre multiple"""
    #print "set_node::mbarre"
    if n == 0:
      self.N0 = node_name
      self.set_length(data_editor.nodes)
    elif n == 1:
      self.N1 = node_name
      self.set_length(data_editor.nodes)
    else:
      print("debug:: unexpected in set_node")

  def set_length(self, nodes):
    """Attribut la longueur de l'élément de type mbarre"""
    node_names = [val.name for val in nodes]
    try:
      N0 = nodes[node_names.index(self.N0)]
      N1 = nodes[node_names.index(self.N1)]
    except ValueError:
      self.l = None
      return
    try:
      self.l = ((N1.x-N0.x)**2 + (N1.y-N0.y)**2)**0.5
    except (TypeError, AttributeError):
      self.l = None

  def get_coors(self, data_editor, d):
    """Retourne les coordonnées du point appartenant à une barre multiple"""
    factor_L = data_editor.unit_conv['L']
    nodes = data_editor.nodes
    try:
      N0_name, N1_name = self.N0, self.N1
    except AttributeError:
      return None
    node_names = data_editor.get_all_nodes()
    try:
      N0_inst = nodes[node_names.index(N0_name)]
      N1_inst = nodes[node_names.index(N1_name)]
    except ValueError:
      return None
    try:
      x0, y0 = N0_inst.x, N0_inst.y
      x1, y1 = N1_inst.x, N1_inst.y
    except AttributeError:
      return None
    try:
      x0*y0*x1*y1 # test valeur None ???
    except TypeError:
      return None
    if d is None:
      return None
    x, y = x0*(1-d)+x1*d, y0*(1-d)+y1*d
    return x, y


  def add_hbox(self, Main):
    """Retourne une nouvelle ligne (hbox) dans l'onglet des barres pour une barre multiple"""
    name = self.name
    barres = Main.data_editor.barres
    nodes = self.get_nodes( Main.data_editor.barres, Main.data_editor.nodes)
    N0, N1 = self.N0, self.N1
    hbox = Gtk.HBox(homogeneous=False, spacing=6)
    eventbox = Gtk.EventBox()
    image = Gtk.Image()
    file1 = self.get_img_file()
    image.set_from_file("glade/%s" % file1)
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_tooltip_text('Nom')
    entry.set_text(name)
    entry.connect("changed", self.update_bar_name, Main)
    hbox.pack_start(entry, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, N0)
    combobox.connect('changed', self._update_combo, Main, 0)
    combobox.set_tooltip_text('Origine')
    hbox.pack_start(combobox, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_tooltip_text('Fin')
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, N1)
    combobox.connect('changed', self._update_combo, Main, 1)
    hbox.pack_start(combobox, False, False, 0)
    up_b = Gtk.Button.new_from_icon_name('go-up', Gtk.IconSize.MENU)
    up_b.set_relief(Gtk.ReliefStyle.NONE)
    up_b.connect('clicked', self.on_move_up, self, Main)
    hbox.pack_start(up_b, False, False, 0)
    down_b = Gtk.Button.new_from_icon_name('go-down', Gtk.IconSize.MENU)
    down_b.set_relief(Gtk.ReliefStyle.NONE)
    down_b.connect('clicked', self.on_move_down, self, Main)
    hbox.pack_start(down_b, False, False, 0)
    self.hbox = hbox
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def get_img_file(self):
    """Retourne le nom du fichier en fonction des relaxations"""
    if self.R0 == 0:
      if self.R1 == 0:
        return "msegment00.png"
      return "msegment01.png"
    if self.R1 == 0:
      return "msegment10.png"
    return "msegment11.png"

  def update_combos(self, Main):
    """Remplit les combo des noeuds pour une barre multiple"""
    nodes = self.get_nodes( Main.data_editor.barres, Main.data_editor.nodes)
    widgets = self.hbox.get_children()
    combobox = widgets[3]
    function.fill_elem_combo(combobox, nodes, self.N0)
    combobox = widgets[4]
    function.fill_elem_combo(combobox, nodes, self.N1)

  def get_is_arc(self):
    """Retourne faux pour une mbarre"""
    return False

  def update_bar_name(self, widget, Main):
    """Met à jour l'instance en cas de changement du nom d'une Barre multiple"""
    new_name = widget.get_text()
    old_name = self.name
    self.name = new_name
    Main.update_bar_names(self, old_name, new_name)
    Main.update_combo_arc(old_name, new_name)
    Main.set_is_changed(True)

  def rename_node_combo(self, de, Node, n):
    """Renomme un noeud dans la liste des noeuds des combo d'une barre multiple"""
    new = Node.name
    widgets = self.hbox.get_children()
    combo = widgets[3]
    self.N0 = function.change_elem_combo2(combo, n, new)
    combo = widgets[4]
    self.N1 = function.change_elem_combo2(combo, n, new)

  def add_node_combo(self, ed, node, force=False):
    """Ajoute un noeud aux combo d'une barre multiple"""
    if not force:
      if node.arc is False: # noeud d'arc mais pas encore défini
        return
      elif not node.arc is None:
        barres = ed.barres
        b_pos = barres.index(self) # tester ou mettre self.pos???
        barres = barres[:b_pos]
        barres = [b.name for b in barres]
        if not node.arc in barres: # l'arc n'est pas encore défini
          return
    node_name = node.name
    combo = self.hbox.get_children()[3]
    combo.append_text(node_name)
    combo = self.hbox.get_children()[4]
    combo.append_text(node_name)

class Liaison(object):
  """Classe pour une liaiosn"""
  class_counter = 0

  def __init__(self, name, content):
    self.id = Liaison.class_counter
    Liaison.class_counter += 1
    self.name = name
    self.d = content

  def get_nodes(self, nodes):
    """Retourne la liste des noms des noeuds"""
    mynodes = []
    for node in nodes:
      mynodes.append(node.name)
    return mynodes

  def add_hbox(self, Main):
    """Retourne une nouvelle ligne (hbox) dans l'onglet des liaisons"""
    name = self.name
    content = self.d
    try:
      value = int(content[0])
    except ValueError:
      value = 0
    if value == 2:
      try:
        angle = content[1]
      except IndexError:
        angle = "0"
    elif value == 3:
      try:
        kx, ky, kz = content[1], content[2], content[3]
      except IndexError:
        kx, ky, kz = "0", "0", "0"
    nodes = self.get_nodes(Main.data_editor.nodes)
    hbox = Gtk.HBox(homogeneous=False, spacing=6)
    eventbox = Gtk.EventBox()
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(90, 30)
    function.fill_elem_combo(combobox, nodes, name)
    combobox.connect('changed', self._changed_node_liaison, Main)
    combobox.set_tooltip_text('Noeud')
    hbox.pack_start(combobox, False, False, 0)

    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(140, 30)
    self._update_combo_liaison(combobox, value)
    combobox.connect('changed', self._changed_liaison, Main)
    combobox.show()
    hbox.pack_start(combobox, False, False, 0)
    if value == 2:
      self._insert_incline(hbox, Main, angle)
    elif value == 3:
      self._insert_rigidity(hbox, Main, kx, ky, kz)
    self.hbox = hbox
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def set_content(self, ed):
      """Actualise les attributs de l'objet liaison"""
      hbox = self.hbox
      node = ed.get_node(self.name)
      if node is None : return
      combo = hbox.get_children()[2]
      l = combo.get_active()
      if l == 2:
        a = hbox.get_children()[4].get_text()
        if a == '': # a tester
          li = ["2"]
        else:
          li = ["2", a.replace(",",".")]
      elif l == 3:
        kx = hbox.get_children()[4].get_text()
        ky = hbox.get_children()[6].get_text()
        kz = hbox.get_children()[8].get_text()
        li = ["3", kx, ky, kz]
      else:
        li = [str(l)]
      node.liaison = li

 
  def _update_combo_liaison(self, combobox, number):
    """Insère les éléments dans le combo des liaisons et rend actif l'élément d'index number"""
    liaisons = ["Encastrement", "Pivot", "Appui simple", "Appui élastique"]
    for elem in liaisons:
      combobox.append_text(elem)
    if not number == "":
      combobox.set_active(number)

  def _insert_incline(self, hbox, Main, angle=""):
    """Ajoute la zone de saisie des appuis simples inclinés"""
    label = Gtk.Label(label="Angle (deg) = ")
    label.set_size_request(100, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_placeholder_text('Option')
    if angle:
      entry.set_text(angle)
    entry.connect("changed", self._changed_angle, Main)
    entry.show()
    hbox.pack_start(entry, False, False, 0)

  def _insert_rigidity(self, hbox, Main, kx="", ky="", kz=""):
    """Ajoute la zone de saisie des rigidités"""
    label = Gtk.Label(label="k<sub>x</sub> = ")
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(kx)
    entry.connect("changed", self._changed_k, Main, 0)
    entry.show()
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label(label="k<sub>y</sub> = ")
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(ky)
    entry.connect("changed", self._changed_k, Main, 1)
    entry.show()
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label(label="k<sub>z</sub> = ")
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(kz)
    entry.connect("changed", self._changed_k, Main, 2)
    entry.show()
    hbox.pack_start(entry, False, False, 0)
    units = Main.data_editor.get_units()
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    label = Gtk.Label(label="en %s / %s" % (unit_F, unit_L))
    label.set_size_request(80, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)

  def _changed_node_liaison(self, widget, Main):
    """Evènement lié à un changement du noeud d'une liaison"""
    self.name = widget.get_active_text()
    self.set_content(Main.data_editor)
    Main.data_editor.set_liaisons()
    Main.set_is_changed(True)

  def _changed_liaison(self, widget, Main):
    """Evènement lié à un changement du combo des liaisons"""
    #print "_changed_liaison"
    hbox = widget.get_parent()
    liaison = widget.get_active()
    self._remove_option(hbox)
    if liaison == 2:
      self._insert_incline(hbox, Main)
    elif liaison == 3:
      self._insert_rigidity(hbox, Main)

    self.set_content(Main.data_editor)
    Main.set_is_changed(True)


  def _remove_option(self, hbox):
    """Supprime dans la zone de saisie les champs complémentaires """
    for i, elem in enumerate(hbox):
      if i > 2: hbox.remove(elem)

  def _changed_angle(self, widget, Main):
    """Evènement lié à un changement d'angle dans un appui de type appui simple"""
    self.set_content(Main.data_editor)
    Main.set_is_changed(True)

  def _changed_k(self, widget, Main, i):
    """Evènement lié à un changement de la raideur dans un appui de type appui élastique"""
    self.set_content(Main.data_editor)
    Main.set_is_changed(True)

  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'une section"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        pass

class Section(object):
  """Classe pour une section droite"""
  class_counter = 0

  def __init__(self, di):
    self.id = Section.class_counter
    Section.class_counter += 1
    self.name = di['name']
    if 's' in di:
      s = di['s']
      if len(s) >= 3 and s[-2:] == ".0":
        s = s[:-2]
      self.s = s
    if 'i' in di:
      i = di['i']
      if len(i) >= 3 and i[-2:] == ".0":
        i = i[:-2]
      self.i = i
    if 'profil' in di:
      self.profil = di['profil'] # profil name
    elif 'file' in di:
      self.file = di['file'] # file name
    if 'h' in di:
      h = di['h']
      if len(h) >= 3 and h[-2:] == ".0":
        h = h[:-2]
      self.h = h
    if 'v' in di:
      v = di['v']
      if len(v) >= 3 and v[-2:] == ".0":
        v = v[:-2]
      self.v = v

  def add_hbox(self, Main):
    """Crée la hbox d'une section"""
    self.boxes = {}
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=5)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)

    label = Gtk.Label(label="Barre(s):")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(self.name)
    entry.set_tooltip_text('Formats possibles:\n\tB1\n\t*\n\tB1,B2,B3')
    entry.set_placeholder_text('Obligatoire')
    entry.connect("changed", self.update_name, Main)
    hbox.pack_start(entry, False, False, 0)
    # Section
    in_hbox = self._get_s_hbox(Main)
    hbox.pack_start(in_hbox, False, False, 0)
    self.boxes['s'] = in_hbox
    self.update_tooltip_s(Main)
    # Moment quadratique
    i = self.i
    in_hbox = self._get_i_hbox(Main)
    hbox.pack_start(in_hbox, False, False, 0)
    self.boxes['i'] = in_hbox
    self.update_tooltip_i(Main)
    # hauteur
    try:
      h = self.h
      in_hbox = self._get_h_hbox(Main)
      hbox.pack_start(in_hbox, False, False, 0)
      self.boxes['h'] = in_hbox
      self.update_tooltip_h(Main)
    except AttributeError:
      pass
    # distance v
    try:
      v = self.v
      in_hbox = self._get_v_hbox(Main)
      hbox.pack_start(in_hbox, False, False, 0)
      self.boxes['v'] = in_hbox
      self.update_tooltip_v(Main)
    except AttributeError:
      pass
    # Nom
    try:
      p = self.profil
      in_hbox = self._get_profil_hbox(Main)
      hbox.pack_start(in_hbox, False, False, 0)
      self.boxes['p'] = in_hbox
    except AttributeError:
      pass
    try:
      p = os.path.basename(self.file)
      label = Gtk.Label(label="Fichier: %s" % p)
      hbox.pack_start(label, False, False, 0)
      #self.boxes['p'] = in_hbox
    except AttributeError:
      pass

    self.hbox = hbox
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def update_tooltip_s(self, Main):
    """Actualise le tooltip de la section droite"""
    units = Main.data_editor.get_units()
    unit = function.return_key(units['S'], Main.data_editor.unit_conv['S'])
    string = 'Section droite en %s' % unit
    self.boxes['s'].get_children()[1].set_tooltip_markup(string)

  def update_tooltip_i(self, Main):
    """Actualise le tooltip du moment quadratique"""
    units = Main.data_editor.get_units()
    unit = function.return_key(units['I'], Main.data_editor.unit_conv['I'])
    string = 'Moment quadratique en %s' % unit
    self.boxes['i'].get_children()[1].set_tooltip_markup(string)

  def update_tooltip_h(self, Main):
    """Actualise le tooltip de la hauteur h"""
    units = Main.data_editor.get_units()
    unit = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    string = 'Hauteur en %s' % unit
    self.boxes['h'].get_children()[1].set_tooltip_markup(string)

  def update_tooltip_v(self, Main):
    """Actualise le tooltip de la hauteur v"""
    units = Main.data_editor.get_units()
    unit = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    string = 'Distance entre la fibre sup. et le cdg en %s' % unit
    self.boxes['v'].get_children()[1].set_tooltip_markup(string)

  def _get_profil_hbox(self, Main):
    """Retourne la hbox contenant le nom"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="Nom:")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_tooltip_text("Nom du profil")
    entry.set_placeholder_text('Option')
    if self.profil:
      entry.set_text(self.profil)
    entry.connect("changed", self.update_profil, Main)
    hbox.pack_start(entry, False, False, 0)
    return hbox

  def _get_s_hbox(self, Main):
    """Retourne la hbox relative à la section droite"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="S=")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_placeholder_text('Obligatoire')
    if self.s:
      entry.set_text(self.s)
    entry.connect('changed', self.update_s, Main)
    hbox.pack_start(entry, False, False, 0)
    return hbox

  def _get_i_hbox(self, Main):
    """Retourne la hbox relative au moment quadratique"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="I=")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_placeholder_text('Obligatoire')
    if self.i:
      entry.set_text(self.i)
    entry.connect('changed', self.update_i, Main)
    hbox.pack_start(entry, False, False, 0)
    return hbox

  def _get_h_hbox(self, Main):
    """Retourne la hbox relative à la hauteur"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="H=")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_placeholder_text('Option')
    if self.h:
      entry.set_text(self.h)
    entry.connect('changed', self.update_h, Main)
    hbox.pack_start(entry, False, False, 0)
    return hbox

  def _get_v_hbox(self, Main):
    """Retourne la hbox relative au moment quadratique"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="v=")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_placeholder_text('Option')
    if self.v:
      entry.set_text(self.v)
    entry.connect('changed', self.update_v, Main)
    hbox.pack_start(entry, False, False, 0)
    return hbox


  def on_set_section(self, widget, Main):
    #print(dir(Main.section_manager.win))
    if not hasattr(Main, 'section_manager'):
      return
    data = Main.section_manager.send_data()
    if data is None:
      return
    self.set_data(data, Main, "m")


  def on_set_profil(self, widget, Main):
    """Affecte les valeurs données par la librairie des profilés"""
    if not hasattr(Main, 'profil_manager') \
		or Main.profil_manager.window.get_window() is None:
      return
    data = Main.profil_manager.send_data()
    if data is None:
      return

    data = [i.replace(',', '.') for i in data]
    self.set_data(data, Main, "cm")

  def set_data(self, data, Main, unit):
    if unit == "cm":
      u = 100
    elif unit == "m":
      u = 1
    elif unit == "mm":
      u = 1000
    else:
      u = 1

    hbox = self.hbox
    boxes = self.boxes
    # S
    entry = boxes["s"].get_children()[1]
    try:
      val = str(float(data[1])/u**2/Main.data_editor.unit_conv['S'])
    except:
      print("Ed::set_data unexpected error")
      val = ""
    entry.set_text(val)
    self.s = val
    # I
    entry = boxes["i"].get_children()[1]
    try:
      val = str(float(data[2])/u**4/Main.data_editor.unit_conv['I'])
    except:
      print("Ed::set_data unexpected error")
      val = ""
    entry.set_text(val)
    self.i = val
    # H
    try:
      val = str(float(data[3])/u/Main.data_editor.unit_conv['L'])
    except:
      val = ''
      print("Ed::set_data unexpected error")
    if not 'h' in boxes:
      self.h = val
      in_hbox = self._get_h_hbox(Main)
      in_hbox.show_all()
      boxes['h'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      hbox.reorder_child(in_hbox, 6)
    else:
      entry =  boxes["h"].get_children()[1]
      entry.set_text(val)
    # v
    val = data[4]
    if val == '': # par défaut, section symétrique -> h/2
      try:
        val = str(float(data[3])/2/u/Main.data_editor.unit_conv['L'])
      except:
        val = ''
    else:
      try:
        val = str(float(val)/u/Main.data_editor.unit_conv['L'])
      except:
        val = ''
    if not 'v' in boxes:
      self.v = val
      in_hbox = self._get_v_hbox(Main)
      in_hbox.show_all()
      boxes['v'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      hbox.reorder_child(in_hbox, 7)
    else:
      entry =  boxes["v"].get_children()[1]
      entry.set_text(val)
    # nom du matériau
    if not 'p' in boxes:
      self.profil = data[0]
      in_hbox = self._get_profil_hbox(Main)
      in_hbox.show_all()
      boxes['p'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      hbox.reorder_child(in_hbox, -1)
    else:
      entry =  boxes["p"].get_children()[1]
      entry.set_text(data[0])


  def update_name(self, widget, Main):
    """Met à jour la barre pour la section"""
    new = widget.get_text()
    old = self.name
    if new == old:
      return None
    self.name = new
    Main.set_is_changed()

  def update_s(self, widget, Main):
    """Met à jour S"""
    new = widget.get_text()
    old = self.s
    if new == old:
      return None
    self.s = new.replace(',', '.')
    Main.set_is_changed()

  def update_i(self, widget, Main):
    """Met à jour I"""
    new = widget.get_text()
    old = self.i
    if new == old:
      return None
    self.i = new.replace(',', '.')
    Main.set_is_changed()

  def update_h(self, widget, Main):
    """Met à jour H"""
    new = widget.get_text()
    old = self.h
    if new == old:
      return None
    self.h = new.replace(',', '.')
    Main.set_is_changed()

  def update_v(self, widget, Main):
    """Met à jour v"""
    new = widget.get_text()
    old = self.v
    if new == old:
      return None
    self.v = new.replace(',', '.')
    Main.set_is_changed()


  def update_profil(self, widget, Main):
    """Met à jour le nom du matériau"""
    new = widget.get_text()
    old = self.profil
    if new == old:
      return None
    self.profil = new
    Main.set_is_changed()


  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'une section"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        try:
          self.profil
          tag0 = 1
        except AttributeError:
          tag0 = 0
        try:
          self.h
          tag1 = 1
        except AttributeError:
          tag1 = 0
        try:
          self.v
          tag2 = 1
        except AttributeError:
          tag2 = 0
        menu1 = Gtk.Menu()
        menuitem1 = Gtk.CheckMenuItem(label="Définir le nom", active=tag0)
        menuitem1.connect("activate", self.on_add_name, Main)
        menu1.append(menuitem1)
        menuitem2 = Gtk.CheckMenuItem(label="Définir la hauteur", active=tag1)
        menuitem2.connect("activate", self.on_add_h, Main)
        menu1.append(menuitem2)
        menuitem3 = Gtk.CheckMenuItem(label="Définir la distance v", active=tag2)
        menuitem3.connect("activate", self.on_add_v, Main)
        menu1.append(menuitem3)
        menuitem4 = Gtk.MenuItem(label="Affecter le profilé")
        menuitem4.connect("activate", self.on_set_profil, Main)
        if hasattr(Main, 'profil_manager'):
          menuitem4.set_sensitive(True)
        else:
          menuitem4.set_sensitive(False)
        menu1.append(menuitem4)
        menuitem5 = Gtk.MenuItem(label="Affecter la section")
        menuitem5.connect("activate", self.on_set_section, Main)
        if hasattr(Main, 'section_manager'):
          menuitem5.set_sensitive(True)
        else:
          menuitem5.set_sensitive(False)
        menu1.append(menuitem5)

        if hasattr(self, "file"):
          menuitem6 = Gtk.MenuItem(label="Ouvrir l'éditeur")
          menuitem6.connect("activate", Main.on_open_section_ed, self.file)
          if hasattr(self, "file"):
            menuitem6.set_sensitive(True)
          else:
            menuitem6.set_sensitive(False)
          menu1.append(menuitem6)

        menuitem7 = Gtk.MenuItem(label="Supprimer")
        menuitem7.connect("activate", self.on_delete, (Main, self.id))
        menuitem7.set_sensitive(False)
        menu1.append(menuitem7)
        menu1.show_all()
        menu1.popup_at_pointer(event)
        return True # bloque la propagation du signal
    return False
    Main.set_is_changed()

  def on_add_h(self, widget, Main):
    """Ajoute la boite pour la hauteur"""
    hbox = self.hbox
    if widget.get_active():
      self.h = ""
      in_hbox = self._get_h_hbox(Main)
      in_hbox.show_all()
      self.boxes['h'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      hbox.reorder_child(in_hbox, 6)
      self.update_tooltip_h(Main)
    else:
      hbox.remove(self.boxes['h'])
      del(self.boxes['h'])
      del(self.h)
    Main.set_is_changed()

  def on_add_v(self, widget, Main):
    """Ajoute la boite pour la hauteur v"""
    hbox = self.hbox
    if widget.get_active():
      self.v = ""
      in_hbox = self._get_v_hbox(Main)
      in_hbox.show_all()
      self.boxes['v'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      if 'h' in self.boxes:
        hbox.reorder_child(in_hbox, 7)
      else:
        hbox.reorder_child(in_hbox, 6)
      self.update_tooltip_v(Main)
    else:
      hbox.remove(self.boxes['v'])
      del(self.boxes['v'])
      del(self.v)
    Main.set_is_changed()


  def on_add_name(self, widget, Main):
    """Ajoute la boite pour le nom de la section"""
    hbox = self.hbox
    if widget.get_active():
      self.profil = ""
      in_hbox = self._get_profil_hbox(Main)
      in_hbox.show_all()
      self.boxes['p'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
    else:
      hbox.remove(self.boxes['p'])
      del(self.boxes['p'])
      del(self.profil)
    Main.set_is_changed()

  def on_delete(self, widget, args):
    """Action de suppression d'une ligne de section depuis le CM"""
    Main, b_id = args
    box = Main.data_box['section']
    items = Main.data_editor.sections
    for i, b in enumerate(items):
      if not b.id == b_id:
        continue
      box.remove(b.hbox.get_parent())
      del(items[i])
      Main.data_editor.size_changed = True
      break
    Main.set_is_changed()

class Material(object):
  """Classe pour un matériau"""

  class_counter = 0

  def __init__(self, name):
    self.name = name
    self.id = Material.class_counter
    Material.class_counter += 1

  def add_hbox(self, Main):
    """Crée la hbox d'un matériau"""
    self.boxes = {}
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=5)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    button = Gtk.Button.new_from_icon_name('insert-object', Gtk.IconSize.MENU)
    button.set_relief(Gtk.ReliefStyle.NONE)
    #button.set_focus_on_click(False)
    if hasattr(Main, 'mat_manager'):
      button.set_sensitive(True)
    else:
      button.set_sensitive(False)
    button.set_tooltip_text('Affecter le matériau')
    button.connect('clicked', self.on_set_materiau, Main)
    hbox.pack_start(button, False, False, 0)

    label = Gtk.Label(label="Barre(s):")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(self.name)
    entry.set_tooltip_text('Formats possibles:\n\tB1\n\t*\n\tB1,B2,B3')
    entry.connect("changed", self.update_name, Main)
    hbox.pack_start(entry, False, False, 0)
    # Module d'Young
    in_hbox = self._get_e_hbox(Main)
    hbox.pack_start(in_hbox, False, False, 0)
    self.boxes['e'] = in_hbox
    self.update_tooltip_E(Main)
    # Masse volumique
    try:
      m = self.m
      in_hbox = self._get_mv_hbox(Main)
      hbox.pack_start(in_hbox, False, False, 0)
      self.boxes['m'] = in_hbox
      self.update_tooltip_m(Main)
    except AttributeError:
      pass
    # Coefficient de dilatation
    try:
      a = self.a
      in_hbox = self._get_a_hbox(Main)
      hbox.pack_start(in_hbox, False, False, 0)
      self.boxes['a'] = in_hbox
      self.update_tooltip_a(Main)
    except AttributeError:
      pass
    # Nom du materiau
    try:
      p = self.profil
      in_hbox = self._get_profil_hbox(Main)
      hbox.pack_start(in_hbox, False, False, 0)
      self.boxes['p'] = in_hbox
    except AttributeError:
      pass
    self.hbox = hbox
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def _get_profil_hbox(self, Main):
    """Retourne la hbox contenant le nom du matériau"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="Matériau:")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(self.profil)
    entry.set_tooltip_text("Facultatif")
    entry.connect("changed", self.update_profil, Main)
    hbox.pack_start(entry, False, False, 0)
    return hbox

  def _get_e_hbox(self, Main):
    """Retourne la hbox relative au module E"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="E=")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_placeholder_text('Obligatoire')
    entry.set_text(self.E)
    entry.connect('changed', self.update_young, Main)
    hbox.pack_start(entry, False, False, 0)
    #hbox.set_name("E")
    return hbox

  def _get_mv_hbox(self, Main):
    """Retourne la hbox relative a la masse volumique"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label='\u03C1=')
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(self.m)
    entry.connect('changed', self.update_mv, Main)
    hbox.pack_start(entry, False, False, 0)
    #hbox.set_name("mv")
    return hbox

  def _get_a_hbox(self, Main):
    """Retourne la hbox relative au coefficient de dilatation"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label='\u03B1=')
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(self.a)
    entry.connect('changed', self.update_alpha, Main)
    hbox.pack_start(entry, False, False, 0)
    #hbox.set_name("a")
    return hbox

  def update_tooltip_E(self, Main):
    """Actualise le tooltip du module d'Young"""
    units = Main.data_editor.get_units()
    unit_E = function.return_key(units['E'], Main.data_editor.unit_conv['E'])
    string = 'Module d\'Young en %s' % unit_E
    self.boxes['e'].get_children()[1].set_tooltip_markup(string)

  def update_tooltip_m(self, Main):
    """Actualise le tooltip de la masse volumique"""
    units = Main.data_editor.get_units()
    unit_M = function.return_key(units['M'], Main.data_editor.unit_conv['M'])
    string = 'Masse volumique en %s' % unit_M
    self.boxes['m'].get_children()[1].set_tooltip_markup(string)

  def update_tooltip_a(self, Main):
    """Actualise le tooltip du coefficient de dilatation"""
    string = 'Coefficient de dilatation en K<sup>-1</sup>'
    self.boxes['a'].get_children()[1].set_tooltip_markup(string)

  def on_add_name(self, widget, Main):
    """Ajoute la boite pour le nom du matériau"""
    hbox = self.hbox
    if widget.get_active():
      self.profil = ""
      in_hbox = self._get_profil_hbox(Main)
      in_hbox.show_all()
      self.boxes['p'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
    else:
      hbox.remove(self.boxes['p'])
      del(self.boxes['p'])
      del(self.profil)
    Main.set_is_changed()

  def on_add_mv(self, widget, Main):
    """Ajoute la boite pour la masse volumique"""
    hbox = self.hbox
    if widget.get_active():
      self.m = ""
      in_hbox = self._get_mv_hbox(Main)
      in_hbox.show_all()
      self.boxes['m'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      hbox.reorder_child(in_hbox, 5)
      self.update_tooltip_m(Main)
    else:
      hbox.remove(self.boxes['m'])
      del(self.boxes['m'])
      del(self.m)
    Main.set_is_changed()

  def on_add_alpha(self, widget, Main):
    """Ajoute la boite pour le coefficient de dilatation"""
    hbox = self.hbox
    if widget.get_active():
      self.a = ""
      in_hbox = self._get_a_hbox(Main)
      in_hbox.show_all()
      self.boxes['a'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      if 'm' in self.boxes:
        hbox.reorder_child(in_hbox, 6)
      else:
        hbox.reorder_child(in_hbox, 5)
      self.update_tooltip_a(Main)
    else:
      hbox.remove(self.boxes['a'])
      del(self.boxes['a'])
      del(self.a)
    Main.set_is_changed()


  def update_name(self, widget, Main):
    """Met à jour l'id du matériau"""
    new = widget.get_text()
    old = self.name
    if new == old:
      return None
    self.name = new
    Main.set_is_changed()

  def update_profil(self, widget, Main):
    """Met à jour le nom du matériau"""
    new = widget.get_text()
    old = self.profil
    if new == old:
      return None
    self.profil = new
    Main.set_is_changed()

  def update_young(self, widget, Main):
    """Met à jour le module d'Young du matériau"""
    new = widget.get_text()
    old = self.E
    if new == old:
      return None
    self.E = new.replace(',', '.')
    Main.set_is_changed()

  def update_mv(self, widget, Main):
    """Met à jour la masse volumique"""
    new = widget.get_text()
    old = self.m
    if new == old:
      return None
    self.m = new.replace(',', '.')
    Main.set_is_changed()

  def update_alpha(self, widget, Main):
    """Met à jour le coef de dilatation"""
    new = widget.get_text()
    old = self.a
    if new == old:
      return None
    self.a = new.replace(',', '.')
    Main.set_is_changed()

  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'un matériau"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        try:
          self.profil
          tag0 = 1
        except AttributeError:
          tag0 = 0
        try:
          self.m
          tag1 = 1
        except AttributeError:
          tag1 = 0
        try:
          self.a
          tag2 = 1
        except AttributeError:
          tag2 = 0
        menu1 = Gtk.Menu()
        menuitem1 = Gtk.CheckMenuItem(label="Définir le nom", active=tag0)
        menuitem1.connect("activate", self.on_add_name, Main)
        menu1.append(menuitem1)
        menuitem2 = Gtk.CheckMenuItem(label="Définir la masse volumique", active=tag1)
        menuitem2.connect("activate", self.on_add_mv, Main)
        menu1.append(menuitem2)
        menuitem3 = Gtk.CheckMenuItem(label="Définir le coefficient de dilatation", active=tag2)
        menuitem3.connect("activate", self.on_add_alpha, Main)
        menu1.append(menuitem3)
        menuitem4 = Gtk.MenuItem(label="Affecter le matériau")
        menuitem4.connect("activate", self.on_set_materiau, Main)
        if hasattr(Main, 'mat_manager'):
          menuitem4.set_sensitive(True)
        else:
          menuitem4.set_sensitive(False)
        menu1.append(menuitem4)


        menuitem5 = Gtk.MenuItem(label="Supprimer")
        menuitem5.connect("activate", self.on_delete, (Main, self.id))
        menuitem5.set_sensitive(False)
        menu1.append(menuitem5)
        menu1.show_all()
        menu1.popup_at_pointer(event)
        return True # bloque la propagation du signal
    return False

  def on_delete(self, widget, args):
    """Action de suppression d'une ligne de materiaux depuis le CM"""
    Main, b_id = args
    box = Main.data_box['mater']
    items = Main.data_editor.materials
    for i, b in enumerate(items):
      if not b.id == b_id:
        continue
      box.remove(b.hbox.get_parent())
      del(items[i])
      Main.data_editor.size_changed = True
      break
    Main.set_is_changed()

  def on_set_materiau(self, widget, Main):
    """Affecte les valeurs données par la librairie des matériaux"""
    if not hasattr(Main, 'mat_manager') \
		or Main.mat_manager.window.get_window() is None:
      return
    data = Main.mat_manager.send_data()
    if data is None:
      return
    data = [i.replace(',', '.') for i in data]
    hbox = self.hbox
    boxes = self.boxes
    # E
    entry = boxes["e"].get_children()[1]
    try:
      val = str(float(data[1])*1e9/Main.data_editor.unit_conv['E'])
    except:
      print("Ed::set_profil unexpected error")
      val = ""
    entry.set_text(val)
    self.E = val
    # rho
    try:
      val = str(float(data[2])/Main.data_editor.unit_conv['M'])
    except:
      val = ''
      print("Ed::set_profil unexpected error")
    if not 'm' in boxes:
      self.m = val
      in_hbox = self._get_mv_hbox(Main)
      in_hbox.show_all()
      boxes['m'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      hbox.reorder_child(in_hbox, 5)
    else:
      entry =  boxes["m"].get_children()[1]
      entry.set_text(val)
    # alpha
    try:
      val = data[3]
    except:
      val = ''
      print("Ed::set_profil unexpected error")
    if not 'a' in boxes:
      self.a = val
      in_hbox = self._get_a_hbox(Main)
      in_hbox.show_all()
      boxes['a'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      hbox.reorder_child(in_hbox, 6)
    else:
      entry =  boxes["a"].get_children()[1]
      entry.set_text(val)
    # nom du matériau
    if not 'p' in boxes:
      self.profil = data[0]
      in_hbox = self._get_profil_hbox(Main)
      in_hbox.show_all()
      boxes['p'] = in_hbox
      hbox.pack_start(in_hbox, False, False, 0)
      hbox.reorder_child(in_hbox, -1)
    else:
      entry =  boxes["p"].get_children()[1]
      entry.set_text(data[0])


# ---------------------------------------------------------------------------
# Chargements
# ---------------------------------------------------------------------------
class Char(object):
  """Classe de base pour un chargement"""

  def __init__(self):
    self.props = {}

  def update_tooltip_L(self, unit_L, unit_F=None):
    """Actualise les tooltips des longueurs suite à un changement d'unité - Ne fait rien"""
    pass

  def update_tooltip_F(self, unit_L, unit_F):
    """Actualise les tooltips des forces suite à un changement d'unité"""
    pass

  def update_labels(self, Main):
    """mise à jour pour widgets de type label"""
    pass

  def remove_char_name(self, deleted, unit_L):
    """Supprime des barres spécifiées par leur nom dans le combo des barres des chargements"""
    combo = self.hbox.get_children()[2]
    model = combo.get_model()
    nodes = [i[0] for i in model]
    indices = []
    for node in deleted:
      if node in nodes:
        indices.append(nodes.index(node))
    for pos in reversed(indices):
      combo.remove(pos)
    active = combo.get_active_text()
    self.update_tooltip_L(unit_L)


  def set_barre_length(self, d_e):
    """Attribue la longueur de barre pour les tooltips"""
    pass

  def update_numeric_L(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de longueur"""
    pass

  def update_numeric_F(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de force"""
    pass

  def update_bars_combo(self, n1, n2, n3, new):
    """Actualise le combo des barres d'un chargement suite à une modification du nom d'une barre"""
    pass

  def update_nodes_combo(self, n, new):
    pass

  def add_combo_bar_item(self, elem):
    """Ajoute un élément barre dans le combo des barres"""
    pass

  def add_combo_arc_item(self, elem):
    """Ajoute un arc dans le combo des arcs"""
    pass

  def add_combo_node_item(self, elem):
    """Ajoute un noeud dans le combo des noeuds"""
    pass

  def get_is_selected(self):
    return self.hbox.get_children()[1].get_active()

  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'une charge"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        menu1 = Gtk.Menu()
        menuitem1 = Gtk.MenuItem(label="Supprimer")
        menuitem1.connect("activate", self.on_delete, Main)
        menu1.append(menuitem1)
        menu1.show_all()
        menu1.popup_at_pointer(event)
        return True # bloque la propagation du signal
    return False

  def on_delete(self, widget, Main):
    """Supprime le chargement depuis le CM"""
    page = Main.charbook.get_nth_page(Main.charbook.get_current_page())
    n_page = Main.charbook.get_current_page()
    vbox = page.get_children()[0].get_children()[0]
    childs = vbox.get_children()
    case = Main.data_editor.cases[n_page]
    for i, char in enumerate(case.chars):
      if not char is self:
        continue
      vbox.remove(childs[i])
      del(case.chars[i])
      break
    Main.set_is_changed(True)

  def copy_char(self, widget, Main):
    Main.set_is_changed()


class CharBar(Char):
  """Classe abstraite pour les chargements appliqués sur barre unique"""

  def __init__(self):
    Char.__init__(self)

  def get_barre_length(self):
    return self.l

  def set_barre_length(self, d_e):
    """Attribue la longueur de barre pour les tooltips pour un segment"""
    b = d_e.get_barre(self.name)
    if b is None:
      self.l = '-'
      return
    if b.l is None:
      self.l = '-'
      return
    self.l = function.PrintValue(b.l)

  def update_bars_combo(self, n1, n2, n3, new):
    """Actualise le combo des barres d'un chargement suite à une modification du nom d'une barre"""
    combo = self.hbox.get_children()[2]
    function.change_elem_combo2(combo, n3, new)
    self.name = combo.get_active_text()

  def add_combo_bar_item(self, barre):
    """Ajoute une barre dans le combo des barres"""
    combo = self.hbox.get_children()[2]
    combo.append_text(barre)

class CharPp(Char):
  """Classe pour un chargement de type poids propre"""

  def __init__(self, status=False):
    Char.__init__(self)
    self.status = status
    self.name = 'pp'
    self.props['type'] = 'pp'

  def set_content(self):
    """Actualise le contenu du chargement pour le poids propre"""
    button = self.hbox.get_children()[1]
    self.status = button.get_active()

  def set_xml_content(self, parent):
    """Retourne le noeud xml pour le poids propre"""
    status = self.status == True and 'true' or 'false'
    ET.SubElement(parent, "pp", {"d": status})

  def  add_hbox(self, Main):
    """Affiche la ligne pour cocher le poids propre"""
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="Prise en compte du poids propre:")
    label.set_size_request(240, 30)
    hbox.pack_start(label, False, False, 0)
    button = Gtk.CheckButton()
    if self.status:
      button.set_active(True)
    button.set_tooltip_text('Activer')
    button.connect('toggled', self.update_char, Main)
    hbox.pack_start(button, False, False, 0)
    hbox.show_all()
    self.hbox = hbox
    return hbox

  def update_char(self, widget, Main):
    self.set_content()
    Main.set_is_changed(True)

  def remove_char_name(self, positions, unit_L):
    """Supprime des barres spécifiées par leur position dans le combo des barres , les indices doivent être donnés par ordre décroissant"""
    pass

  def get_is_selected(self):
    return False

class CharDepi(Char):
  """Classe pour un chargement nodal"""

  def __init__(self, name="", d=""):
    Char.__init__(self)
    self.name = name
    self.props['type'] = 'depi'
    self.d = d

  def set_content(self):
    """Actualise le contenu du chargement pour un affaissement d'appui (depi)"""
    hbox = self.hbox
    widgets = hbox.get_children()
    combobox = widgets[2]
    node = combobox.get_active_text()
    string = ""
    # X
    text = widgets[4].get_text().replace(',', '.')
    try:
      float(text)
    except ValueError:
      return None
    string += "%s," % text
    # Y
    text = widgets[6].get_text().replace(',', '.')
    try:
      float(text)
    except ValueError:
      return None
    string += "%s" % text
    self.d = string

  def add_hbox(self, Main):
    """Création de la boite pour la saisie d'un affaissement d'appui (depi)"""
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    data, node = self.d, self.name
    X, Y = '0', '0'
    if data:
      data = data.split(",")
      n = len(data)
      if n == 2:
        X, Y = data
      elif n == 1:
        X, Y = '0', data[0]

    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    image = Gtk.Image()
    image.set_from_file("glade/depi.png")
    image.show()
    hbox.pack_start(image, False, False, 0)

    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    button.show()
    hbox.pack_start(button, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(100, 30)
    nodes = [val.name for val in Main.data_editor.nodes]
    function.fill_elem_combo(combobox, nodes, node)
    combobox.connect('changed', self.update_char_name, Main)
    combobox.show()
    hbox.pack_start(combobox, False, False, 0)
    label = Gtk.Label(label="X=" )
    label.set_size_request(30, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(X)
    entry.connect('changed', self.update_depi_value, Main)
    entry.show()
    hbox.pack_start(entry, False, False, 0)

    label = Gtk.Label(label="Y=")
    label.set_size_request(30, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(Y)
    entry.connect('changed', self.update_depi_value, Main)
    entry.show()
    hbox.pack_start(entry, False, False, 0)

    hbox.show()
    self.hbox = hbox
    self.update_tooltip_L(unit_L)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def update_tooltip_L(self, unit_L, unit_F=None):
    """Actualise les tooltips des longueurs suite à un changement d'unité pour une charge nodale"""
    widgets = self.hbox.get_children()
    widgets[4].set_tooltip_markup('Valeur du déplacement d\'appui en %s.\nComposante horizontale' % unit_L)
    widgets[6].set_tooltip_markup('Valeur du déplacement d\'appui en %s.\nComposante verticale' % unit_L)

  def update_numeric_L(self, factor):
    widgets = self.hbox.get_children()
    entry = widgets[4]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    entry = widgets[6]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass


  def update_depi_value(self, widget, Main):
    """Mise à jour d'une valeur de déplacement imposée"""
    self.set_content()
    Main.set_is_changed(True)

  def update_char_name(self, combo, Main):
    """Changement du combobox du choix des noeuds pour un déplacement imposé"""
    self.name = combo.get_active_text()
    Main.set_is_changed(True)

  def set_xml_content(self, parent):
    """Retourne le noeud xml pour un un déplacement imposé"""
    if self.name is None:
      return
    node = ET.SubElement(parent, "depi")
    node.set("id", self.name)
    node.set("d", self.d)

  def update_nodes_combo(self, n, new):
    """Actualise le combo des deplacements imposés suite à une modification du nom d'un noeud"""
    combo = self.hbox.get_children()[2]
    function.change_elem_combo2(combo, n, new)
    self.name = combo.get_active_text()

  def add_combo_node_item(self, node):
    """Ajoute un noeud au combo des charges nodales"""
    combo = self.hbox.get_children()[2]
    combo.append_text(node)

class CharNo(Char):
  """Classe pour un chargement nodal"""

  def __init__(self, name="", d=""):
    Char.__init__(self)
    self.name = name
    self.props['type'] = 'node'
    self.d = d

  def set_content(self):
    """Actualise le contenu du chargement pour un chargement nodal"""
    hbox = self.hbox
    widgets = hbox.get_children()
    # si le checkbutton est coché, on ne compte pas le chargement
    #checkbutton = [1]
    #if checkbutton.get_active():
    #  return None
    combobox = widgets[2]
    node = combobox.get_active_text()
    #if node is None:
    #  return None
    string = ""
    # polar or not
    is_polar = False
    combobox = widgets[3]
    text = combobox.get_active_text()
    if text == 'Pol':
      string += "<,"
      is_polar = True
    # Fx
    text = widgets[5].get_text().replace(',', '.')
    try:
      float(text)
    except ValueError:
      return None
    string += "%s," % text
    # Fy
    text = widgets[7].get_text().replace(',', '.')
    try:
      float(text)
    except ValueError:
      return None
    string += "%s," % text
    # Mz
    text = widgets[9].get_text().replace(',', '.')
    try:
      float(text)
    except ValueError:
      return None
    string += text
    self.d = string

  def set_xml_content(self, parent):
    """Retourne le noeud xml pour une charge nodale"""
    if self.name is None:
      return
    node = ET.SubElement(parent, "node")
    node.set("id", self.name)
    node.set("d", self.d)

  def update_numeric_L(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de longueur pour charge nodale"""
    widgets = self.hbox.get_children()
    entry = widgets[9]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass

  def update_numeric_F(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de force pour charge nodale"""
    widgets = self.hbox.get_children()
    entry = widgets[5]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    combobox = widgets[3]
    text = combobox.get_active_text()
    if text == 'Pol':
      is_polar = True
    elif text == 'Car':
      is_polar = False
    else:
      is_polar = False
      print("debug::_update_numeric_vals")
    entry = widgets[7]
    if not is_polar:
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass
    entry = widgets[9]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass


  def add_hbox(self, Main):
    """Création de la boite pour la saisie d'une charge nodale
    Retourne une hbox"""
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    Fx, Fy, Mz = '0', '0', '0'
    data, node = self.d, self.name
    is_polar = False
    if data:
      data = data.split(",")
      n = len(data)
      if n == 4 and data[0] == '<':
        is_polar = True
        del(data[0])
        n = n-1
      Fx = data[0]
      Fy = data[1]
      Mz = data[2]
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    image = Gtk.Image()
    image.set_from_file("glade/nod.xpm")
    image.show()
    hbox.pack_start(image, False, False, 0)

    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    button.show()
    hbox.pack_start(button, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(100, 30)
    nodes = [val.name for val in Main.data_editor.nodes]
    function.fill_elem_combo(combobox, nodes, node)
    combobox.connect('changed', self.update_char_name, Main)
    combobox.show()
    hbox.pack_start(combobox, False, False, 0)
    # cartésien or polar coordonates
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(60, 30)
    string = 'Coordonnées <u>Car</u>tésiennes ou <u>Pol</u>aires'
    combobox.set_tooltip_markup(string)
    for elem in ["Car", "Pol"]:
      combobox.append_text(elem)
    if is_polar:
      combobox.set_active(1)
    else:
      combobox.set_active(0)
    combobox.connect('changed', self.update_char, Main)
    combobox.show()
    hbox.pack_start(combobox, False, False, 0)

    if is_polar:
      string = 'F = '
    else:
      string = "F<sub>x</sub> = "
    label = Gtk.Label(label=string)
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(Fx)
    entry.connect('changed', self.update_char_entry, Main)
    entry.show()
    hbox.pack_start(entry, False, False, 0)

    if is_polar:
      string = '\u03B8 = '
    else:
      string = "F<sub>y</sub> = "
    label = Gtk.Label(label=string)
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(Fy)
    entry.connect('changed', self.update_char_entry, Main)
    entry.show()
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label(label="M<sub>z</sub> = ")
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    label.show()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(Mz)
    entry.connect('changed', self.update_char_entry, Main)
    entry.show()
    hbox.pack_start(entry, False, False, 0)
    hbox.show()
    self.hbox = hbox
    self.update_labels(Main)
    self.update_tooltip_L(unit_L, unit_F)
    self.update_tooltip_F(unit_L, unit_F)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def update_char_entry(self, widget, Main):
    self.set_content()
    Main.set_is_changed(True)

  def update_char(self, widget, Main):
    """Mise à jour du chargement nodal pour les coordonnées polaires/cartésiennes"""
    self.set_content()
    self.update_labels(Main)
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    self.update_tooltip_F(unit_L, unit_F)
    Main.set_is_changed(True)

  def update_nodes_combo(self, n, new):
    """Actualise le combo des noeuds d'une charge nodale suite à une modification du nom d'un noeud"""
    combo = self.hbox.get_children()[2]
    function.change_elem_combo2(combo, n, new)
    self.name = combo.get_active_text()

  def add_combo_node_item(self, node):
    """Ajoute un noeud au combo des charges nodales"""
    combo = self.hbox.get_children()[2]
    combo.append_text(node)

  def update_labels(self, Main):
    """mise à jour pour widgets de type label pour une charge nodale"""
    #print "update_labels node"
    hbox = self.hbox
    widgets = hbox.get_children()
    combo = widgets[3]
    val = combo.get_active_text()
    if val == 'Car':
      is_polar = False
    else:
      is_polar = True
    label = widgets[4]
    if is_polar:
      string = 'F = '
    else:
      string = 'F<sub>x</sub> = '
    label.set_text(string)
    label.set_use_markup(True)
    label = widgets[6]
    if val == 'Car':
      string = 'F<sub>y</sub> = '
    else:
      string = '\u03B8 = ' # téta
    label.set_text(string)
    label.set_use_markup(True)

  def update_tooltip_L(self, unit_L, unit_F=None):
    """Actualise les tooltips des longueurs suite à un changement d'unité pour une charge nodale"""
    widgets = self.hbox.get_children()
    string = 'Moment extérieur:\n%s.%s' % (unit_F, unit_L)
    widgets[9].set_tooltip_markup(string)


  def update_tooltip_F(self, unit_L, unit_F):
    """Actualise les tooltips des forces suite à un changement d'unité pour une charge nodale"""
    widgets = self.hbox.get_children()
    is_polar = widgets[3].get_active_text() == 'Pol' and True or False
    if is_polar:
      string = 'Intensité de la force'
    else:
      string = 'Composante suivant X'
    string += '\nUnité: %s' % unit_F
    widgets[5].set_tooltip_markup(string)
    if is_polar:
      string = 'Angle en degré'
    else:
      string = 'Composante suivant Y'
      string += '\nUnité: %s' % unit_F
    widgets[7].set_tooltip_markup(string)
    self.update_tooltip_L(unit_L, unit_F)

  def update_char_name(self, combo, Main):
    """Changement du combobox du choix des noeuds"""
    self.name = combo.get_active_text()
    Main.set_is_changed(True)

class CharQu(Char):
  """Classe pour un chargement uniforme"""

  def __init__(self, name="", d=""):
    Char.__init__(self)
    self.name = name
    self.props['type'] = 'entry'
    self.d = d

  def set_content(self):
    """Actualise le contenu du chargement pour un charge uniforme"""
    widgets = self.hbox.get_children()
    barre = widgets[2].get_text()
    if barre == '':
      return None
    string = ""
    combobox = widgets[3]
    rel = combobox.get_active_text()
    if rel == 'Rel':
      string += "@,"
    # qx
    qx = widgets[5].get_text().replace(',', '.')
    try:
      float(qx)
    except ValueError:
      return None
    # qy
    qy = widgets[7].get_text().replace(',', '.')
    try:
      float(qy)
    except ValueError:
      return None
    # start
    a1 = widgets[9].get_text().replace(',', '.')
    # end
    a2 = widgets[11].get_text().replace(',', '.')
    tag = widgets[12].get_active()
    if tag:
      string += "%%%s,%%%s,%s,%s" % (a1, a2, qx, qy)
    else:
      string += "%s,%s,%s,%s" % (a1, a2, qx, qy)
    self.d = string

  def set_xml_content(self, parent):
    """Retourne le noeud xml pour une charge uniforme"""
    if self.name is None:
      return
    node = ET.SubElement(parent, "barre")
    node.set("id", self.name)
    node.set("qu", self.d)

  def update_numeric_L(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de longueur pour qu"""
    widgets = self.hbox.get_children()
    entry = widgets[5]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val/factor
      entry.set_text(str(val))
    except ValueError:
      pass

    entry = widgets[7]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val/factor
      entry.set_text(str(val))
    except ValueError:
      pass
    check = widgets[12]
    if check.get_active():
      return
    entry = widgets[9]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    entry = widgets[11]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass

  def update_numeric_F(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de force pour charge qu"""
    widgets = self.hbox.get_children()
    combo = widgets[3]
    text = combo.get_active_text()
    tag = text == "Rel" and True or False
    entry = widgets[5]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    entry = widgets[7]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass


  def add_hbox(self, Main):
    """Création de la boite pour la saisie d'une charge uniforme
    Retourne une hbox"""
    qx, qy, a1, a2 = '0', '0', '', ''
    barre, data = self.name, self.d
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    isRelative = False
    l_is_relative = False
    if data:
      data = data.split(",")
      if len(data) == 5 and data[0][0] == '@':
        isRelative = True
        del(data[0])
      n = len(data)
      if n == 2:
        qx, qy = data[0], data[1]
      elif n == 3:
        a2 = data[0]
        qx, qy = data[1], data[2]
      elif n == 4:
        a1 = data[0]
        a2 = data[1]
        qx, qy = data[2], data[3]
      if not a1 == '' and a1[0] == '%':
        a1 = a1[1:]
        a2 = a2[1:]
        l_is_relative = True
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    image = Gtk.Image()
    image.set_from_file("glade/qu.xpm")
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    # beam name
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(barre)
    entry.connect('changed', self.update_char_name, Main)
    entry.set_tooltip_text('Formats possibles:\n\tB1\n\t*\n\tB1,B2,B3')
    hbox.pack_start(entry, False, False, 0)
    # relative or absolute streigth
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(60, 30)
    for elem in ["Abs", "Rel"]:
      combobox.append_text(elem)
    if isRelative:
      combobox.set_active(1)
    else:
      combobox.set_active(0)
    string = 'Coordonnées dans le repère <u>Abs</u>olu\nou dans le repère <u>Rel</u>atif à la barre'
    combobox.set_tooltip_markup(string)
    combobox.connect('changed', self.update_char, Main)
    hbox.pack_start(combobox, False, False, 0)
    # x intensity
    string = "q<sub>x</sub> ="
    label = Gtk.Label(label=string)
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(qx)
    entry.connect('changed', self.update_char_entry, Main)
    hbox.pack_start(entry, False, False, 0)
    # y intensity
    string = "q<sub>y</sub> ="
    label = Gtk.Label(label=string)
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(qy)
    entry.connect('changed', self.update_char_entry, Main)
    hbox.pack_start(entry, False, False, 0)
    # start default = 0
    string = 'x<sub>0</sub> ='
    label = Gtk.Label(label=string)
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(a1)
    entry.connect('changed', self.update_char_entry, Main)
    hbox.pack_start(entry, False, False, 0)
    # end default = 1
    string = 'x<sub>1</sub> ='
    label = Gtk.Label(label=string)
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(a2)
    entry.connect('changed', self.update_char_entry, Main)
    hbox.pack_start(entry, False, False, 0)

    button = Gtk.CheckButton()
    if l_is_relative:
      button.set_active(True)
    button.set_tooltip_text('Position relative')
    button.connect('toggled', self.update_char2, Main)
    hbox.pack_start(button, False, False, 0)
    hbox.show_all()
    self.hbox = hbox
    self.update_labels(Main)
    self.update_tooltip_L(unit_L, unit_F)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def update_char_name(self, widget, Main):
    """Changement du entry du nom d'une charge qu"""
    self.name = widget.get_text()
    self.set_content()
    Main.set_is_changed(True)

  def update_char_entry(self, widget, Main):
    """Changement d'une valeur d'une charge qu"""
    self.set_content()
    Main.set_is_changed(True)

  def update_char(self, widget, Main):
    """Mise à jour du chargement pour une charge qu"""
    self.set_content()
    self.update_labels(Main)
    Main.set_is_changed(True)

  def update_char2(self, widget, Main):
    self.set_content()
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    self.update_tooltip_L(unit_L, unit_F)
    Main.set_is_changed(True)

  def update_tooltip_L(self, unit_L, unit_F=None):
    """Actualise les tooltips des longueurs suite à un changement d'unité pour une charge uniforme"""
    widgets = self.hbox.get_children()
    self._update_tooltip1(widgets, unit_L, unit_F)
    self._update_tooltip2(widgets, unit_L)

  def update_tooltip_F(self, unit_L, unit_F):
    """Actualise les tooltips des forces suite à un changement d'unité pour une charge uniforme"""
    widgets = self.hbox.get_children()
    self._update_tooltip1(widgets, unit_L, unit_F)

  def _update_tooltip1(self, widgets, unit_L, unit_F):
    """Met à jour les tooltips de qx et qy pour la charge qu"""
    rep = widgets[3].get_active_text()
    if rep == "Rel":
      tag = True
    else:
      tag = False
    if tag:
      string = 'Composante parallèle à la barre'
    else:
      string = 'Composante suivant X dans le repère absolu'
    string += '\nUnité: %s/%s' % (unit_F, unit_L)
    widgets[5].set_tooltip_markup(string)
    if tag:
      string = 'Composante perpendiculaire à la barre'
    else:
      string = 'Composante suivant Y dans le repère absolu'
    string += '\nUnité: %s/%s' % (unit_F, unit_L)
    widgets[7].set_tooltip_markup(string)


  def _update_tooltip2(self, widgets, unit_L):
    """Met à jour les tooltips des positions pour la charge qu"""
    is_rel = widgets[12].get_active()
    entry = widgets[9]
    if is_rel:
      entry.set_tooltip_text('Optionnel\nPosition du début de la charge\nValeur entre 0 et 1')
    else:
      entry.set_tooltip_text('Position du début de la charge\nOptionnel\nUnité : %s' % unit_L)

    entry = widgets[11]
    if is_rel:
      entry.set_tooltip_text('Optionnel\nPosition de la fin de la charge\nValeur entre 0 et 1')
    else:
      entry.set_tooltip_text('Position de la fin de la charge\nOptionnel\nUnité : %s' % unit_L)


  def remove_char_name(self, positions, unit_L):
    """Supprime des barres spécifiées par leur position dans le combo des barres , les indices doivent être donnés par ordre décroissant"""
    pass

class CharFp(CharBar):
  """Classe pour un chargement nodal"""

  def __init__(self, name="", d="", type='barre'):
    CharBar.__init__(self)
    self.name = name
    self.d = d
    if type == "arc":
      self.props['type'] = 'arc'
    elif type == "barre":
      self.props['type'] = 'barre'

  def set_content(self):
    """Actualise le contenu du chargement pour un chargement ponctuelle sur barre"""
    hbox = self.hbox
    widgets = self.hbox.get_children()
    #checkbutton = widgets[1]
    #if checkbutton.get_active():
    #  return None
    combobox = widgets[2]
    barre = combobox.get_active_text()
    #if barre is None:
    #  return None
    string = ""
    combobox = widgets[3]
    rel = combobox.get_active_text()
    is_rel = False
    if rel == 'Rel':
      is_rel = True
      string += "@"
    # polar or not
    is_polar = False
    combobox = widgets[4]
    text = combobox.get_active_text()
    if text == 'Pol':
      string += "<"
      is_polar = True
    if is_polar or is_rel:
      string += ","

    # position
    text = widgets[6].get_text().replace(',', '.')
    # longueur en pourcent
    tag = widgets[7].get_active()
    if tag:
      string += "%%%s," % text
    else:
      string += "%s," % text
    # fx
    text = widgets[9].get_text().replace(',', '.')
    try:
      float(text)
    except ValueError:
      text = '0'
    string += "%s," % text
    # fy
    text = widgets[11].get_text().replace(',', '.')
    try:
      float(text)
    except ValueError:
      text = '0'
    string += "%s," % text
    # Mz
    text = widgets[13].get_text().replace(',', '.')
    try:
      float(text)
    except ValueError:
      text = '0'
    string += "%s" % text
    self.d = string

  def set_xml_content(self, parent):
    """Retourne le noeud xml pour une charge ponctuelle sur barre"""
    if self.name is None:
      return
    if self.props['type'] == 'arc':
      node = ET.SubElement(parent, "arc")
    else:
      node = ET.SubElement(parent, "barre")
    node.set("id", self.name)
    node.set("fp", self.d)

  def update_numeric_L(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de longueur pour fp"""
    widgets = self.hbox.get_children()
    entry = widgets[6]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    entry = widgets[13]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass

  def update_numeric_F(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de force pour charge fp"""
    widgets = self.hbox.get_children()
    is_pol = [False, True][widgets[4].get_active()]
    entry = widgets[9]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    if not is_pol:
      entry = widgets[11]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except:
        pass
    entry = widgets[13]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass

  def add_hbox(self, Main):
    """Création de la boite pour la saisie d'une charge ponctuelle sur barre"""
    barre_name, data = self.name, self.d
# -------- remettre pour inclure les arcs
    barres = Main.data_editor.get_all_barres()
# -----------
    #barres = Main.data_editor.get_barres()
    #arcs = Main.data_editor.get_arcs()
    self.set_barre_length(Main.data_editor)
    fx, fy, mz, a = '0', '0', '0', '0'
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    is_rel = False
    is_pol = False
    l_is_relative = False
    if data:
      data = data.split(",")
      n = len(data)
      if n == 5:
        if data[0][0] == '@':
          is_rel = True
          try:
            if data[0][1] == '<':
              is_pol = True
          except IndexError:
            pass
        elif data[0][0] == '<':
          is_pol = True
        del(data[0])
        n = n-1
      if n == 4:
        a = data[0]
        fx = data[1]
        fy = data[2]
        mz = data[3]

      if not a == '' and a[0] == '%':
        a = a[1:]
        l_is_relative = True

    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    image = Gtk.Image()
    image.set_from_file("glade/fp.xpm")
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    # beam name
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(100, 30)
    function.fill_elem_combo(combobox, barres, barre_name)
    combobox.connect('changed', self.update_char_name, Main)
    hbox.pack_start(combobox, False, False, 0)
    # relative or absolute streigth
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(60, 30)
    for elem in ["Abs", "Rel"]:
      combobox.append_text(elem)
    if is_rel:
      combobox.set_active(1)
    else:
      combobox.set_active(0)
    string = 'Coordonnées dans le repère <u>Abs</u>olu\nou dans le repère <u>Rel</u>atif à la barre'
    combobox.set_tooltip_markup(string)
    combobox.connect('changed', self.update_char, Main)
    hbox.pack_start(combobox, False, False, 0)
    # cartésien or polar coordonates
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(60, 30)
    string = 'Coordonnées <u>Car</u>tésiennes ou <u>Pol</u>aires'
    combobox.set_tooltip_markup(string)
    for elem in ["Car", "Pol"]:
      combobox.append_text(elem)
    if is_pol:
      combobox.set_active(1)
    else:
      combobox.set_active(0)
    combobox.connect('changed', self.update_char2, Main)
    hbox.pack_start(combobox, False, False, 0)

    # position = 0
    label = Gtk.Label(label="")
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(a)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    # checkbutton longueur pourcentage
    button = Gtk.CheckButton()
    if l_is_relative:
      button.set_active(True)
    button.set_tooltip_text('Position relative')
    button.connect('toggled', self.update_char2, Main)
    hbox.pack_start(button, False, False, 0)

    # x intensity
    label = Gtk.Label()
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(fx)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    # y intensity
    label = Gtk.Label()
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(fy)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    # mz intensity
    label = Gtk.Label(label="M<sub>z</sub> =")
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(mz)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    hbox.show_all()
    self.hbox = hbox
    self._update_labels(Main)
    self.update_tooltip_L(unit_L, unit_F)
    self.update_tooltip_F(unit_L, unit_F)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def _update_labels(self, Main):
    """Actualise les labels pour la charge fp"""
    widgets = self.hbox.get_children()
    is_rel = [False, True][widgets[3].get_active()]
    is_pol = [False, True][widgets[4].get_active()]
    # x position
    label = widgets[5]
    string = 'x ='
    label.set_text(string)

    if is_rel and not is_pol:
      string1 = 'F<sub>x\'</sub> ='
      string2 = 'F<sub>y\'</sub> ='
    elif not is_rel and not is_pol:
      string1 = 'F<sub>x</sub> ='
      string2 = 'F<sub>y</sub> ='
    else:
      string1 = 'F ='
      string2 = '\u03B8 ='
    label = widgets[8]
    label.set_text(string1)
    label.set_use_markup(True)
    label = widgets[10]
    label.set_text(string2)
    label.set_use_markup(True)


  def update_tooltip_F(self, unit_L, unit_F):
    """Actualise les tooltips des forces suite à un changement d'unité pour une charge ponctuelle sur barre"""
    widgets = self.hbox.get_children()
    self._update_tooltip1(widgets, unit_L, unit_F)
    self._update_tooltip2(widgets, unit_L, unit_F)
    self._update_tooltip3(widgets, unit_L, unit_F)


  def update_tooltip_L(self, unit_L, unit_F=None):
    """Actualise les tooltips des longueurs suite à un changement d'unité pour une charge ponctuelle sur barre"""
    hbox = self.hbox
    widgets = hbox.get_children()
    entry = widgets[6]
    l = self.get_barre_length()
    tag = widgets[7].get_active()
    if tag:
      string = 'Distance comprise entre 0 et 1'
    else:
      string = 'Distance comprise entre 0 et %s %s' % (l, unit_L)
    entry.set_tooltip_text(string)
    self._update_tooltip3(widgets, unit_L, unit_F)


  def _update_tooltip1(self, widgets, unit_L, unit_F):
    """Met à jour le tooltip de Fx ou F pour la charge nodale en fonction du type de coordonnées polaires ou cartésiennes"""
    entry = widgets[9]
    is_rel = widgets[3].get_active_text() == 'Rel' and True or False
    is_polar = widgets[4].get_active_text() == 'Pol' and True or False
    if is_rel:
      rep = 'de la barre'
    else:
      rep = 'global'
    if is_polar:
      string = 'Intensité de la force'
    else:
      string = 'Composante suivant X dans le repère %s' % rep
    string += '\nUnité: %s' % unit_F
    entry.set_tooltip_markup(string)

  def _update_tooltip2(self, widgets, unit_L, unit_F):
    """Met à jour le tooltip de Fy ou teta pour la charge nodale"""
    entry = widgets[11]
    is_rel = widgets[3].get_active_text() == 'Rel' and True or False
    is_polar = widgets[4].get_active_text() == 'Pol' and True or False
    if is_rel:
      rep = 'de la barre'
    else:
      rep = 'global'
    if is_polar:
      string = 'Angle en degré'
    else:
      string = 'Composante suivant Y dans le repère %s' % rep
      string += '\nUnité: %s' % unit_F
    entry.set_tooltip_markup(string)

  def _update_tooltip3(self, widgets, unit_L, unit_F):
    """Met à jour le tooltip du moment pour la charge nodale"""
    string = 'Moment extérieur:\n%s.%s' % (unit_F, unit_L)
    widgets[13].set_tooltip_markup(string)


  def update_char_name(self, combo, Main):
    """Changement du combobox du choix des barres dans un chargement fp"""
    #print "update_char_name fp"
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    self.name = combo.get_active_text()
    barres = Main.data_editor.barres
    for barre in barres:
      if self.name == barre.name:
        if barre.get_is_arc():
          self.props['type'] = 'arc'
        else:
          self.props['type'] = 'barre'
    self.set_barre_length(Main.data_editor)
    self.update_tooltip_L(unit_L)
    Main.set_is_changed(True)

  def update_char(self, widget, Main):
    """Charge fp"""
    self.set_content()
    Main.set_is_changed(True)

  def update_char2(self, widget, Main):
    """Charge fp"""
    self._update_labels(Main)
    self.set_content()
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    self.update_tooltip_L(unit_L, unit_F)
    self.update_tooltip_F(unit_L, unit_F)
    Main.set_is_changed(True)


  def add_char_name(self, name):
    """Ajoute une barre dans le combo des barres pour une charge fp"""
    combobox = self.hbox.get_children()[2]
    combobox.append_text(name)

class CharTh(CharBar):
  """Classe pour un chargement thermique"""

  def __init__(self, name="", d="0,0"):
    CharBar.__init__(self)
    self.name = name
    self.d = d

# enlever les returrn
  def set_content(self):
    """Actualise le contenu du chargement pour un charge thermique"""
    widgets = self.hbox.get_children()
    #checkbutton = widgets[1]
    #if checkbutton.get_active():
    #  return None
    combobox = widgets[2]
    barre = combobox.get_active_text()
    if barre is None:
      return None
    string = ""
    # Tsup
    text = widgets[4].get_text().replace(',', '.')
    try:
      text = str(float(text))
    except:
      return None
    string += "%s," % text
    # Tinf
    text = widgets[6].get_text().replace(',', '.')
    try:
      text = str(float(text))
    except:
      return None
    string += text
    self.d = string

  def set_xml_content(self, parent):
    """Retourne le noeud xml pour une charge thermique"""
    if self.name is None:
      return
    if self.props['type'] == 'arc':
      node = ET.SubElement(parent, "arc")
    else:
      node = ET.SubElement(parent, "barre")
    node.set("id", self.name)
    node.set("therm", self.d)

  def add_hbox(self, Main):
    """Création de la boite pour la saisie d'une charge thermique
    Retourne une hbox"""
    barre_name, data = self.name, self.d
    barres = Main.data_editor.get_all_barres()
    arcs = Main.data_editor.get_arcs()
    if barre_name in arcs:
      self.props['type'] = 'arc'
    else:
      self.props['type'] = 'barre'
    t_sup, t_inf = '0', '0'
    if data:
      data = data.split(",")
      if len(data) == 2:
        t_sup = data[0]
        t_inf = data[1]
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    image = Gtk.Image()
    image.set_from_file("glade/sun-char.png")
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(100, 30)
    function.fill_elem_combo(combobox, barres, barre_name)
    combobox.connect('changed', self.update_char_name, Main)
    hbox.pack_start(combobox, False, False, 0)
    label = Gtk.Label(label="T<sub>s</sub> =")
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(t_sup)
    entry.set_tooltip_text('Température en fibre extrême positive\nUnité : °C')
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label(label="T<sub>i</sub> =")
    label.set_size_request(30, 30)
    label.set_use_markup(True)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(t_inf)
    entry.set_tooltip_text('Température en fibre extrême négative\nUnité : °C')
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    hbox.show_all()
    self.hbox = hbox
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def update_char_name(self, combo, Main):
    """Changement du combobox du choix des barres dans un chargement thermique"""
    self.name = combo.get_active_text()
    barres = Main.data_editor.barres
    for barre in barres:
      if self.name == barre.name:
        if barre.get_is_arc():
          self.props['type'] = 'arc'
        else:
          self.props['type'] = 'barre'
    Main.set_is_changed(True)

  def update_char(self, combo, Main):
    self.set_content()
    Main.set_is_changed(True)

class CharTr(CharBar):
  """Classe pour un chargement triangulaire"""

  def __init__(self, name="", d=""):
    CharBar.__init__(self)
    self.name = name
    self.d = d
    self.props['type'] = 'barre'

# enlever les returns
  def set_content(self):
    """Actualise le contenu du chargement pour un charge triangulaire"""
    widgets = self.hbox.get_children()
    #if checkbutton.get_active():
    #  return None
    combobox = widgets[2]
    barre = combobox.get_active_text()
    #if barre is None:
    #  return None
    string = ""
    combobox = widgets[3]
    rel = combobox.get_active_text()
    is_rel = False
    if rel == 'Rel':
      is_rel = True
      string += "@"
    string += ","
    # q1
    q1 = widgets[5].get_text().replace(',', '.')
    try:
      float(q1)
    except ValueError:
      return None
    # q2
    q2 = widgets[7].get_text().replace(',', '.')
    try:
      float(q2)
    except ValueError:
      return None
    # angle
    angle = widgets[9].get_text().replace(',', '.')
    try:
      float(angle)
    except ValueError:
      return None
    # position 1
    a1 = widgets[11].get_text().replace(',', '.')
    # position 2
    a2 = widgets[13].get_text().replace(',', '.')
    # longueur en pourcent
    tag = widgets[14].get_active()
    if tag:
      string += "%%%s,%%%s,%s,%s,%s" % (a1, a2, q1, q2, angle)
    else:
      string += "%s,%s,%s,%s,%s" % (a1, a2, q1, q2, angle)
    self.d = string

  def set_xml_content(self, parent):
    """Retourne le noeud xml pour une charge triangulaire"""
    if self.name is None:
      return
    node = ET.SubElement(parent, "barre")
    node.set("id", self.name)
    node.set("tri", self.d)

  def update_numeric_L(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de longueur pour tri"""
    widgets = self.hbox.get_children()
    check = widgets[14]
    if check.get_active():
      return
    entry = widgets[13]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    entry = widgets[11]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass

  def update_numeric_F(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de force pour charge tri"""
    widgets = self.hbox.get_children()
    entry = widgets[5]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass
    entry = widgets[7]
    try:
      val = float(entry.get_text().replace(",", "."))
      val = val*factor
      entry.set_text(str(val))
    except ValueError:
      pass

  def add_hbox(self, Main):
    """Création de la boite pour la saisie d'une charge triangulaire
    Retourne une hbox"""
    barre_name, data = self.name, self.d
    barres = Main.data_editor.get_barres()
    self.set_barre_length(Main.data_editor)
    a0, a1, q1, q2, angle = '0', '1', '', '', '90'
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    l_is_relative = True
    is_rel = False
    if data:
      data = data.split(",")
      n = len(data)
      if n == 6:
        if data[0] and data[0][0] == '@':
          is_rel = True
        del(data[0])
        n = n-1
      if n == 5:
        a0 = data[0]
        a1 = data[1]
        q1 = data[2]
        q2 = data[3]
        angle = data[4]

      if not a0 == '' and a0[0] == '%':
        a0 = a0[1:]
        a1 = a1[1:]
      else:
        l_is_relative = False

    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    image = Gtk.Image()
    image.set_from_file("glade/trapeze.xpm")
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    # beam name
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(100, 30)
    function.fill_elem_combo(combobox, barres, barre_name)
    combobox.connect('changed', self.update_char_name, Main)
    hbox.pack_start(combobox, False, False, 0)
    # relative or absolute streigth
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(60, 30)
    for elem in ["Abs", "Rel"]:
      combobox.append_text(elem)
    if is_rel:
      combobox.set_active(1)
    else:
      combobox.set_active(0)
    string = 'Coordonnées dans le repère <u>Abs</u>olu\nou dans le repère <u>Rel</u>atif à la barre'
    combobox.set_tooltip_markup(string)
    combobox.connect('changed', self.update_char_rep, Main)
    hbox.pack_start(combobox, False, False, 0)

    # q1 intensity start
    label = Gtk.Label(label='q<sub>1</sub> =')
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(q1)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    # q2 intensity end
    label = Gtk.Label(label='q<sub>2</sub> =')
    label.set_use_markup(True)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    #entry.set_has_frame(False)
    entry.set_width_chars(10)
    entry.set_text(q2)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)

    # angle
    string = '\u03B8 = '
    label = Gtk.Label(label=string)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(angle)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)

    # position = 0
    label = Gtk.Label(label='x<sub>0</sub> =')
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(a0)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)

    # position = 1
    label = Gtk.Label(label='x<sub>1</sub> =')
    label.set_use_markup(True)
    label.set_size_request(30, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(a1)
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)

    # checkbutton longueur pourcentage
    button = Gtk.CheckButton()
    if l_is_relative:
      button.set_active(True)
    button.connect('toggled', self.update_char2, Main)
    button.set_tooltip_text('Position relative')
    hbox.pack_start(button, False, False, 0)
    hbox.show_all()
    self.hbox = hbox
    self.update_tooltip_L(unit_L)
    self.update_tooltip_F(unit_L, unit_F)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def update_char_name(self, combo, Main):
    """Changement du combobox du choix des barres dans un chargement tri"""
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    self.name = combo.get_active_text()
    self.set_barre_length(Main.data_editor)
    self.update_tooltip_L(unit_L)
    Main.set_is_changed(True)

  def update_char(self, combo, Main):
    """Charge triangulaire"""
    self.set_content()
    Main.set_is_changed(True)

  def update_char2(self, widget, Main):
    """Charge triangulaire"""
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    self.update_tooltip_L(unit_L)
    self.set_content()
    Main.set_is_changed(True)

  def update_char_rep(self, combo, Main):
    """Charge triangulaire"""
    self.set_content()
    units = Main.data_editor.get_units()
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    self.update_tooltip_F(unit_L, unit_F)
    Main.set_is_changed(True)

  def update_tooltip_F(self, unit_L, unit_F):
    """Actualise les tooltips des forces suite à un changement d'unité pour une charge triangulaire"""
    widgets = self.hbox.get_children()
    is_rel = [False, True][widgets[3].get_active()]
    entry = widgets[5]
    self.update_unit_F_tooltip(entry, 'x0', unit_F)
    entry = widgets[7]
    self.update_unit_F_tooltip(entry, 'x1', unit_F)
    entry = widgets[9]
    self.update_tooltip2(entry, is_rel)

  def update_unit_F_tooltip(self, entry, comp, unit_F):
    """Met à jour le tooltip de q1 (ou de q2) pour la charge trapezoidale en fonction du type de coordonnées (abs ou rel)"""
    string = "Intensité de l'action pour %s" % comp
    string += '\nUnité: %s' % unit_F
    entry.set_tooltip_markup(string)

  def update_tooltip2(self, entry, is_rel):
    """Met à jour le tooltip de l'angle dans le chargement trapézoidal"""
    string = "Angle en degré\ndans le repère"
    if is_rel:
      string += ' lié à la barre'
    else:
      string += ' global'
    entry.set_tooltip_markup(string)


  def update_tooltip_L(self, unit_L, unit_F=None):
    """Actualise les tooltips des longueurs suite à un changement d'unité pour une charge triangulaire"""
    hbox = self.hbox
    l = self.get_barre_length()
    tag = hbox.get_children()[14].get_active()
    if tag:
      string = 'Distance comprise entre 0 et 1'
    else:
      string = 'Distance comprise entre 0 et %s %s' % (l, unit_L)
    entry = hbox.get_children()[11]
    entry.set_tooltip_text(string)
    entry = hbox.get_children()[13]
    entry.set_tooltip_text(string)

  def update_bars_combo(self, n1, n2, n3, new):
    """Actualise le combo des barres d'un chargement suite à une modification du nom d'une barre pour une charge tri"""
    combo = self.hbox.get_children()[2]
    function.change_elem_combo2(combo, n2, new)
    self.name = combo.get_active_text()

class CharArc(Char):
  """Classe pour un chargement sur un arc"""

  def __init__(self, name="", d="", proj=""):
    Char.__init__(self)
    self.props['type'] = 'arc'
    self.name = name
    if d == "":
      self.rel = True
    elif d[0] == '%':
      self.rel = True
      d = d[1:]
    else:
      self.rel = False
    self.unif = False
    if d == "":
      self.d = {"x1": 0., "x2": 1., "q1x": '0', "q1y": '0', "q2x":'0', "q2y": '0'}
      self.unif = True
    else:
      try:
        d = [float(i) for i in d.split(',')]
        self.d = {"x1": d[0], "x2": d[1], "q1x": d[2], "q1y": d[3], "q2x":d[4], "q2y": d[5]}
        if d[2] == d[4] and d[3] == d[5]:
          self.unif = True
      except ValueError:
        self.d = {"x1": 0., "x2": 1., "q1x": '0', "q1y": '0', "q2x":'0', "q2y": '0'}
        self.unif = True
    if proj == '':
      self.proj = 0
    else:
      self.proj = int(proj)
    self.rel = True


  def set_xml_content(self, parent):
    """Retourne le noeud xml pour une charge sur un arc"""
    if self.name is None:
      return
    node = ET.SubElement(parent, "arc")
    node.set("id", self.name)
    d = self.d
# finir relatif/non relatif
    d = "%%%s,%s,%s,%s,%s,%s" % (d['x1'], d['x2'], d['q1x'], d['q1y'], d['q2x'], d['q2y'])
    node.set("qu", d)
    node.set("proj", str(self.proj))

  def add_hbox(self, Main):
    """Création de la boite pour la saisie d'une charge sur un arc
    Retourne une hbox"""
    arcs = Main.data_editor.get_arcs()
    units = Main.data_editor.get_units()
    unit_L = function.return_key(units['L'], Main.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], Main.data_editor.unit_conv['F'])

    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    image = Gtk.Image()
    image.set_from_file(self._get_img())
    hbox.pack_start(image, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    # beam name
    combobox = Gtk.ComboBoxText()
    combobox.set_size_request(100, 30)
    function.fill_elem_combo(combobox, arcs, self.name)
    combobox.connect('changed', self.update_char_name, Main)
    hbox.pack_start(combobox, False, False, 0)

    q_hbox = self._get_q_hbox(Main)
    hbox.pack_start(q_hbox, False, False, 0)
    x_hbox = self._get_x_hbox(Main)
    hbox.pack_start(x_hbox, False, False, 0)
    self.hbox = hbox
    self.update_tooltip_F(unit_L, unit_F)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox

  def _get_x_hbox(self, Main):
    """Retourne la hbox relative aux positions x"""
    d = self.d
    x1, x2 = d["x1"], d["x2"]
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    if not x1 == 0.:
      label = Gtk.Label(label='x<sub>1</sub> =')
      label.set_use_markup(True)
      label.set_size_request(35, 30)
      hbox.pack_start(label, False, False, 0)
      entry = Gtk.Entry()
      entry.set_name("x1")
      entry.set_width_chars(10)
      entry.set_text(str(x1))
      entry.connect('changed', self.update_char, Main)
      entry.set_tooltip_text("Valeur comprise entre 0 et 1")
      hbox.pack_start(entry, False, False, 0)
    if not x2 == 1.:
      label = Gtk.Label(label='x<sub>2</sub> =')
      label.set_use_markup(True)
      label.set_size_request(35, 30)
      hbox.pack_start(label, False, False, 0)
      entry = Gtk.Entry()
      entry.set_name("x2")
      entry.set_width_chars(10)
      entry.set_text(str(x2))
      entry.connect('changed', self.update_char, Main)
      entry.set_tooltip_text("Valeur comprise entre 0 et 1")
      hbox.pack_start(entry, False, False, 0)
    return hbox

  def _get_q_hbox(self, Main):
    """Retourne la hbox relative aux charges q pour un arc"""
    d = self.d
    q1x, q1y, q2x, q2y = d['q1x'], d['q1y'], d['q2x'], d['q2y']
    hbox = Gtk.HBox(homogeneous=False, spacing=10)
    if self.proj == 2:
      if self.unif:
        label = Gtk.Label(label='q =')
      else:
        label = Gtk.Label(label='q<sub>1</sub> =')
      label.set_use_markup(True)
      label.set_size_request(35, 30)
      hbox.pack_start(label, False, False, 0)
      entry = Gtk.Entry()
      entry.set_name("q1y")
      entry.set_width_chars(10)
      entry.set_text(str(q1y))
      entry.connect('changed', self.update_char, Main)
      hbox.pack_start(entry, False, False, 0)
      if self.unif:
        return hbox
      label = Gtk.Label(label='q<sub>2</sub> =')
      label.set_use_markup(True)
      label.set_size_request(35, 30)
      hbox.pack_start(label, False, False, 0)
      entry = Gtk.Entry()
      entry.set_name("q2y")
      entry.set_width_chars(10)
      entry.set_text(str(q2y))
      entry.connect('changed', self.update_char, Main)
      hbox.pack_start(entry, False, False, 0)
      return hbox

    if self.unif:
      label = Gtk.Label(label='q<sub>x</sub> =')
    else:
      label = Gtk.Label(label='q<sub>1x</sub> =')
    label.set_use_markup(True)
    label.set_size_request(35, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_name("q1x")
    entry.set_width_chars(10)
    entry.set_text(str(q1x))
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    if self.unif:
      label = Gtk.Label(label='q<sub>y</sub> =')
    else:
      label = Gtk.Label(label='q<sub>1y</sub> =')
    label.set_use_markup(True)
    label.set_size_request(35, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_name("q1y")
    entry.set_width_chars(10)
    entry.set_text(str(q1y))
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    if self.unif:
      return hbox

    label = Gtk.Label(label='q<sub>2x</sub> =')
    label.set_use_markup(True)
    label.set_size_request(35, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_name("q2x")
    entry.set_width_chars(10)
    entry.set_text(str(q2x))
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label(label='q<sub>2y</sub> =')
    label.set_use_markup(True)
    label.set_size_request(35, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_name("q2y")
    entry.set_width_chars(10)
    entry.set_text(str(q2y))
    entry.connect('changed', self.update_char, Main)
    hbox.pack_start(entry, False, False, 0)
    return hbox

  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'une charge sur arc"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        if self.proj == 0:
          is_active = (1, 0, 0)
        elif self.proj == 1:
          is_active = (0, 1, 0)
        elif self.proj == 2:
          is_active = (0, 0, 1)
        menu1 = Gtk.Menu()
        menuitem1 = Gtk.CheckMenuItem(label="Charge linéique", active=is_active[0])
        menuitem1.set_name('proj0')
        menuitem1.connect("activate", self.update_arc_type, Main)
        menu1.append(menuitem1)
        menuitem2 = Gtk.CheckMenuItem(label="Charge projetée", active=is_active[1])
        menuitem2.set_name('proj1')
        menuitem2.connect("activate", self.update_arc_type, Main)
        menu1.append(menuitem2)
        menuitem3 = Gtk.CheckMenuItem(label="Charge radiale", active=is_active[2])
        menuitem3.set_name('proj2')
        menuitem3.connect("activate", self.update_arc_type, Main)
        menu1.append(menuitem3)

        menuitem4 = Gtk.CheckMenuItem(label="Charge uniforme", active=self.unif)
        menuitem4.connect("activate", self.update_unif, Main)
        menu1.append(menuitem4)

        start = not self.d['x1'] == 0.
        end = not self.d['x2'] == 1.
        menuitem5 = Gtk.CheckMenuItem(label="Ajouter un point de départ", active=start)
        menuitem5.connect("activate", self.add_start_point, Main)
        menu1.append(menuitem5)

        menuitem6 = Gtk.CheckMenuItem(label="Ajouter un point de fin", active=end)
        menuitem6.connect("activate", self.add_end_point, Main)
        menu1.append(menuitem6)

        menuitem7 = Gtk.MenuItem(label="Dupliquer")
        menuitem7.connect("activate", self.on_duplicate, Main)
        menuitem7.set_sensitive(False)
        menu1.append(menuitem7)
        menuitem8 = Gtk.MenuItem(label="Supprimer")
        menuitem8.connect("activate", self.on_delete, Main)
        menu1.append(menuitem8)
        menu1.show_all()
        menu1.popup_at_pointer(event)

        return True # bloque la propagation du signal
    return False

  def on_duplicate(self, widget, args):
    pass

  def update_unif(self, widget, Main):
    """Met à jour les widgets selon que la charge est uniforme ou non"""
    self.unif = widget.get_active()
    if self.unif:
       d = self.d
       d['q2x'],  d['q2y'] = d['q1x'], d['q1y']
    hbox = self.hbox
    widgets = hbox.get_children()
    hbox.remove(widgets[3])
    q_hbox = self._get_q_hbox(Main)
    hbox.pack_start(q_hbox, False, False, 0)
    hbox.reorder_child(q_hbox, 3)
    hbox.show_all()
    Main.set_is_changed(True)

  def add_start_point(self, widget, Main):
    """Ajoute ou supprime les widgets pour spécifier l'origine de la charge"""
    hbox = self.hbox
    tag = widget.get_active()
    widgets = hbox.get_children()
    hbox.remove(widgets[4])
    if tag:
      self.d['x1'] = ""
    else:
      self.d['x1'] = 0.
    x_hbox = self._get_x_hbox(Main)
    hbox.pack_start(x_hbox, False, False, 0)
    hbox.show_all()
    Main.set_is_changed()

  def add_end_point(self, widget, Main):
    """Ajoute ou supprime les widgets pour spécifier la fin de la charge"""
    hbox = self.hbox
    tag = widget.get_active()
    widgets = hbox.get_children()
    hbox.remove(widgets[4])
    if tag:
      self.d['x2'] = ""
    else:
      self.d['x2'] = 1.
    x_hbox = self._get_x_hbox(Main)
    hbox.pack_start(x_hbox, False, False, 0)
    hbox.show_all()
    Main.set_is_changed()

  def update_arc_type(self, widget, Main):
    """Changement du type de chargement pour une charge d'arc"""
    self.proj = int(widget.get_name()[4])
    hbox = self.hbox
    widgets = hbox.get_children()
    hbox.remove(widgets[0])
    image = Gtk.Image()
    image.set_from_file(self._get_img())
    hbox.pack_start(image, False, False, 0)
    hbox.reorder_child(image, 0)
    image.show()

    hbox.remove(widgets[3])
    q_hbox = self._get_q_hbox(Main)
    hbox.pack_start(q_hbox, False, False, 0)
    hbox.reorder_child(q_hbox, 3)
    hbox.show_all()
    Main.set_is_changed(True)

  def _get_img(self):
    """Retourne le path du fichier image"""
    if self.proj == 0:
      img = "glade/arc-char0.png"
    elif self.proj == 1:
      img = "glade/arc-char1.png"
    else:
      img = "glade/arc-char2.png"
    return img

  #def update_bars_combo(self, n, new):
  def update_bars_combo(self, n1, n2, n3, new):
    """Actualise le combo des barres suite à une modification du nom d'un arc"""
    combo = self.hbox.get_children()[2]
    function.change_elem_combo2(combo, n1, new)
    self.name = combo.get_active_text()


  def update_char(self, entry, Main):
    name = entry.get_name()
    try:
      val = float(entry.get_text().replace(",", "."))
    except ValueError:
      val = ""
    self.d[name] = val
    if self.unif:
      if name == 'q1x':
        self.d['q2x'] = val
      elif name == 'q1y':
        self.d['q2y'] = val
    Main.set_is_changed(True)

  def add_combo_arc_item(self, elem):
    """Ajoute un arc dans le combo des arcs"""
    combo = self.hbox.get_children()[2]
    combo.append_text(elem)

  def update_char_name(self, combo, Main):
    """Changement du combobox du choix des arcs"""
    self.name = combo.get_active_text()
    Main.set_is_changed(True)

  def update_tooltip_F(self, unit_L, unit_F):
    """Actualise les tooltips des forces suite à un changement d'unité pour un arc"""
    widgets = self.hbox.get_children()
    qhbox = widgets[3]
    childs = qhbox.get_children()
    if self.proj == 2:
      entry = childs[1]
      entry.set_tooltip_text('Charge en %s' % unit_F)
    else:
      entry = childs[1]
      entry.set_tooltip_text('Charge en %s' % unit_F)
      entry = childs[3]
      entry.set_tooltip_text('Charge en %s' % unit_F)

  def update_numeric_F(self, factor):
    """Actualise les valeurs numériques dans les champs de type entry après changement unité de force pour charge sur un arc"""
    widgets = self.hbox.get_children()
    qhbox = widgets[3]
    childs = qhbox.get_children()
    if self.proj == 2:
      entry = childs[1]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass
    else:
      entry = childs[1]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass
      entry = childs[3]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass

class Case(object):
  """Classe pour un cas de charge"""

  def __init__(self, name):
    self.name = name
    self.chars = []


class Combi(object):
  """Classe pour une combinaison de cas de charge"""

  class_counter = 0

  def __init__(self, name):
    self.id = AbstractNode.class_counter
    AbstractNode.class_counter += 1
    self.name = name

  def add_hbox(self, Main):
    """Crée la hbox d'un noeud simple de la page des noeuds"""
    eventbox = Gtk.EventBox()
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    self.hbox = hbox
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sélectionner')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    #entry.set_name('test')
    #entry.set_placeholder_text('Nom')
    #entry.set_width_chars(-1)
    entry.set_text(self.name)
    entry.set_tooltip_text(self.name)
    entry.connect("event", self.update_combi_name, Main)
    hbox.pack_start(entry, False, False, 0)
    self._add_coef(hbox, Main)
    eventbox.add(hbox)
    eventbox.show_all()
    eventbox.connect("event", self.onCMenu, Main)
    return eventbox


  def _add_coef(self, hbox, Main):
    """Retourne les hbox contenant les entry des coefs d'une combinaison"""
    cases = Main.data_editor.get_cases_name()
    for case in cases:
      if case in self.coef:
        coef = self.coef[case]
      else:
        coef = 0.
      #sep = Gtk.VSeparator()
      cell = Gtk.HBox(homogeneous=False, spacing=0)
      label = Gtk.Label(label=case)
      hbox.set_spacing(10)
      cell.pack_start(label, False, False, 0)
      label = Gtk.Label(label="=")
      cell.pack_start(label, False, False, 0)
      entry = Gtk.Entry() # max car
      entry.set_width_chars(5)
      entry.set_text(str(coef))
      entry.connect("changed", self.update_combi_coef, Main)
      cell.pack_start(entry, False, False, 0)
      hbox.pack_start(cell, False, False, 0)

  def update_combi_name(self, widget, event, Main):
    """Evènement lié à la modification du nom d'une combinaison
    Pas de solution simple trouvée pour connaitre la valeur du nom de la combi avant l'évènement donc on lit toute la page pour recréer le dictionnaire - à voir"""
    #if event.type == Gdk.EventType.EXPOSE:
    #  text = widget.get_text()
    #  layout = widget.get_layout()
    #  w, h = layout.get_pixel_size()
    #  w0, h0 = widget.size_request()
    #  if not w + 10 == w0:
    #    widget.set_size_request(w+10, 30)

    if event.type == Gdk.EventType.KEY_RELEASE:
    # Note : entry is modified after KEY_PRESS
    # attention au maJ + autre touche qui crée 2 KEY_RELEASE et 2 BUTTON_PRESS
      combi_name = widget.get_text().strip()
      if self.name == combi_name:
        return
      self.name = combi_name
      widget.set_tooltip_text(self.name)
      Main.show_combi_error(Main.data_editor.get_n_combis_by_name())
      Main.set_is_changed()

  def update_combi_coef(self, widget, Main):
    """Evènement lié au changement de la valeur d'un coef d'une combi"""
    coef = widget.get_text().strip()
    try:
      coef = float(coef.replace(",", "."))
    except ValueError:
      coef = 0.
    name = widget.get_parent().get_children()[0].get_text()
    self.coef[name] = coef
    Main.set_is_changed()


  def onCMenu(self, widget, event, Main):
    """Affiche le menu contextuel d'une combinaison"""
    if event.type == Gdk.EventType.ENTER_NOTIFY:
      Main.set_hover(widget)
    elif event.type == Gdk.EventType.MOTION_NOTIFY:
      return True
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        menu1 = Gtk.Menu()
        menuitem1 = Gtk.MenuItem(label="Dupliquer")
        menuitem1.connect("activate", self.on_duplicate, (Main, self))
        menu1.append(menuitem1)
        menuitem2 = Gtk.MenuItem(label="Supprimer")
        menuitem2.connect("activate", self.on_delete, (Main, self.id))
        menu1.append(menuitem2)
        menu1.show_all()
        menu1.popup_at_pointer(event)

        return True # bloque la propagation du signal
    return False

  def on_duplicate(self, widget, args):
    """Action de suppression d'une ligne depuis le CM"""
    Main, combi = args
    Main.on_paste_combinaison(combi)

  def on_delete(self, widget, args):
    """Action de suppression d'une ligne depuis le CM"""
    Main, id = args
    #Main.remove_combinaison
    box = Main.data_box['combi']
    items = Main.data_editor.combis
    for i, item in enumerate(items):
      if not item.id == id:
        continue
      box.remove(item.hbox.get_parent())
      del(items[i])
      break
    Main.show_short_help()
    Main.set_is_changed()


class DataEditor(object):
  """Classe pour les données rdm d'une étude"""

  def __init__(self, rdm, UP):
    #self.name = name
    self.name = rdm.GetStructName()
    self.path = rdm.GetStructPath()
    self.XMLNodes = rdm.XMLNodes
    self._set_attributes()
    self.set_data_editor(rdm, UP)
    if self.path is None:
      self.is_changed = True
    else:
      self.is_changed = False
    self.size_changed = False
    self.need_drawing = False

  def _set_attributes(self):
    """Inialise les variables"""
    self.nodes = []
    self.barres = []
    self.liaisons = []
    self.sections = []
    self.materials = []
    self.cases = []
    self.combis = []

  def set_data_editor(self, rdm, UP):
    """Initialise la structure des données à partir de xml, rdm et UP"""
    self.G = str(rdm.GetG(UP))
    self.conv = rdm.GetConv(UP)
    self.unit_conv = rdm.GetUnits(UP)
    isSI = self.unit_conv['F'] in [1., 10., 1000.] # provisoire
    self.unit_si = isSI
    self.add_nodes(self._get_xml_nodes())
    self.add_barres()
    self.add_liaisons( self.get_xml_liaisons())
    self.add_sections(self._get_xml_sections())
    self.add_materials(self._get_xml_materials())
    self.add_cases()
    self.get_barres_by_node()
    try:
      combis = rdm.GetCombi()
    except AttributeError:
      combis = {}
    self.add_combis(combis)

  def set_data_editor2(self):
    """Initialise une partie de la structure des données à partir du xml"""
    self._set_attributes()
    self.add_nodes(self._get_xml_nodes())
    self.add_barres()
    self.add_liaisons(self.get_xml_liaisons())
    self.add_sections(self._get_xml_sections())
    self.add_materials(self._get_xml_materials())
    self.add_cases()
    self.get_barres_by_node()
    combis = self._get_combis_from_xml()
    self.add_combis(combis)

  def _get_combis_from_xml(self):
    """Retourne le dictionnaire des combinaisons"""
    #print "_get_combis_from_xml"
    cases = self.get_cases_name()
    nbCas = len(cases)
    diCombi = {}
    li_node = self.XMLNodes["combinaison"].iter('combinaison')
    for combi in li_node:
      name = combi.get("id")
      content = combi.get("d")
      if content is None:
        continue
      content = content.split(",")
      if not len(content) == nbCas:
        continue
      i = 0
      di = {}
      for coef in content:
        try: # a revoir
          di[cases[i]] = float(coef)
        except (KeyError, ValueError):
          #exception levée si tous les cas de charges sont supprimés
          di[cases[i]] = 0.
        i += 1
      diCombi[name] = di
    return diCombi

  def ini_xml(self):
    """Initialise la structure xml des données"""
    string = Const.XML % (Const.SITE_URL, Const.VERSION)
    self.XML = ET.ElementTree(ET.fromstring(string))
    self.XMLNodes = list(self.XML.iter('elem'))
    self._make_xml_cases()

  def get_units(self):
    """Retourne le jeu d'unités"""
    if self.unit_si:
      return Const.UNITS
    return Const.UNITS2

# inutile
  def set_imperial_unit(self):
    units = Const.UNITS2
    di = {}
    for key, val in units.items():
      di[key] = val.values()[0]
    self.unit_conv = di

  def get_new_name(self, element):
    """Retourne un nom pour un nouveau noeud"""
    def get_name(name, nodes):
      for elem in nodes:
        if elem.name == name:
          return False
      return True

    if element == "node":
      prefix = "N"
      elements = self.nodes
    elif element == "bar":
      prefix = "B"
      elements = self.barres
    elif element == "arc":
      prefix = "Arc"
      elements = self.barres
    elif element == "para":
      prefix = "Parabole"
      elements = self.barres
    else:
      print("debug get_new_name")
      return ""
    n = len(elements)
    if n == 0:
      return "%s1" % prefix
    name = "%s%s" % (prefix, (n+1))
    while not get_name(name, elements):
      n = n+1
      name = "%s%s" % (prefix, (n+1))
    return name

  def _get_xml_nodes(self):
    """Retourne un tuple des noeuds de type (["N2"], ["@N1,x1,y1"])
    pour l'éditeur des données
    Attention, pas de dictionnaire pour conserver l'ordre des points"""
    XML = self.XMLNodes
    if XML is None:
      content = {}
      content["id"] = "N1"
      content["d"] = "0,0"
      content["rel"] = "0"
      content["type"] = "node"
      return [content]
    XML = XML['node']
    xml_nodes = []
    for node in XML.iter(): # tous les noeuds, y compris le noeud lui-meme en premier !!
      if node.tag == 'elem':
        continue
      xml_nodes.append(node)
    li = []
    contents1, contents2 = {}, {}
    for node in xml_nodes:
      id = node.get("id")
      tag = node.tag
      content = {}
      content["id"] = node.get("id")
      content["d"] = node.get("d")
      content["rel"] = node.get("r")
      content["type"] = tag
      l = node.get('liaison')
      if not l is None: content["liaison"] = l
      if tag == 'node':
        pass
      elif tag == 'arc':
        content["name"] = node.get("name")
        content["pos_on_curve"] = node.get("pos_on_curve")
      li.append(content)
    return li

  def add_node(self, data):
    """Ajoute une instance de la classe Node"""
    #print(data)
    content = data['d']
    name = data['id']
    node = Node(name, data)
    coors = function.Str2NodeCoors2(node, self.nodes)
    if coors:
      node.x, node.y = coors[0], coors[1]
    return node

  def add_arc_node(self, data):
    """Ajoute une instance de la classe Node"""
    node = ArcNode(data)
    return node

  def add_nodes(self, li):
    """Ajoute des instances de la classe Node dans une liste nodes"""
    for elem in li:
      tag = elem['type']
      if tag == 'node':
        node = self.add_node(elem)
      elif tag == 'arc':
        node = self.add_arc_node(elem)
      self.nodes.append(node)


  def get_node(self, node_name):
    """Retourne l'instance du noeud dont le nom est donné"""
    nodes = [val.name for val in self.nodes]
    try:
      ind = nodes.index(node_name)
    except ValueError:
      return None
    return self.nodes[ind]

# supprimer et utiliser les id
  def get_all_nodes(self):
    """Retourne la liste de tous les noms des noeuds"""
    return [val.name for val in self.nodes if val.name]



  def set_xml_units(self):
    """Crée le contenu xml pour les unités"""
    for elem in self.unit_conv:
      node = ET.SubElement(self.XMLNodes[6], "unit", {"id": elem})
      node.set("d", str(self.unit_conv[elem]))
    node = ET.SubElement(self.XMLNodes[6], "const", {"name":"g", "value" : self.G})
    node = ET.SubElement(self.XMLNodes[6], "const", {"name":"conv", "value": str(self.conv)})

  def set_xml_nodes(self):
    """Crée le contenu xml pour les noeuds"""
    for inst in self.nodes:
      node = inst.set_xml(self.XMLNodes[0])

  def set_xml_barres(self):
    """Crée le contenu xml pour les barres"""
    for inst in self.barres:
      node = inst.set_xml(self.XMLNodes[1])

  def add_liaison(self, data):
    """Ajoute une instance de la classe Liaison"""
    content = data['d']
    name = data['id']
    liaison = Liaison(name, content)
    return liaison

  def set_xml_materials(self):
    """Crée le contenu xml pour les matériaux"""
    for elem in self.materials:
      node = ET.SubElement(self.XMLNodes[3], "barre", {"id": elem.name})
      E = elem.E
      node.set("young", E)
      try:
        node.set("profil", elem.profil)
      except AttributeError:
        pass
      try:
        node.set("mv", elem.m)
      except AttributeError:
        pass
      try:
        node.set("alpha", elem.a)
      except AttributeError:
        pass

  def set_xml_chars(self):
    """Crée le contenu xml pour les cas de charges et chargements"""
    XMLChars = list(self.XMLNodes[4].iter('case'))
    for i, case in enumerate(self.cases):
      parent = XMLChars[i]
      chars = case.chars
      for char in chars:
        char.set_xml_content(parent)


  def _make_xml_cases(self):
    """Crée les noeuds "cas de charge" dans l'arbre xml"""
    cases = self.get_cases_name()
    for cas in cases:
      node = ET.SubElement(self.XMLNodes[4], "case", {"id": cas})

  def set_xml_combis(self):
    """Crée le contenu xml pour les combinaisons"""
    cases = self.get_cases_name()
    for elem in self.combis:
      name = elem.name
      coefs = []
      for case in cases: # attention à l'ordre des coefs qui sont dans un di
        coefs.append(str(elem.coef[case]))
      coefs = ",".join(coefs)
      node = ET.SubElement(self.XMLNodes[5], "combinaison", {"id": name})
      node.set("d", coefs)

  # Barres

  def add_segment(self, di):
    """Ajoute une instance de la classe Barre"""
    bar = Barre(di, self.nodes)
    self.barres.append(bar)
    return bar

  def _get_xml_segment(self, node):
    """Retourne le nom et le contenu d'un segment"""
    name = node.get("id")
    di = {"name": name}
    content = node.get("d")
    if not content is None:
      di.update(self._get_xml_segment2dot3(content))
      return di
    start = node.get("start")
    di['start'] = start
    end = node.get("end")
    di['end'] = end
    r0 = node.get("r0")
    r1 = node.get("r1")
    try:
      r0 = int(r0)
    except (ValueError, TypeError):
      r0 = 0
    try:
      r1 = int(r1)
    except (ValueError, TypeError):
      r1 = 0
    di['r0'] = r0
    di['r1'] = r1
    k0 = node.get("k0")
    try:
      float(k0)
      di['k0'] = k0
    except (ValueError, TypeError):
      pass
    k1 = node.get("k1")
    try:
      float(k1)
      di['k1'] = k1
    except (ValueError, TypeError):
      pass
    mode = node.get("mode")
    if mode is None:
      di['mode'] = 0
    else:
      try:
        mode = int(mode)
        if not mode in [-1, 0, 1]:
          raise ValueError
      except ValueError:
        mode = 0
      di['mode'] = mode
    return di

  def _get_xml_segment2dot3(self, content):
    """Compatibilité version 2.3"""
    content = content.split(',')
    di = {"start": content[0], "end": content[1], "r0": int(content[2]), "r1": int(content[3])}
    return di

  def _get_xml_arc(self, node):
    """Retourne le nom et le contenu d'un arc"""
    name = node.get("id")
    N0 = node.get("start")
    N1 = node.get("end")
    c = node.get("center")
    try:
      R0 = int(node.get("r0"))
    except (TypeError, ValueError):
      R0 = 0
    try:
      R1 = int(node.get("r1"))
    except (TypeError, ValueError):
      R1 = 0
    return {'name': name, 'N0': N0, 'N1': N1, 'c': c, 'R0': R0, 'R1': R1}

  def _get_xml_mbarre(self, node):
    """Retourne le nom et le contenu d'une mbarre"""
    name = node.get("id")
    N0 = node.get("start")
    N1 = node.get("end")
    try:
      R0 = int(node.get("r0"))
    except (TypeError, ValueError):
      R0 = 0
    try:
      R1 = int(node.get("r1"))
    except (TypeError, ValueError):
      R1 = 0
    return {'name': name, 'N0': N0, 'N1': N1, 'R0': R0, 'R1': R1}

  def add_arc(self, content):
    """Crée une instance de la classe Arc"""
    obj = Arc(content, self)
    self.barres.append(obj)
    return obj


  def _get_xml_parabola(self, node):
    """Retourne le nom et le contenu d'une parabole"""
    name = node.get("id")
    N0 = node.get("start")
    N1 = node.get("end")
    f = node.get("f")
    try:
      R0 = int(node.get("r0"))
    except (TypeError, ValueError):
      R0 = 0
    try:
      R1 = int(node.get("r1"))
    except (TypeError, ValueError):
      R1 = 0
    return {'name': name, 'N0': N0, 'N1': N1, 'f': f, 'R0': R0, 'R1': R1}

  def add_parabolum(self, di):
    """Crée une instance de la classe Parabola"""
    obj = Parabola(di, self)
    self.barres.append(obj)
    return obj

  def add_mbarre(self, content):
    """Crée une instance de la classe MBarre"""
    obj = MBarre(content, self)
    self.barres.append(obj)
    return obj


  def add_barres(self):
    """Initialise toutes les segments et arcs à partir des données xml"""
    XML = self.XMLNodes
    if XML is None:
      return {}
    for node in XML['barre'].iter():
      if node.tag == 'elem':
        continue
      tag = node.tag
      if tag == 'barre':
        self.add_segment(self._get_xml_segment(node))
      elif tag == 'mbarre':
        self.add_mbarre(self._get_xml_mbarre(node))
      elif tag == 'arc':
        self.add_arc(self._get_xml_arc(node))
      elif tag == 'parabola':
        self.add_parabolum(self._get_xml_parabola(node))
      else:
        print("Unexpected tag %s in add_barres" % tag)


  def get_barre_pos(self, barre, tag="all"):
    """Retourne la position de la barre dans l'onglet des barres (arc et barre confondus)"""
    if tag == 'all':
      barres = [val.name for val in self.barres]
    elif tag == 'arc':
      barres = self.get_arcs()
    elif tag == 'bar':
      barres = self.get_barres()
    else:
      print('debug in get_barre_pos')
    name = barre.name
    if not name in barres:
      return -1
    return barres.index(name)

  def get_barre(self, name):
    """Retourne l'instance dont le nom est donné"""
    barres = [val.name for val in self.barres]
    try:
      ind = barres.index(name)
    except ValueError:
      return None
    return self.barres[ind]

  def get_barres(self):
    """Retourne la liste des noms des barres"""
    li = []
    for barre in self.barres:
      if barre.get_is_arc():
        continue
      li.append(barre.name)
    return li

  def get_all_barres(self):
    """Retourne la liste de toutes les barres, y compris arcs"""
    li = []
    for barre in self.barres:
      li.append(barre.name)
    return li


  def get_arcs(self):
    """Retourne la liste des noms des arcs"""
    li = []
    for barre in self.barres:
      if not barre.get_is_arc():
        continue
      li.append(barre.name)
    return li

  def get_arcs2(self, pos=None):
    """Retourne la liste des noms des arcs et des mbarre"""
    li = []
    if pos is None:
      pos = len(self.barres)
    for i, barre in enumerate(self.barres):
      if isinstance(barre, Barre):
        continue
      if i > pos:
        break
      li.append(barre.name)
    return li

# optimisation: tester iteration sur instances classes
  def set_char_bar_size(self):
    """Modifie l'attribut l des chargements suite à un changement de longueur de la barre"""
    for case in self.cases:
      for char in case.chars:
        char.set_barre_length(self)

  def set_bars_size(self):
    """Calcule la longueur des barres dans l'attribut barres
    Ajoute ou modifie"""
    #print "Editor::set_bars_size"
    barres = self.barres
    for barre in barres:
      barre.set_length(self.nodes)

  def _update_barres_by_node(self, old_name, new_name):
    """Met à jour le dictionnaire des barres par noeud en cas de changement de nom d'une barre"""
    nodes = self.barres_by_node
    for node in nodes:
      barres = nodes[node]
      for i, barre in enumerate(barres):
        if barre == old_name:
          barres[i] = new_name

  def get_barres_by_node(self):
    """Crée un attribut barres_by_nodes contenant un dictionnaire des noms des barres ayant pour extrémité le noeud - {N1: [B1, B2] ...}
    A voir: Peut contenir 2 fois la même barre (choisi en origine et fin!!)
    Barre comptée même si seule l'origine ou la fin définie"""
    nodes = self.get_all_nodes()
    di = {}
    barres = self.barres
    for barre in barres:
      name = barre.name
      N0 = barre.N0
      N1 = barre.N1
      if N0 == "" or N1 == "":
        continue
      if N0 in di:
        di[N0].append(name)
      else:
        di[N0] = [name]
      N1 = barre.N1
      if N1 in di:
        di[N1].append(name)
      else:
        di[N1] = [name]
    self.barres_by_node = di

  def del_barres_by_node(self, name):
    try:
      del(self.barres_by_node[name])
    except KeyError:
      pass

  def get_xml_liaisons(self):
    """Retourne un  dictionnaire des éléments pour les liaison"""
    XML = self.XMLNodes
    if XML is None:
      return {}, {}
    di1 = {}
    nodes = XML["node"].iter()
    for node in nodes:
      name = node.get("id")
      content = node.get("liaison")
      if not content is None:
        content = content.split(",")
        di1[name] = content
    return di1

  def add_liaisons(self, di):
    """Ajoute des propriétés pour les liaisons"""
    for name in di:
      l = di[name]
      try:
        value = int(l[0])
      except ValueError:
        continue
      liaison = self.add_liaison({'id': name, 'd' : l})
      self.liaisons.append(liaison)

  def set_liaisons(self):
    """Actualise toutes les liaisons des objets Node à partir de la lecture des combobox de la page des liaisons"""
    for node in self.nodes:
      try:
        del(node.liaison)
      except AttributeError:
        pass
    for liaison in self.liaisons:
      liaison.set_content(self)


  # Sections

  def get_section(self, name):
    """Retourne l'instance du noeud dont le nom est donné"""
    sections = [val.name for val in self.sections]
    ind = sections.index(name)
    return self.sections[ind]

  def get_sections(self):
    """Retourne la liste des noms des barres"""
    li = []
    for section in self.sections:
      li.append(section.name)
    return li


  def set_xml_sections(self):
    """Crée le contenu xml pour les sections"""
    for elem in self.sections:
      node = ET.SubElement(self.XMLNodes[2], "barre", {"id": elem.name})
      try:
        node.set("profil", elem.profil)
      except AttributeError:
        pass
      try:
        node.set("file", elem.file)
      except AttributeError:
        pass
      value = elem.s
      node.set("s", value)
      value = elem.i
      node.set("igz", value)
      try:
        value = elem.h
        node.set("h", value)
      except AttributeError:
        pass
      try:
        value = elem.v
        node.set("v", value)
      except AttributeError:
        pass


  def _get_xml_sections(self):
    """Retourne un dictionnaire
    contenant les dictionnaires des caractéristiques des barres
    à afficher dans l'éditeur"""
    XML = self.XMLNodes
    if XML is None:
      return [{'name': '', 's': '', 'igz': '', 'profil': '', 'h': '', 'v': ''}]

    nodes = XML['geo'].iter('barre')
    li = []
    for node in nodes:
      name = node.get("id")
      di = {'name': name}
      profil = node.get("profil")
      if not profil is None:
        di["profil"] = profil
      f = node.get("file")
      if not f is None:
        if os.path.isfile(f):
          di["file"] = f
      s = node.get("s")
      if not s is None:
        di["s"] = s
      i = node.get("igz")
      if not i is None:
        di["i"] = i
      h = node.get("h")
      if not h is None:
        di['h'] = h
      v = node.get("v")
      if not v is None:
        di['v'] = v
      li.append(di)
    return li

  def add_section(self, content):
    """Crée une instance de la classe Section"""
    return Section(content)

  def add_sections(self, li):
    """Ajoute des instances de la classe Section dans une liste sections"""
    for elem in li:
      section = self.add_section(elem)
      self.sections.append(section)

  # Materials
  def _get_xml_materials(self):
    """Retourne une liste contenant 3 dictionnaires pour young, mv, alpha
    à afficher dans l'éditeur"""
    XML = self.XMLNodes
    if XML is None:
      return [{'name': '', 'profil': '', 'E': '', 'm': '', 'a': ''}]
    li = []
    nodes = self.XMLNodes["material"].iter('barre')
    for node in nodes:
      name = node.get("id")
      if name is None:
        continue
      di = {'name': name}
      profil = node.get("profil")
      if not profil is None:
        di["profil"] = profil
      young = node.get("young")
      if not young is None:
        di["E"] = young
      mv = node.get("mv")
      if not mv is None:
        di["m"] = mv
      alpha = node.get("alpha")
      if not alpha is None:
        di['a'] = alpha
      li.append(di)
    return li


  def add_material(self, di):
    mat = Material(di['name'])
    E = di['E']
    if len(E) >= 3 and E[-2:] == ".0":
      E = E[:-2]
    mat.E = E
    try:
      mat.profil = di['profil']
    except KeyError:
      pass
    try:
      m = di['m']
      if len(m) >= 3 and m[-2:] == ".0":
        m = m[:-2]
      mat.m = m
    except KeyError:
      pass
    try:
      mat.a = di['a']
    except KeyError:
      pass
    return mat

  def add_materials(self, li):
    """Ajoute des instances de la classe Material dans une liste materials"""
    for di in li:
      mat = self.add_material(di)
      self.materials.append(mat)


  # Case
  def _get_xml_case(self):
    """retourne une liste contenant les chaines de caractères
    pour tous les chargements (nodal, barre fp, barre qu et therm, ....)
    à afficher dans l'éditeur"""
    # un dictionnaire ne peut convenir car plusieurs charges par barre
    XML = self.XMLNodes
    cas = Const.DEFAULT_CASE
    if XML is None:
      return {cas: [CharPp(False)]}, [cas]
    n = len(XML["char"].findall('case'))
    if n == 0:
      return {cas: [CharPp(False)]}, [cas]
    data = {}
    cases = []
    # recherche du poids propre
    status = False
    first_case_name = XML["char"].find('case').get("id")
    pp = XML["char"].find('case').find('pp')
    if 'd' in pp.keys():
      status = pp.get("d")
    if status:
      if status == 'true':
        status = True
      else:
        status = False
    else:
      status = False
    data[first_case_name] = [CharPp(status)]

    i = 0
    for case in  XML["char"].iter('case'):
      name = case.get("id")
      cases.append(name)
      if not name in data:
        data[name] = []
      for char in case.iter():
        if char.tag == 'node':
          data[name].append(CharNo(char.get("id"), char.get("d")))
        elif char.tag == 'depi':
          data[name].append(CharDepi(char.get("id"), char.get("d")))
        elif char.tag == 'barre':
          content = char.get("qu")
          if not content is None:
            data[name].append(CharQu(char.get("id"), content))
            continue
          content = char.get("fp")
          if not content is None:
            data[name].append(CharFp(char.get("id"), content))
            continue
          content = char.get("therm")
          if not content is None:
            data[name].append(CharTh(char.get("id"), content))
            continue
          content = char.get("tri")
          if not content is None:
            data[name].append(CharTr(char.get("id"), content))
            continue
        elif char.tag == 'arc':
          content = char.get("qu")
          if not content is None:
            proj = char.get("proj")
            data[name].append(CharArc(char.get("id"), content, proj))
            continue
          content = char.get("fp")
          if not content is None:
            data[name].append(CharFp(char.get("id"), content, type='arc'))
            continue
      i += 1
    return data, cases # en attendant dictionnaires ordonnés

  def add_cases(self):
    """Ajoute des instances de la classe Case dans une liste cases"""
    data, cases = self._get_xml_case()
    for case_name in cases:
      case = Case(case_name)
      case.chars.extend(data[case_name])
      self.cases.append(case)

  def get_cases_name(self):
    """Retourne la liste des noms des cas"""
    return [e.name for e in self.cases]

  def remove_case(self, name):
    """Supprime un cas de charge"""
    for i, case in enumerate(self.cases):
      if case.name == name:
        del(self.cases[i])
        break

  # Combinaisons

  def add_combi(self, name, coefs=None):
    """Ajoute une combinaison dans le dictionnaire des combinaisons"""
    combi = Combi(name)
    if coefs is None:
      di = {}
      for case in self.cases:
        di[case.name] = 0.
      combi.coef = di
    else:
      combi.coef = coefs
    self.combis.append(combi)
    return combi

  def add_combis(self, di):
    """Ajoute les combinaisons dans la liste des instances de Combi"""
    # tri par nom
    names = list(di.keys())
    names.sort()
    for name in names:
      combi = Combi(name)
      combi.coef = di[name]
      self.combis.append(combi)

  def get_combi(self, name):
    """Retourne la combi dont le nom est donné"""
    combis = [val.name for val in self.combis]
    ind = combis.index(name)
    return self.combis[ind]

  def get_combis_name(self):
    """Retourne une liste des noms des combinaisons"""
    combis = self.combis
    combis = [e.name for e in combis]
    #combis.sort()
    return combis

  def get_cases(self):
    """Retourne la liste des noms des cas"""
    return self.get_cases_name()

# revoir cette fonction !!!
#  def get_combis(self):
#    """Retourne la liste des noms des combis et des cas"""
#    return self.get_combis_name()

  def add_case_in_combis(self, name):
    """Ajoute un cas dans le dictionnaire des combinaisons avec un coefficient nul par défaut"""
    combis = self.combis
    for combi in combis:
      combi.coef[name] = 0.

  def remove_combi(self, name):
    """Supprime une combinaison par nom"""
    for i, combi in enumerate(self.combis):
      if combi.name == name:
        del(self.combis[i])


  def del_case_in_combis(self, name):
    """Supprime un cas dans le dictionnaire des combinaisons"""
    combis = self.combis
    for combi in combis:
      del(combi.coef[name])

  def rename_case_in_combis(self, old_name, new_name):
    """Renomme un cas dans le dictionnaire des combinaisons"""
    if old_name == new_name:
      return
    combis = self.combis
    for combi in combis:
      combi.coef[new_name] = combi.coef[old_name]
      del(combi.coef[old_name])

  def get_n_combis_by_name(self):
    """Retourne un dictionnaire ayant pour clé les noms des combi et pour valeurs le nombre d'occurences rencontrées"""
    di = {}
    combis = self.get_combis_name()
    for name in combis:
      di[name] = di.get(name, 0) + 1
    return di

# inutilisée mais fonctionne
  def rename_combi(self, old_name, new_name):
    """Renomme une combi dans le dictionnaire des combinaisons"""
    combis = self.combis
    combis_name = self.get_combis_name()
    if new_name in combis_name:
      return False
    combis[new_name] = combis[old_name]
    del(combis[old_name])
    return True

  def save_study(self, status):
    """Sauve les études ayant été modifiées"""
    path = self.path
    if path is None:
      return False
    # plateforme
    #if sys.platform == 'win32':
    #  path = path.decode('utf-8')
    if not status == -1:
      self.set_xml_structure()
    root = self.XML.getroot() # keep
    function.indent(root) # keep
    #print ET.tostring(root)

    try:
      self.XML.write(path, encoding="UTF-8", xml_declaration=True)
    except IOError:
      print("Ecriture impossible dans %s" % path)
    return True

  def set_xml_structure(self):
    """Crée la structure xml des données à partir des données de l'éditeur"""
    self.ini_xml()
    self.set_xml_units()
    # Noeuds
    self.set_xml_nodes()
    # Barres
    self.set_xml_barres()
    # Section , Igz
    self.set_xml_sections()
    self.set_xml_materials()
    self.set_xml_chars()
    self.set_xml_combis()

  def get_xml(self):
    """Retourne la structure XML de l'étude"""
    try:
      return self.XML
    except AttributeError: # pas encore calculé (pas de modification dans data)
      self.set_xml_structure()
    return self.XML


  def print_node(self):
    for node in self.nodes:
      print("*****")
      try:
        print("\tNom : ", node.name)
      except AttributeError:
        pass
      try:
        print("\t(x,y) : %f %f" % (node.x, node.y))
      except AttributeError:
        pass
      if hasattr(node, 'x'):
        assert type(node.x) is type(0.)
      try:
        print("\tentry : ", node.s_x, node.s_y)
        print("\trelatif= : ", node.rel)
        print("\tpolaire= : ", node.pol)

      except AttributeError:
        pass
      if hasattr(node, 's'):
        assert type(node.s) is type("s") or type(node.s) is type("s")
      try:
        print("\tLiaison : %s finir" % node.liaison[0])
      except AttributeError:
        pass
      if hasattr(node, 'l'):
        assert type(node.liaison) is type([])
        for val in node.liaison:
          assert type(val) is type("") or  type(val) is type("")

      try:
        print("\tkz : %s %s" % (node.kz[0], node.kz[1]))
        assert type(node.kz[1]) is type("s") or type(node.kz[1]) is type("s")
      except AttributeError:
        pass

  def print_barres(self):
    for barre in self.barres:
      print("\tBarre : %s de %s à %s" % (barre.name, barre.N0, barre.N1))
      print("\t\tL = %s, R0 = %d, R1 = %d" % (barre.l, barre.R0, barre.R1))
    print("Affichage des barres par noeud")
    for node in self.barres_by_node:
      print("\tNoeud:", node, self.barres_by_node[node])

  def print_combis_and_cases(self):
    print("Liste des cas :")
    for case in self.cases:
      print("\t%s" % case.name)
    print("Dictionnaire des combinaisons :")
    for combi in self.combis:
      print("\t", combi.name, combi.coef)

  def print_sections(self):
    print("Affichage des sections")
    for section in self.sections:
      print("\tSection : %s Profil: %s S=%s I=%s" % (section.name, section.p, section.s, section.i))
      if hasattr(section, "h"):
        print("\tH=%s" % section.h)
      if hasattr(section, "v"):
        print("\tv=%s" % section.v)


class Editor(object):
  """Classe unique pour l'éditeur des données"""

  def __init__(self, study, w1app):
    #print "Editor::__init"
    self.w1app = w1app
    self.xml_status = 0
    self.id_handler_list = {}

    builder = self.builder = Gtk.Builder()
    builder.add_from_file("glade/editor.glade")
    self.w2 = builder.get_object("window2")
    builder.connect_signals(self)
    self.book = builder.get_object("book1")
    self.toolbar = builder.get_object("toolbar1")
    self._ini_window()
    self.w2.show()
    self.selected = None # attribut contenant un widget sélectionné
    self.cm_popup = False # attribut d'ouverture d'un popup
    self.rename_tab_tag = None

    self.w2_label = builder.get_object("w2_label")
    self.ini_box_dict()
    self._ini_di_methode()
    self.handler_id = {}
    #--------------------
    self.data_editors = {}
    rdm = study.rdm
    self.data_editor = DataEditor(rdm, self.UP)
    self.data_editors = {study.id: self.data_editor}
    self.unit_si = self.data_editor.unit_si
    # attention, les combo ne doivent être connectés qu'une seule fois
    # car ils ne sont pas effacés
    self._ini_units_page()
    self.update_window()
    self.update_editor_title()
    self.book_status = 0
    self._set_toolbar()
    self.book.connect("switch_page", self._on_switch_page)
    self.record_button = builder.get_object("w2_save")
    self.record_button.connect("clicked", w1app.update_from_editor)
    #self.has_updates = False

  def print_message(self, text):
    """Affiche les messages en bas de la fenetre"""
    #print "print_message", text
    label = self.w2_label
    label.set_text(text)

  def popup_event(self, widget, event):
    """Evenement depuis un menu popup"""
    selected = self.selected
    if event.type == Gdk.EventType.BUTTON_PRESS:
      self.cm_popup = False
      selected.override_background_color(Gtk.StateType.NORMAL, None)
    elif event.type == Gdk.EventType.KEY_PRESS:
      key = Gdk.keyval_name (event.keyval)
      if key == "Escape":
        self.cm_popup = False
        selected.override_background_color(Gtk.StateType.NORMAL, None)
      elif key == "Return":
        self.cm_popup = False
        selected.override_background_color(Gtk.StateType.NORMAL, None)

  def set_hover(self, eventbox):
    """Survol d'une hbox"""
    s_old = self.selected
    if self.cm_popup:
      return
    context = eventbox.get_style_context()
    context.add_class("css_hover")
    if not s_old is None and not s_old is eventbox:
      context = s_old.get_style_context()
      context.remove_class("css_hover")
    self.selected = eventbox


  def on_w2_add(self, widget):
    """Action liée au bouton d'ajout"""
    if self.xml_status == -1:
      self._xml_exit()
      return
    n_page = self.book.get_current_page()
    if n_page == 3:
      self.on_add_liaison()
    elif n_page == 4:
      self.on_add_section()
    elif n_page == 5:
      self.on_add_material()
    elif n_page == 7:
      self.on_add_combinaison()

  def on_w2_remove(self, widget):
    """Action liée au bouton de suppression"""
    if self.xml_status == -1:
      return
    n_page = self.book.get_current_page()
    if n_page == 1:
      self.remove_nodes()
    elif n_page == 2:
      self.remove_barres()
    elif n_page == 3:
      self.remove_liaisons()
    elif n_page == 4:
      self.remove_sections()
    elif n_page == 5:
      self.remove_materials()
    elif n_page == 6:
      self.remove_chars()
    elif n_page == 7:
      self.remove_combinaisons()

  def _xml_exit(self):
    """Quitte le mode xml sans actualisation"""
    print('_xml_exit')
    vbox = self.w2.get_children()[0]
    childs = vbox.get_children()
    sw = childs[1]
    vbox.remove(sw)
    vbox.pack_start(self.book, True, True, 0)
    vbox.reorder_child(self.book, 1)
    self.xml_status = 0
    self.update_window()
    self._set_toolbar()

  def on_w2_xml(self, widget):
    """Basculement en mode xml ou normal"""
    #print ("on_w2_xml")
    vbox = self.w2.get_children()[0]
    childs = vbox.get_children()
    if isinstance(childs[1], Gtk.Notebook):
      vbox.remove(self.book)
      sw = self._get_xml_window()
      vbox.pack_start(sw, True, True, 0)
      vbox.reorder_child(sw, 1)
      self.xml_status = -1
    else:
      sw = childs[1]
      textview = sw.get_children()[0]
      textbuffer = textview.get_buffer()
      start = textbuffer.get_start_iter()
      end = textbuffer.get_end_iter()
      xml = textbuffer.get_text(start, end, False)
      try:
        xml = ET.ElementTree(ET.fromstring(xml))
      except:
        print("Erreur dans le xml")
        return
      XMLNodes = {}
      childs = xml.iter('elem')
      for child in childs:
        name = child.get("id")
        XMLNodes[name] = child
      self.data_editor.XMLNodes = XMLNodes
      try:
        self.data_editor.set_data_editor2()
      except:
        print("Erreur dans le xml")
        return
      vbox.remove(sw)
      vbox.pack_start(self.book, True, True, 0)
      vbox.reorder_child(self.book, 1)
      self.xml_status = 0
      self.update_window()
    self._set_toolbar()

  def _set_toolbar(self):
    """Actualise la barre d'outils principales"""
    mode = self.xml_status
    status = self.book_status
    add_b = self.toolbar.get_nth_item(4)
    remove_b = self.toolbar.get_nth_item(5)
    if self.xml_status == -1:
      add_b.set_sensitive(True)
      add_b.set_icon_name('list-remove')
      add_b.set_tooltip_text("Abandonner les modifications XML")
      remove_b.hide()
    else:
      add_b.set_icon_name('list-add')
      add_b.set_tooltip_text("Ajouter un élément")
      remove_b.show()
      if status == 0:
        add_b.set_sensitive(False)
        remove_b.set_sensitive(False)
      elif status == 1:
        add_b.set_sensitive(False)
        remove_b.set_sensitive(True)
        self.set_node_toolbar()
      elif status in [3, 4, 5, 7]:
        add_b.set_sensitive(True)
        remove_b.set_sensitive(True)
      elif status in [2, 6]:
        add_b.set_sensitive(False)
        remove_b.set_sensitive(True)

  def set_node_toolbar(self, tag=None):
    """Actualise la barre d'outils de l'onglet des noeuds"""
    box = self.book.get_nth_page(1)
    toolbar = box.get_children()[0]
    arc_b = toolbar.get_children()[1]
    if tag is None:
      arcs = self.data_editor.get_arcs2()
      if len(arcs) == 0:
        tag = False
      else:
        tag = True
    arc_b.set_sensitive(tag)

  def _get_xml_window(self):
    """Retourne la sw contenant le textview des données xml"""
    textview = Gtk.TextView()
    textview.set_left_margin(10)
    textview.set_pixels_above_lines(5)
    textbuffer = textview.get_buffer()
    self.data_editor.set_xml_structure()
    root = self.data_editor.XML.getroot()
    function.indent(root)
    text = ET.tostring(root).decode()
    textbuffer.set_text(text)
    textview.set_buffer(textbuffer)
    textbuffer.connect('changed', self._on_xml_changed)
    sw = Gtk.ScrolledWindow()
    sw.add(textview)
    sw.show_all()
    return sw

  def _on_xml_changed(self, buffer):
    """Changement du contenu du textview pour le xml"""
    #print ("_on_xml_changed", buffer)
    start = buffer.get_start_iter()
    end = buffer.get_end_iter()
    text = buffer.get_text(start, end, True).replace('\n', '').replace('\t', '')
    message = ""
    try:
      self.data_editor.XML = ET.ElementTree(ET.fromstring(text))
    except:
      message = "Attention: données xml non valides"
    #root = self.data_editor.XML.getroot()
    #print ET.tostring(root)
    self.print_message(message)
    self.set_is_changed(True)
    self.data_editor.size_changed = True


  def _ini_window(self):
    self.UP = classPrefs.UserPrefs()
    try:
      self._w, self._h = self.UP.get_w2_size()
    except:
      self._w, self._h = 500, 500
    self.w2.resize(self._w, self._h)

  def on_w2_configure(self, widget, event):
    """Gère les évènements correspondant au redimensionnement de la fenetre"""
    #print "Editor::_configure_event"
    size = self.w2.get_size()
    self._w = size[0]
    self._h = size[1]

  def new_page_editor(self, study):
    """Actualise l'éditeur de données pour la nouvelle étude"""
    id = study.id
    rdm = study.rdm
    #print "new_page_editor", rdm.name
    try:
      self.data_editor = self.data_editors[id]
      self.data_editor.name = rdm.GetStructName()
    except KeyError:
      self.data_editor = DataEditor(rdm, self.UP)
      self.data_editors[id] = self.data_editor
    self.id_handler_list = {}
    self.rename_tab_tag = None
    self.update_window()
    self.update_editor_title(self.data_editor.is_changed)

  def update_window(self):
    """Met à jour immédiatement l'onglet actif et an arrière plan les autres onglets"""
    def BG_update(current_page):
      for page in self._fct:
        #sleep(3)
        if current_page == page:
          continue
        self._fct[page]()

# les données sont perdues en mode xml quand on passe d'une étude à l'autre
    if self.xml_status == -1:
      vbox = self.w2.get_children()[0]
      textview = vbox.get_children()[1].get_children()[0]
      textbuffer = textview.get_buffer()
      self.data_editor.set_xml_structure()
      root = self.data_editor.XML.getroot()
      function.indent(root)
      text = ET.tostring(root).decode()
      textbuffer.set_text(text)
      textview.set_buffer(textbuffer)
      return

    n_page = self.book.get_current_page()
    self._fct[n_page]()
    GLib.idle_add(BG_update, n_page)

  def _on_switch_page(self, book, page, page_num):
    """Changement d'onglet sur le notebook général"""
    #print "_on_switch_page", page_num
    self.book_status = page_num
    self._set_toolbar()

  def _ini_di_methode(self):
    di = {
		0: self._update_units_page,
		1: self._ini_node_page,
		2: self._ini_barre_page,
		3: self._ini_liaisons_page,
		4: self._ini_sections_page,
		5: self._ini_material_page,
		6: self._ini_cases_book,
		7: self._ini_combi_page,
	}
    self._fct = di

  def ini_box_dict(self):
    """Initialise le dictionnaire contenant les vbox des onglets"""
    self.data_box = {}
    self.data_box['unit'] = self.book.get_nth_page(0)


  def _save_unit_pref(self, widget):
    self.UP.save_default_units(self.data_editor)

# -------------------------------------
# -------- page des unités ------------
# -------------------------------------

  def _ini_units_page(self):
    """Remplit la combobox des unités lors de l'ouverture de la fenetre
    Connecte les combobox"""
    #print "Editor::_ini_units_page"
    box = self.data_box['unit']
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="<b>Contrôle des unités</b>", halign=Gtk.Align.START)
    label.set_margin_start(10)
    label.set_use_markup(True)
    hbox.pack_start(label, True, True, 0)
    b = Gtk.Button.new_from_icon_name('preferences-system', Gtk.IconSize.MENU)
    b.set_property('halign', Gtk.Align.END)
    b.set_relief(Gtk.ReliefStyle.NONE)
    b.connect('clicked', self._save_unit_pref)
    b.set_tooltip_text("Enregistrer comme valeurs par défaut")
    hbox.pack_start(b, False, False, 0)
    box.pack_start(hbox, False, False, 0)

# seul élément qui n'est pas dans un hbox
    button = Gtk.CheckButton(label="Convertir les valeurs numériques")
    button.set_active(True)
    box.pack_start(button, False, False, 0)

    hbox = Gtk.HBox(homogeneous=False, spacing=5)
    label = Gtk.Label(label="Angle :", xalign=0.)
    label.set_margin_start(10)
    label.set_size_request(220, 30)
    hbox.pack_start(label, False, False, 0)
    label = Gtk.Label(label="degré")
    hbox.pack_start(label, False, False, 0)
    box.pack_start(hbox, False, False, 0)

    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="g (accélération pesanteur) :", xalign=0.)
    label.set_margin_start(10)
    label.set_size_request(220, 30)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_width_chars(10)
    entry.set_text(self.data_editor.G)
    entry.connect("changed", self._update_G)
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label(label="ms<sup>-2</sup>")
    label.set_margin_start(10)
    label.set_use_markup(True)
    hbox.pack_start(label, False, False, 0)
    box.pack_start(hbox, False, False, 0)

    self.ini_units_box(box)

    button = Gtk.CheckButton(label="Unités impériales")
    id = button.connect('clicked', self._set_imperial)
    self.handler_id['SI'] = id
    box.pack_start(button, False, False, 0)

    b = Gtk.CheckButton(label="Convention inversée")
    conv = self.data_editor.conv
    if conv == -1:
      b.set_active(True)
    id = b.connect("clicked", self._update_conv)
    self.handler_id['conv'] = id
    box.pack_start(b, False, False, 0)
    box.show_all()

  def ini_units_box(self, box):
    """Remplit la zone pour les unités avec les labels et combobox vides"""
    combo_box = Gtk.VBox(homogeneous=False, spacing=0)
    texts = {'L': "Longueur",
		'S': "Section droite",
		'E': "Module élastique",
		'I': "Moment quadratique",
		'F': "Force",
		'C': "Contrainte normale",
		'M': "Masse volumique"
		}
    for name, text in texts.items():
      hbox = Gtk.HBox(homogeneous=False, spacing=0)
      label = Gtk.Label(label="%s :" % text, xalign=0.)
      label.set_margin_start(10)
      label.set_size_request(220, 30)
      hbox.pack_start(label, False, False, 0)
      combobox = Gtk.ComboBox()
      combobox.set_size_request(80, 35)
      combobox.set_name(name)
      crt = Gtk.CellRendererText()
      combobox.pack_start(crt, True)
      combobox.add_attribute(crt, 'markup', 0)
      hbox.pack_start(combobox, False, False, 0)
      combo_box.pack_start(hbox, False, False, 0)
      id = combobox.connect('changed', self._update_new_unit)
      self.handler_id[name] = id
    box.pack_start(combo_box, False, False, 0)
    self.fill_units_combo()


  def fill_units_combo(self):
    """Remplit les combobox des unités avec les unités impériales ou SI"""
    #print "fill_units_combo"
    box = self.data_box['unit']
    handler_id = self.handler_id
    units = self.data_editor.get_units()
    combo_box = box.get_children()[4]
    for elem in combo_box.get_children():
      combobox = elem.get_children()[1]
      name = combobox.get_name()
      combobox.handler_block(handler_id[name])
      li = list(units[name].keys())
      ls = combobox.get_model()
      if not ls is None:
        ls.clear()
      ls = Gtk.ListStore(str)
      for val in li:
        ls.append([val])
      combobox.set_model(ls)
      combobox.handler_unblock(handler_id[name])


  def _update_units_page(self):
    """Active la bonne unité dans les combobox des unités"""
    #print "Editor::_update_units_page"
    box = self.data_box['unit']
    handler_id = self.handler_id
    childs = box.get_children()
    G_entry = childs[3].get_children()[1]
    G_entry.set_text(str(self.data_editor.G))
    combo_box = childs[4]
    units = self.data_editor.get_units()
    unit = self.data_editor.unit_conv
    if not self.data_editor.unit_si == self.unit_si:
      self.unit_si = self.data_editor.unit_si
      self.fill_units_combo()
    for elem in combo_box.get_children():
      combobox = elem.get_children()[1]
      name = combobox.get_name()
      combobox.handler_block(handler_id[name])
      name = combobox.get_name()
      text = function.return_key(units[name], unit[name])
      self._update_combo(combobox, text)
      combobox.handler_unblock(handler_id[name])
    b = childs[5]
    b.handler_block(handler_id['SI'])
    b.set_active(not self.data_editor.unit_si)
    b.handler_unblock(handler_id['SI'])
    b = childs[6]
    b.handler_block(handler_id['conv'])
    conv = self.data_editor.conv
    if conv == -1:
      b.set_active(True)
    else:
      b.set_active(False)
    b.handler_unblock(handler_id['conv'])


  def _set_imperial(self, widget):
    """Change les unités en unités impériales"""
    if widget.get_active():
      self.data_editor.unit_si = False
      self.unit_si = False
    else:
      self.data_editor.unit_si = True
      self.unit_si = True
    self.fill_units_combo()
    box = self.data_box['unit']
    childs = box.get_children()
    combo_box = childs[4]
    for elem in combo_box.get_children():
      combobox = elem.get_children()[1]
      self._update_new_unit(combobox)
    self._update_units_page()


  def _update_numeric_L(self, factor):
    """Met à jour les valeurs numériques suite à un changement d'unité de longueur"""
    for node in self.data_editor.nodes:
      node.update_numeric_L(factor)
      node.set_coors_label(self.data_editor)
    self.data_editor.set_bars_size()
    self.data_editor.set_char_bar_size()
    self._update_unit_L_char_tooltip() # revoir optimisation

    for barre in self.data_editor.barres:
      barre.update_numeric_L(factor)

    self._update_liaison_num(1/factor)

    sections = self.data_editor.sections
    for s in sections:
      boxes = s.boxes
      if 'h' in boxes:
        entry = boxes['h'].get_children()[1]
        try:
          val = float(entry.get_text().replace(",", "."))
          val = val*factor
          entry.set_text(str(val))
        except ValueError:
          pass
      if 'v' in boxes:
        entry = boxes['v'].get_children()[1]
        try:
          val = float(entry.get_text().replace(",", "."))
          val = val*factor
          entry.set_text(str(val))
        except ValueError:
          pass
    # chargements
    for case in self.data_editor.cases:
      for char in case.chars:
        char.update_numeric_L(factor)



  def _update_numeric_I(self, factor):
    """Met à jour les valeurs numériques suite à un changement d'unité de moment quadratique"""
    sections = self.data_editor.sections
    for s in sections:
      boxes = s.boxes
      entry = boxes['i'].get_children()[1]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass

  def _update_numeric_S(self, factor):
    """Met à jour les valeurs numériques suite à un changement d'unité de la section"""
    sections = self.data_editor.sections
    for s in sections:
      boxes = s.boxes
      entry = boxes['s'].get_children()[1]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass

  def _update_numeric_E(self, factor):
    """Met à jour les valeurs numériques suite à un changement d'unité du module d'Young"""
    materials = self.data_editor.materials
    for mat in materials:
      boxes = mat.boxes
      entry = boxes['e'].get_children()[1]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass

  def _update_numeric_M(self, factor):
    """Met à jour les valeurs numériques suite à un changement d'unité de la masse volumique"""
    materials = self.data_editor.materials
    for mat in materials:
      boxes = mat.boxes
      if not 'm' in boxes:
        continue
      entry = boxes['m'].get_children()[1]
      try:
        val = float(entry.get_text().replace(",", "."))
        val = val*factor
        entry.set_text(str(val))
      except ValueError:
        pass


  def _update_numeric_F(self, factor):
    """Met à jour les valeurs numériques suite à un changement d'unité de force"""
    # appui élastique
    self._update_liaison_num(factor)
    # pivots élastiques
    for b in self.data_editor.barres:
      b.update_numeric_F(factor)

    # chargements
    for case in self.data_editor.cases:
      for char in case.chars:
        char.update_numeric_F(factor)

  def _update_numeric_vals(self, name, factor):
    """Convertit les valeurs numériques de l'ensemble des onglets dans la nouvelle unité"""
    #print "_update_numeric_vals", name, factor
    if name == 'L':
      self._update_numeric_L(factor)
    elif name == 'I':
      self._update_numeric_I(factor)
    elif name == 'S':
      self._update_numeric_S(factor)
    elif name == 'E':
      self._update_numeric_E(factor)
    elif name == 'M':
      self._update_numeric_M(factor)
    elif name == 'F':
      self._update_numeric_F(factor)

  def _update_texts_L(self):
    """Convertit les labels suite à un changement d'unité de longueur"""
    #print "_update_texts_L"
    units = self.data_editor.get_units()
    unit_F = function.return_key(units['F'], self.data_editor.unit_conv['F'])
    unit_L = function.return_key(units['L'], self.data_editor.unit_conv['L'])
    for node in self.data_editor.nodes:
      node.update_tooltip_L(unit_L)
    for barre in self.data_editor.barres:
      barre.update_tooltip_L(unit_L)
    # hauteurs des sections droites
    sections = self.data_editor.sections
    for s in sections:
      boxes = s.boxes
      if 'h' in boxes:
        s.update_tooltip_h(self)
      if 'v' in boxes:
        s.update_tooltip_v(self)


    vbox = self.data_box["liaison"]
    for i, elem in enumerate(vbox.get_children()):
      ev = elem.get_children()[0]
      combobox = ev.get_children()[2]
      index = combobox.get_active()
      if index == 3:
        label = ev.get_children()[-1]
        text = 'en %s / %s' % (unit_F, unit_L)
        label.set_text(text)
    # chargements
    for case in self.data_editor.cases:
      for char in case.chars:
        char.update_tooltip_L(unit_L, unit_F)

  def _update_texts_I(self):
    """Convertit les tooltips suite à un changement d'unité de moment qua"""
    sections = self.data_editor.sections
    for s in sections:
      boxes = s.boxes
      s.update_tooltip_i(self)

  def _update_texts_S(self):
    """Convertit les tooltips suite à un changement d'unité de surface"""
    sections = self.data_editor.sections
    for s in sections:
      boxes = s.boxes
      s.update_tooltip_s(self)

  def _update_texts_E(self):
    """Convertit les tooltips suite à un changement d'unité de module élastique"""
    materials = self.data_editor.materials
    for mat in materials:
      boxes = mat.boxes
      if not 'e' in boxes:
        continue
      mat.update_tooltip_E(self)

  def _update_texts_M(self):
    """Convertit les tooltips suite à un changement d'unité de masse volumique"""
    materials = self.data_editor.materials
    for mat in materials:
      boxes = mat.boxes
      if not 'm' in boxes:
        continue
      mat.update_tooltip_m(self)


  def _update_texts_F(self):
    """Convertit les labels suite à un changement d'unité de force"""
    units = self.data_editor.get_units()
    unit_L = function.return_key(units['L'], self.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], self.data_editor.unit_conv['F'])
    vbox = self.data_box["liaison"]
    for i, elem in enumerate(vbox.get_children()):
      ev = elem.get_children()[0]
      combobox = ev.get_children()[2]
      index = combobox.get_active()
      if index == 3:
        label = ev.get_children()[-1]
        text = 'en %s / %s' % (unit_F, unit_L)
        label.set_text(text)

    # pivots élastiques
    for barre in self.data_editor.barres:
      barre.update_tooltip_F(unit_F)

    # chargements
    for case in self.data_editor.cases:
      for char in case.chars:
        char.update_tooltip_F(unit_L, unit_F)

  def _update_new_unit(self, widget):
    """Actualise les unités dans les labels de l'éditeur et tooltips"""
    #print "Editor::_update_new_unit"
    name = widget.get_name()
    isSI = self.data_editor.unit_si
    model = widget.get_model()
    index = widget.get_active()
    if index == -1:
      unit = Const.get_default_unit_text(name, isSI)
    else:
      unit = model[index][0]
    units = self.data_editor.get_units()
    # récupération de la nouvelle unité pour les conversions
    new = units[name][unit]
    old = self.data_editor.unit_conv[name]
    self.data_editor.unit_conv[name] = new
    # conversion des valeurs numériques
    box = self.data_box['unit']
    if box.get_children()[1].get_active():
      self._update_numeric_vals(name, old/new)

    if name == 'L':
      self._update_texts_L()
    elif name == 'I':
      self._update_texts_I()
    elif name == 'S':
      self._update_texts_S()
    elif name == 'E':
      self._update_texts_E()
    elif name == 'M':
      self._update_texts_M()
    elif name == 'F':
      self._update_texts_F()
    self.set_is_changed(True)

  def _update_liaison_num(self, factor):
      """Actualise les valeurs numériques pour les changements d'unité dans les liaisons"""
      #print "_update_liaison_num", factor
      for i, ev in enumerate(self.data_box["liaison"].get_children()):
        hbox = ev.get_children()[0]
        combobox = hbox.get_children()[2]
        index = combobox.get_active()
        if not index == 3:
          continue
        for j in [4, 6, 8]:
          entry = hbox.get_children()[j]
          try:
            val = float(entry.get_text().replace(",", "."))
            val = val*factor
            entry.set_text(str(val))
          except ValueError:
            pass

  def _update_conv(self, widget):
    """Evènement de changement de la convension des signes de l'étude"""
    #print "_update_conv"
    if widget.get_active():
      self.data_editor.conv = -1
    else:
      self.data_editor.conv = 1
    self.set_is_changed()

  def _update_G(self, widget):
    """Change la valeur de G"""
    g = widget.get_text().replace(",", ".")
    try:
      float(g)
      message = ""
    except ValueError:
      g = str(Const.G)
      message = "Valeur non valide pour g"
    self.print_message(message)
    self.data_editor.G = g
    self.set_is_changed()



# -------------------------------------
# -------- page des noeuds ------------
# -------------------------------------

  def _ini_node_page(self):
    """Initialise les widgets de la page des noeuds"""
    #print "Editor::_ini_node_page"
    box = self.book.get_nth_page(1)
    if len(box) == 2: # suppression des contenus précédents
      box.remove(box.get_children()[1])
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    viewport = Gtk.Viewport()
    viewport.set_events(Gdk.EventMask.POINTER_MOTION_MASK
		| Gdk.EventMask.BUTTON_PRESS_MASK
		| Gdk.EventMask.BUTTON_RELEASE_MASK
		| Gdk.EventMask.KEY_PRESS_MASK
		| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    viewport.connect("event", self.onCMenu)
    vbox = Gtk.VBox(homogeneous=False, spacing=0)
    vbox.set_border_width(20)
    nodes = self.data_editor.nodes
    #self.data_editor.print_node()
    nodes_vbox = Gtk.VBox(homogeneous=False, spacing=0)
    for node in nodes: # ne pas trier les noeuds à cause des noeuds relatifs
      hbox = node.add_hbox(self)
      nodes_vbox.pack_start(hbox, False, False, 0)
    self.data_box["noeud"] = nodes_vbox
    vbox.pack_start(nodes_vbox, False, False, 0)
    viewport.add(vbox)
    sw.add(viewport)
    sw.show_all()
    box.add(sw)


  def on_add_node1(self, widget=None):
    """Ajoute un noeud ordinaire dans la page des noeuds"""
    # sw -> viewport -> vbox
    box = self.data_box['noeud']
    name = self.data_editor.get_new_name("node")
    node = self.data_editor.add_node({'id': name, 'd': "0,0"})
    self.data_editor.nodes.append(node)
    self.data_editor.size_changed = True
    self.set_is_changed(True)
    hbox = node.add_hbox(self)
    box.pack_start(hbox, False, False, 0)
    # modification des pages nécessitant les noeuds
    self._add_node_combo(node)

  def on_add_node2(self, widget=None):
    """Ajoute un noeud sur un arc dans la page des noeuds"""
    box = self.data_box['noeud']
    name = self.data_editor.get_new_name("node")
    node = self.data_editor.add_arc_node({'id': name, 'd': '0.5', 'name': False})
    self.data_editor.nodes.append(node)
    self.data_editor.size_changed = True
    self.set_is_changed(True)
    hbox = node.add_hbox(self)
    box.pack_start(hbox, False, False, 0)
    # modification des pages nécessitant les noeuds
    self._add_node_combo(node)
    #self.set_node_toolbar(True)


  def remove_nodes(self, action=None):
    """Supprime les noeuds sélectionnés"""
    old_nodes = self.data_editor.get_all_nodes()
    nodes = self.data_editor.nodes
    are_deleted = []
    lines = []
    box = self.data_box['noeud']
    i = 0
    for node in old_nodes:
      node = nodes[i]
      checkbutton = node.hbox.get_children()[1]
      if checkbutton.get_active():
        box.remove(node.hbox.get_parent())
        are_deleted.append(nodes[i].name)
        del(nodes[i])
        lines.append(i)
        self.set_is_changed(True)
        self.data_editor.size_changed = True
      else:
        i += 1
    if len(lines) == 0:
      return
    self._fill_preceding_node(lines[0])
    # modification de la page contenant des combobox avec des noeuds
    self.remove_liaison2(are_deleted)
    self.remove_nodes_combos(old_nodes, are_deleted)
    self._remove_combo_char_items(are_deleted)

  def _add_node_combo(self, node):
    """Ajoute le noeud dans les combo contenant des noeuds."""
    ed = self.data_editor
    barres = self.data_editor.barres
    for barre in barres:
      barre.add_node_combo(ed, node)

    node_name = node.name
    box = self.data_box['liaison']
    for i, elem in enumerate(box.get_children()):
      combo = elem.get_children()[0].get_children()[1]
      combo.append_text(node_name)
    for case in self.data_editor.cases:
      for char in case.chars:
        char.add_combo_node_item(node_name)


  def remove_nodes_combos(self, old_nodes, deleted_nodes):
    """Supprime le noeud dans les combo contenant des noeuds."""
    indices = []
    for node in deleted_nodes:
      pos = old_nodes.index(node)
      indices.append(pos)
      self.data_editor.del_barres_by_node(node)
    indices.sort()
    indices.reverse()
    barres = self.data_editor.barres
    for barre in barres:
      barre.remove_nodes_combo(deleted_nodes)

    for elem in self.data_editor.liaisons:
      combo = elem.hbox.get_children()[1]
      for pos in indices:
        combo.remove(pos)
      #model = combo.get_model()
      #nodes = [i[0] for i in model]
      #print(nodes)


  def _update_node_list(self, Node, pos):
    """Actualise les combo contenant des noeuds"""
    self._update_node_list1(Node, pos)
    self._update_node_list2(pos, Node.name)
    self._update_node_list3(pos, Node.name)

  def _update_node_list1(self, Node, node_pos):
    """Actualise la liste des noeuds pour la page des barres en cas
    d'ajout de noeuds, de supression de noeud ou de modification du nom"""
    nodes = self.data_editor.nodes
    Id = Node.id
    barres = self.data_editor.barres
    prec_b = []
    for barre in barres:
      ids = []
      b_name = barre.name
      for i, node in enumerate(nodes):
        id = node.id
        arc = node.arc
        if arc is None:
          ids.append(node.id)
          continue
        if arc in prec_b:
          ids.append(node.id)
      prec_b.append(b_name)
      if not Node.id in ids:
        continue
      node_pos = ids.index(Node.id)
      barre.rename_node_combo(self.data_editor, Node, node_pos)


  def _update_node_list2(self, n, new):
    """Actualise la liste des noeuds pour la page des liaisons en cas
    d'ajout de noeuds, de supression de noeud ou de modification du nom"""
    #box = self.data_box['liaison']
    for elem in self.data_editor.liaisons:
      combo = elem.hbox.get_children()[1]
      function.change_elem_combo2(combo, n, new)
      if combo.get_active() == n:
        elem.name = new
      #elem.set_content(self.data_editor)



  def _update_node_list3(self, n, new):
    """Actualise la liste des noeuds pour la page des chargements en cas
    d'ajout de noeuds, de supression de noeud ou de modification du nom"""
    for case in self.data_editor.cases:
      for char in case.chars:
        char.update_nodes_combo(n, new)


  def _fill_preceding_node(self, start_line):
    """Remplace tous les combobox des noeuds relatifs dans la page des noeuds suite à une suppression d'un noeud par exemple à partir de start_line"""
    box = self.data_box["noeud"]
    nodes = self.data_editor.nodes[start_line:]
    node_names = self.data_editor.get_all_nodes()
    node_names.insert(0, '')
    for i, node in enumerate(nodes):
      combobox = node.hbox.get_children()[3]
      combobox.handler_block(node.ids[0])
      node.fill_preceding_node(combobox, node_names[0:i+start_line+1])
      combobox.handler_unblock(node.ids[0])

  def update_combo_arc(self, old_name, new_name):
    """Actualise les noms des arcs sur la page des noeuds"""
    #print "update_combo_arc"
    nodes = self.data_editor.nodes
    arcs = self.data_editor.get_arcs2()
    for node in nodes:
      node.update_arc_name(arcs, old_name, new_name)

  def update_nodes(self, widget, user_node):
    """Met à jour les coordonnées absolues des noeuds et la longueur des barres"""
    nodes = self.data_editor.nodes
    is_changed = False
    modified_nodes = []
    # les lignes précédent le widget modifié doivent être inchangées
    for node in nodes:
      widgets = node.hbox.get_children()
      if node is user_node:
        is_changed = True
        node.set_content_from_widgets()
        node.set_coors_label(self.data_editor)
        self.set_is_changed(True)
        self.data_editor.size_changed = True
        modified_nodes.append(node.name)
        continue
      if not is_changed:
        continue
      resu = node.update_coors(modified_nodes, self.data_editor)
      if resu:
        modified_nodes.append(resu)
    self.data_editor.set_bars_size()
    self.data_editor.set_char_bar_size()
    self._update_unit_L_char_tooltip() # revoir optimisation




# -------------------------------------
# -------- page des barres ------------
# -------------------------------------

  def _ini_barre_page(self, widget=None):
    """Crée la page des barres
    Affichage de la page en mode entry"""
    box = self.book.get_nth_page(2)
    if len(box) == 2: # suppression des contenus précédents
      box.remove(box.get_children()[1])
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    viewport = Gtk.Viewport()
    viewport.set_events(Gdk.EventMask.POINTER_MOTION_MASK
		| Gdk.EventMask.BUTTON_PRESS_MASK
		| Gdk.EventMask.BUTTON_RELEASE_MASK
		| Gdk.EventMask.KEY_PRESS_MASK
		| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    viewport.connect("event", self.onCMenu)
    vbox = Gtk.VBox(homogeneous=False, spacing=0)
    vbox.set_border_width(20)
    barres_vbox = Gtk.VBox(homogeneous=False, spacing=0)
    barres = self.data_editor.barres
    for barre in barres:
      hbox = barre.add_hbox(self)
      barres_vbox.pack_start(hbox, False, False, 0)
    self.data_box["barre"] = barres_vbox
    vbox.pack_start(barres_vbox, False, False, 0)
    viewport.add(vbox)
    sw.add(viewport)
    sw.show_all()
    box.add(sw)


  def update_bars_combo(self, name):
    """Effectue les opérations nécessaires à la suite d'un événement de changement d'un noeud d'une barre ou d'un arc"""
    #print "update_bars_combo"
    self.data_editor.get_barres_by_node()
    nodes = self.data_editor.nodes
    modified = []
    for i, node in enumerate(nodes):
      try:
        arc = node.arc
        if not arc == name:
          continue
        modified.append(node.name)
        node.set_coors_label(self.data_editor)
        continue
      except AttributeError:
        pass
      if node.rel in modified:
        node.set_coors_label(self.data_editor)


    # modification tooltip fp
    self._update_unit_L_char_tooltip()

  def update_bar_names(self, barre, old_name, new_name):
    n1 = self.data_editor.get_barre_pos(barre, 'arc')
    n2 = self.data_editor.get_barre_pos(barre, 'bar')
    n3 = self.data_editor.get_barre_pos(barre, 'all') # regrouper?
    data_editor = self.data_editor
    data_editor._update_barres_by_node(old_name, new_name)
    self.update_combo_char_barre(old_name, new_name)
    for case in self.data_editor.cases:
      for char in case.chars:
        char.update_bars_combo(n1, n2, n3, new_name)
        continue


  def on_add_arc(self, widget=None):
    """Ajoute une ligne dans la page des barres pour une barre de type arc"""
    box = self.data_box["barre"]
    name = self.data_editor.get_new_name("arc")
    arc = self.data_editor.add_arc({'name': name, 'N0': '', 'N1': '', 'c': '', 'R0': 0, 'R1': 0})
    hbox = arc.add_hbox(self)
    box.pack_start(hbox, False, False, 0)
    self._add_barre_combo("arc", name)

  def on_add_parabola(self, widget=None):
    """Ajoute une ligne dans la page des barres pour une barre de type parabole"""
    box = self.data_box["barre"]
    name = self.data_editor.get_new_name("para")
    arc = self.data_editor.add_parabolum({'name': name, 'N0': '', 'N1': '', 'f': '', 'R0': 0, 'R1': 0})
    hbox = arc.add_hbox(self)
    box.pack_start(hbox, False, False, 0)
    self._add_barre_combo("arc", name)

  def on_add_multiple(self, widget=None):
    """Ajoute une ligne dans la page des barres pour une barre de type barre à plusieurs noeuds"""
    box = self.data_box["barre"]
    name = self.data_editor.get_new_name("bar")
    bar = self.data_editor.add_mbarre({'name': name, 'N0': '', 'N1': '', 'R0': 0, 'R1': 0})
    hbox = bar.add_hbox(self)
    box.pack_start(hbox, False, False, 0)
    self._add_barre_combo("mbarre", name)


  def on_relax_all(self, widget=None):
    self.on_cm_relax_all(widget=widget, selected=False, active=1)
  
  def on_cm_relax_all(self, widget=None, selected=True, active=0):
    box = self.data_box["barre"]
    barres = self.data_editor.barres
    i = 0
    for elem in box.get_children():
      barre = barres[i]
      image, checkbutton = barre.hbox.get_children()[0:2]
      if not selected or (selected and checkbutton.get_active()):
        checkbutton.set_active(False)
        barre.R0, barre.R1 = active, active
        file1 = barre.get_img_file()
        image.set_from_file("glade/%s" % file1)
      i = i+1
    self.set_is_changed(True)

  def on_remove_relax(self, widget=None):
    self.on_cm_relax_all(widget=widget, selected=False, active=0)

  def on_add_segment(self, widget=None):
    """Ajoute une ligne dans la page des barres pour une barre de type segment"""
    box = self.data_box["barre"]
    name = self.data_editor.get_new_name("bar")
    barre = self.data_editor.add_segment({"name": name, "start": "", "end": "", "r0": 0, "r1": 0})
    hbox = barre.add_hbox(self)
    box.pack_start(hbox, False, False, 0)
    self._add_barre_combo("barre", name)

  def remove_barres(self, action=None):
    """Supprime les barres sélectionnées"""
    #print "remove_barres"
    box = self.data_box["barre"]
    barres = self.data_editor.barres
    i = 0
    del_barres = []
    for elem in box.get_children():
      barre = barres[i]
      checkbutton = barre.hbox.get_children()[1]
      if checkbutton.get_active():
        box.remove(elem)
        del_barres.append(self.data_editor.barres[i].name)
        del(self.data_editor.barres[i])
        self.set_is_changed(True)
      else:
        i += 1
    self.data_editor.get_barres_by_node()
    nodes = self.data_editor.nodes
    for node in nodes:
      node.remove_combo_items(del_barres)


    # chargement
    self._remove_combo_char_items(del_barres)
    self.data_editor.size_changed = True


# ---------------------------------------
# -------- page des liaisons ------------
# ---------------------------------------

  def _ini_liaisons_page(self):
    """Initialisation de la page des liaisons"""
    box = self.book.get_nth_page(3)
    if len(box) == 1: # suppression des contenus précédents
      box.remove(box.get_children()[0])
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    viewport = Gtk.Viewport()
    viewport.set_events(Gdk.EventMask.POINTER_MOTION_MASK
		| Gdk.EventMask.BUTTON_PRESS_MASK
		| Gdk.EventMask.BUTTON_RELEASE_MASK
		| Gdk.EventMask.KEY_PRESS_MASK
		| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    viewport.connect("event", self.onCMenu)
    vbox = Gtk.VBox(homogeneous=False, spacing=0)
    vbox.set_border_width(20)
    liaisons = self.data_editor.liaisons
    nodes_vbox = Gtk.VBox(homogeneous=False, spacing=0)
    for l in liaisons:
      hbox = l.add_hbox(self)
      nodes_vbox.pack_start(hbox, False, False, 0)
    self.data_box["liaison"] = nodes_vbox
    vbox.pack_start(nodes_vbox, False, False, 0)
    viewport.add(vbox)
    sw.add(viewport)
    sw.show_all()
    box.add(sw)



  def on_add_liaison(self):
    """Ajoute une ligne dans la page des liaisons"""
    box = self.data_box["liaison"]
    liaison = self.data_editor.add_liaison({'id': '', 'd': '0'})
    self.data_editor.liaisons.append(liaison)
    hbox = liaison.add_hbox(self)
    box.pack_start(hbox, False, False, 0)

  def remove_liaisons(self, action=None):
    """Supprime des lignes dans la page des liaisons"""
    box = self.data_box["liaison"]
    liaisons = self.data_editor.liaisons
    i = 0
    for elem in box.get_children():
      liaison = liaisons[i]
      checkbutton = liaison.hbox.get_children()[0]
      if checkbutton.get_active():
        box.remove(elem)
        del(self.data_editor.liaisons[i])
        self.set_is_changed(True)
      else:
        i += 1
    self.data_editor.set_liaisons()

  def remove_liaison2(self, deleted):
    """Supprime les hbox des liaisons à partir d'une liste de noeuds"""
    box = self.data_box["liaison"]
    liaisons = self.data_editor.liaisons
    i = 0
    for elem in box.get_children():
      liaison = liaisons[i]
      name = liaison.name
      if name in deleted:
        box.remove(elem)
        del(self.data_editor.liaisons[i])
        self.set_is_changed(True)
      else:
        i += 1








# --------------------------------------------------
# -------- page des sections droites des barres ----
# --------------------------------------------------

  def _ini_sections_page(self):
    """Initialise la page des matériaux"""
    box = self.book.get_nth_page(4)
    if len(box) == 2: # suppression des contenus précédents
      box.remove(box.get_children()[1])
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    viewport = Gtk.Viewport()
    viewport.set_events(Gdk.EventMask.POINTER_MOTION_MASK
		| Gdk.EventMask.BUTTON_PRESS_MASK
		| Gdk.EventMask.BUTTON_RELEASE_MASK
		| Gdk.EventMask.KEY_PRESS_MASK
		| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    viewport.connect("event", self.onCMenu)
    vbox = Gtk.VBox(homogeneous=False, spacing=0)
    vbox.set_border_width(20)
    content_vbox = Gtk.VBox(homogeneous=False, spacing=0)
    sections = self.data_editor.sections
    if len(sections) == 0:
      S = self.data_editor.add_section({'name': '*', 's': '', 'i': ''})
      self.data_editor.sections.append(S)
    for S in sections:
      hbox = S.add_hbox(self)
      content_vbox.pack_start(hbox, False, False, 0)
    self.data_box["section"] = content_vbox
    vbox.pack_start(content_vbox, False, False, 0)
    viewport.add(vbox)
    sw.add(viewport)
    sw.show_all()
    box.add(sw)



  def on_add_section(self):
    """Ajoute une ligne dans la page des matériaux"""
    box = self.data_box['section']
    S = self.data_editor.add_section({'name': '', 's': '', 'i': ''})
    self.data_editor.sections.append(S)
    hbox = S.add_hbox(self)
    box.pack_start(hbox, False, False, 0)

  def remove_sections(self, action=None):
    """Supprime les barres sélectionnées"""
    box = self.data_box["section"]
    sections = self.data_editor.sections
    i = 0
    for elem in box.get_children():
      S = sections[i]
      checkbutton = S.hbox.get_children()[0]
      if checkbutton.get_active():
        box.remove(elem)
        del(self.data_editor.sections[i])
        self.set_is_changed()
      else:
        i += 1

  def on_open_section_ed(self, widget=None, path=None):
    if hasattr(self, 'section_manager'):
      self.section_manager.window.present()
      return
    self.section_manager = classSectionEditor.SectionWindow(path)
    self.section_manager.window.connect("delete_event", self._close_section)
    #self.set_selection_button(True, self.data_editor.sections)

  def on_open_lib1(self, widget=None):
    if hasattr(self, 'profil_manager'):
      self.profil_manager.window.present()
      return

    self.profil_manager = classProfilManager.ProfilManager()
    self.profil_manager.window.connect("delete_event", self._close_library1)
    #self.profil_manager.button = widget
    self.set_selection_button(True, self.data_editor.sections)

  def on_open_lib2(self, widget=None):
    if hasattr(self, 'mat_manager'):
      self.mat_manager.window.present()
      return

    self.mat_manager = classProfilManager.MaterialManager()
    self.mat_manager.window.connect("delete_event", self._close_library2)
    #self.mat_manager.button = widget
    #self.set_selection_button(True, self.data_editor.materials)

  def set_selection_button(self, tag, lines):
    """Gère la sensibilité des boutons de choix d'un profil"""
    for s in lines:
      s.hbox.get_children()[1].set_sensitive(tag)

  def _close_section(self, widget, event):
    #self.section_manager.destroy()
    self.section_manager.window = None
    del(self.section_manager)
    #self.set_selection_button(False, self.data_editor.sections)

  def _close_library1(self, widget, event):
    #print ("Editor::_close_library1")
    self.profil_manager.destroy()
    self.profil_manager.window = None
    del(self.profil_manager)
    self.set_selection_button(False, self.data_editor.sections)

  def _close_library2(self, widget, event):
    self.mat_manager.destroy()
    self.mat_manager.window = None
    del(self.mat_manager)
    self.set_selection_button(False, self.data_editor.materials)




# ----------------------------------------
# -------- page des matériaux ------------
# ----------------------------------------

  def _ini_material_page(self):
    """Initialise la page des matériaux"""
    box = self.book.get_nth_page(5)
    if len(box) == 2: # suppression des contenus précédents
      box.remove(box.get_children()[1])
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    viewport = Gtk.Viewport()
    viewport.set_events(Gdk.EventMask.POINTER_MOTION_MASK
		| Gdk.EventMask.BUTTON_PRESS_MASK
		| Gdk.EventMask.BUTTON_RELEASE_MASK
		| Gdk.EventMask.KEY_PRESS_MASK
		| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    viewport.connect("event", self.onCMenu)
    vbox = Gtk.VBox(homogeneous=False, spacing=0)
    vbox.set_border_width(20)
    content_vbox = Gtk.VBox(homogeneous=False, spacing=0)
    materials = self.data_editor.materials
    if len(materials) == 0:
      mat = self.data_editor.add_material({'name': '*', 'E': ''})
      self.data_editor.materials.append(mat)
    for mat in materials:
      hbox = mat.add_hbox(self)
      content_vbox.pack_start(hbox, False, False, 0)
    self.data_box["mater"] = content_vbox
    vbox.pack_start(content_vbox, False, False, 0)
    viewport.add(vbox)
    sw.add(viewport)
    sw.show_all()
    box.add(sw)



  def on_add_material(self):
    """Ajoute une ligne dans la page des matériaux"""
    box = self.data_box['mater']
    mat = self.data_editor.add_material({'name': '', 'E': ''})
    self.data_editor.materials.append(mat)
    hbox = mat.add_hbox(self)
    box.pack_start(hbox, False, False, 0)

  def remove_materials(self, action=None):
    """Supprime les barres sélectionnées"""
    box = self.data_box["mater"]
    materials = self.data_editor.materials
    i = 0
    for elem in box.get_children():
      mat = materials[i]
      checkbutton = mat.hbox.get_children()[0]
      if checkbutton.get_active():
        box.remove(elem)
        del(self.data_editor.materials[i])
        self.set_is_changed()
      else:
        i += 1





# ---------------------------------------------
# --------- cas de charges --------------------
# ---------------------------------------------

  def _ini_cases_book(self):
    """Les cas de charges sont placés dans un notebook
    Crée le notebook pour les cas de charge"""
    box = self.book.get_nth_page(6)
    for elem in box.get_children()[1:]:
      box.remove(elem)
    book = self.charbook = Gtk.Notebook()
    book.set_scrollable(True)
    book.set_border_width(5)
    book.show()
    # Récupération des cas de charge
    cases = self.data_editor.cases
    for i, case in enumerate(cases):
      page = self._ini_case_page(case)
      eventbox = self._ini_tab(case.name, page)
      book.append_page(page, eventbox)

    close_b = Gtk.Button.new_from_icon_name('list-add', Gtk.IconSize.MENU)
    close_b.set_relief(Gtk.ReliefStyle.NONE)
    close_b.connect('clicked', self._on_add_case)
    close_b.show_all()
    page = Gtk.HBox()
    page.show()
    book.append_page(page, close_b)
    book.connect("switch_page", self._on_switch_case)
    box.add(book)

  def _on_switch_case(self, book, page, page_num):
    """Changement d'onglet sur le notebook des chargements"""
    n_pages = book.get_n_pages()
    if not self.rename_tab_tag is None:
      case = self.data_editor.cases[self.rename_tab_tag]
      page = self.charbook.get_nth_page(self.rename_tab_tag)
      tab_box = self._ini_tab(case.name, page)
      self.charbook.set_tab_label(page, tab_box)
      self.rename_tab_tag = None

    #if page_num == n_pages-1:
    #  book.stop_emission("switch-page")
    self.data_editor.need_drawing = True
    self.w1app.update_drawing(page_num)


  def _ini_tab(self, name, page):
    """Retourne le contenu de l'onglet du Notebook des cas de charge"""
    #print "_ini_tab", page
    tab_box = Gtk.HBox(homogeneous=False, spacing=2)
    eventbox = Gtk.EventBox()
    eventbox.connect("event", self._put_entry_tab)
    label = Gtk.Label(label=name)
    label.set_margin_start(4)
    tab_box.pack_start(label, False, False, 0)
    close_b = Gtk.Button.new_from_icon_name('window-close', Gtk.IconSize.MENU)
    close_b.set_relief(Gtk.ReliefStyle.NONE)
    close_b.connect('clicked', self._remove_case, page)
    tab_box.pack_start(close_b, False, False, 0)
    tab_box.show_all()
    eventbox.add(tab_box)
    return eventbox

# non utilisé
  def on_duplicate(self, widget):
    """Copie les chargements sélectionnés"""
    pass


  def onCMenu(self, widget, event):
    """Affiche le menu contextuel de la scrollwindow"""
    if event.type == Gdk.EventType.MOTION_NOTIFY:
      if self.selected:
        context = self.selected.get_style_context()
        context.remove_class("css_hover")
        self.selected = None
    elif event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        self.on_empty_cm(event)
        return True
    return False

  def on_empty_cm(self, event):
    actions = {
      1 : [{'f':self.remove_nodes, 'label':"Supprimer"}],
      2 : [{'f':self.on_cm_relax_all, 'label':"Tout relaxer", 'data':(True, 1)}, {'f':self.on_cm_relax_all, 'label':"Supprimer les relaxations", 'data':(True, 0)}, {'f':self.remove_barres, 'label':"Supprimer"} ],
      3 : [{'f':self.remove_liaisons, 'label':"Supprimer"}],
      4 : [{'f':self.remove_sections, 'label':"Supprimer"}],
      5 : [{'f':self.remove_materials, 'label':"Supprimer"}],
      6 : [{'f':self.remove_chars, 'label':"Supprimer"}],
      7 : [{'f':self.remove_combinaisons, 'label':"Supprimer"}]
   }
    menu1 = Gtk.Menu()
    n_page = self.book.get_current_page()
    is_sensitive = False

    if n_page == 1:
      nodes = self.data_editor.nodes
      for node in nodes:
        checkbutton = node.hbox.get_children()[1]
        if checkbutton.get_active():
          is_sensitive = True
          break
    elif n_page == 2:
      nodes = self.data_editor.barres
      for node in nodes:
        checkbutton = node.hbox.get_children()[1]
        if checkbutton.get_active():
          is_sensitive = True
          break
    elif n_page == 3:
      nodes = self.data_editor.liaisons
      for node in nodes:
        checkbutton = node.hbox.get_children()[0]
        if checkbutton.get_active():
          is_sensitive = True
          break
    elif n_page == 4:
      nodes = self.data_editor.sections
      for node in nodes:
        checkbutton = node.hbox.get_children()[0]
        if checkbutton.get_active():
          is_sensitive = True
          break
    elif n_page == 5:
      nodes = self.data_editor.materials
      for node in nodes:
        checkbutton = node.hbox.get_children()[0]
        if checkbutton.get_active():
          is_sensitive = True
          break
    elif n_page == 6:
      case_page = self.charbook.get_current_page()
      page = self.charbook.get_nth_page(case_page)
      vbox = page.get_children()[0].get_children()[0]
      childs = vbox.get_children()
      case = self.data_editor.cases[case_page]
      for i, hbox in enumerate(childs):
        char = case.chars[i]
        if char.get_is_selected():
          is_sensitive = True
          break
    elif n_page == 7:
      nodes = self.data_editor.combis
      for node in nodes:
        checkbutton = node.hbox.get_children()[0]
        if checkbutton.get_active():
          is_sensitive = True
          break

    for action in actions[n_page]:
      menuitem = Gtk.MenuItem(label=action['label'])
      menuitem.set_sensitive(is_sensitive)
      if 'data' in action:
        menuitem.connect("activate", action['f'], action['data'][0],  action['data'][1])
      else:
        menuitem.connect("activate", action['f'])
      menu1.append(menuitem)
    menu1.show_all()
    menu1.popup_at_pointer(event)
    return True


  def _ini_case_page(self, case):
    """Crée un onglet dans le notebook des cas de charge. Retourne une scrolled window"""
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    viewport = Gtk.Viewport()
    viewport.set_events(Gdk.EventMask.POINTER_MOTION_MASK
		| Gdk.EventMask.BUTTON_PRESS_MASK
		| Gdk.EventMask.BUTTON_RELEASE_MASK
		| Gdk.EventMask.KEY_PRESS_MASK
		| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    viewport.connect("event", self.onCMenu)
    vbox = Gtk.VBox(homogeneous=False, spacing=0)
    vbox.set_border_width(10)
    chars = case.chars
    for char in chars:
      hbox = char.add_hbox(self)
      vbox.pack_start(hbox, False, False, 0)
    vbox.show()
    viewport.add(vbox)
    sw.add(viewport)
    sw.show_all()
    return sw

  def on_w2_add_char_qu(self, widget):
    """Ajoute une charge uniformément répartie"""
    n = self.charbook.get_current_page()
    page = self.charbook.get_nth_page(n)
    try:
      vbox = page.get_children()[0].get_children()[0]
    except:
      return None
    case = self.data_editor.cases[n]
    char = CharQu()
    case.chars.append(char)
    hbox = char.add_hbox(self)
    vbox.pack_start(hbox, False, False, 0)

  def on_w2_add_char_fp(self, widget):
    """Ajoute une charge ponctuelle sur barre"""
    n = self.charbook.get_current_page()
    page = self.charbook.get_nth_page(n)
    try:
      vbox = page.get_children()[0].get_children()[0]
    except:
      return None
    case = self.data_editor.cases[n]
    char = CharFp()
    case.chars.append(char)
    hbox = char.add_hbox(self)
    vbox.pack_start(hbox, False, False, 0)

  def on_w2_add_depi(self, widget):
    n = self.charbook.get_current_page()
    page = self.charbook.get_nth_page(n)
    try:
      vbox = page.get_children()[0].get_children()[0]
    except:
      return None
    case = self.data_editor.cases[n]
    char = CharDepi()
    case.chars.append(char)
    hbox = char.add_hbox(self)
    vbox.pack_start(hbox, False, False, 0)


  def on_w2_add_char_nod(self, widget):
    """Ajoute une charge nodale"""
    n = self.charbook.get_current_page()
    page = self.charbook.get_nth_page(n)
    try:
      vbox = page.get_children()[0].get_children()[0]
    except:
      return None
    case = self.data_editor.cases[n]
    char = CharNo()
    case.chars.append(char)
    hbox = char.add_hbox(self)
    vbox.pack_start(hbox, False, False, 0)

  def on_w2_add_char_tri(self, widget):
    """Ajoute une charge trapézoidale"""
    n = self.charbook.get_current_page()
    page = self.charbook.get_nth_page(n)
    try:
      vbox = page.get_children()[0].get_children()[0]
    except:
      return None
    case = self.data_editor.cases[n]
    char = CharTr()
    case.chars.append(char)
    hbox = char.add_hbox(self)
    vbox.pack_start(hbox, False, False, 0)

  def on_w2_add_char_therm(self, widget):
    """Ajoute une charge nodale"""
    n = self.charbook.get_current_page()
    page = self.charbook.get_nth_page(n)
    try:
      vbox = page.get_children()[0].get_children()[0]
    except:
      return None
    case = self.data_editor.cases[n]
    char = CharTh()
    case.chars.append(char)
    hbox = char.add_hbox(self)
    vbox.pack_start(hbox, False, False, 0)

  def on_w2_add_char_arc0(self, widget):
    """Ajoute une charge sur un arc proj=0"""
    n = self.charbook.get_current_page()
    page = self.charbook.get_nth_page(n)
    try:
      vbox = page.get_children()[0].get_children()[0]
    except:
      return None
    case = self.data_editor.cases[n]
    char = CharArc()
    case.chars.append(char)
    hbox = char.add_hbox(self)
    vbox.pack_start(hbox, False, False, 0)

  def remove_chars(self, widget=None):
    """Supprime les chargements sélectionnés"""
    #print "Editor::remove_chars"
    page = self.charbook.get_nth_page(self.charbook.get_current_page())
    n_page = self.charbook.get_current_page()
    vbox = page.get_children()[0].get_children()[0]
    childs = vbox.get_children()
    case = self.data_editor.cases[n_page]
    i = 0
    for hbox in childs:
      char = case.chars[i]
      if not char.get_is_selected():
        i += 1
        continue
      vbox.remove(hbox)
      del(case.chars[i])
      self.set_is_changed(True)


  def _on_add_case(self, widget):
    """Crée un nouvel onglet dans le notebook des chargements
    création de la nouvelle page"""
    n = self.charbook.get_n_pages()
    ind = n
    name = "cas %s" % ind
    cases = self.data_editor.get_cases_name()
    while name in cases:
      ind += 1
      name = "cas %s" % ind
    case = Case(name)
    self.data_editor.cases.append(case)
    page = self._ini_case_page(case)
    tab_box = self._ini_tab(name, page)
    self.charbook.insert_page(page, tab_box, n-1)
    # combinaison initialisation: default value = 0
    self.data_editor.add_case_in_combis(name)
    self._ini_combi_page()
    self.set_is_changed(True)

  def _remove_case(self, widget, page):
    """supprime un onglet du notebook des cas de charge"""
    #print "Editor::_remove_case", page
    n = self.charbook.page_num(page)
    if self.charbook.get_n_pages() == 2: # impossible de supprimer onglet 0
      return
    if page == None:
      return
    if not self.rename_tab_tag is None:
      case = self.data_editor.cases[self.rename_tab_tag]
      page = self.charbook.get_nth_page(self.rename_tab_tag)
      tab_box = self._ini_tab(case.name, page)
      self.charbook.set_tab_label(page, tab_box)
      self.rename_tab_tag = None
    label = self.charbook.get_tab_label(page).get_children()[0].get_children()[0]
    case_name = label.get_text()
    message = "Voulez-vous vraiment effacer le cas de charges : %s?" % case_name
    if not file_tools.exit_as_ok_func2(message):
      return
    self.data_editor.remove_case(case_name)
    self.data_editor.del_case_in_combis(case_name)
    active = self.charbook.get_current_page()
    self.charbook.remove(page)
    # building combis page
    self._ini_combi_page()
    # on reconstruit la nouvelle première page pour ajouter le pp
    if n == 0:
      page = self.charbook.get_nth_page(n)
      if not page:
        return
      self.charbook.remove(page)
      case = self.data_editor.cases[0]
      case.chars.insert(0, CharPp())
      case_name = case.name
      page = self._ini_case_page(case)
      tab_box = self._ini_tab(case_name, page)
      self.charbook.insert_page(page, tab_box, 0)
    self.charbook.set_current_page(max(active-1, 0))
    self.set_is_changed(True)



  def _update_unit_L_char_tooltip(self):
    """Met à jour tous les tooltips des charges si la longueur des barres a changé (changement noeud ou coordonnées) ou l'unité de longueur"""
    #print "_update_unit_L_char_tooltip"
    units = self.data_editor.get_units()
    unit_L = function.return_key(units['L'], self.data_editor.unit_conv['L'])
    unit_F = function.return_key(units['F'], self.data_editor.unit_conv['F'])
    for case in self.data_editor.cases:
      for char in case.chars:
        char.set_barre_length(self.data_editor)
        char.update_tooltip_L(unit_L, unit_F)


  def update_combo_char_barre(self, old, new):
    """Met à jour la valeur active du combo d'une charge ponctuelle, triangulaire ou thermique si le nom d'une barre a été modifié"""
    for i in range(len(self.data_editor.cases)):
      page = self.charbook.get_nth_page(i)
      vbox = page.get_children()[0].get_children()[0]
      for hbox in vbox.get_children():
        type = hbox.get_name()
        if not (type == "fp" or type == "th" or type == "tri"):
          continue
        combobox = hbox.get_children()[2]
        function.change_elem_combo(combobox, old, new, False)

  def _add_barre_combo(self, key, name):
    """ajoute une barre dans le combo des  barres pour les chargements de ype barre et pour les noeuds d'arc"""
    if key == "barre":
      for case in self.data_editor.cases:
        for char in case.chars:
          char.add_combo_bar_item(name)
    elif key == "arc":
      for case in self.data_editor.cases:
        for char in case.chars:
          char.add_combo_arc_item(name)
      for node in self.data_editor.nodes:
        node.add_combo_item(name)
    elif key == "mbarre":
      for case in self.data_editor.cases:
        for char in case.chars:
          char.add_combo_bar_item(name)
      for node in self.data_editor.nodes:
        node.add_combo_item(name)


  def _remove_combo_char_items(self, deleted):
    """Supprime les barres dans les combobox des charges"""
    units = self.data_editor.get_units()
    unit_L = function.return_key(units['L'], self.data_editor.unit_conv['L'])
    for case in self.data_editor.cases:
      for char in case.chars:
        char.remove_char_name(deleted, unit_L)

  def _put_entry_tab(self, eventbox, event):
    """"Fonction pour renommer les onglets du notebook des cas de charge
    remplace le label de l'onglet par un textentry"""
    tag = False
    if event.type == Gdk.EventType._2BUTTON_PRESS:
      tag = True
    if event.type == Gdk.EventType.BUTTON_PRESS:
      if event.get_button()[1] == 3:
        page = self.charbook.get_nth_page(self.charbook.get_current_page())
        tab = self.charbook.get_tab_label(page)
        if not tab is eventbox:
          return
        tag = True
    if not tag:
      return
    hbox = eventbox.get_children()[0]
    label = hbox.get_children()[0]
    text = label.get_text()
    eventbox.remove(hbox)
    entry = MyEntry()
    entry.set_text(text)
    entry.set_has_frame(False)
    eventbox.add(entry)
    entry.show()
    entry.grab_focus()
    self.rename_tab_tag = self.charbook.get_current_page()
    entry.connect("event", self._on_tab_entry, text)


  def _on_tab_entry(self, widget, event, text):
    """Evènement sur un Entry d'un onglet de chargement"""
    #if event.type == Gdk.EventType.EXPOSE:
    #  text = widget.get_text()
    #  layout = widget.get_layout()
    #  w, h = layout.get_pixel_size()
    #  w0, h0 = widget.size_request()
    #  if not w + 10 == w0:
    #    widget.set_size_request(w+10, 22)

    if event.type == Gdk.EventType.KEY_PRESS:
      key = Gdk.keyval_name (event.keyval)
      if key == "Return":
        # entry -> eventbox -> notebook
        notebook = widget.get_parent().get_parent()
        n_page = notebook.get_current_page()
        self._rename_tab(text, n_page)
        self.rename_tab_tag = None
      elif key == "Escape":
        case = self.data_editor.cases[self.rename_tab_tag]
        page = self.charbook.get_nth_page(self.rename_tab_tag)
        tab_box = self._ini_tab(case.name, page)
        self.charbook.set_tab_label(page, tab_box)
        self.rename_tab_tag = None


  def _rename_tab(self, old_text, n_page):
    """Fonction pour renommer les onglets du notebook des cas de charge
    à partir de la valeur du textentry
    change le nom de l'onglet du notebook
    Il faut déconnecter le signal pour pouvoir le reconnecter
    par la suite avec un autre argument"""
    n_page = self.charbook.get_current_page()
    page = self.charbook.get_nth_page(n_page)
    hbox = self.charbook.get_tab_label(page)

    entry = hbox.get_children()[0]
    new_text = entry.get_text()
    new_text = new_text.replace('_', '-')
    cases = self.data_editor.get_cases_name()
    i = 2
    if not new_text == old_text:
      text = new_text
      while text in cases:
        text = '%s(%s)' % (new_text, i)
        i += 1
      new_text = text

    tab_box = self._ini_tab(new_text, page)
    self.charbook.set_tab_label(page, tab_box)
    self.data_editor.cases[n_page].name = new_text
    self.data_editor.rename_case_in_combis(old_text, new_text)
    self._ini_combi_page()
    self.set_is_changed(True)
    #self.data_editor.print_combis_and_cases()

# ----------------------------------------------------------
# ---------- page des combinaisons--------------------------
# ----------------------------------------------------------

  def _ini_combi_page(self):
    """Initialisation de la page des combinaisons
    Utilisée à l'ouverture de l'éditeur
    et si les cas de charges sont modifiés"""
    combis = self.data_editor.combis
    #cases = self.data_editor.get_cases_name()
    sw = Gtk.ScrolledWindow()
    viewport = Gtk.Viewport()
    viewport.set_events(Gdk.EventMask.POINTER_MOTION_MASK
		| Gdk.EventMask.BUTTON_PRESS_MASK
		| Gdk.EventMask.BUTTON_RELEASE_MASK
		| Gdk.EventMask.KEY_PRESS_MASK
		| Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    viewport.connect("event", self.onCMenu)
    #debug_get_props(sw)
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    box = self.book.get_nth_page(7)
    vbox = Gtk.VBox(homogeneous=False, spacing=0)
    vbox.set_border_width(20)

    for elem in box.get_children():
      box.remove(elem)
    self.data_box['combi'] = vbox
    self.show_short_help()
    for combi in combis:
      combi_vbox = combi.add_hbox(self)
      vbox.pack_start(combi_vbox, False, False, 0)
    viewport.add(vbox)
    sw.add(viewport)
    sw.show_all()
    box.add(sw)
    errors = self.data_editor.get_n_combis_by_name()
    self.show_combi_error(errors)

  def show_short_help(self):
    """Affiche l'aide courte"""
    vbox = self.data_box['combi']
    combis = self.data_editor.combis
    if not len(combis) == 0:
      return
    if len(vbox.get_children()) == 1:
      return
    box = Gtk.VBox(homogeneous=False, spacing=0)
    box.set_name('start')
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="Une combinaison permet d'utiliser ensemble les cas de charge en leur appliquant une pondération. \nUtiliser cette page est facultatif.\nLes coefficients de pondération sont généralement compris entre 0 et 5.")
    hbox.pack_start(label, False, False, 0)
    box.pack_start(hbox, False, False, 0)
    hbox = Gtk.HBox(homogeneous=False, spacing=0)
    label = Gtk.Label(label="Démarrer en cliquant sur \"Ajouter\" ")
    hbox.pack_start(label, False, False, 0)
    b = Gtk.Button.new_from_icon_name('list-add', Gtk.IconSize.MENU)
    b.set_relief(Gtk.ReliefStyle.NONE)
    b.connect('clicked', self.on_w2_add)
    hbox.pack_start(b, False, False, 0)
    box.pack_start(hbox, False, False, 0)
    box.show_all()
    vbox.pack_start(box, False, False, 0)

  def hide_short_help(self):
    """Supprime l'aide courte"""
    box = self.data_box['combi']
    elems = box.get_children()
    try:
      help_box = elems[0]
      if help_box.get_name() == 'start':
        box.remove(help_box)
    except IndexError:
      pass

  def on_add_combinaison(self):
    """Ajoute une nouvelle combinaison"""
    if len(self.data_editor.cases) == 0:
      return None
    self.hide_short_help()
    box = self.data_box['combi']
    combis = self.data_editor.combis
    name = "Combinaison %s" % (len(combis)+1)
    combi = self.data_editor.add_combi(name)
    combi_vbox = combi.add_hbox(self)
    box.pack_start(combi_vbox, False, False, 0)
    self.set_is_changed()

  def on_paste_combinaison(self, Combi):
    """Colle une combinaison"""
    if len(self.data_editor.cases) == 0:
      return None
    box = self.data_box['combi']
    combis = self.data_editor.combis
    if not (len(Combi.name) >= 7 and Combi.name[-7:] == "(copie)"):
      name = "%s(copie)" % Combi.name
    else:
      name = Combi.name
    combi = self.data_editor.add_combi(name, Combi.coef)
    combi_vbox = combi.add_hbox(self)
    box.pack_start(combi_vbox, False, False, 0)
    self.set_is_changed()

  def remove_combinaisons(self, widget=None):
    """Supprime une ligne dans la page des combinaisons"""
    box = self.data_box['combi']
    combis = self.data_editor.combis
    removed_combi = []
    for combi in combis:
      hbox = combi.hbox
      check_b = hbox.get_children()[0]
      if not check_b.get_active():
        continue
      removed_combi.append(hbox.get_children()[1].get_text())
      box.remove(hbox.get_parent())
      self.set_is_changed()
    for combi in removed_combi:
      self.data_editor.remove_combi(combi)
    self.show_short_help()

  def show_combi_error(self, names):
    """Permet de visualiser les noms de combi qui sont présents en double"""
    combis = self.data_editor.combis
    color1 = Gdk.RGBA(1, 0, 0, 1)
    color2 = Gdk.RGBA(0, 0, 0, 1)
    for combi in combis:
      hbox = combi.hbox
      entry = hbox.get_children()[1]
      entry_context = entry.get_style_context()
      name = entry.get_text().strip()
      if names.get(name, 0) > 1:
        entry_context.add_class("css_error")
      else:
        entry_context.remove_class("css_error")



  def get_cases(self):
    """Retourne la liste des noms des combis"""
    return self.data_editor.get_cases()

  # -----------------------------------------------------------
  # ---------- Méthodes pour la barre barre d'outils principale
  # -----------------------------------------------------------

  def save_study(self, study):
    if not study.is_changed:
      message = "Etude déjà enregistrée"
    elif study.save_study(self.xml_status):
      message = "Enregistrement réalisé avec succès"
    else:
      message = "Une erreur est survenue durant l'enregistrement. Vérifier les permissions"
    study.is_changed = False
    study.size_changed = False
    self.update_editor_title(False)
    self.print_message(message)

  def set_is_changed(self, redraw=False):
    #print "set_is_changed"
    self.data_editor.is_changed = True
    self.update_editor_title(True)
    if redraw:
      self.data_editor.need_drawing = True
      GLib.idle_add(self.w1app.update_drawing)


  def update_editor_title(self, changed=False):
    if changed:
      symbol = "*"
    else:
      symbol = ""
    title = "%s - Editeur : %s%s" % (Const.SOFT, symbol, self.data_editor.name)
    self.w2.set_title(title)

  def get_modified_studies(self):
    """Retourne la liste des numéros des études ayant été modifiées"""
    studies = self.data_editors
    changes = []
    for id, study in studies.items():
      if study.is_changed:
        changes.append(id)
    return changes

# inutile ????
  def _quit(self, widget):
    """Action sur le bouton quitter - Emet un signal de fermeture"""
    print("quit")
    event = Gdk.Event(Gdk.EventType.DELETE)
    self.w2.emit("delete-event", event)


  def on_w2_destroy(self, widget, event=None):
    """Destruction de la fenetre de l'éditeur et w5 en répercussion"""
    #print("on_w2_destroy")
    self.UP.save_w2_config(self._w, self._h)
    if hasattr(self, "w5"):
      self.w5.destroy()
      del(self.w5)
    if hasattr(self, "profil_manager"):
      self.profil_manager.destroy()
      self.profil_manager.window = None
      del(self.profil_manager)
    if hasattr(self, "mat_manager"):
      self.mat_manager.destroy()
      self.mat_manager.window = None
      del(self.mat_manager)
    if hasattr(self, "section_manager"):
      self.section_manager.window = None
      del(self.section_manager)

  def on_w2_help(self, widget):
    """Fenêtre d'aide"""
    if hasattr(self, 'w5') and not self.w5 is None:
      self.w5.present()
      return
    builder = Gtk.Builder()
    builder.add_from_file("glade/help.glade")
    self.w5 = builder.get_object("window5")
    builder.connect_signals(self)
    #self.w5.set_destroy_with_parent(True)
    self.w5.set_title("%s - Fenêtre d'aide" % Const.SOFT)
    page = self.book.get_current_page()
    self._show_doc(page)
    self.w5.show()


  def _show_doc(self, page):
    """Affiche la documentation de l'éditeur de données"""
    textview = self.w5.get_children()[0].get_children()[0]
    textview.set_editable(False)
    textview.set_cursor_visible(False)
    textbuffer = Gtk.TextBuffer()
    end_iter = textbuffer.get_end_iter()
    try:
      xml = ET.parse('help.xml')
    except IOError:
      text = "Fichier d'aide introuvable"
      textbuffer.insert(end_iter, text)
      textview.set_buffer(textbuffer)
      return
    except:
      text = "Erreur dans le fichier d'aide"
      textbuffer.insert(end_iter, text)
      textview.set_buffer(textbuffer)
      return
    root = xml.getroot()
    themes = root.findall("theme")
    theme = themes[page]
    text = theme.find("content").text
    litext = text.split('\n')
    color = Gdk.RGBA(0, 1, 0, 1)
    h1 = textbuffer.create_tag("h1", weight=Pango.Weight.BOLD,size_points=16.0,foreground = "purple")
    h2 = textbuffer.create_tag("h2", weight=Pango.Weight.BOLD, size_points=12.0)
    h3 = textbuffer.create_tag("h3", weight=Pango.Weight.BOLD, size_points=11.0)
    p = textbuffer.create_tag("p", weight=Pango.Weight.BOLD, background_rgba=color)
    for i,text in enumerate(litext):
      if text == '' : continue
      if text[0:3] == "***" :
        textbuffer.insert_with_tags(end_iter,"%s\n"% text[3:], h3)
      elif text[0:2] == "**" :
        textbuffer.insert_with_tags(end_iter,"%s\n" % text[2:], h2)
      elif text[0] == "*" :
        textbuffer.insert_with_tags(end_iter,"%s\n" % text[1:], h1)
      elif text[0] == "\t" :
        textbuffer.insert(end_iter,"\t")
        textbuffer.insert_with_tags(end_iter,text[1:]+"\n",p)
      else:
        textbuffer.insert(end_iter,text+"\n")
    textview.set_buffer(textbuffer)
    textview.show()
    return True

  # destruction de la fenetre w5
  def on_w5_destroy(self, widget, event):
    if hasattr(self, "w5"):
      self.w5.destroy()
      del(self.w5)

  # --------------------------------------
  # ----------------- Outils -------------
  # --------------------------------------

  def _update_combo(self, combobox, val):
    """Rend actif le combo pour la valeur val"""
    model = combobox.get_model()
    for i in range(len(model)):
      if model[i][0] == val:
        combobox.set_active(i)
        return
    combobox.set_active(0)
    print("Editor::error in _update_combo")

  def on_w2_change_page(self, widget, dummy, pagenum):
    page_widget = widget.get_nth_page(pagenum)

    if hasattr(self, "w5"):
      self._show_doc(pagenum)
    self.print_message("")

  def _hide_tool(self, toolbar, isHide):
    """Cache ou affiche les boutons ajouter et supprimer des barres d'outils
    pour les pages noeuds, barres, section"""
    for i, toolitem in enumerate(toolbar.get_children()):
      if i == 0:
        continue
      if isHide:
        toolitem.get_children()[0].hide()
      else:
        toolitem.get_children()[0].show()




  def _get_widget_line(self, parent, child):
    """Retourne le numéro de ligne du widget contenue dans le hbox child"""
    for i, elem in enumerate(parent.get_children()):
      if elem is child:
        return i
    return None


def Main():
    Gtk.main()
    return 0

if __name__ == "__main__":
  print("Not implemented")
