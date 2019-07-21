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
    <node d="1,0" id="N2" liaison="2" />
    <node d="2,0" id="N3" liaison="2" />
  </elem>
  <elem id="barre">
    <barre end="N2" id="B1" r0="0" r1="0" start="N1" />
    <barre end="N3" id="B2" r0="0" r1="0" start="N2" />
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
      <depi id="N2" d="0,-0.01" />
      <barre id="B1" qu="0,,0.0,-10.0" />
    </case>
    <case id="cas 2">
      <barre id="B2" qu="0,,0.0,-10.0" />
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
  <draw id="prefs" />
</data>"""
string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1" dep="0.01,0.01" />
		<node d="@N1,2,0" id="N2" liaison="2,45"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre h="" id="*" igz="1.0" s="1e-06" v=""/>
	</elem>
	<elem id="material">
		<barre id="*" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N1"  d="0.01,0.01" />
		</case>
		<case id="cas 2">
			<depi id="N1"  d="0.01,0.01" />
			<barre id="B1" tri="@,%50,%60,0.0,10000.0,90.0"/>
		</case>
	</elem>
	<elem id="combinaison"/>
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


# Lecture des données soit à partir d'un fichier

#xml = fakeReadXMLFile("/home/.../pyBar/fichier.dat")

# soit à partir d'une chaine de caractère contenant du xml

xml = fakeReadXMLString(string)


rdm = fakeRdm(xml)
rdm.struct.PrintErrorConsole()
#print(rdm.struct.Barres)
print(rdm.struct.InvMatK)

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

