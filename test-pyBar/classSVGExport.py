#!/usr/bin/env python
# -*- coding: utf-8 -*-
import classDrawing
import function
import cairo
import Const
import classDialog

from fakeclassRdm import fakeRdm, fakeReadXMLString, fakeReadXMLFile
from classRdm import *


__version__='1'

__date__ = "2015-6-17"


class fakeStudy(classDrawing.Study):
  """Classe héritée de classe Study utilisée hors de l'interface graphique"""

  
  def __init__(self, rdm):
    self.rdm = rdm
    self.id = 0
    self.name = ""

class fakeDrawing(classDrawing.Drawing):
  """"""
  OPTIONS = {
	'Node': True,
	'Barre': True,
	'Axis': True,
	'Title': True,
	'Series': True,
	}

  
  def __init__(self, w, h, id=0):
    message = classDialog.Message()
    message.ini_message(None)
    self.mapping = classDrawing.AreaMapping()
    super(fakeDrawing, self).__init__(self.mapping, id)
    self.w, self.h = w, h

  def draw(self, study, output, status):
    self.set_drawing_prefs(fakeDrawing.OPTIONS)
    self.set_geometric_prefs(study)
    
    self.status = status
    surface = cairo.SVGSurface(output, self.w, self.h)
    cr = cairo.Context(surface)
    self.expose_drawing(cr, study)
    self.paint_drawing(cr)

    surface.finish()

  def set_drawing_prefs(self, options):
    self.options = options

  def set_geometric_prefs(self, study):
    self.set_all_sizes(study)

  def set_all_sizes(self, study):
    size = Const.DRAWING_SIZE
    struct = study.rdm.struct
    margin = Const.AREA_MARGIN
    sw_w = self.w - 2*margin
    sw_h = self.h - 2*margin
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

class SVGExport(object):

  def __init__(self, myfile, w, h):
    xml = fakeReadXMLFile(myfile)
    rdm = fakeRdm(xml)
    rdm.struct.PrintErrorConsole()
    self.study = fakeStudy(rdm)
    self.drawing = fakeDrawing(w, h)

  def printDiagram(self, output):
    status = 1
    self.drawing.draw(self.study, output, status)

  def printCharDiagram(self, output, s_case):
    status = 2
    self.drawing.s_case = s_case
    self.drawing.draw(self.study, output, status)


  def printNDiagram(self, output, s_cases):
    status = 4
    self.drawing.s_cases = s_cases
    self.drawing.draw(self.study, output, status)

  def printVDiagram(self, output, s_cases):
    status = 5
    self.drawing.s_cases = s_cases
    self.drawing.draw(self.study, output, status)

  def printMDiagram(self, output, s_cases):
    status = 6
    self.drawing.s_cases = s_cases
    self.drawing.draw(self.study, output, status)



class fromXML_SVGExport(SVGExport):

  def __init__(self, string, w, h):
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    rdm.struct.PrintErrorConsole()
    self.study = fakeStudy(rdm)
    self.drawing = fakeDrawing(w, h)


