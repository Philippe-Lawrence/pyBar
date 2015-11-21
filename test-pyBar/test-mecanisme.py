#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import os
from numpy import *
from fakeclassRdm import fakeRdm
from xml.dom import minidom
from classRdm import *
import function

string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.31">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="0,3" id="N2"/>
		<node d="4,3" id="N3"/>
		<node d="4,0" id="N4" liaison="1"/>
	</elem>
	<elem id="barre">
		<barre d="N1,N2,0,0" id="B1"/>
		<barre d="N2,N3,1,1" id="B2"/>
		<barre d="N3,N4,0,0" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.14" id="*" igz="1.509e-05" profil="HE 140 B" s="0.0043" v="0.07"/>
	</elem>
	<elem id="material">
		<barre alpha="1e-5" id="*" mv="7800" young="210000000000"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="1.0,0.0,0.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
		<const g="9.81"/>
		<conv conv="1.0"/>
	</elem>
</data>
"""

string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.31">
	<elem id="node">
		<node d="0,0" id="N1" liaison="2"/>
		<node d="1,0" id="N2" liaison="2"/>
		<node d="2,0" id="N3"/>
		<node d="3,0" id="N4" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre d="N1,N2,0,0" id="B1"/>
		<barre d="N2,N3,0,1" id="B2"/>
		<barre d="N3,N4,0,0" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.14" id="*" igz="1.509e-05" profil="HE 140 B" s="0.0043" v="0.07"/>
	</elem>
	<elem id="material">
		<barre alpha="1e-5" id="*" mv="7800" young="210000000000"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,1.0,0.0" id="N3"/>
		</case>
	</elem>
	<elem id="combinaison">
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
		<const g="9.81"/>
		<conv conv="1.0"/>
	</elem>
</data>
"""
string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.31">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="1,0" id="N2"/>
		<node d="3,0" id="N3" liaison="1"/>
	</elem>
	<elem id="barre">
		<barre d="N1,N2,0,0" id="B1"/>
		<barre d="N2,N3,1,0" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.14" id="*" igz="1.509e-05" profil="HE 140 B" s="0.0043" v="0.07"/>
	</elem>
	<elem id="material">
		<barre alpha="1e-5" id="*" mv="7800" young="210000000000"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,1.0,0.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
		<const g="9.81"/>
		<conv conv="1.0"/>
	</elem>
</data>
"""

rdm = fakeRdm(string)
print "Passage 1"
print rdm.struct.CalculDegreH()
if rdm.struct.status == 2:
  print rdm.Chars['cas 1'].ddlValue

rdm.struct.PrintErrorConsole()
#print "len=", rdm.struct.Lengths
#print "angles", rdm.struct.Angles
#print "Reactions=", rdm.Chars['cas 1'].Reactions
#Char = rdm.GetCharByNumber(0)

rdm.char_error = []
rdm.struct.Liaisons['N2'] = 3
rdm.struct.RaideurAppui['N2'] = (1., 1., 1.)
#print rdm.struct.Liaisons
print "status=", rdm.struct.status
rdm.struct.status = 1
rdm.struct.GetInvMatK()
print "Passage 2"
#rdm = classRdm.R_Structure(struct)
rdm.Cases = rdm.GetCasCharge()
rdm.CombiCoef = rdm.GetCombi()
xmlnode = rdm.struct.XMLNodes["char"].getElementsByTagName('case')
rdm.Chars = {}
for cas in rdm.Cases:
  Char = CasCharge(cas, xmlnode, rdm.struct)
  rdm.Chars[cas] = Char
rdm.SolveCombis()
print rdm.Chars['cas 1'].ddlValue
