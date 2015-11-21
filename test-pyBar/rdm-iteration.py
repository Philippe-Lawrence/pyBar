#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from fakeclassRdm import fakeRdm
from classRdm import *
import function

string = """<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.4">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="0,3" id="N2" />
    <node d="4,3" id="N3" />
    <node d="4,0" id="N4" liaison="1" />
  </elem>
  <elem id="barre">
    <barre d="N1,N2,0,0" id="B1" />
    <barre d="N2,N3,0,0" id="B2" />
    <barre d="N3,N4,0,0" id="B3" />
    <barre d="N2,N4,1,1" id="B4" />
    <barre d="N1,N3,1,1" id="B5" />
  </elem>
  <elem id="geo">
    <barre h="0.14" id="*" igz="1.509e-05" profil="HE 140 B" s="0.0043" v="0.07" />
    <barre h="" id="B4,B5" igz="1e-3" profil="" s="1e-3" v="" />
  </elem>
  <elem id="material">
    <barre alpha="1e-5" id="*" mv="7800" young="210000000000" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <node d="10000.0,0.0,0.0" id="N2" />
    </case>
    <case id="cas 2">
      <barre id="B2" qu="0,1,0.0,-120000.0" />
    </case>
    <case id="cas 3" />
  </elem>
  <elem id="combinaison">
    <combinaison d="1.35,1.5,0.0" id="combi1" />
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
  <draw id="prefs">
  </draw>
</data>"""
string = """<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.4">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="0,5.2" id="N2" />
    <node d="@N2,6.2,0" id="N3" />
    <node d="@N1,6.2,0" id="N4" liaison="1" />
    <node d="@N3,6.2,0" id="N5" />
    <node d="@N4,6.2,0" id="N6" liaison="1" />
    <node d="@N5,6.2,0" id="N7" />
    <node d="@N6,6.2,0" id="N8" liaison="1" />
  </elem>
  <elem id="barre">
    <barre end="N2" id="B1" r0="0" r1="1" start="N1" />
    <barre end="N3" id="B2" r0="0" r1="0" start="N2" />
    <barre end="N4" id="B3" r0="0" r1="0" start="N3" />
    <barre end="N5" id="B4" r0="0" r1="0" start="N3" />
    <barre end="N6" id="B5" r0="0" r1="0" start="N5" />
    <barre end="N7" id="B6" r0="0" r1="0" start="N5" />
    <barre end="N8" id="B7" r0="0" r1="0" start="N7" />
    <barre end="N4" id="B8" r0="1" r1="1" start="N2" mode="1" />
    <barre end="N3" id="B9" r0="1" r1="1" start="N1" mode="1" />
    <barre end="N6" id="B10" r0="1" r1="1" start="N3" mode="1" />
    <barre end="N5" id="B11" r0="1" r1="1" start="N4" mode="1" />
    <barre end="N8" id="B12" r0="1" r1="1" start="N5" mode="1" />
    <barre end="N7" id="B13" r0="1" r1="1" start="N6" mode="1" />
  </elem>
  <elem id="geo">
    <barre h="" id="*" igz="5.696e-05" profil="" s="0.00781" v="" />
  </elem>
  <elem id="material">
    <barre id="*" young="210000000000" />
  </elem>
  <elem id="char">
    <case id="cas1">
      <pp d="false" />
      <node d="-10000.0,0.0,0.0" id="N2" />
    </case>
    <case id="cas2">
      <node d="10000.0,0.0,0.0" id="N2" />
    </case>
  </elem>
  <elem id="combinaison">
    <combinaison d="1.0,1.1" id="combi1" />
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
rdm = fakeRdm(string)
rdm.struct.PrintErrorConsole()
# les données géométrique se trouvent dans rdm.struct
# print rdm.struct.Sections
# récupération du cas à partir du numéro
Char = rdm.GetCharByNumber(2)
#print "DDL=", Char.ddlValue
print "Reactions dans =", Char.Reactions
#print "Reactions dans la combinaison =", rdm.Combis['combinaison'].Reactions
#print rdm.Combis['combi1'].EndBarSol
print Char.EndBarSol['B9']
print "Sections=", rdm.struct.Sections

#print "Reactions dans cas1=", Char.Reactions

