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

#from function import *
import function
import classRdm
from gi.repository import Gtk, Gdk



#-------------------------------------------------------------------------
#
#                     FENETRE DES LIGNES D'INFLUENCE
#
#-------------------------------------------------------------------------
class LigneInfluBox(object):

  def __init__(self, main, study, influ_obj, selected_bars):
    self.influ_obj = influ_obj
    structure = study.rdm.struct
    self.struct = structure
    self.Nodes = self.struct.Liaisons.keys()
    #self.Nodes.sort()
    if selected_bars:
      self.Barres = self.struct.GetBarsNames2(selected_bars)
    else:
      self.Barres = self.struct.GetBarsNames()
    # plus de tri ; tester"
    self.vbox = Gtk.Box(spacing=5, orientation=Gtk.Orientation.VERTICAL) # permet de controler la largeur du combo
    self.vbox.set_border_width(5)
    self._fill(main)
    self.vbox.set_name("influ")
    self._ini_menu(selected_bars)
    self._connect_radio_button()


  def _fill(self, main):
    label = Gtk.Label(label="Ligne d'influence:", xalign=0.)
    label.set_margin_start(10)
    self.vbox.pack_start(label, False, False, 0)
    button = Gtk.RadioButton.new_with_label_from_widget(None, "Effort tranchant")
    button.set_name("1")
    self.vbox.pack_start(button, False, False, 0)

    button = Gtk.RadioButton.new_with_label_from_widget(button, "Moment fléchissant")
    button.set_name("2")
    self.vbox.pack_start(button, False, False, 0)
    button = Gtk.RadioButton.new_with_label_from_widget(button, "Flèche")
    button.set_name("3")
    self.vbox.pack_start(button, False, False, 0)
    button = Gtk.RadioButton.new_with_label_from_widget(button, "Réaction d'appui")
    button.set_name("4")
    self.vbox.pack_start(button, False, False, 0)
    self.group = button.get_group()

    self.combobox1 = Gtk.ComboBoxText()
    hbox = Gtk.Box(spacing=0, orientation=Gtk.Orientation.HORIZONTAL) # permet de controler la largeur du combo
    label = Gtk.Label(label="Elément: ")
    hbox.pack_start(label, False, False, 0)
    self.combobox1.set_size_request(80, -1)
    hbox.pack_start(self.combobox1, False, False, 0)
    self.vbox.pack_start(hbox, False, False, 0)

    hbox = Gtk.Box(spacing=0, orientation=Gtk.Orientation.HORIZONTAL) # permet de controler la largeur du combo
    label = self.spin_label1 = Gtk.Label(label="Position en %: ")
    hbox.pack_start(label, False, False, 0)
    adjust = Gtk.Adjustment(value=0., lower=0., upper=100., step_increment=1., page_increment=5.)
    spin = self.spin1 = Gtk.SpinButton.new(adjust, 5, 0)
    spin.connect("event", self._update)
    hbox.pack_start(spin, False, False, 0)
    self.vbox.pack_start(hbox, False, False, 0)

    b = self.check1 = Gtk.CheckButton(label="Longueur en m")
    b.connect('clicked', self._set_length_unit)
    self.vbox.pack_start(b, False, False, 0)

    toolbar = Gtk.Toolbar()
    b = Gtk.ToolButton(icon_widget=Gtk.Image.new_from_file("glade/influ.png"))
    b.set_label("Calculer")
    b.set_tooltip_text("Calculer la ligne d'influence")
    b.connect("clicked", main.area_expose_influ)
    toolbar.insert(b, -1)
    b = Gtk.ToolButton(icon_widget=Gtk.Image.new_from_file("glade/influ2.png"))
    b.set_label("Superposer")
    b.set_tooltip_text("Superposer une nouvelle ligne d'influence")
    b.connect("clicked", main.area_expose_influ, False)
    toolbar.insert(b, -1)
    b = Gtk.ToolButton(icon_widget=Gtk.Image.new_from_file("glade/influ3.png"))
    b.set_label("Effacer")
    b.set_tooltip_text("Effacer les lignes d'influence")
    b.connect("clicked", main.on_del_influs)
    toolbar.insert(b, -1)
    self.vbox.pack_start(toolbar, False, False, 0)

    self.vbox.show_all()

  def _update(self, widget, event):
    """Force une mise à jour du spin button en cas de modification par saisie clavier"""
    if event.type == Gdk.EventType.LEAVE_NOTIFY:
      widget.update()

  def _ini_menu(self, bars=[]):
    """initialise le menu des lignes d'influence"""
    influ_obj = self.influ_obj
    if influ_obj is None:
      status = 1
      elem = None
      u = 0
    else:
      status = influ_obj.status
      elem = influ_obj.elem
      u = influ_obj.u*100
    self.spin1.set_value(u)
    if status == 4:
      self._set_nodes()
    else:
      self._set_barres()
    for button in self.group:
      if int(button.get_name()) == status:
        button.set_active(True)
        break
      

  def _connect_radio_button(self):
    """Connecte les radio V, M, defo et Réac"""
    for button in self.group:
      if button.get_name() == '4':
        button.connect("clicked", self._set_nodes)
      else:
        button.connect("clicked", self._set_barres)

  def _set_combo(self, elems, active=None):
    """Remplit le combo avec les élements "elems" et rend actif l'élément "active" """
    function.fill_elem_combo(self.combobox1, elems, active)

  def _set_barres(self, widget=None):
    """Affiche dans le combobox la liste des barres
    Efface la liste précédente"""
    #print "_set_barres", self.influ_obj.elem
    if not widget is None and widget.get_active() is False:
      return
    if not self.influ_obj is None:
      if self.influ_obj.elem in self.Barres:
        active = self.Barres[self.influ_obj.elem]
      else:
        active = None
    else:
      active = None
    elems = list(self.Barres.values())
    elems.sort()
    self._set_combo(elems, active)
    self.spin1.set_sensitive(True)

  def _set_nodes(self, widget=None):
    """Affiche dans le combobox la liste des barres
    Efface la liste précédente"""
    #print "_set_nodes", self.influ_obj.elem
    if not widget is None and widget.get_active() is False:
      return
    if not self.influ_obj is None:
      active = self.influ_obj.elem
    else:
      active = None
    elems = list(self.Nodes)
    elems.sort()
    self._set_combo(elems, active)

    self.spin1.set_sensitive(False)


  def _set_length_unit(self, widget):
    """Convertit le format des longueurs (% ou m)"""
    combobox = self.combobox1
    model = combobox.get_model()
    index = combobox.get_active()
    if not index == -1:
      barre = model[index][0]
    if not barre in self.struct.Barres:
      return False
    b, label = self.spin1, self.spin_label1
    value = b.get_value()
    l = self.struct.Lengths[barre]
    if widget.get_active():
      digit = 2
      text = "Position en m:"
      value = value*l/100
      b.set_increments(0.01, 0.05)
      b.set_digits(digit)
      b.set_range(0, l)
    else:
      digit = 0
      text = "Position en %:"
      value = value/l*100
      b.set_increments(1, 5)
      b.set_digits(digit)
      b.set_range(0, 100)
    b.set_value(value)
    label.set_text(text)

  def get_box(self):
    """Retourne la vbox du menu"""
    return self.vbox

  def  get_data(self):
    """Récupère les données du combo et spin de la fenetre des lignes d'influence"""
    model = self.combobox1.get_model()
    index = self.combobox1.get_active()
    if index == -1:
      return None
    elem = model[index][0]
    u = self.spin1.get_value()
    for button in self.group:
      if button.get_active():
        if button.get_name() == "1":
          status = 1
        elif button.get_name() == "2":
          status = 2
        elif button.get_name() == "3":
          status = 3
        elif button.get_name() == "4":
          status = 4
          u = 0 # pas besoin de u dans ce cas
    l = 1
    if status in [1, 2, 3]:
      # inversion
      d = self.Barres
      elem = list(d.keys())[list(d.values()).index(elem)] # Améliorer
      l = self.struct.Lengths[elem]
    if self.check1.get_active():
      u = u / l
    else:
      u = u / 100
    return {'elem': elem, 'u': u, 'status': status}




