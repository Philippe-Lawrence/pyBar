#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import os
from numpy import *
from fakeclassRdm import fakeRdm
from xml.dom import minidom
from classRdm import *
import function
import classRdm


string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.31">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="8,0" id="N2" liaison="2"/>
		<node d="22,0" id="N3" liaison="2"/>
		<node d="30,0" id="N4" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre d="N1,N2,0,0" id="B1"/>
		<barre d="N2,N3,0,0" id="B2"/>
		<barre d="N3,N4,0,0" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.16" id="*" igz="9.25e-06" profil="UPN 160" s="0.0024" v="0.08"/>
	</elem>
	<elem id="material">
		<barre id="B2,B3" mv="3000" young="200000000000"/>
		<barre id="B1" mv="6000" young="210000000000"/>
	</elem>
	<elem id="char">
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
</data>"""

rdm = fakeRdm(string)
m_rdm = classRdm.Moving_Structure(rdm.struct, ((2, 0),))
N = 10 # position convoi
mini, maxi, env_inf, env_sup = m_rdm.get_moving_data(N, 5)
print mini, maxi

m_rdm.Char.ini(4)
m_rdm.SolveOneCase(m_rdm.Char)

print m_rdm.GetValue("B2", 0., m_rdm.Char, 5)[1]

#print m_rdm.Char.charBarFp


#print "len=", rdm.struct.Lengths
#print "angles", rdm.struct.Angles
rdm.struct.PrintErrorConsole()
#rdm.struct.Curves['parabol1'].draw(None)
#print "Reactions=", rdm.Chars['cas1'].Reactions
#print "Reactions=", rdm.Chars['cas2'].Reactions
#print "Combis=", rdm.Combis['combi1'].Reactions
#Char = rdm.GetCharByNumber(0)
#print rdm.GetArcSollValues('parabol1', Char, 2, 1e-8)
#print Char.ddlValue
#print rdm.struct.Sections


