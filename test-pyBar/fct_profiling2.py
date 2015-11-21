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

class A(object):
  def __init__(self, a):
    x = fct1(a)

class B(object):
  def __init__(self, a):
    if not a == 0:
      x = fct2(0)

n = 100000
      
def test1():
  for i in range(n):
    a = A(0)

def test2():
  for i in range(n):
    a = B(0)

#cProfile.run('test1()') #  0,55 CPUs
cProfile.run('test2()') # # 0.29 CPUs
