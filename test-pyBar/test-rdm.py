#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from fakeclassRdm import fakeRdm, fakeReadXMLString, fakeReadXMLFile
from classRdm import *
import function
string="""<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.3">
  <elem id="node">
    <node id="N1" d="0,0" liaison="2,-45" />
    <node id="N2" d="1,0" liaison="2,45" />
  </elem>
  <elem id="barre">
    <barre id="B1" start="N1" end="N2" r0="0" r1="0" />
  </elem>
  <elem id="geo">
    <barre id="*" profil="IPE 80" s="0.0007639999999999999" igz="8.014e-07" h="0.08" v="0.04" />
  </elem>
  <elem id="material">
    <barre id="*" young="200e9" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <barre id="B1" fp="0.5,0,-1000,0" />
    </case>
  </elem>
  <elem id="combinaison" />
  <elem id="prefs">
    <unit id="L" d="1.0" />
    <unit id="C" d="1.0" />
    <unit id="E" d="1.0" />
    <unit id="F" d="1.0" />
    <unit id="I" d="1.0" />
    <unit id="M" d="1.0" />
    <unit id="S" d="1.0" />
    <const name="g" value="9.81" />
    <const name="conv" value="1" />
  </elem>
</data>"""


# Lecture des données soit à partir d'un fichier

#xml = fakeReadXMLFile("/home/.../pyBar/fichier.dat")

# soit à partir d'une chaine de caractère contenant du xml

xml = fakeReadXMLString(string)


rdm = fakeRdm(xml)
rdm.struct.PrintErrorConsole()
#print(rdm.struct.Barres)

# les données géométrique se trouvent dans rdm.struct
# print rdm.struct.Sections

# récupération du cas à partir du numéro
Char = rdm.GetCharByNumber(0)
#Char = rdm.Combis['combi1']

#print Char.EndBarSol # sollicitation aux bouts des barres

# Degré de liberté
#print("DDL=", Char.ddlValue['N5'])
#print("DDL=", Char.ddlValue['N6'])

# Récupération des contraintes normales aux fibres sup et inf
#print(rdm.GetSigma(Char, 0., "B1"))

# réactions d'appuis
print("Reactions dans cas1=", Char.Reactions)
print("DDL=", Char.ddlValue)
#print("Soll=", Char.EndBarSol)
# Récupération d'un cas de charge ou d'une combinaison à partir du nom
#print("Reactions dans la combinaison =", rdm.Combis['combi1'].Reactions)
#print rdm.Combis['combinaison'].EndBarSol

