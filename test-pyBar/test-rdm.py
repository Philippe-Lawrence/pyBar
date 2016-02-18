#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from fakeclassRdm import fakeRdm, fakeReadXMLString, fakeReadXMLFile
from classRdm import *
import function
string="""<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.24">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="1,0" id="N2" liaison="1" />
    <arc d="0.25" id="N3" name="Parabole1" pos_on_curve="true" r="0" />
  </elem>
  <elem id="barre">
    <parabola end="N2" f="0.1" id="Parabole1" r0="0" r1="0" start="N1" />
  </elem>
  <elem id="geo">
    <barre id="*" igz="1" s="0.1" />
  </elem>
  <elem id="material">
    <barre id="*" young="200e9" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <arc fp="%0.25,0,-1,0" id="Parabole1" />
    </case>
  </elem>
  <elem id="combinaison" />
  <elem id="prefs">
    <unit d="1.0" id="C" />
    <unit d="1.0" id="E" />
    <unit d="1.0" id="F" />
    <unit d="1.0" id="I" />
    <unit d="1.0" id="M" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="S" />
    <const g="9.81" />
    <conv conv="1.0" />
  </elem>
  <draw id="prefs">
    <drawing axis="false" bar_name="true" node_name="true" scale="254.0" scale_pos="36.0,93.0,58,25" show_title="true" status="3,0" title="130.0,38.0,181,25,test-parabole.dat" x0="80.0" y0="158.0" />
  </draw>
</data>"""



# Lecture des données soit à partir d'un fichier

#xml = fakeReadXMLFile("/home/.../pyBar/fichier.dat")

# soit à partir d'une chaine de caractère contenant du xml

xml = fakeReadXMLString(string)


rdm = fakeRdm(xml)
rdm.struct.PrintErrorConsole()


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

# Récupération d'un cas de charge ou d'une combinaison à partir du nom
#print("Reactions dans la combinaison =", rdm.Combis['combi1'].Reactions)
#print rdm.Combis['combinaison'].EndBarSol

