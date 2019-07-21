#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from fakeclassRdm import fakeRdm, fakeReadXMLString, fakeReadXMLFile
from classRdm import *
import function
string="""<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.4">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="2,0" id="N2" liaison="1" />
    <arc d="0.5" id="N3" name="Parabole2" pos_on_curve="true" r="0" />
  </elem>
  <elem id="barre">
    <parabola end="N2" f="0.4" id="Parabole2" r0="0" r1="0" start="N1" />
    <barre end="N3" id="B2" r0="0" r1="0" start="N1" mode="1"/>
    <barre end="N2" id="B3" r0="0" r1="0" start="N3" mode="1"/>
  </elem>
  <elem id="geo">
    <barre h="" id="*" igz="1" profil="" s="1" v="" />
  </elem>
  <elem id="material">
    <barre alpha="" id="*" mv="1" young="200000000000" />
  </elem>
  <elem id="char">
    <case id="cas1">
      <pp d="false" />
      <arc id="Parabole2" proj="0" qu="%0.0,1.0,0.0,-1000.0,0.0,-1000.0" />
    </case>
    <case id="cas2">
      <node d="0,-1000,0" id="N3" />
    </case>
  </elem>
  <elem id="combinaison">
    <combinaison d="1.0,2.0" id="combi1" />
  </elem>
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
Char = rdm.Combis['combi1']

#print Char.EndBarSol # sollicitation aux bouts des barres

# Degré de liberté
#print("DDL=", Char.ddlValue['N2'])
#print("DDL=", Char.ddlValue['N6'])

# Récupération des contraintes normales aux fibres sup et inf
#print(rdm.GetSigma(Char, 0., "B1"))

# réactions d'appuis
print()
print("Reactions dans cas1=", Char.Reactions)
#print("Soll=", Char.EndBarSol)

# Récupération d'un cas de charge ou d'une combinaison à partir du nom
#print("Reactions dans la combinaison =", rdm.Combis['combi1'].Reactions)
#print rdm.Combis['combinaison'].EndBarSol

