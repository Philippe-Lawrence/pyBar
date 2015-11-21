#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Test de la vitesse d'accès à des valeurs dans un dictionnaire

# Conclusion : écarter la méthode get !!!
# Préferer : if key in di:


def fct1(x):
  a = 0
  if a == 0: return x
  return x

def fct2(x):
  a = 0
  return x

import cProfile
import math
n = 10000

class A(object):
  def __init__(self, a):
    for i in range(n):
      self.calcul(a)
  def calcul(self, a):
    if a == 0:
      return a 
    return math.sin(a)
    
class B(object):
  def __init__(self, a):
    def do(a):
      if a == 0:
        return a
      self.calcul(a)

    for i in range(n):
      do(a)
    
  def calcul(self, a):
    return math.sin(a)

def test():
  a = A(0)

#cProfile.run('test1()') #  0,55 CPUs
cProfile.run('test()') # # 0.29 CPUs
