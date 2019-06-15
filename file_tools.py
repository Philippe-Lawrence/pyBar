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
from gi.repository import Gtk
import Const

def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""
    return hasattr(sys, "frozen")

def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""
    #if we_are_frozen():
    #    return os.path.dirname(sys.executable, sys.getfilesystemencoding( ))
    return os.path.dirname(__file__)

def set_user_dir():
    """Crée le dossier pour les fichiers utilisateur"""
    path = Const.PATH
    if not os.path.isdir(path):
      import shutil
      os.mkdir(path)
      path = os.path.join(path, Const.DIREXEMPLES)
      os.mkdir(path)
      script_path = module_path()
      src = os.path.join(script_path, "exemples")
      try:
        files = os.listdir(src)
      except OSError:
        files = []
      for file in files:
        file_src = os.path.join(src, file)
        if os.path.isdir(file_src):
          continue
        shutil.copy(file_src, path)


# -----------------------------------------------------
#
#    OUVERTURE D'UN NOUVEAU FICHIER
#
#-------------------------------------------------------

def recursive_file_select(path):
    path = file_save(path)
    if path is None:
      return None
    if not path[-4:] == ".dat" :
      path += ".dat"
    if save_as_ok_func(path):
      return path
    else:
      recursive_file_select()

def exit_as_ok_func(filename):
    err = "Enregistrer le fichier '%s'?"  % filename
    dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL,
                                         Gtk.MessageType.QUESTION,
                                         Gtk.ButtonsType.YES_NO, err)
    dialog.add_button("Oui pour tous", 2)
    dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
    dialog.set_icon_from_file("glade/logo.png")
    result = dialog.run()
    dialog.destroy()
    if result == Gtk.ResponseType.YES:
      return 1
    if result == Gtk.ResponseType.CANCEL:
      return -1
    if result == 2:
      return 2
    return 0

def exit_as_ok_func2(message):
    dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.MODAL,
                                        Gtk.MessageType.QUESTION,
                                        Gtk.ButtonsType.YES_NO, message)
    dialog.set_icon_from_file("glade/logo.png")
    result = dialog.run()
    dialog.destroy()
    if result != Gtk.ResponseType.YES:
      return False
    return True



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


def open_as_ok_func(filename):
    if filename is None:
      return
    if os.path.exists(filename):
      dialog = Gtk.MessageDialog(None, Gtk.DialogFlags.DESTROY_WITH_PARENT,
					Gtk.MessageType.INFO,
					Gtk.ButtonsType.OK,
			"Le fichier '%s' est déjà ouvert"  % filename)
      dialog.set_icon_from_file("glade/logo.png")
      result = dialog.run()
      dialog.destroy()


def open_dialog_resol():
    """Fenêtre d'affichage de choix de la résolution"""
    dialog = Gtk.Dialog("Exportation Bitmap",
			None,
			Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
    dialog.set_icon_from_file("glade/logo.png")

    vbox = Gtk.VBox(False, 0)
    vbox.set_border_width(5)

    label = Gtk.Label(label="Choix de la résolution")
    label.set_size_request(-1, 30)
    label.set_alignment(0, 0.5)
    vbox.pack_start(label, False, True, 0)

    adj = Gtk.Adjustment(50., 0., 100., 10., 20.0, 0.0)
    spin = Gtk.SpinButton.new(adj, 0, 0)
    spin.set_size_request(30, -1)
    #spin.set_wrap(True) ???
    vbox.pack_start(spin, False, False, 0)

    dialog.vbox.add(vbox)
    dialog.show_all()
    result = dialog.run()
    dialog.destroy()
    if result == Gtk.ResponseType.OK:
      return spin.get_value()
    return False

def open_dialog_bars(bars, selected_bars):
    """Fenêtre d'affichage de sélection des barres actives"""
    dialog = Gtk.Dialog("Choix des barres",
			None,
			Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))
    dialog.set_icon_from_file("glade/logo.png")

    vbox = Gtk.VBox(False, 0)
    vbox.set_border_width(5)

    label = Gtk.Label(label="Choix des barres")
    label.set_size_request(-1, 30)
    label.set_alignment(0, 0.5)
    vbox.pack_start(label, False, True, 0)

    buttons = []
    keys = list(bars.keys())
    keys.sort()
    for bar in keys:
      button = Gtk.CheckButton(bars[bar])
      buttons.append(button)
      if bar in selected_bars:
        button.set_active(True)
      vbox.pack_start(button, False, False, 0)

    dialog.vbox.add(vbox)
    dialog.show_all()
    result = dialog.run()
    dialog.destroy()
    if result == Gtk.ResponseType.OK:
      resu = {}
      for i, button in enumerate(buttons):
       if button.get_active():
         key = keys[i]
         resu[key] = bars[key]
      return resu
    return False


def file_export(path, preselect=None):
  """Return selected file name or None"""
  # Create a new file selection widget
  dialog = Gtk.FileChooserDialog("Enregistrer sous",
		None, Gtk.FileChooserAction.SAVE,
		(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
		Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
  dialog.set_icon_from_file("glade/logo.png")
  dialog.set_current_folder(path)
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
    #if sys.platform == 'win32':
    #  file = file.decode('utf-8')
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

def file_save(path, ext=".dat", preselect=None):
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


# -----------------------------------------------------
#
#    OUVERTURE D'UN FICHIER
#
#-------------------------------------------------------

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
  
  dir_exemple = os.path.join(script_path, "exemples")
  dialog.add_shortcut_folder(dir_exemple)
  if path is None:
    path = dir_exemple
  dialog.set_current_folder(path)
  filtre = Gtk.FileFilter()
  filtre.set_name("Fichiers %s" % Const.SOFT)
  filtre.add_pattern("*.dat")
  filtre.add_pattern("*.dxf")
  filtre.add_pattern("*.DXF")
  dialog.add_filter(filtre)
  reponse = dialog.run()
  if reponse == Gtk.ResponseType.OK:
    file = dialog.get_filename()
# suppression juin 2014
    #if sys.platform == 'win32':
    #  file = file.decode('utf-8')
  else:
    file = None
  dialog.destroy()
  return file



