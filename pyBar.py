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

import sys

# revoir sys.platform dans Const !!!!

import gi
gi.require_version('Gtk', '3.0')


from gi.repository import Gtk, Gdk, Pango, GObject, GdkPixbuf
#print Gtk.pygtk_version
#print Gtk.gtk_version
import cairo
#import gio # debug py2exe windows remettre?
import classEditor
import classDrawing
import classRdm
import classLigneInflu
import classDialog
import Const
import classProfilManager
import classPrefs
import classCMenu
import threading
import copy
import os
#import pickle
import function
import file_tools
#from time import sleep
import xml.etree.ElementTree as ET

#import signal
#signal.signal(signal.SIGINT, signal.SIG_DFL)
# -------------

file_tools.set_user_dir()
if Const.SYS == "win32":
  path = os.path.join(Const.PATH, "stdout.log")
  sys.stdout = open(path, "w")
  path = os.path.join(Const.PATH, "stderr.log")
  sys.stderr = open(path, "w")
GObject.threads_init()



__version__ = Const.VERSION
__author__ = Const.AUTHOR
__date__ = "2014-06-01"
__file__ = Const.SOFT # redéfini pour py2exe en attendant mieux

print("%s%s Copyright (C) 2007 %s\nThis program comes with ABSOLUTELY NO WARRANTY\nThis is free software, and you are welcome to redistribute it under certain conditions." % (Const.SOFT, __version__, __author__))

screen = Gdk.Screen.get_default()
css_provider = Gtk.CssProvider()
css_provider.load_from_path('gtk-widgets.css')
context = Gtk.StyleContext()
context.add_provider_for_screen(screen, css_provider,
                                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
class CombiButton(Gtk.CheckButton):
  """Boutons à cocher des combinaisons"""

  def __init__(self, label):
    Gtk.CheckButton.__init__(self, label)
    #self.n_type = n_type

def About():
    dialog = Gtk.AboutDialog()
    dialog.set_icon_from_file("glade/logo.png")
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size("glade/logo.png", 25, 25)
    dialog.set_logo(pixbuf)

    dialog.set_program_name(Const.SOFT)
    dialog.set_version(Const.VERSION)
    dialog.set_authors([Const.AUTHOR])
    dialog.set_website(Const.SITE_URL)
    dialog.set_comments("%s est un logiciel libre de calcul de structures planes, basé sur la méthode des déplacements, écrit en Python et GTK\n%s" % (Const.SOFT, Const.CONTACT))
    dialog.set_license("Vous pouvez modifier et redistribuer ce programme\nsous les conditions énoncées\npar la licence GNU GPL (version 2 ou ultérieure).\nUne copie de la licence GPL\nest dans le fichier « COPYING » fourni avec %s.\nAucune garantie n'est fournie pour l'utilisation de ce programme." % Const.SOFT)
    result = dialog.run()
    dialog.destroy()



class CombiBox(Gtk.VBox):
# revoir main_win, study
  def __init__(self, *args, **kwargs):
    Gtk.VBox.__init__(self, *args, **kwargs)
    self.set_name("combi")


  def fill_box(self, study, main_win):
    self.handler_list = []
    rdm = study.rdm
    try:
      status = rdm.status
    except AttributeError: # for EmptyRdm
      status = -1
    if status == -1:
      return
    Cases = rdm.Cases
    n_cases = len(Cases)
    try:
      ErrorCases = rdm.char_error
    except AttributeError:
      ErrorCases = []
    CombiCoef = rdm.CombiCoef
    combis = function.sortedDictKeys(CombiCoef)
    n_combi = len(combis)

    # création de la liste des cas de charge
    label = Gtk.Label(label="Cas de charge:")
    label.set_alignment(0.2, 0.7)
    self.pack_start(label, False, False, 0)

    for i, val in enumerate(Cases):
      button = CombiButton(val)
      id = button.connect("clicked", main_win.event_combi_button, i)
      self.handler_list.append(id)
      button.set_name(str(i))
      if val in ErrorCases:
        button.set_sensitive(False)
      self.pack_start(button, False, False, 0)
    # création de la liste des combinaisons
    if not n_combi == 0:
      label = Gtk.Label(label="Combinaisons:")
      label.set_alignment(0.2, 0.7)
      self.pack_start(label, False, False, 0)
    for i, val in enumerate(combis):
      button = CombiButton(val)
      n = i + n_cases
      # numéro pour combinaison négatif à partir de -1
      id = button.connect("clicked", main_win.event_combi_button, n)
      self.handler_list.append(id)
      button.set_name(str(n))
      self.pack_start(button, False, False, 0)
    self.show_all()


#####################################################################
#
#                       CLASSE PRINCIPALE
#
#####################################################################

class MainWindow(object):

  def __init__(self):
    # initialisation de la page d'accueil
    builder = self.builder = Gtk.Builder()
    builder.add_from_file("glade/main.glade")
# XXX enlever le mapping comme dans Editor
    builder.connect_signals(self)

    self.window = builder.get_object("window1")
    self.main_box = builder.get_object("main_box")
    self._ini_first_page()
    self.window.show() # après le resize
    self._handler_id = {}
    self._tabs = []
    self.studies = {}
    self.message = classDialog.Message()
    self.is_press = False # attribut pour le bouton "Clic Gauche"
    self.key_press = False # attribut pour la clavier "Control_L"

# XXX enlever dans main.glade
  def on_state_event(self, widget, event):
    """Evènement de type passage en plein écran ou retour"""
    #print event.type
    return
    if event.changed_mask & Gdk.WindowState.ICONIFIED:
      if event.new_window_state & Gdk.WindowState.ICONIFIED:
         print('Window was minimized!')
      else:
         print('Window was unminimized!')

  def on_w1_configure(self, widget, event):
    """Gère les évènements correspondant au redimensionnement de la fenetre"""
    #print("Main::_configure_event")
    pass

  def on_w1_destroy(self, widget, event=None):
    """Closing main window - Save user preferences"""
    self.new_version = False
    menu_button = self.builder.get_object("menu_cas")
    display_combi = menu_button.get_active() == True and 'on' or 'off'
    w, h = self.window.get_size()
    self.UP.save_w1_config(w, h, display_combi, self.options)
    if hasattr(self, "editor"):
      changes = self.editor.get_modified_studies()
      must_save = self._get_record_id(changes)
      if must_save is None:
      # must return True to prevent window closing
        return True
      ed_data = self.editor.data_editors
      for id in must_save:
          self._set_name(id)
          ed_study = ed_data[id]
          if not ed_study.path is None:
            self.editor.save_study(ed_study)

      self.UP.save_w2_config(self.editor._w, self.editor._h)

    # sauvegarde des préférences des études
    studies = self.studies
    for study in studies.values():
      self.save_drawing_prefs(study)

    Gtk.main_quit()

  def expose_first_page(self, widget, cr):
    """Méthode expose-event pour le drawingarea du lancement"""
    #print("expose_first_page", cr)
    cr.set_source_surface(self.surface, 0, 0)
    cr.paint()

  def configure_first_page(self, widget, event):
    """Méthode configure-event pour le drawingarea du lancement"""
    w_alloc = widget.get_allocated_width()
    h_alloc = widget.get_allocated_height()
    self.surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w_alloc, h_alloc)
    cr = cairo.Context(self.surface)

    cr.save()
    cr.set_source_rgb(1.0, 1.0, 1.0)
    cr.rectangle(0, 0, w_alloc, h_alloc)
    cr.fill()
    cr.restore()

    img = cairo.ImageSurface.create_from_png("glade/home.png")
    w, h = img.get_width(), img.get_height()
    x, y = (w_alloc-w)/2, (h_alloc-h)/2
    cr.set_source_surface(img, x, y)
    cr.paint()
    cr.save()
    cr.set_source_rgb(0.0, 0.0, 1.0)
    cr.set_font_size(60)
    cr.move_to(x+280, y+180)
    cr.show_text(Const.VERSION)
    cr.stroke()
    cr.restore()
    self.draw_first_tools(widget, x+20, max(h_alloc-70, 0))

  def draw_first_tools(self, layout, x, y):
    if hasattr(self, 'tools'):
      layout.move(self.tools, x, y)
      return
    hbox = Gtk.HBox(False, 10)
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_OPEN, '+')
    b.set_tooltip_text("Ouvrir une étude existante")
    b.connect('clicked', self.on_open_file)
    hbox.pack_start(b, False, False, 0)
    b = Gtk.Button()
    function.add_icon_to_button2(b, Gtk.STOCK_NEW, '+')
    b.set_tooltip_text("Ouvrir une nouvelle étude")
    b.connect('clicked', self.on_new_file)
    hbox.pack_start(b, False, False, 0)
    layout.put(hbox, x, y)
    hbox.show_all()
    self.tools = hbox
    #layout.queue_draw()

    #event = Gdk.Event(Gdk.EventType.EXPOSE)
    #layout.emit("configure-event", event)


  def _ini_first_page(self):
    """Dessine la page de lancement de l'application
    Read size User preferences"""
    self.new_version = None
    #self._set_user_dir()
    self.UP = classPrefs.UserPrefs()
    menu_button = self.builder.get_object("menu_cas")
    tag = self.UP.get_w1_box()
    menu_button.set_active(tag)
    menu_button.connect('activate', self._manage_combi_window)
    sizes = self.UP.get_w1_size()
    if sizes is None:
      height = Gdk.Screen.height()
      if height > 880:
        self.window.resize(700, 700)
    else:
      w, h = sizes
      self.window.resize(w, h)

    layout = Gtk.Layout()
    #layout.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#f3f3f3"))
    layout.connect("size-allocate", self.configure_first_page)
    layout.connect("draw", self.expose_first_page)
    layout.show()
    self.main_box.add(layout)
    self.draw_first_tools(layout, 0, 0)

    # new version search
    opt = self.UP.get_version()
    if opt == 0:
      try:
        GObject.timeout_add(1000, self._get_info_version, opt) # destroy if callback return False
      except:
        pass
    else:
      self.UP.save_version(opt-1)

    # options d'affichage (à déplacer?)
    self.options = self.UP.get_w1_options()


  # -----------------------------------------------------------
  #
  # Méthodes relatives au notebook des drawings
  #
  # -----------------------------------------------------------

  def _ini_application(self):
    """drawings notebook initilisation - button setup
    return drawing_book"""
    # suppression image accueil
    self.main_box.remove(self.main_box.get_children()[0])
    self.surface.finish()
    del(self.surface)
    del(self.tools)

    # drawings notebook ini
    book = Gtk.Notebook()
    book.set_scrollable(True)
    #book.set_show_tabs(False)

# provisoire en attendant version 2.20 de gtk
    b = Gtk.Button()
    b.connect('clicked', self.on_new_tab)
    function.add_icon_to_button(b, Gtk.STOCK_ADD)
    page = Gtk.HBox()
    book.append_page(page, b)
    self.book = book
    self._handler_id['book'] = book.connect("switch_page", self.on_switch_page)
    # ligne pour les messages
    hbox = Gtk.HBox()
    hbox.set_size_request(-1, 40)
    hbox.set_property('border_width', 4)
    self.message.ini_message(hbox) # évite pb avec singleton
    #self.bottom_info_box = hbox
    self.main_box.pack_start(book, True, True, 0)
    self.main_box.pack_start(hbox, False, True, 0)
    self.main_box.show_all()
    return book

  def _ini_drawing_page(self, position):
    """Initialisation d'un onglet de dessin"""
    #print "Main::_ini_drawing_page"
    book = self.main_box.get_children()[0]
    # initialisation
    if not isinstance(book, Gtk.Notebook):
      book = self._ini_application()
      self._set_buttons_ini()
    book.disconnect(self._handler_id["book"])

    self._add_book_page(book, position)
    tab = self.active_tab

    # scrolling arrows for notebook
    n_pages = book.get_n_pages()
    #if n_pages >= 2:
    #  book.set_show_tabs(True)
    self._handler_id['book'] = book.connect("switch_page", self.on_switch_page)

    layout = tab.layout
    layout.set_can_focus(True)
    layout.grab_focus()
    layout.connect("size-allocate", tab.configure_event)
# modif
    layout.connect("draw", tab.draw_event)
    tab.handler_layout = layout.connect("motion-notify-event", self.motion_notify_event)
    layout.connect("leave-notify-event", self.leave_notify_event)
    layout.connect("button-press-event", self.button_press_event)
    layout.connect("button-release-event", self._button_release_event)
    layout.connect("key-press-event", self._key_press_event)
    layout.connect("key-release-event", self._key_release_event)

  def _add_book_page(self, book, position):
    """Ajoute une page au notebook des dessins"""
    #print("Main::_add_book_page")
    tab = classDrawing.Tab(self)
    self.active_tab = tab
    vbox = Gtk.VBox(False, 0)
    w = self.window.get_allocated_width()-180
    hpaned = Gtk.HPaned()
    hpaned.set_position(w)
    hpaned.add1(tab.sw)

    menu_button = self.builder.get_object("menu_cas")
    if menu_button.get_active() == True:
      sw = self._make_combi_box(tab)
      hpaned.pack2(sw, False)
    else:
      tab.right_menu = None

    hpaned.show()
    vbox.pack_start(hpaned, True, True, 0)
    vbox.show()

    tab_box = Gtk.HBox(False, 2)

    tab_label = Gtk.Label() # gérer en fonction de la longueur dispo
    tab_label.set_padding(4, 0)
    tab.title = tab_label
    close_b = Gtk.Button()
    close_b.connect('clicked', self._on_remove_page, book, vbox)
    function.add_icon_to_button(close_b, Gtk.STOCK_CLOSE)
    tab_box.pack_start(tab_label, False, True, 0)
    tab_box.pack_start(close_b, False, True, 0)
    tab_box.show_all()
    self._tabs.insert(position, tab)
    book.insert_page(vbox, tab_box, position)
# à tester fonctionne pour les widgets mais évidemment pas pour les Tab
    #book.set_tab_reorderable(vbox, True)
    book.set_current_page(position)



  def _remove_page(self, book, n_page):
    """Fonction de suppression de page
    Attention le notebook n'est pas actualisé
    avant le changement de page qui suit"""
    studies = self.studies
    tabs = self._tabs
    closed_tab = tabs[n_page]
    opened_studies = [] # études ouvertes sur une autre page
    for tab in tabs:
      if tab is closed_tab:
        continue
      drawings = tab.drawings
      for drawing in drawings.values():
        id_study = drawing.id_study
        if not id_study in opened_studies:
          opened_studies.append(id_study)

    drawings = closed_tab.drawings
    for drawing in drawings.values():
      id_study = drawing.id_study
      if id_study in opened_studies:
        continue
      try:
        del (studies[id_study])
      except KeyError:
        continue

    if hasattr(self, "editor"):
      ed_data = self.editor.data_editors
      for id in list(ed_data):
        if id in opened_studies:
          continue
        del(self.editor.data_editors[id])
    del(self._tabs[n_page])
    frame = book.get_nth_page(n_page)
    # on déconnecte le changement de page pour éviter un numéro de page éroné
    book.disconnect(self._handler_id["book"])
    book.remove(frame)
    self._handler_id['book'] = book.connect("switch_page", self.on_switch_page)
    n_page = book.get_current_page()
    n_pages = book.get_n_pages()
    if n_page == n_pages-1:
      book.set_current_page(n_page-1)

  def _on_remove_page(self, button, book, frame):
    """Méthode de suppression d'une page"""
    n_page = book.page_num(frame)
    n_pages = self.book.get_n_pages()
    if n_pages == 2:
      return
    tab = self._tabs[n_page]
    if hasattr(self, "editor"):
      for drawing in tab.drawings.values():
        try:
          ed_data = self.editor.data_editors[drawing.id_study]
        except KeyError:
          continue
        if ed_data.is_changed:
          if file_tools.exit_as_ok_func2("Enregistrer le fichier '%s'?"  % ed_data.name):
            if ed_data.path is None:
              path = file_tools.recursive_file_select(self.UP.get_default_path())
              if not path is None:
                ed_data.path = path
            self.editor.save_study(ed_data)
    self._remove_page(book, n_page)

  def on_switch_page(self, widget=None, page=None, n=0):
    """Gestionnaire des évènements lors du changement de page du notebook"""
    #print 'Main::on_switch_page', n
    book = self.book
    n_pages = book.get_n_pages()
    if n == n_pages-1:
      book.stop_emission("switch-page")
      return
    self.active_tab = tab = self._tabs[n]
    drawing = tab.active_drawing
    if drawing is None:
      rdm_status = 0
      errors = []
    else:
      id_study = drawing.id_study
      study = self.studies[id_study]
      rdm_status = study.rdm.status
      errors = study.rdm.errors
    # mise à jour de l'éditeur
    if hasattr(self, "editor"):
      if self.editor.w2.get_window() is None:
        del (self.editor)
      else:
        self._update_editor()
    self._set_buttons_rdm(rdm_status)
    self._update_titles()
    self._show_message(errors, False)
    
  # -----------------------------------------------------------
  #
  # Méthodes relatives aux évènements
  #
  # -----------------------------------------------------------
  def _key_release_event(self, widget, event):
    tab = self.active_tab
    key = Gdk.keyval_name (event.keyval)
    if key == 'Control_L':
      self.key_press = False
      event = Gdk.Event(Gdk.EventType.MOTION_NOTIFY)
      tab.layout.emit("motion-notify-event", event)

# attention si la fenetre de pybar n'a pas le focus, les événements clavier ne sont pas interceptés alors que les évènements souris le sont.
  def _key_press_event(self, widget, event):
    key = Gdk.keyval_name (event.keyval)
    tab = self.active_tab
    is_selected  = tab.is_selected
    if key == 'Control_L':
      self.key_press = True
    elif key == 'Escape':
      tab.is_selected = False
      tab.remove_tools_box()
      watch = Gdk.Cursor.new(Gdk.CursorType.ARROW)
      tab.layout.get_root_window().set_cursor(watch)
      tab.set_surface(tab.area_w, tab.area_h)
      cr = cairo.Context(tab.surface)
      tab.paint_all_struct(cr, None, 1.)
      tab.layout.queue_draw()
    elif key == 'Return':
      if not is_selected:
        return
      selected = is_selected[0]
      if selected == 'draw':
        drawing = is_selected[1]
        tab.active_drawing = drawing
        tab.do_new_drawing(False)
        self._update_combi_box()
    elif key == 'Delete':
      if not is_selected:
        return
      selected = is_selected[0]
      if selected == 'value':
        drawing, n_case, legend = is_selected[1:]
        self.on_hide_value(None, drawing, n_case, legend)


  def _button_release_event(self, widget, event):
    #print('_button_release_event')
    self.active_tab.finish_dnd(event, self.is_press)
    self.is_press = False

  def motion_notify_event(self, area, event):
    #if Gtk.events_pending():
    #  return
    self.active_tab.start_dnd(area, event, self.is_press)
# mettre une info ici

  def leave_notify_event(self, layout, event):
    """événement : le curseur quitte la zone du layout"""
    #print("leave_notify_event")
    if not self.is_press is False:
      return
    tab = self.active_tab
    tab.set_surface(tab.area_w, tab.area_h)
    cr = cairo.Context(tab.surface)
    tab.paint_all_struct(cr, None, 1.)
    layout.queue_draw()
    self.is_press = False
    watch = Gdk.Cursor.new(Gdk.CursorType.ARROW)
    self.window.get_root_window().set_cursor(watch)

# Double clic : génére : press -> release -> press -> press -> 2Button -> release
  def button_press_event(self, widget, event):
    #print("button_press_event")
    tab = self.active_tab
    try:
      obj_selected = tab.is_selected
    except AttributeError:
      obj_selected = False
    if event.type == Gdk.EventType.BUTTON_PRESS:
      watch = Gdk.Cursor.new(Gdk.CursorType.FLEUR)
      if event.get_button()[1] == 1:
        self.is_press = (event.x, event.y)
        tab.motion = (0, 0) # provisoire, en attendant mieux
        if obj_selected is False:
          return
        drawing = obj_selected[1]
        status = drawing.status
        if obj_selected[0] == 'entry':
          entry = obj_selected[2]
          destroy_ev = Gdk.Event(Gdk.EventType.DESTROY)
          entry.emit("event", destroy_ev)
          tab.remove_entry_box()
          tab.remove_tools_box()
          tab.is_selected = ('draw', drawing)
          return

        if obj_selected[0] == 'curve':
          self._select_curve(drawing, obj_selected[2])
          return
        elif obj_selected[0] == 'draw':
          tab.layout.get_root_window().set_cursor(watch)
          self._select_drawing(obj_selected[1])
          return
        elif obj_selected[0] == 'info':
          tab.layout.get_root_window().set_cursor(watch)
          return
        elif obj_selected[0] == 'value':
          tab.layout.get_root_window().set_cursor(watch)
          return
        elif obj_selected[0] == 'node':
          content = tab.get_message()
          self.message.set_message(content)
          return
        elif obj_selected[0] == 'bar':
          content = tab.get_message()
          self.message.set_message(content)
          return
      elif event.get_button()[1] == 3:
        #self.is_press = (event.x, event.y)
        x, y = event.x, event.y
        if obj_selected is False:
          self._create_menu5(event)
          return True
        drawing = obj_selected[1]
        if obj_selected[0] == 'value':
            self._create_menu7(event, obj_selected[1], obj_selected[2], obj_selected[3])
            return
        if obj_selected[0] == 'curve':
            self._create_menu6(event, obj_selected[1], obj_selected[2], obj_selected[4])
            return
        if obj_selected[0] == 'node':
            widget.get_root_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.ARROW))
            node = obj_selected[2]
            # ajouter ici les menus pour les noeuds
            self._create_menu3(event, drawing, node)
            return
        if obj_selected[0] == 'bar':
            widget.get_root_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.ARROW))
            self._create_menu2(event, obj_selected[2])
            return
        self._create_menu1(event, obj_selected[1])
        return

    elif event.type == Gdk.EventType._2BUTTON_PRESS:
      if obj_selected is False:
        return
      drawing = obj_selected[1]
      status = drawing.status
      if obj_selected[0] == 'node':
        return
        # ajouter ici les menus pour les noeuds
      if obj_selected[0] == 'bar':
        self.on_bar_select(None, barre=obj_selected[2])
        return
      if obj_selected[0] == 'curve':
        self._select_curve(drawing, obj_selected[2])
        return
      if obj_selected[0] == 'info':
        if not drawing.title_id == obj_selected[2]:
          return
        self._on_edit_title(drawing, obj_selected[2])
        return
      if obj_selected[0] == 'value':
        self._on_edit_value(drawing, obj_selected[2], obj_selected[3])
        return
      # double clic

  def on_delete_value(self, widget, data):
    """Supprime une valeur sur une courbe"""
    drawing, n_curve, legend = data
    drawing.delete_value(n_curve, legend)
    drawing.s_case = n_curve
    drawing.del_patterns()
    tab = self.active_tab
    #tab.del_surface()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()

  def on_hide_value(self, widget, data):
    """Cache une valeur sur une courbe"""
    drawing, n_curve, legend = data
    drawing.set_hide_value(n_curve, legend)
    drawing.s_case = n_curve
    drawing.del_patterns()
    tab = self.active_tab
    #tab.del_surface()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()

  def on_set_anchor(self, widget, data):
    """Ancre une valeur sur le dessin"""
    drawing, n_curve, obj = data
    user_values = drawing.user_values
    tab = self.active_tab
    is_selected  = tab.is_selected
    barre = is_selected[3]
    if not drawing.status in user_values:
      user_values[drawing.status] = {}
    values = user_values[drawing.status]
    if not n_curve in values:
      values[n_curve] = {}
    if not barre in values[n_curve]:
      values[n_curve][barre] = {}
    value = values[n_curve][barre]
    pos = obj.is_selected[2]
    if pos is None:
       id_study = drawing.id_study
       study = self.studies[id_study]
       rdm = study.rdm
       arc = rdm.struct.Curves[barre]
       pos = arc.get_curve_abs(obj.is_selected[1], obj.is_selected[0], rdm.struct.Lengths)
       #pos = arc.pos[obj.is_selected[1]]
    value[pos] = {0: (0, 0, False)} # dx, dy, hidden
    drawing.del_patterns()
    #tab.del_surface()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()

  def on_display_value(self, widget, data):
    """Affiche les valeurs sur la courbe n_curve"""
    drawing, n_curve = data
    if widget.get_active():
      drawing.s_values.append(n_curve)
      drawing.restore_values(n_curve)
    else:
      # provisoire : astuce pour remettre les valeurs de la courbe s_curve
      if drawing.s_curve == n_curve: 
        drawing.restore_values(n_curve)
      try:
        drawing.s_values.remove(n_curve)
      except ValueError:
        pass
    self._do_new_drawing()

  def on_display_char(self, widget, data):
    """Ouvre un dessin du chargement"""
    drawing, n_curve, curve = data
    tab = self.active_tab
    #drawing = tab.active_drawing
    drawing.s_case = n_curve
    tab.add_char_drawing(drawing)

  def on_select_curve(self, widget, data):
    """Sélectionne une courbe sur un dessin depuis un menu"""
    drawing, n, curve = data
    self._select_curve(drawing, n)

  def _select_curve(self, drawing, n_curve):
    """Sélectionne une courbe sur un dessin"""
    #print("_select_curve", drawing.id)
    tab = self.active_tab
    tab.active_drawing = drawing
    id_study = drawing.id_study
    study = self.studies[id_study]
    rdm = study.rdm
    if drawing.status == 8:
      drawing.s_influ = n_curve
      content = drawing.get_influ_message(study, n_curve)
      self.message.set_message(content)
      return
    drawing.s_curve = n_curve

    drawing.del_patterns()
    #tab.del_surface()

    # actualisation dessin de chargement si il existe
    #char_drawing = drawing.char_drawing
    key = drawing.get_char_drawing()
    if not key is None:
      child = drawing.childs[key]
      child.s_case = n_curve
      child.del_patterns()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()

    content = tab.get_char_message(rdm, n_curve)
    self.message.set_message(content)

  def _on_edit_value(self, drawing, n_case, legend):
    """Modification de la position en x (sur la barre) de la légende"""
    tab = self.active_tab
    tab.on_show_value_box(drawing, n_case, legend)

  def _on_edit_title(self, drawing, info_id):
    """Action de modification du titre d'un dessin"""
    #print "_on_edit_title", info_id
    tab = self.active_tab
    tab.on_show_title_box(drawing)

  def on_select_drawing(self, widget, drawing):
    """Sélectionne le diagramme"""
    #print "on_select_drawing"
    self._select_drawing(drawing)

  def _select_drawing(self, drawing):
    #print('_select_drawing remettre')
    tab = self.active_tab
    prec_drawing = tab.active_drawing
    id_study = drawing.id_study
    study = self.studies[id_study]
    rdm = study.rdm
    if drawing.get_is_char_drawing():
      tab.do_new_drawing(False)
      content = tab.get_char_message(rdm, drawing.s_case)
      self.message.set_message(content)
      return
    tab.active_drawing = drawing
    tab.paint_drawings()
    self._fill_right_menu()
    self._update_combi_box()
    # maj de l'éditeur
    if hasattr(self, "editor") and not (prec_drawing is drawing):
      self._update_editor()
    self._update_titles()
    self._show_message(rdm.errors, False)
    self._set_buttons_rdm(rdm.status)

  def on_select_bars(self, widget, drawing):
    """Lance l'ouverture de la fenetre de choix des barres et remplace l'set s_influ_bars"""
    #tab = self.active_tab
    #drawing = tab.active_drawing
    id_study = drawing.id_study
    study = self.studies[id_study]
    rdm = study.rdm
    bars = rdm.struct.GetBarsNames()
# trier barre ?? XXX
    #bars.sort()
    try:
      s_influ_bars = drawing.s_influ_bars
    except AttributeError:
      s_influ_bars = []
    bars = file_tools.open_dialog_bars(bars, s_influ_bars)

    if bars is False or bars == []:
      return
    drawing.s_influ_bars = bars
    self._fill_right_menu()
    self._do_new_drawing()

  def on_node_display(self, widget, drawing):
    """Relance un affichage en fonction de l'état de l'option"""
    tab = self.active_tab
    tab.active_drawing = drawing
    drawing.options['Node'] = widget.get_active()
    self._do_new_drawing()


  def on_barre_display(self, widget, drawing):
    """Relance un affichage en fonction de l'état de l'option"""
    tab = self.active_tab
    tab.active_drawing = drawing
    drawing.options['Barre'] = widget.get_active()
    self._do_new_drawing()

  def on_axis_display(self, widget, drawing):
    """Relance un affichage en fonction de l'état de l'option"""
    tab = self.active_tab
    tab.active_drawing = drawing
    drawing.options['Axis'] = widget.get_active()
    self._do_new_drawing()

  def on_title_display(self, widget, drawing):
    """Affichage du titre du dessin"""
    tab = self.active_tab
    tab.active_drawing = drawing
    drawing.set_title_visibility(widget.get_active())
    drawing.options['Title'] = widget.get_active()
    self._do_new_drawing()

  def on_series_display(self, widget, drawing):
    """Affiche les légendes des courbes"""
    tab = self.active_tab
    tab.active_drawing = drawing
    drawing.set_series_visibility(widget.get_active())
    drawing.options['Series'] = widget.get_active()
    self._do_new_drawing()

  def on_synchronise(self, widget, drawing):
    drawing.options['Sync'] = widget.get_active()
    if widget.get_active():
      drawing.s_cases = drawing.parent.s_cases
      drawing.s_case = drawing.parent.s_case
    else:
      drawing.s_cases = copy.copy(drawing.parent.s_cases)
    
    self._do_new_drawing()
    self._fill_right_menu()
    self._update_combi_box()

  def on_add_sigma_drawing(self, widget, drawing):
    """Ajoute un dessin des contraintes normales"""
    tab = self.active_tab
    id_study = drawing.id_study
    study = self.studies[id_study]
    tab.add_sigma_drawing(drawing, study)

  def on_add_drawing(self, widget, drawing):
    """Ajoute un diagramme à partir du diagramme sélectionné"""
    #print "on_add_drawing"
    tab = self.active_tab
    id_study = drawing.id_study
    study = self.studies[id_study]
    tab.add_drawing(drawing, study)
    self._fill_right_menu()
    self._update_combi_box()

  def save_drawing_prefs(self, study):
    """"Sauve les préférences du dessin de l'étude study"""
    #print "save_drawing_prefs"
    id_study = study.id
    tab = self.active_tab
    rdm = study.rdm
    if isinstance(rdm, classRdm.EmptyRdm):
      return
    xml = rdm.struct.XML
    root = xml.getroot()
    node = xml.find('draw')
    if not node is None:
      root.remove(node)
    drawing_pref = ET.SubElement(root, "draw", {"id": "prefs"})
    for id in tab.drawings:
      drawing = tab.drawings[id]
      if not drawing.id_study == id_study:
        continue
      if not drawing.get_is_parent():
        continue
      node1 = drawing.get_xml_prefs(drawing_pref)
      for key in drawing.childs:
        d = drawing.childs[key]
        node2 = d.get_xml_prefs(node1)
    path = study.path
    if path is None:
      return
    function.indent(root)
    #print ET.tostring(root)
    #return
    try:
      xml.write(path, encoding="UTF-8", xml_declaration=True)
    except IOError:
      print("Ecriture impossible dans %s" % path)



  def on_save_drawings(self, widget, drawing):
    """Enregistre l'état de l'étude (graphes et préférences)"""
    tab = self.active_tab
    id_study = drawing.id_study
    study = self.studies[id_study]
    self.save_drawing_prefs(study)
    tab.remove_drawings_by_study(drawing)
    self._fill_right_menu()
    self._update_combi_box()
    if hasattr(self, "editor"):
      try:
        del(self.editor.data_editors[id_study])
      except KeyError:
        pass
      self._update_editor()
    self._update_titles()
    drawing = tab.active_drawing
    if drawing is None:
      status = 2
    else:
      status = study.rdm.status
    self._set_buttons_rdm(status)


  def on_del_drawing(self, widget, drawing):
    """Supprime le diagramme sélectionné"""
    #print "on_del_drawing", len(self.studies), drawing.id_study
    tab = self.active_tab
    id_study = drawing.id_study
    study = self.studies[id_study]
    if drawing.get_is_parent():
      self.save_drawing_prefs(study)
    tab.remove_drawing(drawing)
    self._fill_right_menu()
    self._update_combi_box()
    if hasattr(self, "editor"):
      try:
        del(self.editor.data_editors[id_study])
      except KeyError:
        pass
      self._update_editor()
    self._update_titles()
    drawing = tab.active_drawing
    if drawing is None:
      status = 2
    else:
      status = study.rdm.status
    self._set_buttons_rdm(status)

  def on_bar_select(self, widget, barre):
    tab = self.active_tab
    drawing = tab.active_drawing
    id_study = drawing.id_study
    study = self.studies[id_study]
    li = drawing.get_bar_drawings()
    for key in li:
      child = drawing.childs[key]
      child.draw_new_bar(tab, study.rdm.struct, barre.name) 
    drawing.s_bar = barre.name

  def on_del_influ(self, widget, data):
    """Efface une courbe de ligne d'influence donnée par n"""
    drawing, n, curve = data
    try:
      del(drawing.user_values[drawing.status][n])
    except KeyError:
      pass
    del(drawing.influ_list[n])
    drawing.s_influ = None
    self._do_new_drawing()


  def open_node_dialog(self, widget, node):
    """Clic droit sur un noeud à terminer ou supprimer"""
    pass

# --------------------------------------------------
#
#                  Menus contextuels
#
# --------------------------------------------------

# Modif GTK3 popup devient self.popup pour que ça marche ??
# XXX tester s'il faut laisser self.popup plutot que menu_cont.popup

  def _create_menu1(self, event, drawing):
    """Crée et affiche le menu contextuel pour le survol zone drawing
 """
    study = self.studies[drawing.id_study]
    rdm = study.rdm

    menu_cont = classCMenu.CMenu(self)
    menu_cont.get_menu1(drawing, rdm)
    #self.popup_menu = menu_cont.uimanager.get_widget('/popup')
    self.popup.popup(None, None, None, None, event.get_button()[1], event.time)
    return True

  def _create_menu2(self, event, barre):
    """Crée et affiche le menu contextuel survol barre"""
    tab = self.active_tab
    drawing = tab.active_drawing
    id_study = drawing.id_study
    study = self.studies[id_study]
    rdm = study.rdm
    menu_cont = classCMenu.CMenu(self)
    menu_cont.menu2(barre, drawing, rdm)
    self.popup.popup(None, None, None, None, event.get_button()[1], event.time)
    return True

  # désactivé, ne pas effacer
  def _create_menu3(self, event, drawing, node):
    """Menu contextuel survol des noeuds"""
    menu_cont = classCMenu.CMenu(self)
    menu_cont.get_menu3(node, drawing)
    popup_menu = menu_cont.uimanager.get_widget('/popup')
    if not popup_menu == None:
      popup_menu.popup(None, None, None, None, event.get_button()[1], event.time)

  def _create_menu4(self, event, chart):
    """Menu contextuel survol"""
    pass


  def _create_menu5(self, event):
    """Menu contextuel survol zone vide"""
    menu_cont = classCMenu.CMenu(self)
    menu_cont.get_menu5()
    self.popup.popup(None, None, None, None, event.get_button()[1], event.time)
    return True

  def _create_menu6(self, event, drawing, n_curve, curve):
    """Menu contextuel survol courbe"""
    #print "menu6", n_curve, curve
    status = drawing.status
    menu_cont = classCMenu.CMenu(self)
    if status == 8:
      menu_cont.get_menu4(drawing, n_curve, curve)
    else:
      menu_cont.get_menu6(drawing, n_curve, curve)
    #popup_menu = menu_cont.uimanager.get_widget('/popup')
    #if not popup_menu == None:
    #  popup_menu.popup(None, None, None, None, event.get_button()[1], event.time)
    self.popup.popup(None, None, None, None, event.get_button()[1], event.time)
    return True

# voir utilité des args
  def _create_menu7(self, event, drawing, n_curve, legend):
    """Menu contextuel survol valeur courbe"""
    menu_cont = classCMenu.CMenu(self)
    menu_cont.menu7(drawing, n_curve, legend)
    #popup_menu = menu_cont.uimanager.get_widget('/popup')
    #if not popup_menu == None:
    #  popup_menu.popup(None, None, None, None, event.get_button()[1], event.time)
    self.popup.popup(None, None, None, None, event.get_button()[1], event.time)
    return True

  # -----------------------------------------------------------
  #
  # Méthodes relatives au menu des combinaisons et cas
  #
  # -----------------------------------------------------------

  def _click_close_combi(self, widget):
    """Gère l'évènement de fermeture de la boite des combinaisons"""
    #print 'Main::_click_close_combi'
    menu_button = self.builder.get_object("menu_cas")
    menu_button.set_active(False)

  def _close_combi(self):
    """Ferme la boite de gestion des combinaisons"""
    book = self.book
    n_pages = book.get_n_pages()
    for i in range(n_pages-1): # dernier onglet = bouton
      page = book.get_nth_page(i)
      hbox = page.get_children()[0]
      child = hbox.get_children()
      if not len(child) == 2:
        break
      sw = child[1]
      hbox.remove(sw)
      tab = self._tabs[i]
      tab.right_menu = None

  def _open_combi(self, widget=None):
    """Ouvre la boite de gestion des combinaisons"""
    #print 'Main::_open_combi'
    book = self.book
    n_pages = book.get_n_pages()
    for i in range(n_pages-1): # dernier onglet pour bouton
      book_page = book.get_nth_page(i)
      paned = book_page.get_children()[0]
      tab = self._tabs[i]
      sw = self._make_combi_box(tab)
      paned.add2(sw)
      self._fill_right_menu(i)
    self._update_combi_box()


  def _manage_combi_window(self, widget):
    """Gère l'évènement d'ouverture ou de fermeture de la fenetre des combi"""
    #print "Main::_manage_combi_window"
    if not widget.get_active():
      self._close_combi()
    else:
      self._open_combi()

  def _make_combi_box(self, tab):
    """Crée la boite pour les combi (sw, bouton fermeture, box pour contenu
    Retourne la zone (box) pour le contenu"""
    #print("_make_combi_box")
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    #color = Gdk.RGBA(0.6, 0.6, 1, 1)
    #sw.override_background_color(Gtk.StateType.NORMAL, color)
    pbox = Gtk.VBox(False, 0)
    #pbox.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(.5,.5,.5,1.))

    #sw.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("#ffffff"))
    # close button
    align = Gtk.Alignment.new(1, 1, 0, 0)
    image = Gtk.Image()
    image.set_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
    button = Gtk.Button()
    button.set_relief(Gtk.ReliefStyle.NONE)
    button.connect('clicked', self._click_close_combi)
    button.add(image)
    align.add(button)
    pbox.pack_start(align, False, False, 2)
    # combi and cas in box
    sw.add_with_viewport(pbox)
    sw.show_all()
    tab.right_menu = pbox
    return sw

  def _fill_right_menu(self, n=None):
    """Supprime et crée un nouveau contenu dans la boite des menu de droite"""
    #print "_fill_right_menu"
    if n is None:
      tab = self.active_tab
    else:
      tab = self._tabs[n]
    box = tab.right_menu
    if box is None:
      return
    drawing = tab.active_drawing
    if drawing is None:
      self._fill_combi_menu(tab, box)
    elif drawing.status == 8:
      self._fill_influ_menu(tab, box)
    else:
      self._fill_combi_menu(tab, box)


  def _fill_combi_menu(self, tab, box):
    """Supprime et crée un nouveau contenu dans la boite des combinaisons"""
    #print "_fill_combi_menu"
    drawing = tab.active_drawing
    childs = box.get_children()
    try:
      child = childs[1]
      box.remove(child)
    except IndexError:
      pass
    if drawing is None: 
      return
    pbox = CombiBox(False, 0)
    box.pack_start(pbox, False, False, 0)
    study = self.studies[drawing.id_study]
    pbox.fill_box(study, self)

# renommer
  def _update_combi_box(self):
    """Positionne la sensibilité et l'activité des boutons des cas et combis en fonction du status et des erreurs rencontrées"""
    #print "_update_combi_box"
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    box = tab.right_menu
    if box is None:
      return
    
    if drawing.status == 8:
      box.set_sensitive(True)
      return
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    view = drawing.get_combi_view(rdm, self._get_has_textview())
    if view is None:
      box.set_sensitive(False)
      return
    box.set_sensitive(True)
    pbox = box.get_children()[1]
    buttons = pbox.get_children()
    i = 0
    for button in buttons:
      if not isinstance(button, CombiButton):
        continue
      ind = int(button.get_name())
      button.handler_block(pbox.handler_list[ind])
      etat = view[i]
      button.set_active(etat[0])
      button.set_sensitive(etat[1])
      button.handler_unblock(pbox.handler_list[ind])
      i += 1


  def _event_combi_radio(self, widget):
    """Fonctionnement des boutons des combis en mode radio"""
    #print "_event_combi_radio"
    tab = self.active_tab
    box = tab.right_menu.get_children()[1]
    drawing = tab.active_drawing
    if widget.get_active():
      buttons = box.get_children()
      for button in buttons:
        if not isinstance(button, CombiButton):
          continue
        ind = int(button.get_name())
        if widget is button:
          drawing.s_case = ind
          drawing.s_curve = ind
          continue
        button.handler_block(box.handler_list[ind])
        button.set_active(False)
        button.handler_unblock(box.handler_list[ind])
      return True
    ind = int(widget.get_name())
    widget.handler_block(box.handler_list[ind])
    widget.set_active(True)
    widget.handler_unblock(box.handler_list[ind])
    return False

  def _event_combi_check(self, widget, n_case):
    """Fonctionnement des boutons des combis en mode case à cocher"""
    #print "_event_combi_check", n_case
    tab = self.active_tab
    drawing = tab.active_drawing
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    s_cases = drawing.s_cases
    if widget.get_active():
      if not n_case in s_cases:
        s_cases.append(n_case)
        drawing.s_curve = n_case
    else:
      if n_case in s_cases:
        s_cases.remove(n_case)
      try:
        drawing.s_curve = s_cases[0]
      except IndexError:
        drawing.s_curve = None
    s_cases.sort()
    content = tab.get_char_message(rdm, drawing.s_curve)
    self.message.set_message(content)

  def event_menu_button(self, widget, data):
    """Evènement sur un bouton à cocher de combinaisons depuis le menu contextuel"""
    drawing, n_case = data
    #drawing = tab.active_drawing
    status = drawing.status
    if status in [0, 2, 3]:
      drawing.s_case = n_case
    else:
      self._event_combi_check(widget, n_case)
    self._do_new_drawing()

  def event_combi_button(self, widget, n_case):
    """Evènement sur un bouton à cocher de combinaisons"""
    tab = self.active_tab
    drawing = tab.active_drawing
    status = drawing.status
    study = self.studies[drawing.id_study]
    sw = tab.sw
    if self._get_has_textview() == True:
      is_drawing = False
    else:
      is_drawing = True

    # mode radio
    if not is_drawing or status in [0, 2, 3]:
      if not self._event_combi_radio(widget):
        return
    # mode checkbutton
    else:
      self._event_combi_check(widget, n_case)
    if is_drawing:
      self._do_new_drawing()
    else:
      textview = sw.get_child()
      self._print_message(textview)

    # Maj sensibilité boutons
    self._set_buttons_rdm(study.rdm.status)


  # -----------------------------------------------------------
  #
  # Méthodes relatives à la mise à jour des boutons et titre
  #
  # -----------------------------------------------------------

  def _update_titles(self):
    """Affichage du titre de la zone de dessin"""
    #print "Main::update_titles"
    book = self.book
    w1 = self.window
    tab = self.active_tab
    tab_label = tab.title
    drawing = tab.active_drawing
    if drawing is None:
      w1.set_title("%s" % Const.SOFT)
      tab_label.set_text("(Vide)")
      tab_label.set_tooltip_text("")
      return
    status = drawing.status
    study = self.studies[drawing.id_study]
    name = study.name
    path = study.path
    tab_label.set_text(name)
    if not path is None:
      tab_label.set_tooltip_text(path)

    titre = "%s - " % name
    if status == 0:
      titre += "Noeuds"
    elif status == 1:
      titre += "Barres"
    elif status == 2:
      titre += "Chargement"
    elif status == 3:
      titre += "Réaction d'appuis"
    elif status == 4:
      titre += "Effort normal"
    elif status == 5:
      titre += "Effort tranchant"
    elif status == 6:
      titre += "Moment fléchissant"
    elif status == 7:
      titre += "Déformée"
    elif status == 8:
      titre += "Ligne d'influence"
    w1.set_title("%s - %s" % (Const.SOFT, titre))

  def _set_buttons_ini(self):
    """Activation des boutons après la page d'accueil"""
    items = [
		"menu_save",
		"menu_save_as",
		"menu_save_copy",
		"menu_export",
		"menu_reload",
		"menu_cas",
		"button_export",
		"button_zoom_best",
		"button_zoom_more",
		"button_zoom_less",
		"button_chart_less",
		"button_chart_more",
		]
    # activation des boutons
    for item in items:
      widget = self.builder.get_object(item)
      widget.set_sensitive(True)

  def _set_buttons_rdm(self, rdm_status):
    """Fonction qui sert à modifier la sensibilité des boutons
    en fonction de l'état de l'objet rdm"""
    #print "_set_buttons_rdm", rdm_status
    items1 = ["button_ddl",
		"menu_ddl",
		"button_eq",
		"menu_eq",
		"button_barre",
		"menu_barre",
		"menu_char",
		"button_char",
		"menu_degree",
		"menu_reac",
		"button_reac",
		"menu_n",
		"button_n",
		"menu_v",
		"button_v",
		"menu_m",
		"button_m",
		"menu_defo",
		"button_defo",
		"menu_influ",
		"button_influ",
			]

    items2 = ["button_build",
		"menu_build"
	]
    items3 = ["button_editor",
		"button_error",
		"menu_editor",
		"menu_error",
		]
    # activation des boutons
    if rdm_status == 2:
      status = True
    else:
      status = False
    for item in items1:
      widget = self.builder.get_object(item)
      widget.set_sensitive(status)
    if rdm_status == -1:
      status = False
    else:
      status = True
    for item in items2:
      widget = self.builder.get_object(item)
      widget.set_sensitive(status)
    if rdm_status == -1:
      status = False
    else:
      status = True
    for item in items3:
      widget = self.builder.get_object(item)
      widget.set_sensitive(status)



  # -----------------------------------------------------------
  #
  # Méthodes relatives aux actions sur des boutons
  #
  # -----------------------------------------------------------

  def on_zoom_more(self, widget):
    """Agrandit la taille du drawing_area"""
    tab = self.active_tab
    if not tab.status == 0:
      return
    drawing = tab.active_drawing
    if drawing is None: 
      return
    study = self.studies[drawing.id_study]
    drawing.set_zoom("+")
    drawing.set_scale(study.rdm.struct)
    tab.get_layout_size([drawing])
    drawing.del_patterns()
    #tab.del_surface()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()

  def on_zoom_100(self, widget):
    """Agrandit la taille du drawing_area"""
    tab = self.active_tab
    if not tab.status == 0:
      return
    drawing = tab.active_drawing
    if drawing is None: 
      return
    status = drawing.status
    study = self.studies[drawing.id_study]
    w, h = drawing.width, drawing.height
    m = Const.AREA_MARGIN_MIN
    sw = tab.sw
    sw_w = float(sw.get_hadjustment().get_page_size()) - 2*m
    sw_h = float(sw.get_vadjustment().get_page_size()) - 2*m
    if w == 0 and h == 0:
      return
    if w == 0:
      coef = sw_h/h
    elif h == 0:
      coef = sw_w/w
    else:
      coef = min(sw_w/w, sw_h/h)
    drawing.zoom_best(coef, study.rdm.struct)
    tab.get_layout_size(list(tab.drawings.values()))
    drawing.del_patterns()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()


  def on_zoom_less(self, widget):
    """Agrandit la taille du drawing_area"""
    tab = self.active_tab
    if not tab.status == 0:
      return
    drawing = tab.active_drawing
    if drawing is None: 
      return
    status = drawing.status
    study = self.studies[drawing.id_study]
    drawing.set_zoom("-")
    drawing.set_scale(study.rdm.struct)
    drawing.del_patterns()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()


  def on_chart_zoom_more(self, widget):
    tab = self.active_tab
    if not tab.status == 0:
      return
    self._set_chart_zoom(None, 'more')

  def on_chart_zoom_less(self, widget):
    tab = self.active_tab
    if not tab.status == 0:
      return
    self._set_chart_zoom(None, 'less')

  def _set_chart_zoom(self, widget=None, tag='more'):
    """Augmente ou diminue la valeur du zoom du graphe"""
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None: 
      return
    #zoom = drawing.chart_zoom
    if tag == "more":
      zoom = 1.2
    else:
      zoom = 1 / 1.2
    status = drawing.status
    if status >= 4:
      if status in drawing.chart_zoom:
        drawing.chart_zoom[status] *= zoom
      else:
        drawing.chart_zoom[status] = zoom

    self._do_new_drawing()

  def on_recents(self, widget=None):
    import urllib
    try:
      book = self.book
    except AttributeError:
      self._ini_drawing_page(0)
    path = widget.get_current_uri()
    p = urllib.parse.urlparse(path)
    path = os.path.abspath(os.path.join(p.netloc, p.path))
    path = urllib.parse.unquote(path)
    GObject.idle_add(self._on_open_study, path) # permet à la zone de dessin de se mettre en place

  def _on_open_study(self, path):
    self._open_study(path)
    self._update_titles()
    if hasattr(self, "editor"):
      self._update_editor()

  def on_open_file(self, widget=None):
    """Evènement d'ouverture d'une étude existante"""
    try:
      book = self.book
    except AttributeError:
      self._ini_drawing_page(0)
    
    path = self.UP.get_default_path()
    path = file_tools.file_selection(path)
    #print(path)
    self._on_open_study(path)
    #self._update_titles()
    #if hasattr(self, "editor"):
    #  self._update_editor()

  def on_new_tab(self, widget):
    """Evènement d'ouverture d'un onglet"""
    #print "on_new_tab"
    try:
      book = self.book
      pos = book.get_n_pages() - 1
    except AttributeError:
      pos = 0
    self._ini_drawing_page(pos)
    if hasattr(self, "editor"):
      self._update_editor()
    self._update_titles()



  def _write_save_file(self, file):
    """Ecriture du fichier de sauvegarde"""
    #print "_write_save_file"
    tab = self.active_tab
    study = self.studies[tab.active_drawing.id_study]
    content = study.rdm.struct.RawReadFile()
    try:
      f = open(file, 'w')
      f.write(content)
      f.close()
    except IOError as e: 
      content = ("%s" % e, 0) # formatage obligatoire
      classDialog.Message().set_message(content)
    except:
      content = ("Enregistrement impossible", 0)
      classDialog.Message().set_message(content)

  def _open_study(self, path):
    """Ouverture d'une étude dans l'onglet actif"""
    #print("_open_study")
    def ConvertDXF2XML(path): # pour test
      return path[-3:]+"dat"

    book = self.book
    page = book.get_current_page()
    tab = self.active_tab
    if not path:
      return False
    if os.path.splitext(path)[1].lower() == '.dxf':
      #path = ConvertDXF2XML(path) # convertit et retourne le chemin du .dat
      if path is None:
        return False
    self.UP.save_default_path(os.path.dirname(path))
    if self._file_is_closed(path):
      study, drawings = tab.add_study(path, self.options)
      if drawings is None:
        self._show_message([("Une erreur s'est produite dans %s" % path, 0)])
        return
      if drawings == []:
        self._show_message(study.rdm.errors)
        return
      tab.get_layout_size(drawings)
      tab.configure_event(tab.layout)
      tab.layout.queue_draw()

      rdm = study.rdm
      self._fill_right_menu()
      self._update_combi_box()
      rdm_status = rdm.status
      self._set_buttons_rdm(rdm_status)
      if not rdm_status in [-1, 0]:
        self._write_save_file('%s.dat~' % path[:-4])
      self._show_message(rdm.errors)
    else:
      file_tools.open_as_ok_func(path)

  def on_save(self, widget=None):
    """Evènement d'enregistrement d'une étude modifiée"""
    #print "Main::_on_save"
    if not hasattr(self, 'editor'):
      content = ("Etude déjà enregistrée ou vide", 2)
      classDialog.Message().set_message(content)
      return
    if not hasattr(self.editor, 'w2'):
      content = ("Etude déjà enregistrée", 2)
      classDialog.Message().set_message(content)
      return
    win = self.editor.w2.get_window()
    if win is None:
      content = ("Etude déjà enregistrée", 2)
      classDialog.Message().set_message(content)
      return
    self.update_from_editor()

  def on_save_as(self, widget):
    """Enregistre une étude et l'ouvre à la place de l'étude précédente"""
    #print "on_save_as"
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    if isinstance(rdm, classRdm.EmptyRdm):
      self.on_save()
      return

    content = rdm.struct.RawReadFile()
    path = file_tools.file_save(self.UP.get_default_path())
    if not path:
      return
    self.UP.save_default_path(os.path.dirname(path))
    if not file_tools.save_as_ok_func(path):
      return
    try:
      f = open(path, 'w')
      f.write(content)
      f.close()
    except IOError as e: 
      content = ("%s" % e, 0) # formatage obligatoire
      classDialog.Message().set_message(content)
      return
    name = os.path.basename(path)
    if self._file_is_closed(path):
      rdm.struct.RenameObject(path)
      study.path = path
      study.name = name
      drawing.set_status(1)
      self._do_new_drawing()
    else:
      content = ("Enregistrement impossible: étude déjà ouverte", 0)
      classDialog.Message().set_message(content)
    # mise à jour de la fenetre de l'éditeur
    if hasattr(self, "editor"):
      self._update_editor()
    self._update_titles()
    self._update_combi_box()

  def on_save_copy(self, widget):
    """Enregistre une étude et l'ouvre à la place de l'étude précédente"""
    #print "on_save_copy"
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    if isinstance(rdm, classRdm.EmptyRdm):
      content = ("Impossible de copier une étude vide", 1)
      classDialog.Message().set_message(content)
      return

    content = rdm.struct.RawReadFile()
    path = file_tools.file_save(self.UP.get_default_path())
    if not path:
      return
    self.UP.save_default_path(os.path.dirname(path))
    if not file_tools.save_as_ok_func(path):
      return
    try:
      f = open(path, 'w')
      f.write(content)
      f.close()
    except IOError as e: 
      content = ("%s" % e, 0)
      classDialog.Message().set_message(content)

  def on_reload(self, widget):
    """Recharge l'étude active"""
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    if isinstance(rdm, classRdm.EmptyRdm):
      return
    structure = classRdm.StructureFile(study.path)
    if structure.status == -1: # suppression fichier ou erreur
      content = ("Une erreur est survenue durant le chargement", 0)
      classDialog.Message().set_message(content)
      return
    study.rdm = classRdm.R_Structure(structure)
    self._do_new_drawing()
    if hasattr(self, "editor"):
      self._update_editor()
    self._update_titles()
    self._fill_right_menu()
    self._update_combi_box()


  def on_new_file(self, widget):
    """Ouverture d'une nouvelle étude dans l'onglet actif"""
    try:
      book = self.book
    except AttributeError:
      self._ini_drawing_page(0)
    GObject.idle_add(self.on_new_study) # permet à la zone de dessin de se mettre en place

  def on_new_study(self, widget=None, x=None, y=None):
    """Ouverture d'une nouvelle étude dans l'onglet actif"""
    book = self.book
    current_page = book.get_current_page()
    tab = self._tabs[current_page]
    study, drawing = tab.add_empty_study(self.options, x, y)
    if hasattr(tab, "surface"):
      #tab.del_surface()
      tab.configure_event(tab.layout)
    else:
      event = Gdk.Event(Gdk.EventType.CONFIGURE)
      tab.layout.emit("configure-event", event)

    tab.layout.queue_draw()
    name = study.name

    if hasattr(self, "editor"):
      self._update_editor()
    else:
      self.editor = classEditor.Editor(study, self)
      self.editor.w2.connect("delete-event", self._destroy_editor)
    self._update_titles()
    self._set_buttons_rdm(0)
    self._fill_right_menu()
    self._update_combi_box()



  def _file_is_closed(self, path):
    """Vérifie si une étude de chemin path est déjà ouverte"""
    #print "Main::_file_is_closed"
    #for tab in self._tabs:
    for study in self.studies.values():
      if study.path == path:
        return False
    return True


  def on_open_editor(self, widget):
    """Ouverture de l'éditeur"""
    #print "Main::_open_editor"
    if hasattr(self, 'editor') and not self.editor.w2 is None:
      self.editor.w2.present()
    else:
  
      book = self.book
      n_pages = book.get_n_pages()
      current_page = book.get_current_page()
      tab = self.active_tab
      drawing = tab.active_drawing
      if drawing is None:
        return
      study = self.studies[drawing.id_study]

      self.editor = classEditor.Editor(study, self)
      self.editor.w2.connect("delete-event", self._destroy_editor)
      #self.editor.record_button.connect("clicked", self.update_from_editor)


  def on_edit_ddl(self, widget):
    """Ouvre le textview pour les résultats numériques"""
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    if tab.status == 1:
      tab.status = 0
      self._expose_commun(drawing.status)
      self._update_combi_box()
      return
    tab.status = 1
    self._textview_commun()
    self._clear_sw_content()
    textview = self._add_textview()
    self._print_message(textview)
    self._update_combi_box()

  def on_edit_error(self, widget):
    """Ouvre le textview pour les messages d'erreurs"""
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    if tab.status == 2:
      tab.status = 0
      self._expose_commun(drawing.status)
      self._update_combi_box()
      return
    self._textview_commun()
    tab.status = 2
    self._clear_sw_content()
    textview = self._add_textview()
    self._print_message(textview)

  def on_edit_eq(self, widget):
    """Ouvre le textview pour l'affichage des équations"""
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    if tab.status == 3:
      tab.status = 0
      self._expose_commun(drawing.status)
      self._update_combi_box()
      return
    status = drawing.status
    if not status in [4, 5, 6, 7, 8]:
      return
    if status == 8 and drawing.s_influ is None:
      return
    if not drawing.status == 8:
      self._textview_commun()
    tab.status = 3
    self._clear_sw_content()
    textview = self._add_textview()
    self._print_message(textview)


  def _textview_commun(self):
    tab = self.active_tab
    box = tab.right_menu
    if box is None:
      return
    pbox = box.get_children()[1]
    if pbox.get_name() == 'influ':
      self._fill_combi_menu(tab, box)

# not supported
  def _export_jpg(self, file, reso):
    """Exporte le tracé au format jpeg"""
    print("not implemented yet")
    #return
    self.active_tab.draw_jpg_file(file)


  def _export_jpgsauv(self, file, reso):
    """Exporte le tracé au format jpeg"""
    tab = self.active_tab
    area = tab.layout
    width = tab.area_w
    height = tab.area_h
    pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)

    rect = (0, 0, width, height)
    tab.draw_event(area, rect)
    try:
      drawable = area.bin_window
    except AttributeError:
      return
    colormap = Gdk.colormap_get_system() 
    pixbuf.get_from_drawable(drawable, colormap, 0, 0, 0, 0, width, height)
    pixbuf.save(file, "jpeg", {"quality": str(reso)})

  def _export_svg(self, file):
    """Exporte le tracé au format svg"""
    self.active_tab.draw_svg_file(file)

  def _export_png(self, file):
    """Exporte le tracé au format svg"""
    self.active_tab.draw_png_file(file)

  def on_export(self, widget):
    """Effectue une sauvegarde de l'écran au format jpg ou svg"""
    tab = self.active_tab
    if not tab.status == 0:
      return
    drawing = tab.active_drawing
    try:
      status = drawing.status
    except AttributeError:
      status = -1
    if status == -1:
      return
    data = file_tools.file_export(self.UP.get_default_path())
    if data is None:
      return
    file = data[0]
    format = data[1]
    if not file_tools.save_as_ok_func(file):
      return
    watch = Gdk.Cursor.new(Gdk.CursorType.WATCH)
    self.window.get_root_window().set_cursor(watch)

    if format == 'JPEG': # ne fonctionne plus
      reso = file_tools.open_dialog_resol()
      if reso == False:
        return
      self._export_jpg(file, reso)
    if format == 'PNG':
      self._export_png(file)
    elif format == 'SVG':
      self._export_svg(file)
    watch = Gdk.Cursor.new(Gdk.CursorType.ARROW)
    self.window.get_root_window().set_cursor(watch)

  def on_about(self, widget):
    About()

  def _get_info_version(self, value):
    """Vérifie la dernière version et lance Dialog - Return False"""
    #print "_get_info_version", self.new_version, value
    if self.new_version is None:
      return True
    if self.new_version is False:
      return False

    self._open_dialog_version(self.new_version)
    return False


  def _open_dialog_version(self, last):
    """Ouverture du Dialog de la nouvelle version"""
    dialog = Gtk.Dialog("Nouvelle version",
			None,
			Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
			(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
    dialog.set_icon_from_file("glade/logo.png")
    text = "La version %s de %s est disponible." % (last, Const.SOFT)
    button = Gtk.LinkButton(Const.DOWNLOAD_URL, text)
# todo ne fonctionne pas sous windows
    button.set_relief(Gtk.ReliefStyle.NONE)
    button.connect('clicked', self._dialog_destroy)
    button.set_border_width(20)
    vbox = dialog.vbox
    vbox.add(button)
    button = Gtk.CheckButton("Me le rappeler plus tard")
    button.connect('clicked', self._set_version_pref)
    vbox.add(button)
    vbox.show_all()
    result = dialog.run()
    dialog.destroy()

  def _set_version_pref(self, widget):
    """Enregistre la préférence pour la recherche de la nouvelle version"""
    if widget.get_active():
      self.UP.save_version(10)
    else:
      self.UP.save_version(0)

  def _dialog_destroy(self, widget):
    """Fermeture du Dialog de la nouvelle version"""
    widget.get_parent().get_parent().destroy()

  def on_open_help(self, widget):
    import webbrowser
    try:
      webbrowser.open(Const.HELP_URL)
    except:
      classDialog.Message().set_message("Erreur avec le navigateur", 0)

  def on_edit_degree(self, widget):
    """Affiche le degré d'hyperstaticité"""
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None: 
      return
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    try:
      deg = str(rdm.struct.CalculDegreH())
      state = 2
    except AttributeError:
      deg = 'Une erreur est survenue'
      state = 0
    content = ("Degré d'hyperstaticité de la structure: %s" % deg, state)
    classDialog.Message().set_message(content)

  def _show_message(self, content, dialog=True):
    #print("_show_message", content)
    errors = [i[0] for i in content if i[1] == 0]
    warnings = [i[0] for i in content if i[1] == 1]
    if errors:
      self.message.set_message((errors[0], 0))
      if dialog:
        classDialog.Dialog(errors)
    elif warnings:
      self.message.set_message(('', 1))
    else:
      self.message.set_message(None)


  # -----------------------------------------------------------
  #
  # Méthodes relatives au dessin
  #
  # -----------------------------------------------------------

  def _do_new_drawing(self):
    """Lance une mise à jour de l'area sans refaire de calcul de l'instance rdm """
    #print("Main::_do_new_drawing")
    tab = self.active_tab
    sw = tab.sw
    if isinstance(sw.get_child(), Gtk.TextView):
      self._clear_sw_content()
      self._add_drawing_widget()
    tab.do_new_drawing(True)

  def update_drawing(self, case_page=None):
    """Met à jour le dessin en status 0 depuis l'éditeur de données"""
    if self.editor.data_editor.need_drawing == False:
      return
    #print "update_drawing"
    tab = self.active_tab
    drawing = tab.active_drawing
    if not drawing.parent is None:
      drawing = drawing.parent
    if not drawing.status == 0:
      return
    study = self.studies[drawing.id_study]
    if case_page is None:
      if not self.editor.xml_status == -1:
        self.editor.data_editor.set_xml_structure()
      study.rdm = classRdm.EmptyRdm(self.editor.data_editor.XML, self.editor.data_editor.name)
      self._fill_right_menu()
      self._update_combi_box()
      self._set_buttons_rdm(study.rdm.status)
      self.editor.data_editor.need_drawing = False
    else:
      drawing.s_case = case_page
      self._fill_right_menu()
      self._update_combi_box()
    tab.do_new_drawing2(study, drawing)
    self.message.set_message(("Enregistrer l'étude pour continuer", 1))

  def on_dynamic_expose(self, widget):
    drawing = self.active_tab.active_drawing
    if drawing is None:
      return
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    try:
      n_cases = rdm.n_cases
    except AttributeError:
      n_cases = 1
    if drawing.s_case > n_cases-1:
      drawing.s_case = 0

    if hasattr(self, "editor"):
      ed_data = self.editor.data_editors[drawing.id_study]
      drawing.status = 0
      if ed_data.is_changed:
        self.update_drawing()
      else:
        self._expose_commun(0)
        self._update_combi_box()
        self._update_titles()
    else:
      self._expose_commun(0)
      self._update_combi_box()
      self._update_titles()

  def on_bar_expose(self, widget):
    drawing = self.active_tab.active_drawing
    if drawing is None:
      return
    self._expose_commun(1)
    self._update_combi_box()
    self._update_titles()

  def on_char_expose(self, widget):
    drawing = self.active_tab.active_drawing
    if drawing is None:
      return
    self._expose_commun(2)
    self._update_combi_box()
    self._update_titles()

  def on_expose_reac(self, widget):
    drawing = self.active_tab.active_drawing
    if drawing is None:
      return
    self._expose_commun(3)
    self._update_combi_box()
    self._update_titles()

  def on_expose_n(self, widget):
    drawing = self.active_tab.active_drawing
    if drawing is None:
      return
    self._expose_commun(4)
    self._update_combi_box()
    self._update_titles()

  def on_expose_v(self, widget):
    drawing = self.active_tab.active_drawing
    if drawing is None:
      return
    self._expose_commun(5)
    self._update_combi_box()
    self._update_titles()

  def on_expose_m(self, widget):
    drawing = self.active_tab.active_drawing
    if drawing is None:
      return
    self._expose_commun(6)
    self._update_combi_box()
    self._update_titles()

  def on_expose_defo(self, widget):
    drawing = self.active_tab.active_drawing
    if drawing is None:
      return
    self._expose_commun(7)
    self._update_combi_box()
    self._update_titles()

  def _expose_commun(self, new_status):
    #print("_expose_commun")
    tab = self.active_tab
    tab.status = 0
    drawing = tab.active_drawing
    old_status = drawing.status
    drawing.set_status(new_status)
    if old_status == 8:
      self._fill_right_menu()
    if not new_status in [4, 5, 6, 7]:
      key = drawing.get_char_drawing()
      if not key is None:
        char_drawing = tab.drawings[key]
        del(drawing.childs[key])
        char_drawing.mapping.remove_map(key)
        del(tab.drawings[key])


    li = drawing.get_bar_drawings()
    for key in li:
      child = drawing.childs[key]
      sync = child.options['Sync']
      if sync:
        child.del_patterns()
        child.set_status(new_status)

    if not drawing.get_is_parent():
      parent = drawing.parent
      sync = drawing.options['Sync']
      if sync:
        parent.del_patterns()
        parent.set_status(new_status)

    drawing.del_patterns()
    layout = tab.layout
    sw = tab.sw
    if isinstance(sw.get_child(), Gtk.TextView):
      self._clear_sw_content()
      self._add_drawing_widget()
    tab.configure_event(layout)
    tab.layout.queue_draw()


  # -----------------------------------------------------------
  #
  # Méthodes relatives au basculement de mode (graphe/info)
  #
  # -----------------------------------------------------------

# pas très utile
  def _get_has_textview(self):
    """Return True if screen is textview"""
    tab = self.active_tab
    if tab.status == 0:
      return False
    return True

  def _add_drawing_widget(self, tab=None):
    """Ajoute le dessin"""
    #print("_add_drawing_widget finir")
    if tab is None:
      tab = self.active_tab
    tab.status = 0
    sw = tab.sw
    area = tab.layout 
    sw.add(area) # déclenche 1 configure_event

  def _add_textview(self):
    """Ajoute le textview"""
    tab = self.active_tab
    sw = tab.sw
    textview = Gtk.TextView()
    textview.show()
    #sw.add_with_viewport(textview)
    sw.add(textview)
    return textview


#à renommer
  def _clear_sw_content(self, tab=None):
    """Supprime le layout ou le textview"""
    #print "_clear_sw_content"
    if tab is None:
      tab = self.active_tab
    sw = tab.sw
    #viewport = sw.get_children()[0]
    child = sw.get_child()
    sw.remove(child)


  def _do_buffer_error(self, textview):
    """Crée le buffer avec mise en forme pour afficher
    les erreurs"""
    #print 'Main::_do_buffer_error'
    textbuffer = Gtk.TextBuffer()
    end_iter = textbuffer.get_end_iter()
    h1 = textbuffer.create_tag("h1", weight = Pango.Weight.BOLD,
		size_points = 12.0, foreground = "purple")
    h2 = textbuffer.create_tag("h2", weight = Pango.Weight.BOLD,
		size_points = 11.0)
    p = textbuffer.create_tag("p", weight = Pango.Weight.NORMAL,
		size_points = 9.0)
    id_image = {0 : Gtk.STOCK_STOP, 1 : Gtk.STOCK_DIALOG_WARNING, 2 : Gtk.STOCK_INFO, 3 : Gtk.STOCK_APPLY}
    
    tab = self.active_tab
    drawing = tab.active_drawing
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    try:
      errors = rdm.errors
    except AttributeError:
      errors = None

    text = "Messages pour l'étude \"%s\"\n" % study.name
    textbuffer.insert_with_tags(end_iter, text, h1)
    # li contient toujours un élément
    li_anchor = []
    if errors is None:
        anchor = textbuffer.create_child_anchor(end_iter)
        li_anchor.append((anchor, 3))
        text = " Veuillez enregistrer l'étude en cours.\n"
        textbuffer.insert_with_tags(end_iter, text, p)

    elif len(errors) == 0:
        anchor = textbuffer.create_child_anchor(end_iter)
        li_anchor.append((anchor, 3))
        text = " Aucune erreur a été détectée pendant la lecture des données.\n"
        textbuffer.insert_with_tags(end_iter, text, p)
    else:
      for elem in errors:
        code = elem[1]
        text = elem[0]
        anchor = textbuffer.create_child_anchor(end_iter)
        li_anchor.append((anchor, code))
        text = ' %s' % text
        textbuffer.insert_with_tags(end_iter, '%s\n' % text, p)

    textview.set_buffer(textbuffer)
    # insertion des images
    for elem in li_anchor:
      code = elem[1]
      image = Gtk.Image()
      image.set_from_stock(id_image[code], Gtk.IconSize.MENU)
      image.show()
      textview.add_child_at_anchor(image, elem[0])
    #textview.scroll_to_iter(end_iter, 0) fonctionne pas
    #return textbuffer

  def _do_buffer_eq(self):
    textbuffer = Gtk.TextBuffer()
    #pixbuf = GdkPixbuf.Pixbuf.new_from_xpm_data(book_closed_xpm)
    tab = self.active_tab
    drawing = tab.active_drawing
    status = drawing.status
    if status == 8:
      self.fill_buffer1(textbuffer, drawing)
    else:
      self.fill_buffer2(textbuffer, drawing)
    return textbuffer

  def fill_buffer1(self, textbuffer, drawing):
    """Remplit le buffer pour une ligne d'influence"""
    h1 = textbuffer.create_tag("h1", weight=Pango.Weight.BOLD, size_points=12.0, foreground="purple")
    h2 = textbuffer.create_tag("h2", weight=Pango.Weight.BOLD, size_points=11.0)
    end_iter = textbuffer.get_end_iter()
    study = self.studies[drawing.id_study]
    rdm = study.influ_rdm
    struct = rdm.struct
    units = struct.units
    factor_F = units['F']
    factor_L = units['L']
    unit_F = study.get_unit_name('F')
    unit_L = study.get_unit_name('L')
    if drawing.s_influ is None:
      return
    obj = drawing.influ_list[drawing.s_influ]
    status = obj.status
    u = obj.u
    elem = obj.elem
    if status == 1 or status == 4:
      type = "F"
    elif status == 2:
      type = "M"
    elif status == 3:
      type = "L"
    texts = {1: "Effort tranchant", 2: "Moment fléchissant", 3: "Déformée", 4: "Réaction d'appui"}
    text = "Equations des courbes d'influence :\n%s\n" % texts[status]
    textbuffer.insert_with_tags(end_iter, text, h1)
    if status == 4:
      text = "Noeud : %s\n" % elem
    else:
      text = "Barre : %s, position x=%s\n" % (elem, u)
    textbuffer.insert(end_iter, text)
    try:
      bars = drawing.s_influ_bars
    except AttributeError:
      bars = rdm.struct.Barres
    for barre in bars:
      data = rdm.InfluBarre(barre, elem, u, status, True)
      text = "\tBarre = %s\n" % barre
      textbuffer.insert_with_tags(end_iter, text, h2)
      text2 = ''
      xprec = 0.
      for tu in data:
        x, coefs = tu[0], tu[1]
        x /= factor_L
        text2 += "x compris entre %s et %s %s\n" % (xprec, x, unit_L)
        text2 += self.set_equation_string(coefs, factor_L, factor_F, unit_L, unit_F, type)
        xprec = x
      textbuffer.insert(end_iter, text2)

  def fill_buffer2(self, textbuffer, drawing):
    """Remplit le buffer pour les sollicitations ou déformée"""
    h1 = textbuffer.create_tag("h1", weight=Pango.Weight.BOLD, size_points=12.0, foreground="purple")
    h2 = textbuffer.create_tag("h2", weight=Pango.Weight.BOLD, size_points=11.0)
    end_iter = textbuffer.get_end_iter()
    study = self.studies[drawing.id_study]
    status = drawing.status
    rdm = study.rdm
    struct = rdm.struct
    units = struct.units
    factor_F = units['F']
    factor_L = units['L']
    unit_F = study.get_unit_name('F')
    unit_L = study.get_unit_name('L')
    if status == 4 or status == 5:
      type = "F"
    elif status == 6:
      type = "M"
    elif status == 7:
      type = "L"
    n_case = drawing.s_curve
    Char = rdm.GetCharByNumber(n_case)
    name = rdm.GetCharNameByNumber(n_case)

    text = "Equations des courbes pour \"%s\"\n" % name
    textbuffer.insert_with_tags(end_iter, text, h1)
    texts = {4: "Effort normal", 5: "Effort tranchant", 6: "Moment fléchissant", 7: "Déformée"}
    text = texts[status]
    textbuffer.insert(end_iter, "(%s)\n" % text)
    for barre in rdm.struct.Barres:
      text = "\tBarre = %s\n" % barre
      textbuffer.insert_with_tags(end_iter, text, h2)
      data = rdm.GetDataEq(barre, Char, status)
      if data == []:
        text = "\tpas d'équation disponible\n"
        textbuffer.insert(end_iter, text)
        continue

      text2 = ''
      xprec = 0.
      for tu in data:
        x, coefs = tu[0], tu[1]
        x /= factor_L
        text2 += "x compris entre %s et %s %s\n" % (xprec, x, unit_L)
        text2 += self.set_equation_string(coefs, factor_L, factor_F, unit_L, unit_F, type)
        xprec = x
      textbuffer.insert(end_iter, text2)

# XXX suppression des 0 à faire
  def set_equation_string(self, coefs, factor_L, factor_F, name_L, name_F, type):
    """Met en forme l'équation donnée par les coefficients"""
    n_coefs = len(coefs)
    li = []
    if type == 'F':
      name = name_F
      conv = 1./factor_F
    elif type == 'M':
      name = "%s.%s" % (name_F, name_L)
      conv = 1./factor_F/factor_L
    elif type == 'L':
      name = name_L
      conv = 1./factor_L
    for c in reversed(coefs):
      c *= conv
      conv *= factor_L
      li.append(c)
    li.reverse()
    coefs = li
    text = ""
    if n_coefs == 2:
      a, b = coefs
      text += "y(%s)=%s*x+%s\n" % (name, a, b)
    elif n_coefs == 4:
      a, b, c, d = coefs
      if a == 0.:
        text += "y(%s)=%s*x^2+%s*x+%s\n" % (name, b, c, d)
      else:
        text += "y(%s)=%s*x^3+%s*x^2+%s*x+%s\n" % (name, a, b, c, d)
    elif len(coefs) == 5:
      a, b, c, d, e = coefs
      if a == 0.:
        text += "y(%s)=%s*x^3+%s*x^2+%s*x+%s\n" % (name, b, c, d, e)
      else:
        text += "y(%s)=%s*x^4+%s*x^3+%s*x^2 +%s*x+%s\n" % (name, a, b, c, d, e)
    elif len(coefs) == 6:
      a, b, c, d, e, f = coefs
      if a == 0.:
        text += "y(%s)=%s*x^4+%s*x^3+%s*x^2 +%s*x+%s\n" % (name, b, c, d, e, f)
      else:
        text += "y(%s)=%s*x^5+%s*x^4+%s*x^3+%s*x^2+%s*x+%s\n" % (name, a, b, c, d, e, f)
    else:
      print('debug in do_buffer_eq',len(tu))
    text = text.replace('+-', '-')
    return text


  def _do_buffer_resu(self):
    """Crée le buffer avec mise en forme pour afficher
    les ddl et autres résultats"""
    textbuffer = Gtk.TextBuffer()
    #pixbuf = GdkPixbuf.Pixbuf.new_from_xpm_data(function.book_closed_xpm)
    end_iter = textbuffer.get_end_iter()
    h1 = textbuffer.create_tag("h1", weight=Pango.Weight.BOLD, size_points=12.0, foreground="purple")
    h2 = textbuffer.create_tag("h2", weight=Pango.Weight.BOLD, size_points=11.0)
    h3 = textbuffer.create_tag("h3", weight=Pango.Weight.BOLD, size_points=10.0)
    tab = self.active_tab
    drawing = tab.active_drawing
    study = self.studies[drawing.id_study]
    rdm = study.rdm
    struct = rdm.struct
    units = struct.units
    RotuleElast = struct.RotuleElast
    case = drawing.s_case
    if case is None:
      try:
        case = drawing.s_cases[0]
      except IndexError:
        case = drawing.get_first_case(rdm)
    if case is None:
      textbuffer.insert_with_tags(end_iter, "Aucune valeur disponible", h1)
      return textbuffer
    Char = rdm.GetCharByNumber(case)
    if Char.r_status == 0:
      textbuffer.insert_with_tags(end_iter, "Aucune valeur disponible", h1)
      return textbuffer
    factor_F = units['F']
    factor_L = units['L']
    unit_F = study.get_unit_name('F')
    unit_L = study.get_unit_name('L')
    text = "Principales valeurs numériques\npour le chargement \"%s\"\n" % Char.name
    textbuffer.insert_with_tags(end_iter, text, h1)
    text = "Valeurs des degrés de liberté\n"
    textbuffer.insert_with_tags(end_iter, text, h2)
    w_relax = Char.GetBarreRotation()
    texts = ['u', 'v', 'w']
    if struct.n_ddl == 0:
      text = '\tAucun degré de liberté non nul\n'
      textbuffer.insert(end_iter, text)
    for node in struct.Nodes:
      ddls = Char.ddlValue[node]
      text = '\tNoeud %s\n' % node
      textbuffer.insert_with_tags(end_iter, text, h3)
      for i, ddl in enumerate(ddls):
        if i == 0 or i == 1:
          name = texts[i]
          unit = unit_L
          ddl /= factor_L
          textbuffer.insert(end_iter, '\t\t%s=%s %s\n' % (name, ddl, unit))
        elif i == 2:
          name = texts[2]
          unit = 'rad'
          if node in RotuleElast:
            barre = RotuleElast[node][0]
            textbuffer.insert(end_iter, '\t\t%s=%s %s\n' % (name, ddl, unit))
            textbuffer.insert(end_iter, '\t\tw=%s %s (%s)\n' % (ddls[3], unit, barre))
          
          elif node in w_relax:
            for barre, w in w_relax[node].items():
              textbuffer.insert(end_iter, '\t\tw=%s %s (%s)\n' % (w, unit, barre))

          else:
            textbuffer.insert(end_iter, '\t\t%s=%s %s\n' % (name, ddl, unit))

    text = "Sollicitations aux extrémités des barres\n"
    textbuffer.insert_with_tags(end_iter, text, h2)
    di = Char.GetSollicitationBarre(rdm.conv)
    texts = ['N', 'V', 'M']
    #unit = function.return_key(Const.UNITS['F'], factor)
    for barre, nodes in di.items():
      text = '\tBarre %s\n' % barre
      textbuffer.insert_with_tags(end_iter, text, h3)
      for node, forces in nodes.items():
        text = '\t\tNoeud %s\n' % node
        textbuffer.insert(end_iter, text)
        for i, force in enumerate(forces):
          if force == 0:
            continue
          force /= factor_F
          name = texts[i]
          if i == 2:
            force /= factor_L
            textbuffer.insert(end_iter, '\t\t\t%s=%s %s.%s\n' % (name, force, unit_F, unit_L))
          else:
            textbuffer.insert(end_iter, '\t\t\t%s=%s %s\n' % (name, force, unit_F))

    text = "Calcul des réactions d'appui\n"
    textbuffer.insert_with_tags(end_iter, text, h2)
    try:
      di = Char.Reactions
    except AttributeError:
      di = Char.GetCombiReac()

    for node, forces in di.items():
      text = '\t\tNoeud %s\n' % node
      textbuffer.insert(end_iter, text)
      for name, force in forces.items():
        force /= factor_F
        if name == 'Mz':
          force /= factor_L
          textbuffer.insert(end_iter, '\t\t\t%s=%s %s.%s\n' % (name, force, unit_F, unit_L))
        else:
          textbuffer.insert(end_iter, '\t\t\t%s=%s %s\n' % (name, force, unit_F))

    return textbuffer

  def _print_message(self, textview):
    """Affichage des messages écrits et mise en forme
    type = 0 : errors
    type = 1 : numerical values"""
    #print "Main::print_message"
    status = self.active_tab.status
    textview.set_left_margin(10)
    textview.set_pixels_above_lines(10)
    textbuffer = Gtk.TextBuffer()
    if status == 1:
      textbuffer = self._do_buffer_resu()
      textview.set_buffer(textbuffer)
    elif status == 2:
      self._do_buffer_error(textview)
    elif status == 3:
      textbuffer = self._do_buffer_eq()
      textview.set_buffer(textbuffer)


  # -----------------------------------------------------------
  #
  # Méthodes en relation avec les charges roulantes
  #
  # -----------------------------------------------------------


  def on_expose_move(self, widget):
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    #drawing.status = 9
    drawing.set_status(9)
    id_study = drawing.id_study
    study = self.studies[id_study]
    self._do_new_drawing()

  # -----------------------------------------------------------
  #
  # Méthodes en relation avec les lignes d'influence
  #
  # -----------------------------------------------------------

  def on_expose_influ(self, widget):
    #print "on_expose_influ"
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing is None:
      return
    if drawing.get_is_bar_drawing():
      drawing = tab.active_drawing = drawing.parent
    drawing.set_status(8)
    id_study = drawing.id_study
    study = self.studies[id_study]
    self._fill_right_menu()
    self._do_new_drawing()
    self._update_combi_box()
    self._update_titles()


  def _fill_influ_menu(self, tab, box):
    """Crée le menu pour les lignes d'influence"""
    #print "_fill_influ_menu"
    childs = box.get_children()
    try:
      child = childs[1]
      box.remove(child)
    except IndexError:
      pass
    drawing = tab.active_drawing
    id_study = drawing.id_study
    study = self.studies[id_study]
    rdm = study.rdm
    struct = rdm.struct
    barres = struct.UserBars
    if len(barres) == 0 and len(struct.SuperBars) == 0:
      self.message.set_message(("Les lignes d'influence ne fonctionnent que sur des barres rectilignes", 0))
    try:
      obj = drawing.influ_list[drawing.s_influ]
    except (KeyError, AttributeError, TypeError):
      obj = None
    try:
      drawing.s_influ
    except AttributeError:
      drawing.s_influ = None
    try:
      bars = drawing.s_influ_bars
    except AttributeError:
      bars = []
    tab.influ_menu = classLigneInflu.LigneInfluBox(self, study, obj, bars)
    tab.right_menu.pack_start(tab.influ_menu.get_box(), False, False, 0)


  def area_expose_influ(self, widget, reset=True):
    """Méthode de lancement du calcul des lignes d'influ. Récupère les paramètres depuis la fenetre de dialogue. Gère les boutons et titre"""
    #print "area_expose_influ"
    tab = self.active_tab
    drawing = tab.active_drawing
    if drawing.get_is_bar_drawing():
      drawing = tab.active_drawing = drawing.parent
    if reset:
      drawing.influ_list = {}
    params = tab.influ_menu.get_data()
    if params is None:
      self.message.set_message(("Choisir un élément", 1))
      return
    influ_list = drawing.influ_list
    id = 0
    while True:
      if not id in influ_list:
        break
      id += 1
    Obj = classDrawing.InfluParams(id)
    Obj.add(params)
    influ_list[Obj.id] = Obj
    drawing.s_influ = Obj.id
    self._do_new_drawing()
    self._update_combi_box()
    self._update_titles()
    self.message.set_message(None) # mettre autre message


  def on_del_influs(self, widget):
    """Efface toutes les courbes de lignes d'influence"""
    tab = self.active_tab
    drawing = tab.active_drawing
    drawing.influ_list = {}
    try:
      del(drawing.user_values[drawing.status])
    except (KeyError, AttributeError):
      pass

    drawing.s_influ = None
    self._do_new_drawing()



  # -----------------------------------------------------------
  #
  # Méthodes en relation avec l'éditeur de données
  #
  # -----------------------------------------------------------



  def _set_name(self, id_study):
    """Donne un nom à l'étude s'il n'existe pas"""
    study = self.studies[id_study]
    path = study.path
    if not path is None:
      return True
    path = file_tools.recursive_file_select(self.UP.get_default_path())
    if path is None:
      return False
    ed_data = self.editor.data_editors[id_study]
    ed_data.path = path
    name = os.path.basename(path)
    ed_data.name = name
    study.name = name
    study.path = path
    return True


  def update_from_editor(self, widget=None):
    """Gère les évènements liés à l'enregistrement depuis l'éditeur"""
    #print "Main::update_from_editor"
    tab = self.active_tab
    drawing = tab.active_drawing
    drawings = tab.drawings
    id_study = drawing.id_study
    ed_data = self.editor.data_editors[id_study]
    study = self.studies[id_study]
    book = self.book
    status = drawing.status
    old_path = study.path
    if not self._set_name(id_study):
      return
    if old_path is None: # maj du titre du dessin
      drawing.mapping.infos[drawing.id][drawing.title_id].text = study.name

    resize = False
    if ed_data.size_changed:
      resize = True
    if hasattr(study, "influ_rdm"):
      del(study.influ_rdm)

    self._save_rdm_instance(id_study)
    rdm = study.rdm # après _save_rdm_instance
    p_drawings = tab.get_parent_drawings()
    Barres = rdm.struct.GetBars()
    reset = False # suppression des dessins enfant
    del_drawings = []
    if len(Barres) == 0:
      reset = True
    for d in p_drawings:
      if not d.id_study == id_study:
        continue
      d.update_s_data(rdm, Barres)
      if reset:
        for child in d.childs:
          del(tab.drawings[child.id])
        d.childs = {}
        continue
      childs = d.childs
      for key in childs:
        child = d.childs[key]
        resu = child.update_s_data(rdm, Barres)
        if resu is False:
          del_drawings.append(child.id)
          #del(d.childs[key])
    for key in del_drawings:
      d = tab.drawings[key]
      tab.remove_drawing(d)
    status_prec = drawing.status
    self.editor.update_editor_title()
    self.editor.set_is_changed

    rdm_status = rdm.status
    if not rdm_status == 2:
      drawing.status = 0
      if tab.status == 1:
        tab.status = 2
    if tab.status == 0:
      drawings = tab.drawings
      for id, drawing1 in drawings.items():
        if not drawing1.id_study == id_study:
          continue
        if resize:
          drawing1.set_scale(rdm.struct)
        drawing1.del_patterns()
      self._fill_right_menu()
      #tab.del_surface()
      tab.configure_event(tab.layout)
      tab.layout.queue_draw()
    else: # status = 1 ou 2
      layout = tab.sw.get_child()
      tab.sw.remove(layout)
      textview = Gtk.TextView()
      self._print_message(textview)
      textview.show()
      tab.sw.add(textview)
      self._fill_right_menu()
    self._update_combi_box()
    self._update_titles()

    self._show_message(rdm.errors, False)
    # mise à jour des boutons
    self._set_buttons_rdm(rdm_status)


  def _save_rdm_instance(self, id_study):
    """Recalcule l'instance de RDM de l'étude active afin de tenir compte des modifications apportées par l'éditeur"""
    # file writing
    data_editor = self.editor.data_editors[id_study]
    self.editor.save_study(data_editor)
    study = self.studies[id_study]
    path = data_editor.path
    xml = data_editor.get_xml()
    structure = classRdm.Structure(xml, path)
    study.rdm = classRdm.R_Structure(structure)

  def _restore_rdm_instance(self, id_study):
    """Recalcule l'instance de RDM de l'étude active à partir d'une nouvelle lecture du fichier"""
    data_editor = self.editor.data_editors[id_study]
    study = self.studies[id_study]
    path = data_editor.path
    if path is None: # XXX l'étude n'est pas effacée du dessin
      return
    structure = classRdm.StructureFile(path)
    study.rdm = classRdm.R_Structure(structure)


  def _update_editor(self):
    """Effectue les mises à jours de la fenetre de l'éditeur en cas de changement d'étude"""
    #print("_update_editor")
    if self.editor.w2.get_window() is None:
      return
    tab = self.active_tab
    drawing = tab.active_drawing
    ed_data = self.editor.data_editors
    #print len(self.studies),  len(ed_data)
    if drawing is None:
      if len(ed_data) == 0:
        self.editor.w2.destroy()
        del (self.editor)
        return
      self.editor.w2.set_sensitive(False)
      return
    id_study = drawing.id_study
    study = self.studies[id_study]
    try:
      status = drawing.status
    except AttributeError:
      status = 0
    if status == -1:
      self.editor.w2.set_sensitive(False)
    else:
      self.editor.w2.set_sensitive(True)
      self.editor.new_page_editor(study)
    #assert len(self.studies) == len(ed_data)

  def _get_record_id(self, changes):
    """Récupère la liste des études qui doivent être enregistrées à partir des réponses de l'utilisateur"""
    ed_data = self.editor.data_editors
    must_save = []
    action = 0
    for i, id in enumerate(changes):
      study = ed_data[id]
      action = file_tools.exit_as_ok_func(study.name)
      if action == -1:
        return None
      elif action == 1:
        must_save.append(id)
      elif action == 2:
        must_save.extend(changes[i:])
        return must_save
    return must_save

  def _destroy_editor(self, widget, event):
    """Gère les actions à la fermeture de l'éditeur"""
    tab = self.active_tab
    studies = self.studies
    if not tab.status == 0:
      self._clear_sw_content()
      self._add_drawing_widget()
      tab.status = 0

    # maj des études dans la page active
    changes = self.editor.get_modified_studies()
    must_save = self._get_record_id(changes) # études qui doivent être enregistres
    if must_save is None:
      return True # keep True
    else:
      self.editor.w2.destroy()
    for id in changes:
      if id in must_save:
        self._set_name(id)
        self._save_rdm_instance(id)
      else: 
        self._restore_rdm_instance(id)
    for id in tab.drawings: # actualisation des dessins de l'onglet actif
      drawing = tab.drawings[id]
      if drawing.id_study in changes:
        struct = studies[drawing.id_study].rdm.struct
        drawing.set_scale(struct)
        drawing.del_patterns()
    self._fill_right_menu()
    if not tab.active_drawing is None:
      study = studies[tab.active_drawing.id_study]
      self._set_buttons_rdm(study.rdm.status)
    #tab.del_surface()
    tab.configure_event(tab.layout)
    tab.layout.queue_draw()
    self._update_titles()
    self._update_combi_box()
    #self._show_message(study.rdm.errors, False)
    GObject.idle_add(self._bg_from_editor_update, changes)


  def _bg_from_editor_update(self, changes):
    """Met à jour les dessins des onglets non visibles en arrière plan"""
    studies = self.studies
    for tab in self._tabs:
      if tab is self.active_tab:
        continue # already done
      if not tab.status == 0:
        self._clear_sw_content(tab)
        self._add_drawing_widget(tab)
      tab.status = 0
      for id in tab.drawings:
        drawing = tab.drawings[id]
        if drawing.id_study in changes:
          struct = studies[drawing.id_study].rdm.struct
          drawing.set_scale(struct)
          drawing.del_patterns()

      #tab.del_surface()
      tab.configure_event(tab.layout)
    del (self.editor) # enlever si gobject


  # -----------------------------------------------------------
  #
  # Méthodes en relation la fenetre Library
  #
  # -----------------------------------------------------------

  def on_open_lib(self, widget):
    """Ouverture de la librairie des profils depuis la fenetre principale"""
    lib = classProfilManager.ProfilManager()
    lib.window.connect("delete_event", self._close_library, lib)

  def _close_library(self, widget, event, lib):
    """Fermeture de la librairie des profils depuis la fenetre principale"""
    #print "Main::_close_library"
    lib.destroy()
    #lib.window = None
    del(lib)
    if hasattr(self, 'editor'):
      self.editor._active_selection_button(False)
      if hasattr(self.editor, 'profil_manager'):
        self.editor.profil_manager.button.set_sensitive(True)
        del(self.editor.profil_manager)



# ------------ tools ---------------------
  def print_rdm_status(self, rdm):
    """Affichage des status des classes de Rdm :: debug"""
    print("Structure::status=", rdm.struct.status)
    print("R_Structure::status=", rdm.status)
    if rdm.status == -1: return
    for i in rdm.Chars:
      Char = rdm.Chars[i]
      print("Case Name=%s Status lecture=%s Status Inv=%s" % (Char.name, Char.status, Char.r_status))

class MyThread(threading.Thread):

  def __init__(self, main):
    super(MyThread, self).__init__()
    self.main = main
    self.daemon = True
    self.start()

  def run(self):
    self.main.new_version = self._get_next_version()
    #print("new_version=", self.main.new_version)

  def _get_next_version(self):
    """Vérifie la dernière version en ligne et lance Dialog - Return False"""
    import urllib.request
    try:
      sock = urllib.request.urlopen(Const.VERSION_URL)
    except (IOError, EOFError):
      return False
    version = sock.read()
    sock.close()
    try:
      next = float(version.strip())
    except ValueError:
      return False

    if next > float(Const.VERSION):
      return next
    return False

if __name__ == "__main__":
  #try:
  MyApp = MainWindow()
  MyThread(MyApp)
  Gtk.main()
  #except KeyboardInterrupt:
  #  print('eeee')
  #  sys.exit(0)

