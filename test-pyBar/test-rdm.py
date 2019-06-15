#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from fakeclassRdm import fakeRdm, fakeReadXMLString, fakeReadXMLFile
from classRdm import *
import function
string="""<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.3">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="1,0" id="N2" />
    <node d="2,0" id="N3" liaison="1" />
    <node d="1,1" id="N4" />
  </elem>
  <elem id="barre">
    <arc center="N2" end="N4" id="Arc1" r0="0" r1="1" start="N1" />
    <arc center="N2" end="N3" id="Arc2" r0="1" r1="0" start="N4" />
  </elem>
  <elem id="geo">
    <barre h="0.1" id="*" igz="1.71e-06" profil="IPE 100" s="0.00103" v="0.05" />
  </elem>
  <elem id="material">
    <barre alpha="12e-6" id="*" mv="7800" profil="AcierXC10" young="2.16e+11" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <arc fp="1.56,0,0,1" id="Arc1" />
      <arc fp="0.01,0,0,-1" id="Arc2" />
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
    <drawing axis="false" bar_name="true" node_name="true" scale="290.142" scale_pos="56.0,-30.0,66,25" show_title="true" status="3,0" title="150.0,358.0,87,23,arc" x0="100.0" y0="398.0" />
  </draw>
</data>"""

string="""<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.24">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="2,0" id="N3" liaison="1" />
    <node d="1,1" id="N4" />
  </elem>
  <elem id="barre">
    <barre end="N4" id="B3" r0="0" r1="1" start="N1" />
    <barre end="N3" id="B4" r0="1" r1="0" start="N4" />
  </elem>
  <elem id="geo">
    <barre h="0.1" id="*" igz="1.71e-06" profil="IPE 100" s="0.00103" v="0.05" />
  </elem>
  <elem id="material">
    <barre alpha="12e-6" id="*" mv="7800" profil="AcierXC10" young="2.16e+11" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <barre fp="@,%1.,0,0,1" id="B3" />
      <barre fp="@,0.0,0,0,-1" id="B4" />
    </case>
    <case id="cas 2" />
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
  <draw id="prefs" />
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
print("Soll=", Char.EndBarSol)
# Récupération d'un cas de charge ou d'une combinaison à partir du nom
#print("Reactions dans la combinaison =", rdm.Combis['combi1'].Reactions)
#print rdm.Combis['combinaison'].EndBarSol

