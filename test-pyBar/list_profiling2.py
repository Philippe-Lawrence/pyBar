#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Test de la vitesse de modification d'une liste courte

# Conclusion :
# peu de différence

import cProfile


def fct1(li):
  u = li[0]
  v = li[1]
  w = li[2]
  z = u*v*w
  z = u*v*w
  z = u*v*w

def fct2(li):
  z = li[0]*li[1]*li[2]
  z = li[0]*li[1]*li[2]
  z = li[0]*li[1]*li[2]


def test():
  li = [1, 2, 6]
  for i in range(100000):
    fct1(li)

def test2():
  li = [1, 2, 6]
  for i in range(100000):
    fct2(li)


#cProfile.run('test2()') # #  0,32 CPUs
cProfile.run('test()') # #  0,311 CPUs
