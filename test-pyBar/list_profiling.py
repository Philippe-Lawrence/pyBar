#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Test de la vitesse de modification d'une liste courte

# Conclusion :
# peu de différence

import cProfile


def fct1(li):
  u = li[0] + 1
  v = li[1] + 1
  return [u, v, li[2], li[3]]

def fct2(li):
  li[0] += 1
  li[1] += 1

def fct3(li):
  u = li[0] + 1
  v = li[1] + 1
  if len(li) == 2:
    return [u, v]
  elif len(li) == 3:
    return [u, v, li[2]]
  return [u, v, li[2], li[3]]



def test():
  li = [1, 2, 6, 8]
  for i in range(100000):
    li = fct1(li)
  print li

def test2():
  li = [1, 2, 6, 8]
  for i in range(100000):
    fct2(li)
  print li

def test3():
  li = [1, 2, 6, 8]
  for i in range(100000):
    li = fct3(li)
  print li



#cProfile.run('test()') # #  0,27 CPUs
#cProfile.run('test2()') # #  0,30 CPUs
cProfile.run('test3()') # #  0,30 CPUs
