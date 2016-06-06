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

import gi
from gi.repository import Gtk

class CMenu(object):
  ui0 = '''<ui>
         <popup>
         </popup>
         </ui>'''



  ui3 = '''<ui>
         <popup>
             <menuitem name="change" action="Change" />
         </popup>
         </ui>'''

  ui6 = '''<ui>
         <popup>
             <menuitem name="select" action="Select" />
             <menuitem name="delete" action="Delete" />
             <menuitem name="anchor" action="Anchor" />
         </popup>
         </ui>'''
  ui6_1 = '''<ui>
         <popup>
             <menuitem name="select" action="Select" />
             <menuitem name="anchor" action="Anchor" />
             <menuitem name="show_val" action="Show_val" />
         </popup>
         </ui>'''

  ui7 = '''<ui>
         <popup>
             <menuitem name="del" action="Del" />
             <menuitem name="hide" action="Hide" />
         </popup>
         </ui>'''


  ui9 = '''<ui>
         <popup>
             <menuitem action="Open" />
             <menuitem action="New" />
         </popup>
         </ui>'''

  def __init__(self, w1):
    self.w1 = w1
    self.uimanager = Gtk.UIManager()

# tout revoir selon le principe de cette méthode
  def get_menu1(self, drawing, rdm):
    """Menu contextuel pour la sélection drawing"""
    options = drawing.get_menu_options()
    actions = []
    accelgroup = self.uimanager.get_accel_group()
    actiongroup = Gtk.ActionGroup('settings')
    self.uimanager.add_ui_from_string(self.ui0)
    if 'Node' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'node', 'Node', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Node', None, 'Afficher les noeuds', None,
		None, self.w1.on_node_display, options['Node']))
    if 'Barre' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'barre', 'Barre', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Barre', None, 'Afficher les barres', None,
		None, self.w1.on_barre_display, options['Barre']))
    if 'Axis' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'axis', 'Axis', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Axis', None, 'Afficher les repères', None,
		None, self.w1.on_axis_display, options['Axis']))
    if 'Title' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'title', 'Title', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Title', None, 'Afficher le titre', None,
		None, self.w1.on_title_display, options['Title']))
    if 'Series' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'series', 'Series', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Series', None, 'Afficher les légendes', None,
		None, self.w1.on_series_display, options['Series']))
    if 'Sync' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'sync', 'Sync', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Sync', None, 'Synchroniser', None,
		None, self.w1.on_synchronise, options['Sync']))
    actiongroup.add_toggle_actions(actions, drawing)
    self.uimanager.insert_action_group(actiongroup)

    actions = []
    actiongroup = Gtk.ActionGroup('drawing')
    if 'Select' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'select', 'Select', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Select', None, 'Sélectionner le diagramme', None,
		None, self.w1.on_select_drawing))
    id = self.uimanager.new_merge_id()
    self.uimanager.add_ui(id, '/popup', 'del', 'Del', Gtk.UIManagerItemType.MENUITEM, False)
    actions.append(('Del', None, 'Supprimer le diagramme', None,
		None, self.w1.on_del_drawing))
    if 'Save' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'save', 'Save', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Save', None, 'Fermer et enregistrer l\'étude', None,
		None, self.w1.on_save_drawings))
    if 'Add' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'add', 'Add', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Add', None, 'Ajouter un diagramme', None,
		None, self.w1.on_add_drawing))
    if 'Sigma' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'sigma', 'Sigma', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Sigma', None, 'Diagramme de contraintes', None,
		None, self.w1.on_add_sigma_drawing))
    if 'InfluB' in options:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'influ', 'Influ', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Influ', None, 'Choix des barres', None,
		None, self.w1.on_select_bars))

    actiongroup.add_actions(actions, drawing)
    self.uimanager.insert_action_group(actiongroup)

    menu_button = self.w1.builder.get_object("menu_cas")
    if not menu_button.get_active():
      if 'Case' in options:
        self._add_combi_cas(drawing, rdm)
    self.w1.popup = self.uimanager.get_widget("/popup")



  def _add_combi_cas(self, drawing, rdm):
    """Ajoute les cas et combis au menu contextuel"""
    cases = rdm.Cases
    CombiCoef = rdm.CombiCoef
    combis = list(CombiCoef.keys())
    combis.sort()
    n_cases = len(cases)
    n_combis = len(combis)
    view = drawing.get_combi_view(rdm)

    id = self.uimanager.new_merge_id()
    self.uimanager.add_ui(id, '/popup/barre', 'separator',
		None, Gtk.UIManagerItemType.SEPARATOR, False)
    actiongroup = Gtk.ActionGroup('combi')

    # case
    for i, val in enumerate(cases):
      etat = view[i]
      if etat[1] == 0:
        continue
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', val, val, Gtk.UIManagerItemType.MENUITEM, False)
      actiongroup.add_toggle_actions([(val, None, val, None,
		None, self.w1.event_menu_button, etat[0])], (drawing, i))

    # combinaisons
    if not n_combis == 0:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'separator2', None, Gtk.UIManagerItemType.SEPARATOR, False)

    for i, val in enumerate(combis):
      n = i + n_cases
      etat = view[n]
      if etat[1] == 0:
        continue
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', val, val, Gtk.UIManagerItemType.MENUITEM, False)
      actiongroup.add_toggle_actions([(val, None, val, None,
		None, self.w1.event_menu_button, etat[0])], (drawing, n))

    self.uimanager.insert_action_group(actiongroup, 1)

  def menu2(self, barre, drawing, rdm):
    """Menu contextuel pour survol barre"""
    n_barres = rdm.struct.GetBars()
    actions = []
    #actions = [('Resu', None, 'Ouvrir la fenêtre des barres',
#		None, None, self.w1.on_cm_open_w3)]
    self.uimanager.add_ui_from_string(self.ui0)
    if not n_barres == 1:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'select', 'Select', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Select', None, 'Sélectionner la barre', None,
		None, self.w1.on_bar_select))
    accelgroup = self.uimanager.get_accel_group()
    self.w1.window.add_accel_group(accelgroup)
    actiongroup = Gtk.ActionGroup('settings')

    actiongroup.add_actions(actions, barre)
    self.uimanager.insert_action_group(actiongroup, 0)
    self.w1.popup = self.uimanager.get_widget("/popup")

  def get_menu3(self, node, drawing):
    status = drawing.status
    if not status in [0, 1]:
      return
    actions = [('Change', None, 'Modifier le point',
		None, None, self.w1.open_node_dialog)]
    self.uimanager.add_ui_from_string(self.ui3)
    accelgroup = self.uimanager.get_accel_group()
    self.w1.window.add_accel_group(accelgroup)
    actiongroup = Gtk.ActionGroup('settings')
    actiongroup.add_actions(actions, node)
    self.uimanager.insert_action_group(actiongroup, 0)
    self.w1.popup = self.uimanager.get_widget("/popup")

  def get_menu4(self, drawing, n, curve):
    actions = [('Select', None, 'Sélectionner la courbe',
		None, None, self.w1.on_select_curve),
		('Delete', None, 'Supprimer la courbe',
		None, None, self.w1.on_del_influ),
		('Anchor', None, 'Ancrer une valeur',
		None, None, self.w1.on_set_anchor)
		]
    self.uimanager.add_ui_from_string(self.ui6)
    accelgroup = self.uimanager.get_accel_group()
    self.w1.window.add_accel_group(accelgroup)
    actiongroup = Gtk.ActionGroup('settings')
    actiongroup.add_actions(actions, (drawing, n, curve))
    self.uimanager.insert_action_group(actiongroup, 0)
    self.w1.popup = self.uimanager.get_widget("/popup")

  def get_menu5(self):
    #uimanager = Gtk.UIManager()
    uimanager = self.uimanager
    uimanager.add_ui_from_string(self.ui9)
    accelgroup = uimanager.get_accel_group()
    self.w1.window.add_accel_group(accelgroup)
    action_group = Gtk.ActionGroup("Actions")
    action_group.add_actions([
            ('Open', None, 'Ouvrir une étude', None, None,
			self.w1.on_open_file),
            ('New', None, 'Nouvelle étude', None, None,
             self.w1.on_new_study)
        ])
    uimanager.insert_action_group(action_group)
    self.w1.popup = uimanager.get_widget("/popup")

  def get_menu6(self, drawing, n, curve):
    actions = [('Select', None, 'Sélectionner la courbe',
		None, None, self.w1.on_select_curve),
		('Anchor', None, 'Ancrer une valeur',
		None, None, self.w1.on_set_anchor)
		]
    self.uimanager.add_ui_from_string(self.ui6_1)
    char_drawing_id = drawing.get_char_drawing()

    if char_drawing_id is None:
      id = self.uimanager.new_merge_id()
      self.uimanager.add_ui(id, '/popup', 'show', 'Show', Gtk.UIManagerItemType.MENUITEM, False)
      actions.append(('Show', None, 'Afficher le chargement', None,
		None, self.w1.on_display_char))

    accelgroup = self.uimanager.get_accel_group()
    self.w1.window.add_accel_group(accelgroup)
    actiongroup = Gtk.ActionGroup('settings')

    actiongroup.add_actions(actions, (drawing, n, curve))
    s_values = drawing.s_values
    if n in s_values or drawing.s_curve == n:
      has_values = True
    else:
      has_values = False
    tog_actions = [('Show_val', None, 'Afficher les valeurs',
		None, None, self.w1.on_display_value, has_values)]
    actiongroup.add_toggle_actions(tog_actions, (drawing, n))
    self.uimanager.insert_action_group(actiongroup, 0)
    self.w1.popup = self.uimanager.get_widget("/popup")

  def menu7(self, drawing, n, legend):
    actions = [('Hide', None, 'Masquer', None, None, self.w1.on_hide_value),
		('Del', None, 'Supprimer', None, None, self.w1.on_delete_value)
		]
    self.uimanager.add_ui_from_string(self.ui7)
    accelgroup = self.uimanager.get_accel_group()
    self.w1.window.add_accel_group(accelgroup)
    actiongroup = Gtk.ActionGroup('settings')
    actiongroup.add_actions(actions, (drawing, n, legend))
    self.uimanager.insert_action_group(actiongroup, 0)
    self.w1.popup = self.uimanager.get_widget("/popup")



