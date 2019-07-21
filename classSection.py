#!/usr/bin/python
# -*- coding: utf-8 -*- 
import numpy
import numpy.linalg
import math
import xml.etree.ElementTree as ET
import os

def rotation(a, x, y):
  """x, y étant les coordonnées d'un point dans un repère 1, retourne les coordonnées du point dans le repère 2 obtenu par rotation d'angle a"""
  x1 = x*math.cos(a) + y*math.sin(a)
  y1 = -x*math.sin(a) + y*math.cos(a)
  return x1, y1

def get_arc_type(start, end, center, r, a):
  if center is None:
    if end is None:
      cat = 4
    else:
      if a is None:
        cat = 5
      else:
        cat = 3
  else:
    if end is None:
      cat = 2
    else:
      cat = 1
  return cat

def get_arc_box(box, arc):
    #print("get_arc_box")
    x0, y0, x1, y1 = box
    xc, yc, r, teta1, teta2, sign = arc
    if r is None: return box
    #print("teta=", teta1, teta2)
    if teta1 < 0: teta1 += 2*math.pi
    if teta2 < 0: teta2 += 2*math.pi
    if sign == "+":
      if teta2 >= teta1: a = teta2 - teta1
      else: a = teta2 - teta1 + 2*math.pi
    else:
      if teta2 >= teta1: a = teta2 - teta1 - 2*math.pi
      else: a = teta2 - teta1
    n = 20
    pas = a / n
    for i in range(1, n-1):
      teta = teta1 + i*pas
      x, y = xc + r*math.cos(teta), yc + r*math.sin(teta)
      if x < x0: x0 = x
      elif x > x1: x1 = x
      if y < y0: y0 = y
      elif y > y1: y1 = y
    return x0, y0, x1, y1


def calcul_arc(x1, y1, x2, y2, xc, yc):
    #print(x1, y1, x2, y2, xc, yc)
    r = ((x1-xc)**2+(y1-yc)**2)**0.5
    r1 = ((x2-xc)**2+(y2-yc)**2)**0.5
    try:
      assert r == r1
    except AssertionError:
      print("Les rayons sont différents :", r, r1)
      return None, None, None, None
    corde = ((x2-x1)**2+(y2-y1)**2)**0.5
    teta1 = math.atan2(y1-yc, x1-xc)
    teta2 = math.atan2(y2-yc, x2-xc)
    #print("teta1, teta2 = ",teta1, teta2)
    return r, teta1, teta2, corde


class Node(object):

  def __init__(self, id, d):
    self.id = id
    self.d = d
    try:
      coors = d.split(',')
      self.x, self.y = [float(i) for i in coors]
    except ValueError:
      self.x, self.y, self.d = 0, 0, '0,0'

  def draw(self, cr, scale):
    cr.save()
    x, y = self.x, self.y
    cr.arc(x*scale, -y*scale, 4, 0, 6.29)
    cr.fill()
    cr.move_to(x*scale+10, -y*scale+15)
    cr.show_text(self.id)
    cr.stroke()
    cr.restore()

  def set_xml(self, xml):
    root = xml.getroot()
    parent = root.getchildren()[0]
    if not self.d: return
    if not self.id: return
    node = ET.SubElement(parent, "node", {"id": self.id, "d": self.d})

class ArcSegment(object):

  def __init__(self, id, cat, nodes, start=None, end=None, center=None, r=None, a=None, sign="+"):
    self.id = id
    #self.params = {"start": start, "end": end, "center": center, "a": a, "r": r, "sign": sign}
    self.cat = cat
    self.start = start
    self.end = end
    self.center = center
    self.r = r
    self.a = a
    self.sign = sign
    self.calculate(nodes)
    #self.update(nodes, start=start, end=end, center=center, r=r, a=a, sign=sign)

  def update(self, nodes, di):
    for key in di:
      #self.params[key] = di[key]
      setattr(self, key, di[key])
    self.calculate(nodes)

  def calculate(self, nodes):
    #print(self.start, self.end, self.center, self.r, self.cat)
    self.drawable = False
    if self.cat == 0:
      return
    if self.start is None:
      return
    self.x0, self.y0 = nodes[self.start].x, nodes[self.start].y
    if self.cat == 1:
      if self.end is None: return
      self.x1, self.y1 = nodes[self.end].x, nodes[self.end].y
      self.xc, self.yc = nodes[self.center].x, nodes[self.center].y
      self.r, self.teta1, self.teta2, corde = calcul_arc(self.x0, self.y0, self.x1, self.y1, self.xc, self.yc)
      self.drawable = True
        #return
    elif self.cat == 2:
      if self.center is None: return
      #if self.a
      self.xc, self.yc = nodes[self.center].x, nodes[self.center].y
      self.r = ((self.x0-self.xc)**2+(self.y0-self.yc)**2)**0.5
      #self.corde = ((x2-x1)**2+(y2-y1)**2)**0.5
      self.teta1 = math.atan2(self.y0-self.yc, self.x0-self.xc)
      self.teta2 = self.teta1 + self.a
      self.x1 = self.xc + math.cos(self.teta2)
      self.y1 = self.yc + math.sin(self.teta2)
      self.drawable = True
    elif self.cat == 3:
      pass
    elif self.cat == 4:
      pass
    elif self.cat == 5:
      if self.r is None: return
      if self.end is None: return
      self.x1, self.y1 = nodes[self.end].x, nodes[self.end].y
      #print("x0=", self.x0, self.y0, self.x1, self.y1, self.r)
      xi, yi = (self.x0+self.x1)/2, (self.y0+self.y1)/2
      teta = math.atan2(self.y1-self.y0, self.x1-self.x0)
      x0, y0 = rotation(teta, self.x0-xi, self.y0-yi)
      #print("x0 apres=", x0, y0)
      x1, y1 = rotation(teta, self.x1-xi, self.y1-yi)
      #print("x1 apres=", x1, y1)
      corde = ((x1-x0)**2+(y1-y0)**2)**0.5
      d = self.r**2-(corde/2)**2
      #print("d=", d)
      if d < 0: return
      d = d**0.5
      xc, yc = 0, -d
      xc, yc = rotation(-teta, xc, yc)
      #print("ici", xc, yc, teta, d)
      self.xc, self.yc = xc+xi, yc+yi
      try:
        self.teta1 = math.atan2(self.y0-self.yc, self.x0-self.xc)
        self.teta2 = math.atan2(self.y1-self.yc, self.x1-self.xc)
      except TypeError:
        return
      self.drawable = True


  def GetBox(self, box):

    #if self.start is None or self.end is None or self.center is None:
    #  return box
    try:
      tu = self.xc, self.yc, self.r, self.teta1, self.teta2, self.sign
      return get_arc_box(box, tu)
    except AttributeError:
      return box
 
  def draw(self, cr, scale):
    #if self.start is None or self.end is None or self.center is None or self.r is None: return
    #print("drawable",self.drawable)
    if not self.drawable: return
    if self.sign == '-': # rotation sens antitrigo
      cr.arc(self.xc*scale, -self.yc*scale, self.r*scale, -self.teta1, -self.teta2)
    else: # + rotation sens trigo
      cr.arc_negative(self.xc*scale, -self.yc*scale, self.r*scale, -self.teta1, -self.teta2)
    cr.stroke()
    cr.move_to((self.x0+self.x1)/2*scale, -(self.y0+self.y1)/2*scale)
    cr.show_text(self.id)
    cr.stroke()

  def set_xml(self, xml):
    parent = xml.getroot()
    if self.cat == 1: 
    #if self.start is None or self.end is None or self.center is None or self.sign is None: return
      node = ET.SubElement(parent, "arc", {"id": self.id, "start": self.start, "end": self.end, "center": self.center, "sign": self.sign})
    elif self.cat == 2: 
      pass
    elif self.cat == 3: 
      pass
    elif self.cat == 4: 
      pass
    elif self.cat == 5: 
      node = ET.SubElement(parent, "arc", {"id": self.id, "start": self.start, "end": self.end, "r": str(self.r), "sign": self.sign})



class CirclePath(object):


  def GetBox(self, box):
    #if self.r is None: return box
    try:
      x, y, r = self.xc, self.yc, self.r
    except AttributeError:
      return box
    xmin, ymin, xmax, ymax = box
    try:
      x = float(x)
      y = float(y)
      r = float(r)
    except ValueError:
      return box
    if x-r < xmin: xmin = x-r
    if x+r > xmax: xmax = x+r
    if y-r < ymin: ymin = y-r
    if y+r > ymax: ymax = y+r
    return [xmin, ymin, xmax, ymax]

  def draw(self, cr, scale):
    try:
      xc, yc, r = self.xc, self.yc, self.r
    except AttributeError:
      return
    cr.save()
    if self.fill:
      cr.set_source_rgb(0, 0, 0)
    else:
      cr.set_source_rgb(1, 0, 0)
    cr.arc(xc*scale, -yc*scale, r*scale, 0, 6.29)
    cr.stroke()
    cr.restore()

class CirclePathCP(CirclePath):
  """Cercle de centre donné et passant par un point"""

  def __init__(self, id, center, point, fill, nodes):
    self.id = id
    self.center = center
    self.point = point
    self.fill = fill
    if not self.center is None and not self.point is None:
      #self.center, self.point = d.split(" ")
      self.calculate(nodes)


  def calculate(self, nodes, arcs=None):
    try:
      node = nodes[self.center]
    except KeyError:
      self.r = None
      return
    self.xc, self.yc = node.x, node.y
    if self.point is None: return
    if self.point in nodes:
      node = nodes[self.point]
      x, y = node.x, node.y
      self.r = ((self.xc-x)**2+(self.yc-y)**2)**0.5
    else:
      try:
        self.r = float(self.point)
      except ValueError:
        self.r = 0

  def update(self, id, center, point, fill, nodes):
    #print(nodes)
    if id is None or center is None or point is None: return
    self.id = id
    self.center = center
    self.point = point
    self.fill = fill
    self.calculate(nodes)

  def set_xml(self, xml):
    parent = xml.getroot()
    if not self.id: return
    if self.center is None: return
    if self.point is None: return
    if self.fill: fill = "true"
    else: fill = "false"
    node = ET.SubElement(parent, "circle", {"id": self.id, "center": self.center, "point": self.point, "fill": fill})

class CirclePathCR(CirclePath):
  """Cercle de centre et de rayon donnés"""

  def __init__(self, id, center, r, fill, nodes):
    self.id = id
    self.center = center
    self.fill = fill
    try:
      self.r = float(r)
    except TypeError: 
      self.r = 0
    except ValueError:
      self.r = 0
    if not self.r is None:
      self.calculate(nodes)


  def calculate(self, nodes, arcs=None):
    try:
      node = nodes[self.center]
    except KeyError: 
      return
    self.xc, self.yc = node.x, node.y

  def update(self, id, center, r, fill, nodes):
    #print(nodes)
    if id is None or center is None or r is None: return
    self.id = id
    self.center = center
    self.r = r
    self.fill = fill
    self.calculate(nodes)

  def set_xml(self, xml):
    parent = xml.getroot()
    if not self.id: return
    if self.center is None: return
    if self.fill: fill = "true"
    else: fill = "false"
    node = ET.SubElement(parent, "circle", {"id": self.id, "center": self.center, "r": str(self.r), "fill": fill})


class Path(object):
  #class_counter = 1

  def __init__(self, id, d, fill, nodes, xml_arcs):
    self.id = id
    self.fill = fill
    self.d = d # list
    self.cairo_segments = []
    self.segments = [] # contour sans arcs (arc -> corde)
    self.cairo_arcs = []
    self.arcs = []
    if self.d:
      self.calculate(nodes, xml_arcs)

  def calculate(self, nodes, xml_arcs):
    #print("calculate")
    self.cairo_segments = []
# tester
    self.segments = [] # contour sans arcs (arc -> corde)
    self.cairo_arcs = []
    self.arcs = []
# --------------
    for i, elem in enumerate(self.d):
      if elem in xml_arcs:
        a = xml_arcs[elem]
        start, end, center, sign = a.start, a.end, a.center, a.sign
        #xc, yc = nodes[center].x, nodes[center].y
        xc, yc = a.xc, a.yc
        x0, y0 = nodes[start].x, nodes[start].y
        x1, y1 = nodes[end].x, nodes[end].y
        self.cairo_arcs.append(a)
        self.segments.append(tuple((x0, y0)))
        self.segments.append(tuple((x1, y1)))
        self.arcs.append(((x0, y0), (x1, y1), (xc, yc)))
        xprec, yprec = x1, y1
        if i == 0:
          xstart, ystart = x0, y0
      elif elem in nodes:
        node = nodes[elem]
        x, y = node.x, node.y
        self.segments.append(tuple((x, y)))
        if i == 0:
          xstart, ystart = x, y
        else:
          self.cairo_segments.append(tuple((xprec, yprec, x, y)))
        xprec, yprec = x, y
      else: continue
    if xprec != xstart or yprec != ystart:
      self.cairo_segments.append(tuple((xprec, yprec, xstart, ystart))) # cloturer
    #print("segment=", self.cairo_segments)


# ne pas supprimer !!
  def GetBox(self, box):
    return box

  def draw(self, cr, scale):
    cr.save()
    if self.fill:
      cr.set_source_rgb(0, 0, 0)
    else:
      cr.set_source_rgb(1, 0, 0)
    for elem in self.cairo_segments:
      x0, y0, x1, y1 = elem
      #print("draw=", x0, y0, x1, y1)
      cr.move_to(x0*scale, -y0*scale)
      cr.line_to(x1*scale, -y1*scale)
      cr.stroke()
    for a in self.cairo_arcs:
      a.draw(cr, scale)

    cr.restore()

  def set_xml(self, xml):
    parent = xml.getroot()
    if not self.d: return
    if not self.id: return
    if self.fill: fill = "true"
    else: fill = "false"
    d = " ".join(self.d)
    node = ET.SubElement(parent, "path", {"id": self.id, "d": d, "fill": fill})


class Section(object):
  """Classe parent aux classes Sections - Ne doit pas être instanciée en dehors de la classe"""

  def __init__(self):
    self.errors = []


# finir tous les attributs : points ..
  def __add__(self, other):
    #print("add", self.S, other.S)
    if self.S is None or other.S is None:
      return ErrorSection()
    p = Section()
    p.S = self.S + other.S
    #print("S+=",self.S, other.S, p.S)
    if p.S == 0.:
      return EmptySection()
    if self.box is None:
      p.box = other.box
    else:
      x0, y0, x1, y1 = self.box
      x2, y2, x3, y3 = other.box
      p.box = [min(x0, x2), min(y0, y2), max(x1, x3), max(y1, y3)] # coin inférieur G, coin sup Droit
    p.XG = self.S*self.XG + other.S*other.XG
    p.YG = self.S*self.YG + other.S*other.YG
    p.XG /= p.S
    p.YG /= p.S

    p.Igxx = self.Igxx + self.S*(p.YG-self.YG)**2
    p.Igxx += other.Igxx + other.S*(p.YG-other.YG)**2
    p.Igyy = self.Igyy + self.S*(p.XG-self.XG)**2
    p.Igyy += other.Igyy + other.S*(p.XG-other.XG)**2
    p.Igxy = self.Igxy + self.S*(p.XG-self.XG)*(p.YG-self.YG) 
    p.Igxy += other.Igxy + other.S*(p.XG-other.XG)*(p.YG-other.YG)
    return p

  def __sub__(self, other):
    if self.S is None or other.S is None:
      return ErrorSection()
    p = Section()
    p.S = self.S - other.S
    #print("S=",self.S, other.S, p.S)
    if p.S == 0.:
      return EmptySection()
    if self.box is None:
      p.box = other.box
    else:
      x0, y0, x1, y1 = self.box
      x2, y2, x3, y3 = other.box
      p.box = [min(x0, x2), min(y0, y2), max(x1, x3), max(y1, y3)] # coin inférieur G, coin sup Droit
    p.XG = self.S*self.XG - other.S*other.XG
    p.YG = self.S*self.YG - other.S*other.YG
    p.XG /= p.S
    p.YG /= p.S

    p.Igxx = self.Igxx + self.S*(p.YG-self.YG)**2
    p.Igxx -= other.Igxx + other.S*(p.YG-other.YG)**2
    p.Igyy = self.Igyy + self.S*(p.XG-self.XG)**2
    p.Igyy -= other.Igyy + other.S*(p.XG-other.XG)**2
    p.Igxy = self.Igxy + self.S*(p.XG-self.XG)*(p.YG-self.YG)
    p.Igxy -= other.Igxy + other.S*(p.XG-other.XG)*(p.YG-other.YG)
    return p

  def set_data(self):
    return ["", self.S, self.Igyy, self.H, self.YG]

  def print2term(self, echo=True):
    """Affichage en mode console"""
    if self.errors:
      string = "Données non valides :"
      for e in self.errors:
        string +="\tErreur dans la ligne : \"%s\"" % e
      if not echo:
        return string
      print(string)
      return
    if self.S is None:
      string = "Section non valide:: surface nulle"
      if not echo:
        return string
      print(string)
      return
    try:
      string = "Nombre de points (ou segments): %d" % len(self.points)
    except AttributeError:
      string = "Nombre de points (ou segments): \n\tnon disponible"
    string += "\nCoordonnées du CDG dans le repère global :\n\tXG=%.4f\n\tYG=%.4f" % (self.XG, self.YG)
    string += "\nSurface :\n\tS=%.4f" % self.S
    try:
      string += "\nDistance entre le CDG et les fibres extrêmes:\n\tv=%.4f v'=%.4f" % (self.vsup, self.vinf)
    except TypeError:
      string += "\nDistance entre le CDG et les fibres extrêmes:\n\tnon disponible"

    string += "\nMoments quadratiques par rapport au CDG : \n\tIgxx=%.5f\n\tIgxy=%.5f\n\tIgyy=%.5f" % (self.Igxx, self.Igxy, self.Igyy)
    Ixx, Ixy, Iyy = self.getMQuaHuygens(cdg_axis=False)
    string += "\nMoments quadratiques par rapport au repère global : \n\tIxx=%.5f\n\tIxy=%.5f\n\tIyy=%.5f" % (Ixx, Ixy, Iyy)


    matI = numpy.array([[self.Igxx, -self.Igxy], [-self.Igxy, self.Igyy]])
    Iuu, Ivv = numpy.linalg.eig(matI)[0][0:2]
    string += "\nValeurs propres :\n\tIuu=%.4f\n\tIvv=%.4f" % (Iuu, Ivv)
    x0, y0 = 0., 0.
    x1, y1 = numpy.linalg.eig(matI)[1][0]
    
    angle = math.atan2(y1-y0, x1-x0)*180/math.pi
    string += "\nPremière direction principale (par rapport à l'axe X du repère global) :\n\t%.2f deg" % angle
    #angle=math.acos(linalg.eig(matI)[1][0][0])*180/math.pi
    if not echo:
      return string
    print(string)

  def getMQuaHuygens(self, cdg_axis=True):
    """Calcule les moments quadratiques Ixx, Iyy, Ixy dans le repère Global à partir des moments quadratiques dans le cdg"""
    if cdg_axis:
      return self.Igxx, self.Igxy, self.Igyy
    Ixx = self.Igxx + self.S*self.YG**2
    Iyy = self.Igyy + self.S*self.XG**2
    Ixy = self.Igxy + self.S*self.XG*self.YG
    return Ixx, Ixy, Iyy

  def getWidth(self):
    """Retourne la largeur de la boite"""
    if self.box is None: return 0
    Xmin, Ymin, Xmax, Ymax = self.box
    return Xmax-Xmin

  def getHeigth(self):
    """Retourne la hauteur de la boite"""
    if self.box is None: return 0
    Xmin, Ymin, Xmax, Ymax = self.box
    return Ymax-Ymin


  def getVVprime(self):
    """Retourne la position v et v'du CDG suivant y"""
    if self.box is None:
      self.vinf = self.vsup = self.H = None 
      return
    self.vinf = self.box[3]-self.YG
    self.vsup = self.YG-self.box[1]
    self.H = self.box[3] - self.box[1]

class ErrorSection(Section):

  def __init__(self):
    print("error")
    self.errors = []
    self.S = None
    self.XG = None
    self.YG = None

  def print2term(self, echo=True):
    """Affichage en mode console"""
    string = "Impossible de calculer les caractéristiques de la section"
    if not echo:
      return string
    print(string)

class EmptySection(Section):
  """Contour de surface nulle"""

  def __init__(self):
    self.S, self.Igxx, self.Igxy, self.Igyy = 0., 0., 0., 0.
    self.XG, self.YG = 0., 0.
    self.errors = []
    self.box = None

  def print2term(self, echo=True):
    string = "Surface du contour nulle"
    if not echo:
      return string
    print(string)

class Arc(Section):
  """Calcule les caratéristiques d'un arc circulaire (la surface est celle fermée par la corde de l'arc)"""

  def __init__(self, start, end, center):
    self.S = None
    self.x1, self.y1 = start
    self.x2, self.y2 = end
    self.xc, self.yc = center
    Section.__init__(self)
    self.getGeo()
    self.box = self._get_box()

  def _get_box(self):
    if self.r is None: return
    x0, y0, x1, y1 = [min(self.x1, self.x2), min(self.y1, self.y2), max(self.x1, self.x2), max(self.y1, self.y2)]
    n = 20
    pas = self.a / n
    for i in range(1,n-1):
      #print(i)
      teta = self.teta1 + i*pas
      #print('teta=', teta)
      x, y = self.xc + self.r*math.cos(teta), self.yc + self.r*math.sin(teta)
      #print(x, y)
      if x < x0: x0 = x
      if x > x1: x1 = x
      if y < y0: y0 = y
      if y > y1: y1 = y
    return x0, y0, x1, y1

  def getGeo(self):
    """Calcule les coordonnées du CDG dans le repère global et la surface"""
    x1, x2, y1, y2 = self.x1, self.x2, self.y1, self.y2
    xc, yc = self.xc, self.yc
    r, teta1, teta2, corde = calcul_arc(x1, y1, x2, y2, xc, yc)
    self.r, self.teta1, self.teta2 = r, teta1, teta2
    if self.r is None: return
    #print("arc=", r, teta1, teta2)
    a = teta2-teta1
    if a <= 0:
      a += 2*math.pi # finir vérification
    #print("a=", a*180/math.pi)
    self.a = a
    self.S = 0.5*r**2*(a-math.sin(a))
    #print("S=", self.S)
    d = corde**3/12/self.S # distance centre - cdg de la surface
    c = (x1-x2)/corde
    s = (y1-y2)/corde
    self.XG, self.YG = self.xc-s*d, self.yc+c*d
    #print("arc cdg", self.XG, self.YG)
    Ia = r**4/8*(a-math.sin(a)*math.cos(a)) - d**2*self.S # moment par rapport à l'axe principal
    Ib = r**4/24*(3*a-4*math.sin(a)+math.sin(a)*math.cos(a)) # moment par rapport à l'axe principal
    # moment par rapport aux axes XY dans le repère passant par le CDG de l'arc
    self.Igxx = Ia*c**2 + Ib*s**2
    self.Igyy = Ia*s**2 + Ib*c**2
    self.Igxy = -Ia*s*c + Ib*s*c


class Circle(Section):
  """Calcule les caratéristiques d'une section circulaire constituant un contour complet"""

  def __init__(self, x, y, r):
    Section.__init__(self)
    self.XG, self.YG, self.r = x, y, r
    self.box = [x-r, y-r, x+r, y+r]
    self.getSurface()
    self.Igxx, self.Igxy, self.Igyy = self.getMQua(cdg_axis=True)

  def getSurface(self):
    """Calcule les coordonnées du CDG dans le repère global et la surface du cercle"""
    self.S = math.pi*self.r**2


  def getMQua(self, cdg_axis=True):
    """Calcule les moments quadratiques Ixx, Iyy, Ixy du cercle dans le repère GXY ou global"""
    I = self.S*self.r**2/4
    return I, 0., I

class Polygon(Section):
  """Calcule les caratéristiques d'une section constituée d'une suite de segments"""

  def __init__(self, points):
    Section.__init__(self)
    self.points = points
    #print("point=", self.points)
    #if len(self.points) <= 1:
    #  self.S = None
    #  return
    #if len(self.points) <= 2:
    #  self.S = 0.
    #  return
    self._getBoxCoors()
    self.getCDG()
    self.Igxx, self.Igxy, self.Igyy = self.getMQua(cdg_axis=True)
    #print "polygon=", self.XG, self.YG, self.S, self.Igyy

  def _getBoxCoors(self):
    """Crée un attribut contenant la liste des coordonnées de l'enveloppe du contour"""
    Xmin, Ymin = self.points[0]
    Xmax, Ymax = Xmin, Ymin
    for x0, y0 in self.points[1:]:
      if Xmax < x0:
        Xmax = x0
      if Xmin > x0:
        Xmin = x0
      if Ymax < y0:
        Ymax = y0
      if Ymin > y0:
        Ymin = y0
    self.box = [Xmin, Ymin, Xmax, Ymax] # coin inférieur G, coin sup Droit


  def _getXGi(self, x0, y0, x1, y1):
    """Retourne la contribution du segment dans le calcul de XG"""
    return (y1-y0)/6*(x1**2+x1*x0+x0**2)

  def _getYGi(self, x0, y0, x1, y1):
    """Retourne la contribution du segment dans le calcul de YG"""
    return -(x1-x0)/6*(y1**2+y1*y0+y0**2)

  def _getDS(self, x0, y0, x1, y1):
    """Retourne la contribution du segment dans le calcul de la surface"""
    return -(x1-x0)/2*(y0+y1)
    #return (y1-y0)/2*(x0+x1) # les deux formes sont équivalentes

  def _getIxxi(self, x0, y0, x1, y1):
    """Retourne la contribution du segment dans le calcul du moment quadratique Ixx"""
    return -(x1-x0)/12*(y1**2+y0**2)*(y1+y0)

  def _getIyyi(self, x0, y0, x1, y1):
    """Retourne la contribution du segment dans le calcul du moment quadratique Iyy"""
    return (y1-y0)/12*(x1**2+x0**2)*(x1+x0)

# revoir pour simplification éventuelle
  def _getIxyi(self, x0, y0, x1, y1):
    """Retourne la contribution du segment dans le calcul du produit d'inertie Ixy"""
    deltaX = x1-x0
    deltaY = y1-y0
    return deltaY/2*(y0*x0**2 + x0*y0*deltaX + y0/3*deltaX**2 + deltaY/2*x0**2 + 2./3*x0*deltaX*deltaY + deltaY/4*deltaX**2)

  def getMQua(self, cdg_axis=True):
    """Calcule les moments quadratiques Ixx, Iyy, Ixy dans le repère GXY ou global"""
    Ixx, Iyy, Ixy = 0., 0., 0.
    if self.S is None:
      return Ixx, Ixy, Iyy
    i = 1
    for x0, y0 in self.points:
      try:
        x1, y1 = self.points[i]
      except IndexError:
        x1, y1 = self.points[0]
      if cdg_axis:
        x0, y0, x1, y1 = x0-self.XG, y0-self.YG, x1-self.XG, y1-self.YG
      Ixx += self._getIxxi(x0, y0, x1, y1)
      Iyy += self._getIyyi(x0, y0, x1, y1)
      Ixy += self._getIxyi(x0, y0, x1, y1)
      i += 1
    Ixx = self._sign*Ixx
    Ixy = self._sign*Ixy
    Iyy = self._sign*Iyy
    return Ixx, Ixy, Iyy

  def getCDG(self):
    """Calcule les coordonnées du CDG dans le repère global et la surface"""
    XG, YG, S = 0., 0., 0.
    i = 1
    for x0, y0 in self.points:
      try:
        x1, y1 = self.points[i]
      except IndexError:
        x1, y1 = self.points[0]
      XG += self._getXGi(x0, y0, x1, y1)
      YG += self._getYGi(x0, y0, x1, y1)
      S += self._getDS(x0, y0, x1, y1)
      i += 1
    if S == 0.:
      self.S = 0
      self.XG = 0
      self.YG = 0
      self._sign = 0
      return
    self.XG = XG/S
    self.YG = YG/S
    if S < 0:
      self._sign = -1
    else:
      self._sign = 1
    self.S = self._sign*S


class Analyser(object):

  def __init__(self, tree):
    self.xml = tree
    polygon = EmptySection() # initialisation
    # définition des points
    self._Xml2Nodes(tree)
    # définition des arcs comme partie d'un contour
    self._Xml2Arcs(tree)
    outlines1, outlines2, arcs1, arcs2 = self._Xml2Polygons(tree)
    #print( outlines1, outlines2, arcs1, arcs2 )
    for outline in outlines1:
      polygon += Polygon(outline)
    for outline in outlines2:
      polygon -= Polygon(outline)
    circles1, circles2 = self._Xml2Circles(tree)
    for x, y, r in circles1:
      polygon += Circle(x, y, r)
    for x, y, r in circles2:
      polygon -= Circle(x, y, r)
    #arcs1.extend(arcs3)
    #arcs2.extend(arcs4)
    for start, end, center in arcs1:
      polygon += Arc(start, end, center)
    for start, end, center in arcs2:
      polygon -= Arc(start, end, center)
    self.section = polygon
    self.section.getVVprime()
    self.print_errors()


  def print2term(self, echo):
    if self.errors:
      return
    try:
      self.section
    except AttributeError:
      if echo:
        print("Section non définie")
      else:
        return "Section non définie"
    return self.section.print2term(echo)

  def set_data(self):
    if self.errors:
      return None
    try:
      data = self.section.set_data()
    except AttributeError:
      return None
     
    if not self.file is None:
      data[0] = os.path.basename(self.file)
    return data

  def print_errors(self):
    """Affichage des erreurs de lecture du xml"""
    if self.errors:
      for error in self.errors:
        print(error)

  def _Xml2Nodes(self, xml_path):
    self.root = root = xml_path.getroot()
    self.nodes = {} # initialisation des noeuds
    for node in root.getiterator('node'):
      d = node.get("d")
      id = node.get("id")
      self.nodes[id] = Node(id, d)
    #print("Nodes=", self.nodes)


  def _Xml2Circles(self, xml_path):
    """Convertit la structure xml en contours circulaires."""
    #self.circles = {}
    circles1, circles2 = [], []
    root = xml_path.getroot()
    for node in root.getiterator('circle'):
      fill = node.get("fill")
      if fill is None or fill == "true":
        fill = True
      else:
        fill = False
      center = node.get("center")
      r = node.get("r")
      point = node.get("point")
      id = node.get("id")
      if r is None:
        path = CirclePathCP(id, center, point, fill, self.nodes)
      else:
        path = CirclePathCR(id, center, r, fill, self.nodes)
      self.paths[path.id] = path
      if fill:
        circles1.append((path.xc, path.yc, path.r))
      else:
        circles2.append((path.xc, path.yc, path.r))
    return circles1, circles2


  def _Xml2Polygons(self, xml_path):
    """Convertit la structure xml en contours de type polygones."""
    outlines1, outlines2 = [], []
    arcs1, arcs2 = [], []
    self.paths = {}
    self.errors = errors = []
    self.root = root = xml_path.getroot()
    for node in root.getiterator('path'):
      fill = node.get("fill")
      if fill is None or fill == "true":
        fill = True
      else:
        fill = False
      d = node.get("d")
      d = d.strip()
      elems = d.split(' ')
      id = node.get("id")
      path = Path(id, elems, fill, self.nodes, self.arcs)
      self.paths[path.id] = path
      if fill:
        outlines1.append(path.segments)
        arcs1.extend(path.arcs)
      else:
        outlines2.append(path.segments)
        arcs2.extend(path.arcs)
    #print("arc=", arcs1, arcs2)
    return outlines1, outlines2, arcs1, arcs2



  def _Xml2Arcs(self, xml_path):
    """Convertit la structure xml en contours de type arc à parir d'une balise arc."""
    self.arcs = {}
    root = xml_path.getroot()
    for node in root.getiterator('arc'):
      id = node.get("id")
      start = node.get("start")
      end = node.get("end")
      center = node.get("center")
      r = node.get("r")
      if not r is None:
        try:
          r = float(r)
        except ValueError:
          r = None
      a = node.get("a")
      if not a is None:
        try:
          a = float(a)
        except ValueError:
          a = None
      sign = node.get("sign")
      cat = get_arc_type(start, end, center, r, a)
      Obj = ArcSegment(id, cat, self.nodes, start, end, center, r, a, sign)
      self.arcs[id] = Obj

class NewAnalyser(Analyser):

  def __init__(self):
    self.file = None
    self.xml = None
    polygon = EmptySection() # initialisation
    self.paths = {}
    self.nodes = {}
    self.arcs = {}
    self.errors = []



class FileAnalyser(Analyser):

  def __init__(self, path):
    #self.path = path
    self.file = os.path.basename(path)
    tree = self.readFile(path)
    Analyser.__init__(self, tree)

  def readFile(self, path):
    """Lit le fichier de points et retourne une liste contenant les coordonnées de chaque segment"""
    return ET.parse(path)

class StringAnalyser(Analyser):

  def __init__(self, string):
    self.file = "non défini"
    tree = self.readFile(string)
    Analyser.__init__(self, tree)

  def readFile(self, string):
    """Lit le fichier de points et retourne une liste contenant les coordonnées de chaque segment"""
    E = ET.fromstring(string)
    return ET.ElementTree(E)



