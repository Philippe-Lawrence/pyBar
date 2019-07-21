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

import configparser, os
import Const

class Singleton(object):
  def __new__(cls, *args, **kwargs):
    if '_inst' not in vars(cls):
      cls._inst = object.__new__(cls, *args, **kwargs)
    return cls._inst


class UserPrefs(Singleton):

  def __init__(self):
    file = Const.FILEPREFS
    path = Const.PATH
    self.config = configparser.ConfigParser()
    self.file = os.path.join(path, file)
    if os.path.exists(self.file):
      with open(self.file) as fp:
        self.config.read_file(fp)
        fp.close()
    else:
      self._ini_config_file()
 
  def _ini_config_file(self):
    """Initialise la configuration si le fichier n'est pas trouvé"""
    self.config.add_section('Section_w1')
    self.config.add_section('Section_w2')
    self.config.add_section('Section_w3')
    self.config.add_section('Section_units')
    self.config.add_section('Section_file')

  def get_default_path(self):
    try:
      return self.config.get('Section_file', 'last_opened')
    except configparser.NoOptionError:
      return Const.PATH

  def save_default_path(self, path):
    if not self.config.has_section('Section_file'):
      self.config.add_section('Section_file')
    self.config.set('Section_file', 'last_opened', '%s' % path)

  def get_w1_box(self):
    try:
      option = self.config.get('Section_w1', 'display_combi_box')
    except configparser.NoOptionError:
      option = 'on'
    if option == 'on':
      return True
    return False

  def get_version(self):
    """Retourne l'option pour la recherche des nouvelles versions"""
    try:
      option = self.config.getint('Section_w1', 'new_version')
    except configparser.NoOptionError:
      option = 0
    return option

  def save_version(self, val):
    """Enregistre l'option pour la recherche de la nouvelle version"""
    if val < 0:
      val = 0
    if not self.config.has_section('Section_w1'):
      self.config.add_section('Section_w1')
    try:
      self.config.set('Section_w1', 'new_version', '%s' % val)
    except KeyboardInterrupt:
      return
    try:
      with open(self.file, "w") as fp:
        self.config.write(fp)
        fp.close()
    except IOError:
      print("Erreur d'écriture du fichier de préférence")


  def get_w1_options(self):
    options = {}
    options['Node'] = self.get_w1_options1()
    options['Barre'] = self.get_w1_options2()
    options['Axis'] = self.get_w1_options3()
    options['Title'] = self.get_w1_options4()
    options['Series'] = self.get_w1_options5()
    return options


  def get_w1_options1(self):
    try:
      option = self.config.get('Section_w1', 'display_node_name')
    except configparser.NoOptionError:
      option = 'on'
    if option == 'on':
      return True
    return False

  def get_w1_options2(self):
    try:
      option = self.config.get('Section_w1', 'display_barre_name')
    except configparser.NoOptionError:
      option = 'on'
    if option == 'on':
      return True
    return False

  def get_w1_options3(self):
    try:
      option = self.config.get('Section_w1', 'display_axis')
    except configparser.NoOptionError:
      option = 'off'
    if option == 'on':
      return True
    return False

  def get_w1_options4(self):
    try:
      option = self.config.get('Section_w1', 'display_title')
    except configparser.NoOptionError:
      option = 'on'
    if option == 'on':
      return True
    return False

  def get_w1_options5(self):
    try:
      option = self.config.get('Section_w1', 'display_series')
    except configparser.NoOptionError:
      option = 'off'
    if option == 'on':
      return True
    return False


  def get_w1_size(self):
    try:
      return self.config.getint('Section_w1', 'w1_w'), self.config.getint('Section_w1', 'w1_h')
    except configparser.NoOptionError:
      return None

  def get_default_g(self):
    try:
      return self.config.getfloat('Section_units', "g")
    except configparser.NoOptionError:
      return Const.G

  def get_default_conv(self):
    try:
      return self.config.getfloat('Section_units', "conv")
    except configparser.NoOptionError:
      return Const.CONV

  def get_default_units(self):
    if not self.config.has_section('Section_units'): return {}
    di = {}
    for i in ['L', 'C', 'E', 'F', 'I', 'M', 'S']:
      try:
        val = self.config.getfloat('Section_units', i)
      except configparser.NoOptionError:
        val = 1.
      di[i] = val
    return di

  def save_default_units(self, data):
    units = data.unit_conv
    g = data.G
    if not self.config.has_section('Section_units'):
      self.config.add_section('Section_units')
    for unit, val in list(units.items()):
      self.config.set('Section_units', unit, '%s' % val)
    self.config.set('Section_units', "g", '%s' % g)
    conv = data.conv
    self.config.set('Section_units', "conv", '%s' % conv)

  def save_w1_config(self, w, h, display_box, options):
    if not self.config.has_section('Section_w1'):
      self.config.add_section('Section_w1')
    self.config.set('Section_w1', 'w1_w', '%s' % w)
    self.config.set('Section_w1', 'w1_h', '%s' % h)
    self.config.set('Section_w1', 'display_combi_box', display_box)

    has_title = 'on'
    if not options.get('Title', 'on'): has_title = 'off'
    self.config.set('Section_w1', 'display_title', has_title)

    has_node = 'off'
    if options.get('Node'): has_node = 'on'
    self.config.set('Section_w1', 'display_node_name', has_node)

    has_barre = 'off'
    if options.get('Barre'): has_barre = 'on'
    self.config.set('Section_w1', 'display_barre_name', has_barre)

    has_axis = 'off'
    if options.get('Axis'):
      has_axis = 'on'
    self.config.set('Section_w1', 'display_axis', has_axis)
    has_series = 'off'
    if options.get('Series'):
      has_axis = 'on'
    self.config.set('Section_w1', 'display_series', has_series)
    try:
      with open(self.file, "w") as fp:
        self.config.write(fp)
        fp.close()
    except IOError:
      print("Erreur d'écriture du fichier de préférence")

  def get_w2_size(self):
    sizes = (self.config.getint('Section_w2', 'w2_w'),
			self.config.getint('Section_w2', 'w2_h'))
    return sizes

  def save_w2_config(self, w, h):
    if not self.config.has_section('Section_w2'):
      self.config.add_section('Section_w2')
    self.config.set('Section_w2', 'w2_w', '%s' % w)
    self.config.set('Section_w2', 'w2_h', '%s' % h)
    #print self.config.options('Section_units')
    #print self.config.getfloat('Section_units', u'l')
    try:
      with open(self.file, "w") as fp:
        self.config.write(fp)
        fp.close()
    except IOError:
      print("Erreur d'écriture du fichier de préférence")

  def get_w3_size(self):
    sizes = (self.config.getint('Section_w3', 'w3_w'),
			self.config.getint('Section_w3', 'w3_h'))
    return sizes

  def save_w3_config(self, w, h):
    #print 'UP::save_w3_config', w, h
    if not self.config.has_section('Section_w3'):
      self.config.add_section('Section_w3')
    self.config.set('Section_w3', 'w3_w', '%s' % w)
    self.config.set('Section_w3', 'w3_h', '%s' % h)
    try:
      with open(self.file, "w") as fp:
        self.config.write(fp)
        fp.close()
    except IOError:
      print("Erreur d'écriture du fichier de préférence")

