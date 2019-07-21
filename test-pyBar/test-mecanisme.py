#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fakeclassRdm import fakeRdm, fakeReadXMLString
string="""<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.3">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="0,3" id="N2" />
    <node d="4,3" id="N3" />
    <node d="4,0" id="N4" liaison="1" />
  </elem>
  <elem id="barre">
    <barre end="N2" id="B1" r0="0" r1="0" start="N1" />
    <barre end="N3" id="B2" r0="0" r1="0" start="N2" />
    <barre end="N4" id="B3" r0="0" r1="0" start="N3" />
  </elem>
  <elem id="geo">
    <barre h="0.14" id="*" igz="1.509e-05" profil="HE 140 B" s="0.0043" v="0.07" />
  </elem>
  <elem id="material">
    <barre alpha="1e-5" id="*" mv="7800" young="210000000000" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <node d="10.0,0.0,0.0" id="N2" />
    </case>
  </elem>
  <elem id="combinaison" />
  <elem id="prefs">
    <unit d="1.0" id="E" />
    <unit d="1.0" id="M" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="C" />
    <unit d="1.0" id="I" />
    <unit d="1.0" id="S" />
    <unit d="1000.0" id="F" />
    <const name="g" value="9.81" />
    <const name="conv" value="1" />
  </elem>
</data>
"""
xml = fakeReadXMLString(string)
rdm = fakeRdm(xml)

print("Passage 1")
print (rdm.struct.CalculDegreH())
if rdm.struct.status == 2:
  print (rdm.Chars['cas 1'].ddlValue)

rdm.struct.PrintErrorConsole()
#print "len=", rdm.struct.Lengths
#print "angles", rdm.struct.Angles
#print "Reactions=", rdm.Chars['cas 1'].Reactions
#Char = rdm.GetCharByNumber(0)

rdm.char_error = []
rdm.struct.Liaisons['N2'] = 3
rdm.struct.RaideurAppui['N2'] = (1., 1., 1.)
#print rdm.struct.Liaisons
print ("status=", rdm.struct.status)
rdm.struct.status = 1
rdm.struct.GetInvMatK()
print ("Passage 2")
#rdm = classRdm.R_Structure(struct)
rdm.Cases = rdm.GetCasCharge()
rdm.CombiCoef = rdm.GetCombi()
xmlnode = rdm.struct.XMLNodes["char"].getElementsByTagName('case')
rdm.Chars = {}
for cas in rdm.Cases:
  Char = CasCharge(cas, xmlnode, rdm.struct)
  rdm.Chars[cas] = Char
rdm.SolveCombis()
print(dm.Chars['cas 1'].ddlValue)
