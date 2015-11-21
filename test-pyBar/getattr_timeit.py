#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Test de la vitesse de calcul d'une racine carrée

# Conclusion : écarter la méthode avec math.sqrt


#import cProfile
#import timeit

n = 100

class A(object):
  def __getattr__(self, name):
    if name in self.__dict__:
        return self.__dict__[name]
    elif '_struct' in self.__dict__:
        return getattr(self._struct, name)
    else:
        return None

  def __setattr__(self, name, value):
    if name not in self.__dict__:
        self.__dict__[name] = value
    else:
        if hasattr(self._struct, name):
            setattr(self._struct, name, value)
        else:
            setattr(self, name, value)

  def __init__(self, B):
    self.B = B

class B(object):
  def __init__(self):
    self.x = 1

class C(object):

  def __init__(self, B):
    self.B = B

def test():
  b = B()
  for i in range(n):
    a = A(b)
    x = a.x

def test2():
  b = B()
  for i in range(n):
    a = C(b)
    x = a.B.x

def testsauv():
    "Stupid test function"
    L = []
    for i in range(100):
        L.append(i)

if __name__=='__main__':
    from timeit import Timer
    t = Timer("test2()", "from __main__ import test2")
    print t.timeit(number=10000)




#test()
#cProfile.run('test()') # 1,03 CPUs
#cProfile.run('test2()') # 0,33 CPUs
