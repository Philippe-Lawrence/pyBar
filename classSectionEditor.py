#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2015 Philippe LAWRENCE
#
# This file is part of pyBar.
#    This script is free software; you can redistribute it and/or modify
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


import gi
gi.require_version('Gtk', '3.0')
#print(gi.version_info)

from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, GObject, Gio


import cairo
import time
import math
import classSection
import os
import sys
import xml.etree.ElementTree as ET

def file_save(path, ext=".xml", preselect=None):
  """Return selected file name or None"""
  # Create a new file selection widget
  dialog = Gtk.FileChooserDialog("Enregistrer sous",
		None, Gtk.FileChooserAction.SAVE,
		(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
		Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
  dialog.set_icon_from_file("glade/logo.png")
  dialog.set_current_folder(path)
  dialog.set_default_response(Gtk.ResponseType.OK)
  filtre = Gtk.FileFilter()
  filtre.set_name("Fichier données")
  filtre.add_pattern("*%s" % ext)
  dialog.add_filter(filtre)
  # select a specific file 
  if preselect:
    dialog.set_current_name(preselect)
  reponse = dialog.run()
  if reponse == Gtk.ResponseType.OK:
    file = dialog.get_filename()
    #if sys.platform == 'win32':
    #  file = file.decode('utf-8')
    file_ext = os.path.splitext(file)[1].lower()
    if not file_ext == ext:
    #if not file[-4:] == ext:
      file += ext
  else:
    file = None
  dialog.destroy()
  return file

# XXX remplace par file_tools
def file_selection(path, window):
  """Return selected file name or None"""
  # Create a new file selection widget
  dialog = Gtk.FileChooserDialog("Choisir un fichier",
				   window,
				   Gtk.FileChooserAction.OPEN,
				   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 
					Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
  dialog.set_default_response(Gtk.ResponseType.OK)
  dialog.set_icon_from_file("glade/logo.png")
  script_path = os.path.dirname(os.path.realpath(__file__))
  
  dir_exemple = os.path.join(script_path, "sections")
  dialog.add_shortcut_folder(dir_exemple)
  if path is None:
    path = dir_exemple
  dialog.set_current_folder(path)
  filtre = Gtk.FileFilter()
  #filtre.set_name("Fichiers %s" % Const.SOFT)
  filtre.add_pattern("*.xml")
  filtre.add_pattern("*.dxf")
  filtre.add_pattern("*.DXF")
  dialog.add_filter(filtre)
  reponse = dialog.run()
  if reponse == Gtk.ResponseType.OK:
    file = dialog.get_filename()
  else:
    file = None
  dialog.destroy()
  return file



def save_as_ok_func(filename):
    if filename is None:
      return
    if os.path.exists(filename):
      err = "Ecraser le fichier '%s'?"  % filename
      dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL,
                                         Gtk.MessageType.QUESTION,
                                         Gtk.ButtonsType.YES_NO, err)
      dialog.set_icon_from_file("glade/logo.png")
      result = dialog.run()
      dialog.destroy()
      if result != Gtk.ResponseType.YES:
        return False
      return True
    return True



def file_export(preselect=None):
  """Return selected file name or None"""
  # Create a new file selection widget
  dialog = Gtk.FileChooserDialog("Enregistrer sous",
		None, Gtk.FileChooserAction.SAVE,
		(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
		Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
  dialog.set_icon_from_file("glade/logo.png")
  dialog.set_current_folder(os.path.abspath('') )
  dialog.set_default_response(Gtk.ResponseType.OK)
  filter = Gtk.FileFilter()
  filter.set_name("PNG")
  filter.add_mime_type("image/png")
  filter.add_pattern("*.png")
  dialog.add_filter(filter)

  filter = Gtk.FileFilter()
  filter.set_name("SVG")
  filter.add_pattern("*.svg")
  dialog.add_filter(filter)

  # select a specific file 
  if preselect:
    dialog.set_current_name(preselect)
  reponse = dialog.run()
  if reponse == Gtk.ResponseType.OK:
    filter = dialog.get_filter()
    format = filter.get_name()
    file = dialog.get_filename()
    if format == 'JPEG' and  (not file[-4:] == '.jpg' and not file[-4:] == '.jpeg'):
      file += '.jpg'
    elif format == 'PNG' and  not file[-4:] == '.png':
      file += '.png'
    elif format == 'SVG' and  not file[-4:] == '.svg':
      file += '.svg'
    dialog.destroy()
    return file, format
  dialog.destroy()
  return None



def about():
    dialog = Gtk.AboutDialog()
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size("glade/logo.png", 25, 25)
    dialog.set_logo(pixbuf)
    dialog.set_program_name("Gestionnaire de sections droites")
    dialog.set_version("1.0")
    dialog.set_authors(["Philippe Lawrence"])
    #dialog.set_website(Const.SITE_URL)
    dialog.set_comments("Calcule les caractéristiques des sections droites")
    dialog.set_license("GNU-GPL")
    result = dialog.run()
    dialog.destroy()




class Nodes(object):
  NODES = {}
  ARCS = {}

class ArcWidget(object):
  """Classe de base pour les arcs"""

  def __init__(self, name):
    self.id = name
    nodes = Nodes.NODES
    arcs = Nodes.ARCS
    #if not name in arcs:
    arcs[name] = classSection.ArcSegment(name, 0, nodes)

  def add_hbox(self, main, hbox=None):
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_text(self.id)
    entry.connect('changed', self.on_name_update, main)
    hbox.pack_start(entry, False, False, 0)
    b= Gtk.MenuButton()
    b.set_size_request(50, 35)

    menu = Gtk.Menu()
    menuitem = Gtk.MenuItem(label="Départ Fin Centre")
    menuitem.show()
    menuitem.connect_object("activate", main.on_add_arc1, self, 1)
    menu.append(menuitem)
    menuitem = Gtk.MenuItem(label="Départ Centre Angle")
    menuitem.show()
    menuitem.connect_object("activate", main.on_add_arc1, self, 2)
    menu.append(menuitem)
    menuitem = Gtk.MenuItem(label="Départ Fin Angle")
    menuitem.show()
    menuitem.connect_object("activate", main.on_add_arc1, self, 3)
    menu.append(menuitem)
    menuitem = Gtk.MenuItem(label="Départ Rayon Angle")
    menuitem.show()
    menuitem.connect_object("activate", main.on_add_arc1, self, 4)
    menu.append(menuitem)
    menuitem = Gtk.MenuItem(label="Départ Fin Rayon")
    menuitem.show()
    menuitem.connect_object("activate", main.on_add_arc1, self, 5)
    menu.append(menuitem)

    b.set_popup(menu)
    b.show_all()
    hbox.pack_start(b, False, False, 0)
    self.hbox = hbox
    return hbox

  def on_update(self, widget, main):
    self.id = widget.get_text()

  def on_name_update(self, widget, main):
    main.modified = True
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    new = widget.get_text()
    arc.id = new
    del(arcs[self.id])
    arcs[new] = arc
    self.id = new
    main.on_draw()

  def on_sign_update(self, widget, main):
    main.modified = True
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    arc.sign = ['+', '-'][widget.get_active()]
    main.on_draw()

class ArcWidget1(ArcWidget):
  """Arc défini par 2 points et le centre"""

  def __init__(self, name, cat):
    self.cat = cat
    self.id = name
    arcs = Nodes.ARCS
    nodes = Nodes.NODES
    #if not name in arcs:
    #  arcs[name] = classSection.ArcSegment(name, cat, nodes)

  def add_hbox(self, main, hbox=None):
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    if self.cat == 1:
      return self.add_hbox1(main, hbox)
    elif self.cat == 2:
      return self.add_hbox2(main, hbox)
    elif self.cat == 3:
      return self.add_hbox3(main, hbox)
    elif self.cat == 4:
      return self.add_hbox4(main, hbox)
    elif self.cat == 5:
      return self.add_hbox5(main, hbox)


  # départ, fin, centre [cat = 1]
  def add_hbox1(self, main, hbox=None):
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_text(self.id)
    entry.connect('changed', self.on_name_update, main)
    hbox.pack_start(entry, False, False, 0)
    #b= Gtk.MenuButton()
    #b.set_size_request(50, 35)
    #menumodel = Gio.Menu()
    #menumodel.append("Départ centre fin", "win.arc1")
    #menumodel.append("Départ centre angle", "win.arc2")
    #menumodel.append("Départ fin angle", "win.arc3")
    #menumodel.append("Départ rayon angle", "win.arc4")
    #b.set_menu_model(menumodel)
    #b.show_all()
    #hbox.pack_start(b, False, False, 0)
    start = arc.start
    end = arc.end
    center = arc.center

    label = Gtk.Label(label="Départ:")
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("start")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.start)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)
    label = Gtk.Label(label="Fin:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("end")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.end)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)

    label = Gtk.Label(label="Centre:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)

    combo = Gtk.ComboBoxText()
    combo.set_name("center")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.center)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sens de rotation')
    if arc.sign == "-":
      button.set_active(True)
    button.connect('clicked', self.on_sign_update, main)
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Sens horaire")
    hbox.pack_start(label, False, False, 0)
    self.hbox = hbox
    return hbox

  # départ centre angle [cat = 2]
  def add_hbox2(self, main, hbox=None):
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_text(self.id)
    entry.connect('changed', self.on_name_update, main)
    hbox.pack_start(entry, False, False, 0)
    start = arc.start
    end = arc.end
    #center = arc.center

    label = Gtk.Label(label="Départ:")
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("start")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.start)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)
    label = Gtk.Label(label="Centre:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("center")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.center)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)

    label = Gtk.Label(label="Angle:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_name("a")
    if arc.a is None: a = "0"
    else: a = str(arc.a)
    entry.set_text(a)
    entry.connect('changed', self.on_data_update, main)
    hbox.pack_start(entry, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sens de rotation')
    if arc.sign == "-":
      button.set_active(True)
    button.connect('clicked', self.on_sign_update, main)
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Sens horaire")
    hbox.pack_start(label, False, False, 0)
    self.hbox = hbox
    return hbox

  # départ fin angle [cat = 3]
  def add_hbox3(self, main, hbox=None):
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_text(self.id)
    entry.connect('changed', self.on_name_update, main)
    hbox.pack_start(entry, False, False, 0)
    start = arc.start
    end = arc.end
    #center = arc.center

    label = Gtk.Label(label="Départ:")
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("start")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.start)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)
    label = Gtk.Label(label="Fin:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("end")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.end)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)

    label = Gtk.Label(label="Angle:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_name("a")
    if arc.a is None: a = "0"
    else: a = str(arc.a)
    entry.set_text(a)
    entry.connect('changed', self.on_data_update, main)
    hbox.pack_start(entry, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sens de rotation')
    if arc.sign == "-":
      button.set_active(True)
    button.connect('clicked', self.on_sign_update, main)
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Sens horaire")
    hbox.pack_start(label, False, False, 0)
    self.hbox = hbox
    return hbox

  # départ rayon angle [cat = 4]
  def add_hbox4(self, main, hbox=None):
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_text(self.id)
    entry.connect('changed', self.on_name_update, main)
    hbox.pack_start(entry, False, False, 0)
    start = arc.start
    end = arc.end
    #center = arc.center

    label = Gtk.Label(label="Départ:")
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("start")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.start)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)
    label = Gtk.Label(label="Rayon:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_name("r")
    if arc.r is None: r = "0"
    else: r = str(arc.r)
    entry.set_text(r)
    entry.connect('changed', self.on_data_update, main)
    hbox.pack_start(entry, False, False, 0)

    label = Gtk.Label(label="Angle:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_name("a")
    if arc.a is None: a = "0"
    else: a = str(arc.a)
    entry.set_text(a)
    entry.connect('changed', self.on_data_update, main)
    hbox.pack_start(entry, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sens de rotation')
    if arc.sign == "-":
      button.set_active(True)
    button.connect('clicked', self.on_sign_update, main)
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Sens horaire")
    hbox.pack_start(label, False, False, 0)
    self.hbox = hbox
    return hbox



  # départ fin rayon [cat = 5]
  def add_hbox5(self, main, hbox=None):
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_text(self.id)
    entry.connect('changed', self.on_name_update, main)
    hbox.pack_start(entry, False, False, 0)
    start = arc.start
    end = arc.end
    #center = arc.center

    label = Gtk.Label(label="Départ:")
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("start")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.start)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)
    label = Gtk.Label(label="Fin:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_name("end")
    combo.set_entry_text_column(0)
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(arc.end)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_data_update, main)
    hbox.pack_start(combo, False, False, 0)

    label = Gtk.Label(label="Rayon:")
    label.set_size_request(50, 35)
    hbox.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_name("r")
    if arc.r is None: r = "0"
    else: r = str(arc.r)
    entry.set_text(r)
    entry.connect('changed', self.on_data_update, main)
    hbox.pack_start(entry, False, False, 0)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Sens de rotation')
    if arc.sign == "-":
      button.set_active(True)
    button.connect('clicked', self.on_sign_update, main)
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Sens horaire")
    hbox.pack_start(label, False, False, 0)
    self.hbox = hbox
    return hbox




  def on_data_update(self, widget, main):
    main.modified = True
    #center, r, a, end = None, None, None, None
    arcs = Nodes.ARCS
    arc = arcs[self.id]
    nodes = Nodes.NODES
    di = {}
    widgets = self.hbox.get_children()
    di['start'] = widgets[3].get_active_text()
    widget = widgets[5]
    name = widget.get_name()
    if name == "r":
      try:
        val = float(widget.get_text().replace(',', '.'))
        di["r"] = val
      except ValueError:
        pass
    else:
      val = widget.get_active_text()
      di[name] = val
    widget = widgets[7]
    name = widget.get_name()
    if name == "r" or name == "a":
      try:
        val = float(widget.get_text().replace(',', '.'))
        di[name] = val
      except ValueError:
        pass
    else:
      val = widget.get_active_text()
      di[name] = val
    arc.update(nodes, di)
    main.on_draw()




class ContourWidget(object):

  def __init__(self, name):
    self.id = name

  def add_hbox(self, main, hbox=None):
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)
    entry = Gtk.Entry()
    entry.set_max_width_chars(3)
    entry.set_width_chars(2)
    entry.set_text(self.id)
    entry.connect('changed', self.on_update, main)
    hbox.pack_start(entry, False, False, 0)

    b= Gtk.MenuButton()
    b.set_size_request(50, 35)
    menu = Gtk.Menu()
    menuitem = Gtk.MenuItem(label="Cercle")
    menuitem.show()
    menuitem.connect_object("activate", main.on_add_circle, self)
    menu.append(menuitem)
    menuitem = Gtk.MenuItem(label="Polygone")
    menuitem.show()
    menuitem.connect_object("activate", main.on_add_poly, self)
    menu.append(menuitem)
    b.set_popup(menu)
    b.show_all()
    hbox.pack_start(b, False, False, 0)
    self.hbox = hbox
    return hbox


  def on_update(self, widget, main):
    self.id = widget.get_text()

class CircleWidget(ContourWidget):

  def __init__(self, Circle):
    self.id = Circle.id
    self.Circle = Circle

  def add_hbox(self, main, hbox=None):
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Cercle:")
    label.set_size_request(70, 35)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_max_width_chars(3)
    entry.set_width_chars(2)
    entry.set_text(self.Circle.id)
    entry.connect('changed', self.on_update, main)
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label(label="Centre:")
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_entry_text_column(0)

    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(self.Circle.center)
      combo.set_active(active)
    except AttributeError:
      pass 
    except ValueError:
      pass 
    combo.connect('changed', self.on_update, main)
    hbox.pack_start(combo, False, False, 0)
    label = Gtk.Label(label="Passant par:")
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(self.Circle.point)
      combo.set_active(active)
    except AttributeError:
      pass 
    except ValueError:
      pass 
    combo.connect('changed', self.on_update, main)
    hbox.pack_start(combo, False, False, 0)
    button = Gtk.CheckButton()
    if not self.Circle.fill: button.set_active(True)
    button.set_tooltip_text('Creux')
    button.connect('clicked', self.on_update2, main)
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Creux")
    hbox.pack_start(label, False, False, 0)
    self.hbox = hbox
    return hbox

  def on_update(self, widget, main):
    main.modified = True
    nodes = Nodes.NODES
    widgets = self.hbox.get_children()
    name = widgets[2].get_text()
    center = widgets[4].get_active_text()
    point = widgets[6].get_active_text()
    self.Circle.update(name, center, point, self.Circle.fill, nodes)
    main.on_draw()

  def on_update2(self, widget, main):
    main.modified = True
    self.Circle.fill = [True, False][widget.get_active()]
    main.on_draw()

class CircleWidgetCR(ContourWidget):

  def __init__(self, Circle):
    self.id = Circle.id
    self.Circle = Circle

  def add_hbox(self, main, hbox=None):
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Cercle:")
    label.set_size_request(70, 35)
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_max_width_chars(3)
    entry.set_width_chars(2)
    entry.set_text(self.Circle.id)
    entry.connect('changed', self.on_update, main)
    hbox.pack_start(entry, False, False, 0)
    label = Gtk.Label(label="Centre:")
    hbox.pack_start(label, False, False, 0)
    combo = Gtk.ComboBoxText()
    combo.set_entry_text_column(0)

    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(self.Circle.center)
      combo.set_active(active)
    except AttributeError:
      pass 
    except ValueError:
      pass 
    combo.connect('changed', self.on_update, main)
    hbox.pack_start(combo, False, False, 0)
    label = Gtk.Label(label="Rayon:")
    hbox.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(3)
    entry.set_width_chars(2)
    try:
      entry.set_text(str(self.Circle.r))
    except AttributeError:
      pass
    entry.connect('changed', self.on_update, main)
    hbox.pack_start(entry, False, False, 0)
    button = Gtk.CheckButton()
    if not self.Circle.fill: button.set_active(True)
    button.set_tooltip_text('Creux')
    button.connect('clicked', self.on_update2, main)
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Creux")
    hbox.pack_start(label, False, False, 0)
    self.hbox = hbox
    return hbox

  def on_update(self, widget, main):
    main.modified = True
    nodes = Nodes.NODES
    widgets = self.hbox.get_children()
    name = widgets[2].get_text()
    center = widgets[4].get_active_text()
    r = widgets[6].get_text()
    try:
      r = float(r)
    except ValueError:
      r = None
    self.Circle.update(name, center, r, self.Circle.fill, nodes)
    main.on_draw()

  def on_update2(self, widget, main):
    main.modified = True
    self.Circle.fill = [True, False][widget.get_active()]
    main.on_draw()




class PathWidget(ContourWidget):

  def __init__(self, Path):
    self.id = Path.id
    self.Path = Path

  def add_hbox(self, main, hbox=None):
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    arcs = list(Nodes.ARCS)
    arcs.sort()
    nodes.extend(arcs)
    if hbox is None:
      hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Contour:")
    label.set_size_request(70, 35)
    hbox.pack_start(label, False, False, 0)

    entry = Gtk.Entry()
    entry.set_max_width_chars(3)
    entry.set_width_chars(2)
    entry.set_text(self.Path.id)
    entry.connect('changed', self.on_update1, main)
    hbox.pack_start(entry, False, False, 0)
    d = self.Path.d
    for elem in d:
      self.add_combo(hbox, nodes, main, elem)

    button = Gtk.CheckButton()
    if not self.Path.fill: button.set_active(True)
    button.set_tooltip_text('Creux')
    button.connect('clicked', self.on_update2, main)
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Creux")
    hbox.pack_start(label, False, False, 0)
    b = Gtk.Button.new_from_icon_name('list-add', Gtk.IconSize.MENU)
    b.set_relief(Gtk.ReliefStyle.NONE)
    b.connect('clicked', self.on_add_node, main)
    hbox.pack_start(b, False, False, 0)
    self.hbox = hbox
    return hbox

  def on_add_node(self, widget, main):
    nodes = Nodes.NODES
    nodes = list(nodes)
    nodes.sort()
    arcs = list(Nodes.ARCS)
    arcs.sort()
    nodes.extend(arcs)
    combo = self.add_combo(self.hbox, nodes, main, "")
    n = len(self.hbox.get_children())
    self.hbox.reorder_child(combo, n-4)
    self.hbox.show_all()

  def add_combo(self, hbox, nodes, main, actif):
    combo = Gtk.ComboBoxText()
    for node in nodes:
      combo.append_text(node)
    try:
      active = nodes.index(actif)
      combo.set_active(active)
    except ValueError:
      pass 
    combo.connect('changed', self.on_update3, main)
    hbox.pack_start(combo, False, False, 0)
    return combo

  def on_update1(self, widget, main):
    main.modified = True
    new = widget.get_text()
    self.id = new
    main.on_draw()


  def on_update2(self, widget, main):
    main.modified = True
    self.Path.fill = [True, False][widget.get_active()]
    main.on_draw()

  def on_update3(self, widget, main):
    main.modified = True
    nodes = Nodes.NODES
    arcs = Nodes.ARCS
    widgets = self.hbox.get_children()
    d = []
    for widget in widgets:
      if isinstance(widget, Gtk.ComboBoxText):
        node = widget.get_active_text()
        if node is None: continue
        d.append(node)
    self.Path.d = d
    self.Path.calculate(nodes, arcs)
    main.on_draw()

        


class NodeWidget(object):
  def __init__(self, id):
    self.id = id
    nodes = Nodes.NODES
    if not id in nodes:
      nodes[id] = classSection.Node(id, "")
    

  def add_hbox(self, main):
    nodes = Nodes.NODES
    node = nodes[self.id]
    hbox = Gtk.Box(spacing=4)
    button = Gtk.CheckButton()
    button.set_tooltip_text('Supprimer')
    hbox.pack_start(button, False, False, 0)
    label = Gtk.Label(label="Point")
    hbox.pack_start(label, False, False, 0)
    entry = Gtk.Entry()
    entry.set_max_width_chars(3)
    entry.set_width_chars(2)
    entry.set_text(self.id)
    entry.connect('changed', self.on_update1, main)
    hbox.pack_start(entry, False, False, 0)
    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_text(str(node.x))
    entry.connect('changed', self.on_update2, main)
    hbox.pack_start(entry, False, False, 0)
    entry = Gtk.Entry()
    entry.set_max_width_chars(4)
    entry.set_width_chars(3)
    entry.set_text(str(node.y))
    entry.connect('changed', self.on_update2, main)
    hbox.pack_start(entry, False, False, 0)
    button = Gtk.CheckButton()
    hbox.pack_start(button, False, False, 0)
    self.hbox = hbox
    return hbox

  def on_update1(self, widget, main):
    main.modified = True
    nodes = Nodes.NODES
    node = nodes[self.id]
    new = widget.get_text()
    node.id = new
    del(nodes[self.id])
    nodes[new] = node
    self.id = new
    main.on_draw()

  def on_update2(self, widget, main):
    main.modified = True
    nodes = Nodes.NODES
    arcs = Nodes.ARCS
    widgets = self.hbox.get_children()
    x = widgets[3].get_text().replace(',', '.')
    try:
      x = float(x)
    except:
      x = 0
    nodes[self.id].x = x
    y = widgets[4].get_text().replace(',', '.')
    try:
      y = float(y)
    except:
      y = 0
    nodes[self.id].y = y
    nodes[self.id].d = "%g,%g" % (x, y)

# mise à jour des arcs et des contours
    for name in arcs:
      a = arcs[name]
      if a is None: continue
      a.calculate(nodes)
    for p in main.s.paths:
      path = main.s.paths[p]
      if path is None: continue
      path.calculate(nodes, arcs)

    main.on_draw()




class SectionWindow(object):

  def __init__(self, path=None):
    builder = self.builder = Gtk.Builder()
    builder.add_from_file("glade/section.glade")
    builder.connect_signals(self)
    self.window = window = builder.get_object("window1")
    #window = Gtk.ApplicationWindow()
    #app.add_window(window)
    self.sw = builder.get_object("scrolledwindow1")
    self.area = builder.get_object("drawingarea")
    self.notebook = builder.get_object("notebook1")
    self.box1 = builder.get_object("box1")
    self.box2 = builder.get_object("box2")
    self.box3 = builder.get_object("box3")
    self.textview = builder.get_object("textview")
    parse, color = Gdk.Color.parse('white')
    self.area.modify_bg(Gtk.StateType.NORMAL, color) 
    self.margin = 40

    self.area.connect("size-allocate", self.configure_first_page)
    self.area.connect("draw", self.on_expose)
    window.show_all()
    if path is None:
      self.on_new()
    else:
      self.on_open(None, path)

    #action = Gio.SimpleAction.new("arc1", None)
    #action.connect("activate", self.arc1_callback)
    #self.window.add_action(action)

    #action = Gio.SimpleAction.new("arc2", None)
    #action.connect("activate", self.arc2_callback)
    #self.window.add_action(action)


  def ini_box(self):
    nodes =  Nodes.NODES
    for elem in self.box1.get_children():
      self.box1.remove(elem)
    for elem in self.box2.get_children():
      self.box2.remove(elem)
    for elem in self.box3.get_children():
      self.box3.remove(elem)
    li_nodes = list(nodes)
    li_nodes.sort()
    for node in li_nodes:
      Node = nodes[node]
      Obj = NodeWidget(Node.id)
      hbox = Obj.add_hbox(self)
      self.box1.pack_start(hbox, False, False, 0)
    for node in self.s.arcs:
      a = self.s.arcs[node]
      Obj = ArcWidget1(a.id, a.cat)
      hbox = Obj.add_hbox(self)
      self.box2.pack_start(hbox, False, False, 0)
    for node in self.s.paths:
      Path = self.s.paths[node]
      if isinstance(Path, classSection.Path):
        Obj = PathWidget(Path)
      elif isinstance(Path, classSection.CirclePathCP):
        Obj = CircleWidget(Path)
      else:
        Obj = CircleWidgetCR(Path)
      hbox = Obj.add_hbox(self)
      self.box3.pack_start(hbox, False, False, 0)

    self.box1.show_all()
    self.box2.show_all()
    self.box3.show_all()

      

  def ini_xml(self):
    """Initialise la structure xml des données"""
    string = """<xml><nodes /></xml>"""
    return ET.ElementTree(ET.fromstring(string))

  def get_xml(self):
    xml = self.ini_xml()
    nodes =  Nodes.NODES
    li_nodes = list(nodes)
    li_nodes.sort()
    for name in li_nodes:
      Node = nodes[name]
      Node.set_xml(xml)
    arcs =  Nodes.ARCS
    li_arcs = list(arcs)
    li_arcs.sort()
    for name in li_arcs:
      a = arcs[name]
      a.set_xml(xml)
    for name in self.s.paths:
      Node = self.s.paths[name]
      if Node is None: continue
      Node.set_xml(xml)
    root = xml.getroot()
    return ET.tostring(root).decode()
    

  def on_switch_page(self, widget, box, n_page):
    if n_page == 3: 
      self.write_resu()

  def on_run(self, widget):
    self.modified = False
    xml = self.get_xml()
    self.s = classSection.StringAnalyser(xml)
    self.write_resu()
    GLib.idle_add(self.update_drawing)

  def write_resu(self):
    text = self.s.print2term(False)
    textbuffer = self.textview.get_buffer()
    textbuffer.set_text(text)



  def send_data(self):
    data = self.s.set_data()
    return data

  def on_open(self, widget, path=None):
    #self.s = None
    self.modified = False
    if path is None:
      path = file_selection("", self.window)
    if path is None:
      return
    self.path = path
    
    if os.path.isfile(self.path):
      self.s = classSection.FileAnalyser(path)
    else:
      self.s = classSection.NewAnalyser()
      print("Impossible d'ouvrir le fichier") # XXX
    Nodes.NODES = self.s.nodes
    Nodes.ARCS = self.s.arcs
    self.ini_box()
    GLib.idle_add(self.update_drawing)

  def on_new(self, widget=None):
    self.modified = True
    Nodes.NODES = {}
    Nodes.ARCS = {}
    self.s = classSection.NewAnalyser()
    for elem in self.box1.get_children():
      self.box1.remove(elem)
    for elem in self.box2.get_children():
      self.box2.remove(elem)
    for elem in self.box3.get_children():
      self.box3.remove(elem)
    try:
      del(self.p1)
    except AttributeError:
      pass
    self.path = None
    GLib.idle_add(self.area.queue_draw)


  def on_add_node(self, widget):
    self.modified = True
    nodes =  Nodes.NODES
    i = 0
    name = "N1"
    while name in nodes:
      i += 1
      name = "N%d" % i
    Obj = NodeWidget(name)
    hbox = Obj.add_hbox(self)
    self.box1.pack_start(hbox, False, False, 0)
    hbox.show_all()
    self.on_draw()


  def on_add_arc(self, widget):
    self.modified = True
    nodes =  Nodes.ARCS
    i = 0
    name = "Arc1"
    while name in nodes:
      i += 1
      name = "Arc%d" % i
    Obj = ArcWidget(name)
    hbox = Obj.add_hbox(self)
    self.box2.pack_start(hbox, False, False, 0)
    hbox.show_all()

  def on_add_arc1(self, obj, cat):
    self.modified = True
    hbox = obj.hbox
    Id = obj.id
    for child in hbox.get_children():
      hbox.remove(child)
    #path = classSection.Path(Id, [], True, Nodes.NODES, Nodes.ARCS)
    #self.s.paths[Id] = path
    arcs = Nodes.ARCS
    nodes = Nodes.NODES
    arcs[Id] = classSection.ArcSegment(Id, cat, nodes)
    Obj = ArcWidget1(Id, cat)
    hbox = Obj.add_hbox(self, hbox)
    hbox.show_all()

  def on_add_path(self, widget):
    self.modified = True
    nodes = self.s.paths
    i = 0
    name = "C1"
    while name in nodes:
      i += 1
      name = "C%d" % i
    Obj = ContourWidget(name)
    self.s.paths[name] = None
    hbox = Obj.add_hbox(self)
    self.box3.pack_start(hbox, False, False, 0)
    hbox.show_all()

  def on_add_poly(self, obj):
    self.modified = True
    hbox = obj.hbox
    Id = obj.id
    for child in hbox.get_children():
      hbox.remove(child)
    path = classSection.Path(Id, [], True, Nodes.NODES, Nodes.ARCS)
    self.s.paths[Id] = path
    Obj = PathWidget(path)
    hbox = Obj.add_hbox(self, hbox)
    hbox.show_all()

  def on_add_circle(self, obj):
    self.modified = True
    hbox = obj.hbox
    #for child in hbox.get_children()[2:]:
    #  hbox.remove(child)
    b= Gtk.MenuButton()
    b.set_size_request(50, 35)
    menu = Gtk.Menu()
    menuitem = Gtk.MenuItem(label="Cercle centre et point")
    menuitem.show()
    menuitem.connect_object("activate", self.on_add_circle1, obj)
    menu.append(menuitem)
    menuitem = Gtk.MenuItem(label="Cercle centre et rayon")
    menuitem.show()
    menuitem.connect_object("activate", self.on_add_circle2, obj)
    menu.append(menuitem)
    b.set_popup(menu)
    b.show_all()
    hbox.pack_start(b, False, False, 0)

  def on_add_circle1(self, obj):
    hbox = obj.hbox
    Id = obj.id
    for child in hbox.get_children():
      hbox.remove(child)
    path = classSection.CirclePathCP(Id, None, None, True, Nodes.NODES)
    self.s.paths[Id] = path
    Obj = CircleWidget(path)
    hbox = Obj.add_hbox(self, hbox)
    hbox.show_all()


  def on_add_circle2(self, obj):
    hbox = obj.hbox
    Id = obj.id
    for child in hbox.get_children():
      hbox.remove(child)
    path = classSection.CirclePathCR(Id, None, None, True, Nodes.NODES)
    self.s.paths[Id] = path
    Obj = CircleWidgetCR(path)
    hbox = Obj.add_hbox(self, hbox)
    hbox.show_all()



  def on_remove_arc(self, widget):
    self.modified = True
    nodes = Nodes.ARCS
    for elem in self.box2.get_children():
      if elem.get_children()[0].get_active():
        name = elem.get_children()[1].get_text()
        del(nodes[name])
        self.box2.remove(elem)
    self.on_draw()


  def on_remove_path(self, widget):
    self.modified = True
    nodes = Nodes.NODES
    for elem in self.box3.get_children():
      if elem.get_children()[0].get_active():
        name = elem.get_children()[1].get_text()
        del(self.s.paths[name])
        self.box3.remove(elem)
    self.on_draw()

  def on_remove_node(self, widget):
    self.modified = True
    nodes = Nodes.NODES
    for elem in self.box1.get_children():
      if elem.get_children()[0].get_active():
        name = elem.get_children()[2].get_text()
        del(nodes[name])
        self.box1.remove(elem)
    self.on_draw()



  def on_save(self, widget):
    if self.path is None:
      self.path = file_save("")
      if not save_as_ok_func(self.path):
        return
    try:
      f = open(self.path, 'w')
      string = self.get_xml()
      f.write('<?xml version="1.0" encoding="UTF-8"?>'+string)
      f.close()
      print("Recording successfully completed")
    except:
      print("An error has occurred during recording")

  def on_export(self, widget):
    """Effectue une sauvegarde de l'écran au format jpg ou svg"""
    data = file_export()
    if data is None:
      return
    file = data[0]
    format = data[1]
    if not save_as_ok_func(file):
      return

    if format == 'PNG':
      surface = cairo.ImageSurface(cairo.FORMAT_RGB24, self.w, self.h)
      cr = cairo.Context(surface)
      cr.set_source_rgb(1, 1, 1)
      cr.rectangle(0, 0, self.w, self.h)
      cr.fill()

      self.paint(cr)
      surface.write_to_png(file)
      surface.finish()
      print("Export complete")

    elif format == 'SVG':
      surface = cairo.SVGSurface(file, self.w, self.h)
      cr = cairo.Context(surface)
      self.paint(cr)
      surface.finish()

  def on_about(self, widget):
    about()

  def GetBox(self):
    self.box = None
    nodes = Nodes.NODES
    arcs = Nodes.ARCS
    for node_id in nodes:
      node = nodes[node_id]
      x, y = node.x, node.y
      try:
        x = float(x)
        y = float(y)
      except ValueError:
        continue
      if self.box is None:
        self.box = [x, y, x, y]
        continue
      xmin, ymin, xmax, ymax = self.box
      if x < xmin: xmin = x
      elif x > xmax: xmax = x
      if y < ymin: ymin = y
      elif y > ymax: ymax = y
      self.box = [xmin, ymin, xmax, ymax]
    if self.box is None: 
      return None
    xmin, ymin, xmax, ymax = self.box
    for a in arcs:
      arc = arcs[a]
      self.box = arc.GetBox(self.box)
    for id in self.s.paths:
      node = self.s.paths[id]
      if node is None: continue
      self.box = node.GetBox(self.box)



  def GetCairoScale(self, w0, h0):
    self.GetBox()
    if self.box is None: 
      return 1
    xmin, ymin, xmax, ymax = self.box
    w = xmax - xmin
    h = ymax - ymin
    max_s = max(w, h)
    if w == 0: scalex = None
    else: scalex = w0 / w
    if h == 0: scaley = None
    else: scaley = h0 / h
    if scalex is None and scaley is None: return 1
    elif scalex is None: return scaley
    elif scaley is None: return scalex
    return min(scalex, scaley)

  def CairoDraw(self, cr, X0, Y0, w, h):
    nodes = Nodes.NODES
    arcs = Nodes.ARCS
    self.scale = scale = self.GetCairoScale(w, h)
    #print("scale=", scale)
    #print("box=", self.box)
    if self.box is None: return []
    x0, y0, x1, y1 = self.box
    cr.push_group()
    cr.save()
    #cr.arc(100, 100, 50, 0, 1.57)
    #cr.arc_negative(50, 100, 50, 0, 1.57)
    cr.stroke()
    cr.set_line_width(2)
    cr.translate(X0-x0*scale, Y0+y0*scale)
    pattern = []
    # ----- Noeuds -------------
    for node_id in nodes:
      #print("N=", node_id)
      node = nodes[node_id]
      node.draw(cr, scale)
    # ----- Tronçon d'Arc -------------
    cr.save()
    cr.set_line_width(1)
    cr.set_dash([2])
    for a in arcs:
      a = arcs[a]
      a.draw(cr, scale)
    cr.restore()

    # ----- Paths & Circles -------------
    for path_id in self.s.paths:
      path = self.s.paths[path_id]
      if path is None: continue
      path.draw(cr, scale)

    # ---------       CDG
    if not self.modified and not self.s.section.XG is None:
      cr.set_font_size(14)
      cr.set_source_rgb(0, 1, 0)
      cr.arc(self.s.section.XG*scale, -self.s.section.YG*scale, 4, 0, 6.29)
      cr.fill()
      cr.move_to(self.s.section.XG*scale+5, -self.s.section.YG*scale)
      cr.show_text("G")

    cr.restore()
    pattern.append(cr.pop_group())
    return pattern

  def draw_surface_bg(self, cr):
    """Draw white background on drawingare"""
    cr.rectangle(0, 0, self.w, self.h)
    cr.fill()

  def on_draw(self, widget=None):
    GObject.idle_add(self.update_drawing)


  def update_drawing(self):
    x0 = self.x0
    y0 = self.y0
    w = self.w - 2*self.margin
    h = self.h - 2*self.margin
    cr = cairo.Context(self.surface)
    self.draw_surface_bg(cr)
    if hasattr(self, 's'):
      self.p1 = self.CairoDraw(cr, x0, y0, w, h)

    GLib.idle_add(self.area.queue_draw)


  def on_expose(self, widget, cr):
    """Méthode expose-event pour le drawingarea du lancement"""
    cr.set_source_surface(self.surface, 0, 0)
    if hasattr(self, "p1"):
      for pattern in self.p1:
        cr.set_source(pattern)
        cr.paint()

  def configure_first_page(self, widget, event):
    #print("configure")
    self.w = w_alloc = widget.get_allocated_width()
    self.h = h_alloc = widget.get_allocated_height()
    #print("configure=", self.w, self.h)
    self.x0 = self.margin
    self.y0 = self.h - self.margin

    self.surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w_alloc, h_alloc)
    #cr = cairo.Context(self.surface)
    GObject.idle_add(self.update_drawing)

  def on_destroy_main(self, widget, event=None):
    Gtk.main_quit()

  def on_destroy(self, widget, event=None):
    #self.window.destroy()
    return False

 


if __name__=='__main__':
  print ("Not implemented")
