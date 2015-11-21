#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Test de la vitesse d'accès à des valeurs dans un dictionnaire

# Conclusion : écarter la méthode get !!!
# Préferer : if key in di:

import cProfile
di = {}
n = 100000
for i in range(n):
  di[i] = i

class Test(object):
  def __init__(self, name, i):
    self.name = name
    self.x = i

li = []
for i in range(n):
  #key = "N%s" % i
  Inst = Test(i, i)
  li.append(Inst)

def test(di):
  for i in range(n):
    val = di[i]
def test2(li):
  for i in range(n):
    val = li[i].name

cProfile.run('test(di)') # CPUs
#cProfile.run('test2(li)') # # 3,046 CPUs
