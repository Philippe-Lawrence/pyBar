#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from fakeclassRdm import fakeRdm, fakeReadXMLString, fakeReadXMLFile
from classRdm import *
import function
string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="1,0" id="N2"  dep="0.01" liaison="2"/>
		<node d="2,0" id="N3"  dep="0.01" liaison="2"/>
		<node d="3,0" id="N4" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1" k1="0"/>
		<barre start="N2" end="N3" id="B2" k1="0"/>
		<barre start="N3" end="N4" id="B3"/>
		<rot_elast kz="0" node="N2" barre="B1"/>
		<rot_elast kz="0" node="N3" barre="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8.3e-05" s="0.0053" v="0.15"/>

	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
	<barre fp="%0.5,0.0,-1000000.0,0.0" id="B2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi 1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""


string2="""<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.0">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="0,4" id="N2" />
    <node d="5,4" id="N3" />
    <node d="5,0" id="N4" liaison="1" />
  </elem>
  <elem id="barre">
    <barre end="N2" id="B1" r0="0" r1="0" start="N1" />
    <barre end="N3" id="B2" r0="0" r1="0" start="N2" />
    <barre end="N4" id="B3" r0="0" r1="0" start="N3" />
    <barre end="N3" id="B4" mode="-1" r0="1" r1="1" start="N1" />
  </elem>
  <elem id="geo">
    <barre h="0.14" id="*" igz="1.509e-05" profil="HE 140 B" s="0.0043" v="0.07" />
  </elem>
  <elem id="material">
    <barre alpha="1e-5" id="*" mv="7800" young="200000000000" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <node d="1000,0,0" id="N2" />
    </case>
    <case id="cas 2">
      <node d="-500,0,0" id="N2" />
    </case>
  </elem>
  <elem id="combinaison">
    <combinaison d="1.0,1.0" id="combi1" />
  </elem>
  <elem id="prefs">
    <unit d="1.0" id="I" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="M" />
    <unit d="1.0" id="C" />
    <unit d="1.0" id="S" />
    <unit d="1.0" id="F" />
    <unit d="1.0" id="E" />
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


# les données géométrique se trouvent dans rdm.struct
# print rdm.struct.Sections

# récupération du cas à partir du numéro
Char = rdm.GetCharByNumber(1)
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

