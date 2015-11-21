#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Test de la vitesse de calcul d'une racine carrée

# Conclusion : écarter la méthode avec math.sqrt


import cProfile
import math

n = 1000000

def test():
  for i in range(n):
    val = math.sqrt(i)

def test2():
  for i in range(n):
    val = i**0.5

cProfile.run('test()') # 2,56 CPUs
#cProfile.run('test2()') # 0,27 CPUs
