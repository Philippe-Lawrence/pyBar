#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Test de la vitesse d'accès à des valeurs dans un dictionnaire

# Conclusion : écarter la méthode get !!!
# Préferer : if key in di:

import cProfile
di = {}
n = 1000000
for i in range(n):
  key = "N%s" % i
  if i == 50:
    di[key] = 1
  else:
    di[key] = 0


di2 = {"N50": 1}

def test(di):
  for i in range(n):
    val = di["N%s" % i]

def test2(di):
  for i in range(n):
    val = di.get("N%s" % i, 1)

def test3(di):
  for i in range(n):
    key = "N%s" % i
    if key in di:
      val = di[key]
    else:
      val = 0

def test4(di):
  for i in range(n):
    key = "N%s" % i
    try:
      val = di[key]
    except KeyError:
      val = 0
#cProfile.run('test(di)') # 0,544 CPUs
#cProfile.run('test2(di2)') # # 3,046 CPUs
#cProfile.run('test3(di2)') # 0,476 CPUs
cProfile.run('test4(di2)') # #  1,89 CPUs
