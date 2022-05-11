#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#from time import sleep
from fakeclassRdm import fakeRdm, fakeReadXMLString
#from classEditor import Editor
import unittest
#from xml.dom import minidom


class barreSimpleTestCase(unittest.TestCase) :

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="200,0" id="N2" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="1e-4" s="10" v="0.15"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7.8" young="200000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" qu="%0,%1,0,1e-2"/>
			<pp d="true"/>
		</case>
	</elem>
	<elem id="combinaison">
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1." id="I"/>
		<unit d="1000" id="M"/>
		<unit d="0.01" id="L"/>
		<unit d="1e-4" id="S"/>
		<const g="9.81"/>
	</elem>
</data>
"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm=self.rdm
    Char = rdm.Chars['cas 1']
    #rdm=self._genere_instance()
    assert rdm.struct.Nodes == {"N1" : (0,0), "N2" : (2,0)}
    assert rdm.struct.Barres == {"B1" : ["N1","N2",0,0]}
    self.assertEqual(rdm.struct.status,1,"Erreur dans la lecture des données") 
    Char = rdm.Chars['cas 1']
    q = rdm.struct.Sections["*"]*rdm.struct.VolMass["*"]*rdm.struct.G-1
    self.assertAlmostEqual(rdm.DepPoint(Char, "B1",1.)[1], 
      -5.*rdm.struct.Lengths["B1"]**4/384/rdm.struct.MQua["*"]/rdm.struct.Youngs["*"]*q, 7, "La flèche n'est pas correcte")
    self.assertEqual(rdm.struct.CalculDegreH(),0,"Le degré hyper est faux")




class barreSimple2TestCase(unittest.TestCase) :
  def _genere_instance(self):
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id=\"node\">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="2,0" id="N2" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre s="1e-3" igz="1e-8" id="*"/>
	</elem>
	<elem id="material">
		<barre young="200000000.0" id="*"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" fp="1.,0,1,0"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    assert rdm.struct.Nodes == {"N1": (0, 0), "N2": (2,0)}
    assert rdm.struct.Barres == {"B1" : ["N1","N2",0,0]}
    self.assertEqual(rdm.struct.status,1,"Erreur dans la lecture des données") 
    Char = rdm.Chars['cas 1']
    self.assertEqual(rdm.DepPoint(Char, "B1",1.)[1], 
      rdm.struct.Lengths["B1"]**3/48/rdm.struct.MQua["*"]/rdm.struct.Youngs["*"],
      "La flèche n'est pas correcte")
    self.assertEqual(rdm.struct.CalculDegreH(),0,"Le degrè hyper est faux")

class emptyKMatrixTestCase(unittest.TestCase) :
  def _genere_instance(self):
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id=\"node\">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="2,0" id="N2" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre s="1.5e-3" igz="1.5e-8" id="*"/>
	</elem>
	<elem id="material">
		<barre young="200000000000.0" id="*"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" fp="%0.5,0,-2,0"/>
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
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.Reactions["N1"]['Fy'],1,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(rdm.DepPoint(Char, "B1",1)[1],-2.777777e-5,7, 
      "Le déplacement n'est pas correct")

class emptyKMatrix2TestCase(unittest.TestCase) :
  def _genere_instance(self):
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id=\"node\">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="2,0" id="N2" liaison="0"/>
	</elem>
	<elem id="barre">
                <mbarre end="N2" id="B1" r0="0" r1="0" start="N1" />
	</elem>
	<elem id="geo">
		<barre s="1.5e-3" igz="1.5e-8" id="*"/>
	</elem>
	<elem id="material">
		<barre young="200000000000.0" id="*"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" fp="%0.5,0,-2,0"/>
		</case>
	</elem>
	<elem id="combinaison">
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.Reactions["N1"]['Fy'],1,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(rdm.DepPoint(Char, 0,1)[1],-2.777777e-5,7, 
      "Le déplacement n'est pas correct")



class appui_appui_inclineTestCase(unittest.TestCase):
  def _genere_instance(self):
    string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="A" liaison="1"/>
		<node d="-1,-1" id="B"/>
		<node d="0,-1" id="C" liaison="2,90"/>
	</elem>
	<elem id="barre">
		<barre start="A" end="B" id="B1"/>
		<barre start="B" end="C" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.2" id="*" igz="1.0" profil="IPN 200" s="1.0" v="0.1"/>
	</elem>
	<elem id="material">
		<barre alpha="" id="*" mv="" young="1000000.0"/>
	</elem>
	<elem id="char">
		<case id="Cas 1">
			<node d="0.0,-1.0,0.0" id="B"/>
		</case>
	</elem>
	<elem id="combinaison"/>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1000.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['Cas 1']
    self.assertAlmostEqual(Char.ddlValue["C"][1],-0.00141421356237,7, 
      "Le déplacement du noeud C n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["A"]["Fx"],1000,7, 
      "La réaction d'appui du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["C"]["Fx"],-1000,7, 
      "La réaction d'appui du noeud N2 n'est pas correct")

class appui_elast_inclineTestCase(unittest.TestCase):
  def _genere_instance(self):
    string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="A" liaison="1"/>
		<node d="-1,-1" id="B"/>
		<node d="0,-1" id="C" liaison="3,inf,0.0,0.0"/>
	</elem>
	<elem id="barre">
		<barre start="A" end="B" id="B1"/>
		<barre start="B" end="C" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.2" id="*" igz="1.0" profil="IPN 200" s="1.0" v="0.1"/>
	</elem>
	<elem id="material">
		<barre alpha="" id="*" mv="" young="1000000.0"/>
	</elem>
	<elem id="char">
		<case id="Cas 1">
			<node d="0.0,-1000.0,0.0" id="B"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['Cas 1']
    self.assertAlmostEqual(Char.ddlValue["C"][1],-0.00141421356237,7, 
      "Le déplacement du noeud C n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["A"]["Fx"],1000,7, 
      "La réaction d'appui du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["C"]["Fx"],-1000,7, 
      "La réaction d'appui du noeud N2 n'est pas correct")


class appui_incline45_inclineTestCase(unittest.TestCase):
  def _genere_instance(self):
    string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="A" liaison="1"/>
		<node d="-1,-1" id="B"/>
		<node d="0,-1" id="C" liaison="2,45"/>
	</elem>
	<elem id="barre">
		<barre start="A" end="B" id="B1"/>
		<barre start="B" end="C" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.2" id="*" igz="1.0" profil="IPN 200" s="1.0" v="0.1"/>
	</elem>
	<elem id="material">
		<barre alpha="" id="*" mv="" young="1000000.0"/>
	</elem>
	<elem id="char">
		<case id="Cas 1">
			<node d="0.0,-1000.0,0.0" id="B"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['Cas 1']
    self.assertAlmostEqual(Char.ddlValue["C"][1],Char.ddlValue["C"][0],7, 
      "Le déplacement du noeud C n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["C"]["Fx"],-1000,7, 
      "La réaction d'appui du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["C"]["Fy"],1000,7, 
      "La réaction d'appui du noeud N2 n'est pas correct")






class barre4appui_appui_inclineTestCase(unittest.TestCase):
  def _genere_instance(self):
    string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="1,0" id="N2" liaison="2"/>
		<node d="2,0" id="N3" liaison="2"/>
		<node d="3,0" id="N4" liaison="2,45"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8.3e-05" s="0.0053" v="0.15"/>
		<barre h="0.3" id="B2" igz="8e-05" s="0.0053" v="0.15"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre fp="%0.5,0.0,-1000.0,0.0" id="B3"/>
		</case>
		<case id="cas 2">
			<barre id="B1" tri="@,%0.2,%1,0.0,1000.0,90.0"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0,1.5" id="combi 3"/>
		<combinaison d="1.35,1.0" id="combi 2"/>
		<combinaison d="1.0,1.0" id="combi 1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1." id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['cas 1']
    self.assertEqual(rdm.struct.status,1,"Erreur dans la lecture des données") 
    self.assertAlmostEqual(Char.ddlValue["N2"][0],-3.516873286e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][2],5.5599403e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N4"][0],-1.0550619e-06,7, 
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N4"][1],-1.0550619e-06,7, 
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N4"][2],1.432775014e-06,7, 
      "Le déplacement du noeud N4 n'est pas correct")

class barre2appui_appui_incline2TestCase(unittest.TestCase):
  def _genere_instance(self):
    string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
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
			<depi id="N1" d="0.01,0.01"/>
		</case>
		<case id="cas 2">
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['cas 1']
    self.assertEqual(rdm.struct.status,1,"Erreur dans la lecture des données") 
    self.assertAlmostEqual(Char.ddlValue["N1"][0],0.01,7, 
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N1"][1],0.01,7, 
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N1"][2],0.0,7, 
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][0],0.01,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],0.01,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][2],0.0,7, 
      "Le déplacement du noeud N2 n'est pas correct")


class barre2appui_appui_inclineTestCase(unittest.TestCase):
  def _genere_instance(self):
    string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N0" liaison="1"/>
		<node  d="2&lt;45" id="N2" liaison="2,45"/>
	</elem>
	<elem id="barre">
		<barre start="N0" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="8.014e-07" profil="IPE 80" s="0.000764" v="0.04"/>
	</elem>
	<elem id="material">
		<barre id="*" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N2" d="0,0.1"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['cas 1']
    self.assertEqual(rdm.struct.status,1,"Erreur dans la lecture des données") 
    self.assertAlmostEqual(Char.ddlValue["N2"][0],-0.0707106781187,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],0.0707106781187,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][2],0.05,7, 
      "Les rotations ne sont pas correctes")

class barre4appui_2rotule_dep_TestCase(unittest.TestCase):
  def _genere_instance(self):
    string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="1,0" id="N2"  liaison="2"/>
		<node d="2,0" id="N3"  liaison="2"/>
		<node d="3,0" id="N4" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1" k1="0"/>
		<barre start="N2" end="N3" id="B2" k1="0"/>
		<barre start="N3" end="N4" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8.3e-05" s="0.0053" v="0.15"/>

	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N2" d="0,0.01"/>
			<depi id="N3" d="0,0.01"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N2"][1],0.01,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][2],-0.00376506,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][3],0.015,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    barre = 'B2'
    l = rdm.struct.Lengths[barre]
    angle = rdm.struct.Angles[barre]
    liTherm = Char.charBarTherm.get(barre, [])
    charTri = Char.charBarTri.get(barre, {})
    charQu = Char.charBarQu.get(barre, {})
    charFp = Char.charBarFp.get(barre, {})
    chars = charFp, charQu, charTri, liTherm

    defo = rdm.DefoPoint(Char, barre, l, angle, 0.5, Char.ddlValue, rdm.struct.IsRelax, chars)
    self.assertAlmostEqual(defo,-0.00125502,7, 
      "Le déplacement du noeud N2 n'est pas correct")



class barre2appui_dep_TestCase(unittest.TestCase):
  def _genere_instance(self):
    string ="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="5,0" id="N2" liaison="2"/>
		<node d="10,0" id="N3" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8.3e-05" s="0.0053" v="0.15"/>
	</elem>
	<elem id="material">
		<barre id="B1" mv="7800.0" young="200000000000.0"/>
		<barre alpha="1e-5" id="B2" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N2" d="0,0.001"/>
			<barre fp="%0.5,0.0,-10000.0,0.0" id="B1"/>
			<barre fp="%0.5,0.0,-10000.0,0.0" id="B2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self._genere_instance()
    Char = rdm.Chars['cas 1']
    assert rdm.struct.Nodes == {"N1": (0, 0), "N2": (5, 0), "N3": (10, 0)}
    assert rdm.struct.Barres == {"B1" : ["N1","N2",0,0], "B2" : ["N2","N3",0,0]}
    self.assertEqual(rdm.struct.status,1,"Erreur dans la lecture des données") 
    self.assertAlmostEqual(Char.ddlValue["N2"][1],0.001,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N1"][2],-Char.ddlValue["N3"][2],7, 
      "Les rotations ne sont pas correctes")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],2726.6,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N2"]["Fy"],14546.8,7, 
      "La réaction d'appui du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N3"]["Fy"],2726.6,7, 
      "La réaction d'appui du noeud N3 n'est pas correct")
    self.assertEqual(rdm.struct.CalculDegreH(),1,"Le degrè hyper est faux")

class barresimplethermTestCase(unittest.TestCase):
  """Barre iso soumise à dilatation libre"""

  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.3">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="10,0" id="N2" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="1.06e-06" profil="UPN 80" s="0.001102" v="0.04"/>
	</elem>
	<elem id="material">
		<barre alpha="1e-5" id="*" mv="" young="200000000000"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" therm="50.0,-50.0"/>
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
		<const g="9.81"/>
		<conv conv="-1.0"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm=self._genere_instance()
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(rdm.DepPoint(Char, "B1",5)[1],0.15625,7, 
      "Le déplacement n'est pas correct")

class appui_elastTestCase(unittest.TestCase):
  """Barre iso soumise à dilatation libre"""

  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.3">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="1,0" id="N2" liaison="3,0,10,0"/>
		<node d="2,0" id="N3" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="" id="*" igz="1e-08" profil="" s="1.5e-07" v=""/>
	</elem>
	<elem id="material">
		<barre id="*" young="1000000000"/>
	</elem>
	<elem id="char">
		<case id="cas1">
			<node d="0,-1.,0" id="N2"/>
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
		<const g="9.81"/>
		<conv conv="1.0"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm=self._genere_instance()
    Char = rdm.Chars['cas1']
    self.assertAlmostEqual(rdm.DepPoint(Char, "B1",1)[1],-0.0142857142857,7, 
      "Le déplacement n'est pas correct")



class barresimpletherm2TestCase(unittest.TestCase):
  """Barre iso soumise à dilatation libre"""

  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.3">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="10,0" id="N2" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="1.06e-06" profil="UPN 80" s="0.001102" v="0.04"/>
	</elem>
	<elem id="material">
		<barre alpha="1e-5" id="*" mv="" young="200000000000"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" therm="50.0,-50.0"/>
		</case>
	</elem>
	<elem id="combinaison"/>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="0.01" id="L"/>
		<unit d="1.0" id="S"/>
		<const g="9.81"/>
		<conv conv="-1.0"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm=self._genere_instance()
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(rdm.DepPoint(Char, "B1",0.05)[1],0.0015625,7, 
      "Le déplacement n'est pas correct")


class barreBiEncastreeTestCase(unittest.TestCase):
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="0.4,0" id="N2"/>
		<node d="1,0" id="N3" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre s="1e-3" igz='1e-8' h='0.1' id="*"/>
	</elem>
	<elem id="material">
		<barre alpha="1e-5" young="200000000.0" id="*"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" therm="-5,5"/>
			<barre id="B2" therm="-5,5"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm=self._genere_instance()
    assert rdm.struct.Nodes == {"N1" : (0,0), "N2": (0.4, 0), "N3" : (1,0)}
    assert rdm.struct.Barres == {"B1" : ["N1","N2",0,0], "B2" : ["N2","N3",0,0]}
    self.assertEqual(rdm.struct.status,1,"Erreur dans la lecture des données") 
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(rdm.DepPoint(Char, "B1",0.3)[1],1e-10,7, 
      "Le déplacement n'est pas correct")
    self.assertEqual(rdm.struct.CalculDegreH(),3,"Le degrè hyper est faux")

class CompareRotuleElastTestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,2" id="N2"/>
		<node d="@N1,2,1" id="N3" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" r1="1" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1000.0,0.0" id="N2"/>
			<barre fp="1,0.0,-1000.0,0.0" id="B2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,2" id="N2"/>
		<node d="@N1,2,1" id="N3" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1" k1="0"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1000.0,0.0" id="N2"/>
		<barre fp="1,0.0,-1000.0,0.0" id="B2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)
    return rdm1, rdm2

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    rdm2 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    Char2 = rdm2.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N2"][0],-4.623268293626828e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][0],-4.623268293626828e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],-1.7790843764613703e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][1],-1.7790843764613703e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1._RotationIso["B2"][0],-3.9445797545870577e-06,7, 
      "La rotation iso n'est pas correcte")
    self.assertAlmostEqual(Char1._RotationIso["B2"][1],5.208333333333334e-06,7, 
      "La rotation iso n'est pas correcte")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B1"][2],-2.5632921532080148e-07,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B2"][1],3.4064531644764889e-07,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char2.ddlValue["N2"][2],3.4064531644764889e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][3],-2.5632921532080148e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fx'],358.13674296091648,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],719.94177104232233,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Mz'],3.6682851204895535,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N3"]['Fx'],-358.13674296091625,7, 
      "La réaction d'appui du noeud N3 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N3"]['Fy'],1280.0582289576773,7, 
      "La réaction d'appui du noeud N3 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N3"]['Mz'],-214.81470481021381,7, 
      "La réaction d'appui du noeud N3 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Fx'],358.13674296091648,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Fy'],719.94177104232233,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Mz'],3.6682851204895535,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N3"]['Fx'],-358.13674296091625,7, 
      "La réaction d'appui du noeud N3 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N3"]['Fy'],1280.0582289576773,7, 
      "La réaction d'appui du noeud N3 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N3"]['Mz'],-214.81470481021381,7, 
      "La réaction d'appui du noeud N3 n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B1"][0][0],804.09911645708462,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B1"][0][0],804.09911645708462,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B1"][0][1],1.6405069780531292,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B1"][0][1],1.6405069780531292,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B1"][0][2],3.6682851204895535,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B1"][0][2],3.6682851204895535,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B1"][1][0],-804.09911645708462,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B1"][1][1],-1.6405069780531292,7, 
      "La sollicitation n'est pas correcte")
    self.assertEqual(Char1.EndBarSol["B1"][1][2],0,"La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B2"][0][0],451.27199236279603,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B2"][0][1],55.20984671665893,7, 
      "La sollicitation n'est pas correcte")
    self.assertEqual(Char1.EndBarSol["B2"][0][2],0,"La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B2"][1][0],-1158.3787735493434,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B2"][1][1],651.89693446988861,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char1.EndBarSol["B2"][1][2],-214.81470481021381,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B1"][1][0],-804.09911645708462,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B1"][1][1],-1.6405069780531292,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B1"][1][2],0,7,"La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B2"][0][0],451.27199236279603,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B2"][0][1],55.20984671665893,7, 
      "La sollicitation n'est pas correcte")
    self.assertEqual(Char2.EndBarSol["B2"][0][2],0,"La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B2"][1][0],-1158.3787735493434,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B2"][1][1],651.89693446988861,7, 
      "La sollicitation n'est pas correcte")
    self.assertAlmostEqual(Char2.EndBarSol["B2"][1][2],-214.81470481021381,7, 
      "La sollicitation n'est pas correcte")

class PortiqueDiagonaleTestCase(unittest.TestCase):

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="0,5.1" id="N2"/>
		<node d="4.7,5.1" id="N3"/>
		<node d="4.7,0" id="N4" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
		<barre start="N2" end="N4" r0="1" r1="1" id="B4"/>
	</elem>
	<elem id="geo">
		<barre h="0.19" id="*" igz="4e-05" profil="HE 200 A" s="0.005" v="0.095"/>
	</elem>
	<elem id="material">
		<barre alpha="1e-5" id="*" mv="7800.0" young="210000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="1.0,0.0,0.0" id="N2"/>
		</case>
		<case id="cas 2">
			<barre id="B2" qu="0,1,0.0,-120.0"/>
		</case>
		<case id="cas 3"/>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.35,1.5,0.0" id="combi1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1000." id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="0,5.1" id="N2"/>
		<node d="4.7,5.1" id="N3"/>
		<node d="4.7,0" id="N4" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
		<barre start="N2" end="N4" id="B4" k0="0" k1="0"/>
	</elem>
	<elem id="geo">
		<barre h="0.19" id="*" igz="4e-05" profil="HE 200 A" s="0.005" v="0.095"/>
	</elem>
	<elem id="material">
		<barre alpha="1e-5" id="*" mv="7800.0" young="210000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="1.0,0.0,0.0" id="N2"/>
		</case>
		<case id="cas 2">
			<barre id="B2" qu="0,1,0.0,-120.0"/>
		</case>
		<case id="cas 3"/>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.35,1.5,0.0" id="combi1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1000.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)
    return rdm1, rdm2

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    rdm2 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N2"][0],1.9767288572295751e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],5.2111926344368034e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][2],-2.9062520676407443e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B4"][1],-2.6051097110303806e-06,7, 
      "Le déplacement de la barre n'est pas correct")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B4"][2],-2.6051097110303806e-06,7, 
      "Le déplacement de la barre n'est pas correct")

    Char2 = rdm2.Chars['cas 1']
    self.assertAlmostEqual(Char2.ddlValue["N2"][0],1.9767288572295751e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][1],5.2111926344368034e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][2],-2.9062520676407443e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][3],-2.6051097110303806e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N4"][3],-2.6051097110303806e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N4"]["Fx"],Char2.Reactions["N4"]["Fx"],7, "La réaction d'appui n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N4"]["Fy"],Char2.Reactions["N4"]["Fy"],7, "La réaction d'appui n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N4"]["Mz"],Char2.Reactions["N4"]["Mz"],7, "La réaction d'appui n'est pas correcte")

class CompareRotuleElastCoupleTestCase(unittest.TestCase):

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="1,0" id="N2"/>
		<node d="2,0" id="N3" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" r1="1" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1000.0,1000.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="1,0" id="N2"/>
		<node d="2,0" id="N3" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1" k1="0"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1000.0,1000.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)
    return rdm1, rdm2

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    rdm2 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    Char2 = rdm2.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],-1.0416666666666671e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B1"][2],-1.5625e-05,7, 
      "Le déplacement de la barre n'est pas correct")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B2"][1],1.5625e-05,7, 
      "Le déplacement de la barre n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][1],-1.0416666666666671e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][2],1.5625000000000007e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][3],-1.5625000000000007e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")

class CompareRotuleElastEtAppuiInclineTestCase(unittest.TestCase):

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,0" id="N2" liaison="2,45" />
		<node d="@N2,1&lt;45" id="N3" liaison="1"/>


	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1" k1="0"/>
		<barre start="N2" end="N3" id="B2"/>

	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-5" s="5e-3" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200e9"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N2" d="0,-0.01"/>
			<node d="1000.0,0.0,0.0" id="N2"/>
			<barre fp="%0.4,1000.0,-1000.0,0.0" id="B2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1000.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,0"  id="N2" liaison="2,45"/>
		<node d="@N2,1&lt;45" id="N3" liaison="1"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" r1="1" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N2" d="0,-0.01"/>
			<node d="1000000.0,0.0,0.0" id="N2"/>
			<barre fp="%0.4,1000000.0,-1000000.0,0.0" id="B2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)
    return rdm1, rdm2

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    rdm2 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    Char2 = rdm2.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N2"][0],0.00519060306223,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],-0.0089515325615,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][2],0.00434314575051,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][3],-0.0134272988423,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N3"][2],0.0149497474683,7, 
      "Le déplacement du noeud N2 n'est pas correct")

    self.assertAlmostEqual(Char2.ddlValue["N2"][0],0.00519060306223,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][1],-0.0089515325615,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.RelaxBarRotation["B2"][1],0.00434314575051,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.RelaxBarRotation["B1"][2],-0.0134272988423,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N3"][2],0.0149497474683,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N2"]["Fx"], 1710138.31259, 3,
      "Bug réactions appuis du noeud N2 ")
    self.assertAlmostEqual(Char1.Reactions["N2"]["Fy"], -1710138.31259, 3,
      "Bug réactions appuis du noeud N2 ")
    self.assertAlmostEqual(Char2.Reactions["N2"]["Fx"], 1710138.31259, 3,
      "Bug réactions appuis du noeud N2 ")
    self.assertAlmostEqual(Char2.Reactions["N2"]["Fy"], -1710138.31259, 3,
      "Bug réactions appuis du noeud N2 ")

class Compare2RotuleElastTestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,0.5" id="N2"/>
		<node d="@N1,2,0"  id="N3"/>
		<node d="3,0.6" id="N4"/>
		<node d="4,0" id="N5" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" r1="1" id="B1"/>
		<barre start="N2" end="N3" r1="1" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
		<barre start="N4" end="N5" id="B4"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N3" d="0.01,0.02"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 4"/>
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
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,0.5" id="N2"/>
		<node d="@N1,2,0"  id="N3"/>
		<node d="3,0.6" id="N4"/>
		<node d="4,0" id="N5" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1" k1="0"/>
		<barre start="N2" end="N3" id="B2" k1="0"/>
		<barre start="N3" end="N4" id="B3"/>
		<barre start="N4" end="N5" id="B4"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N3" d="0.01,0.02"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 4"/>
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
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)
    return rdm1, rdm2

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    Char1 = rdm1.Chars['cas 1']
    self.assertEqual(Char1.ddlValue["N2"][0],0, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertEqual(Char1.ddlValue["N2"][1],0, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertEqual(Char1.ddlValue["N2"][2],0, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N4"][0], 0.010686363038196251, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N4"][1], 0.015337861476687569, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N4"][2], -0.015306716894571686, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    #self.assertEqual(Char1.Reactions["N1"], {},
    #  "Bug réactions appuis du noeud N1 ")
    self.assertAlmostEqual(Char1.Reactions["N3"]["Fx"], 1541157.5557468545, 7,
      "Bug réactions appuis du noeud N3 ")
    self.assertAlmostEqual(Char1.Reactions["N3"]["Fy"], 448235.79331448837, 7,
      "Bug réactions appuis du noeud N3 ")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B2"][1],0.02,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B2"][2],0.02,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B3"][1],0.0020570830654143175,7, 
      "La rotation n'est pas correcte")

    rdm1 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N2"][0],0, 7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],0,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][2],0.02,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertEqual(Char1.ddlValue["N2"][3],0.0, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N3"][0], 0.01, 7,
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N3"][1], 0.02, 7,
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N3"][2], 0.0020570830654143219, 7,
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N3"][3], 0.02, 7,
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N4"][0], 0.010686363038196251, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N4"][1], 0.015337861476687569, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N4"][2], -0.015306716894571686, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    #self.assertEqual(Char1.Reactions["N1"], {},
    #  "Bug réactions appuis du noeud N1 ")
    self.assertAlmostEqual(Char1.Reactions["N3"]["Fx"], 1541157.5557468545, 7,
      "Bug réactions appuis du noeud N3 ")
    self.assertAlmostEqual(Char1.Reactions["N3"]["Fy"], 448235.79331448837, 7,
      "Bug réactions appuis du noeud N3 ")

class CompareAppuiInclineTestCase(unittest.TestCase):

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,0" id="N2" liaison="2,45"/>
		<node d="@N2,1&lt;45" id="N3" liaison="1"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1" k1="0"/>
		<barre start="N2" end="N3" id="B2"/>

	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-5" s="5e-3" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="2e11"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="1000.0,0.0,0.0" id="N2"/>

		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,0" id="N2" liaison="2,45"/>
		<node d="@N2,1&lt;45" id="N3" liaison="1"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" r1="1" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>

	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-5" s="5e-3" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="2e11"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="1000.0,0.0,0.0" id="N2"/>

		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)
    return rdm1, rdm2

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    rdm2 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    Char2 = rdm2.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N2"][0],3.2808398950131235e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],3.2808398950131235e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][2],0,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][3],4.9212598425196852e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fx'],-328.08398950131237,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],-15.74803149606298,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Mz'],-15.748031496062987,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N2"]['Fx'],-343.83202099737537,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N2"]['Fy'],343.83202099737537,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N3"]['Fx'],-328.08398950131232,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N3"]['Fy'],-328.08398950131232,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")

    self.assertAlmostEqual(Char2.ddlValue["N2"][0],3.2808398950131235e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],3.2808398950131235e-07,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][2],0,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.RelaxBarRotation["B1"][2],4.9212598425196852e-07,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Fx'],-328.08398950131237,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Fy'],-15.74803149606298,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Mz'],-15.748031496062987,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N2"]['Fx'],-343.83202099737537,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N2"]['Fy'],343.83202099737537,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N3"]['Fx'],-328.08398950131232,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N3"]['Fy'],-328.08398950131232,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")


class Compare2RotuleElast2TestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,2" id="N2"/>
		<node d="@N1,2,1" id="N3" />
		<node d="@N1,3,2" id="N4" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" r1="1" id="B1"/>
		<barre start="N2" end="N3" r1="1" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1000.0,0.0" id="N2"/>
			<barre fp="1,0.0,-1000.0,0.0" id="B2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)
    string = """<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,2" id="N2"/>
		<node d="@N1,2,1" id="N3" />
		<node d="@N1,3,2" id="N4" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1" k1="0"/>
		<barre start="N2" end="N3" id="B2" k1="0"/>
		<barre start="N3" end="N4" id="B3"/>

	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1000.0,0.0" id="N2"/>
			<barre fp="1,0.0,-1000.0,0.0" id="B2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)
    return rdm1, rdm2

  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    rdm2 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    Char2 = rdm2.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N2"][0],4.6913311600475541e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],-2.6057634883936417e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N3"][0],3.5618626213091781e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N3"][1],-3.6618626213091778e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B1"][2],-3.5965277425466252e-05,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B2"][1],-1.4872418112856619e-05,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B2"][2],-5.7195050249362268e-06,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char1.RelaxBarRotation["B3"][1],5.4177939319637663e-05,7, 
      "La rotation n'est pas correcte")

    self.assertAlmostEqual(Char2.ddlValue["N2"][0],4.6913311600475541e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][1],-2.6057634883936417e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N3"][0],3.5618626213091781e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N3"][1],-3.6618626213091778e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char2.ddlValue["N2"][3],-3.5965277425466252e-05,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char2.ddlValue["N2"][2],-1.4872418112856619e-05,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char2.ddlValue["N3"][3],-5.7195050249362268e-06,7, 
      "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char2.ddlValue["N3"][2],5.4177939319637663e-05,7, 
      "La rotation n'est pas correcte")

    self.assertAlmostEqual(Char1.Reactions["N1"]['Fx'],259.40002194479058,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],1033.4931968686599,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Mz'],514.69315297907895,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N4"]['Fx'],-259.40002194479058,7, 
      "La réaction d'appui du noeud N4 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N4"]['Fy'],966.50680313133455,7, 
      "La réaction d'appui du noeud N4 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N4"]['Mz'],-1225.9068250761297,7, 
      "La réaction d'appui du noeud N4 n'est pas correcte")

    self.assertAlmostEqual(Char2.Reactions["N1"]['Fx'],259.40002194479058,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Fy'],1033.4931968686599,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Mz'],514.69315297907895,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N4"]['Fx'],-259.40002194479058,7, 
      "La réaction d'appui du noeud N4 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N4"]['Fy'],966.50680313133455,7, 
      "La réaction d'appui du noeud N4 n'est pas correcte")
    self.assertAlmostEqual(Char2.Reactions["N4"]['Mz'],-1225.9068250761297,7, 
      "La réaction d'appui du noeud N4 n'est pas correcte")
    barre = 'B2'
    l = rdm1.struct.Lengths[barre]
    # fléche : valeur non vérifiée
    self.assertAlmostEqual(rdm1.TestDefoPoint(Char1, barre, l/2),-2.02649633607e-06,7, 
      "La fléche n'est pas correcte")
    self.assertAlmostEqual(rdm2.TestDefoPoint(Char2, barre, l/2),-2.02649633607e-06,7, 
      "La fléche n'est pas correcte")

class BarreBiArticuleeChargeeTestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,-0.5" id="N2"/>
		<node d="@N1,2,-1" id="N3"/>
		<node d="@N1,3,-1.5" id="N4" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" r0="1" r1="1" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="210000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre fp="1,0.0,0.0,1.0" id="B2"/>
		</case>
		<case id="cas 2">
			<barre fp="0.5,1.0,1.0,0.0" id="B2"/>
		</case>
		<case id="cas 3">
			<barre id="B2" qu=",,0.0,1.0"/>
		</case>
		<case id="cas 4">
			<barre id="B2" qu="0,0.5,0.0,1.0"/>
		</case>
		<case id="cas 5">
			<barre id="B2" tri="@,0,0.5,0.0,1.0,90.0"/>
		</case>

	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1000.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N2"][0],-1.1091607031248958e-05,7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],-2.2183214062497916e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][0],1.1091607031248966e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],2.2183214062497929e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],400,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],800,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],1000,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fx"],-400,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fy"],-800,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Mz"],1000,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.RelaxBarRotation["B1"][2],-3.3274821093746868e-05,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B2"][1],3.3645689538681721e-05,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B3"][1],-3.3274821093746895e-05,7, "La rotation n'est pas correcte")


    Char = rdm.Chars['cas 2']
    self.assertAlmostEqual(Char.ddlValue["N2"][0],9.4173874329051563e-06,7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],1.8283642174540531e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][0],7.6459408239682471e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],1.4778220064206365e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-538.7100299667004,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],-559.82459176671284,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],-829.17960675006304,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fx"],-461.28997003330358,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fy"],-440.17540823328477,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Mz"],670.82039324993707,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.RelaxBarRotation["B1"][2],2.7590803069191731e-05,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B2"][1],2.8736849590814603e-06,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B3"][1],-2.2321428571428585e-05,7, "La rotation n'est pas correcte")

    Char = rdm.Chars['cas 3']
    self.assertAlmostEqual(Char.ddlValue["N2"][0],5.9623015873015891e-06,7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],1.251984126984127e-05,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][0],5.962301587301595e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],1.2519841269841282e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],-559.01699437494665,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],-559.01699437494744,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fy"],-559.01699437494688,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Mz"],559.01699437494801,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.RelaxBarRotation["B1"][2],1.8601190476190478e-05,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B2"][1],3.1001984126984258e-06,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B3"][1],-1.8601190476190495e-05,7, "La rotation n'est pas correcte")

    Char = rdm.Chars['cas 4']
    self.assertAlmostEqual(Char.ddlValue["N2"][0],4.1796245964181425e-06,7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],8.6744980781537116e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][0],1.1532200642063573e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],2.5235883805952364e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-36.852426966669753,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],-369.77038764167537,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],-388.19660112501037,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fx"],36.852426966669029,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fy"],-130.22961235832406,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Mz"],111.80339887498958,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.RelaxBarRotation["B1"][2],1.2917172451635339e-05,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B2"][1],-4.6362836073897219e-06,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B3"][1],-3.7202380952380986e-06,7, "La rotation n'est pas correcte")

    Char = rdm.Chars['cas 5']
    self.assertAlmostEqual(Char.ddlValue["N2"][0],2.175897826761e-06,7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],4.3517956535219999e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][0],9.24300585937414e-07,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],1.8486011718748274e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-78.470065541656098,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],-156.9401310833122,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],-196.17516385414032,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fx"],-33.333333333333528,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fy"],-66.666666666666615,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Mz"],83.3333333333334,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.RelaxBarRotation["B1"][2],6.5276934802829991e-06,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B2"][1],-1.4737367632693798e-06,7, "La rotation n'est pas correcte")
    self.assertAlmostEqual(Char.RelaxBarRotation["B3"][1],-2.7729017578122412e-06,7, "La rotation n'est pas correcte")

class BarreBiEncastreeTestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="@N1,1,-0.5" id="N2"/>
		<node d="@N1,2,-1" id="N3"/>
		<node d="@N1,3,-1.5" id="N4" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="8e-05" s="0.005" v="0.1"/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="210000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B2" tri="@,0,0.5,0.0,1000.0,90.0"/>
		</case>
		<case id="cas 2">
			<barre id="B2" tri=",0,0.5,0.0,1000.0,90.0"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N2"][0],1.0005688506691629e-06,7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],2.0011377013383254e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][2],2.1428630382494379e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][0],8.566707280138293e-07,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],1.7133414560276586e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][2],-2.1858968637841169e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-67.056553993973964,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],-134.11310798794747,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],-116.02015995485027,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fx"],-44.746844881015669,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fy"],-89.493689762031337,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Mz"],88.779666041660818,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")

    Char = rdm.Chars['cas 2']
    self.assertAlmostEqual(Char.ddlValue["N2"][0],8.3453171208805073e-07,7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],1.8200741102210585e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][2],1.9166349679989897e-06,7, 
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][0],7.2015443978725519e-07,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],1.5554967622795279e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][2],-1.9551255916899536e-06,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-3.2486184602965125,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],-148.31870383726215,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],-103.77158576777767,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fx"],3.2486184602963988,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Fy"],-101.68129616273774,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N4"]["Mz"],79.40694731555331,7, 
      "La réaction d'appui du noeud N4 n'est pas correct")



class portiqueDoubleTraverseTestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.11">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="0,4" id="N2"/>
		<node d="0,5" id="N3"/>
		<node d="4.5,5" id="N4"/>
		<node d="4.5,4" id="N5"/>
		<node d="4.5,0" id="N6" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
		<barre start="N4" end="N5" id="B4"/>
		<barre start="N5" end="N6" id="B5"/>
		<barre start="N5" end="N2" r0="1" id="B6"/>
	</elem>
	<elem id="geo">
		<barre h="" id="*" igz="8.356e-05" s="0.00538" v=""/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<pp d="true"/>
		</case>
		<case id="cas 2">
			<node d="10.0,10.0,0.0" id="N3"/>
			<barre fp="0.5,10.0,0.0,0.0" id="B4"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.35,1.0" id="combi2"/>
		<combinaison d="1.0,1.0" id="combi1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
		<const name="g" value="9.81"/>
		<const name="conv" value="1"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N3"][0],7.2336004030424886e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],-1.260651580118973e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][2],-2.3860473972472603e-05,7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],27.107608766937116,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],3959.0572003808693,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],68.594668178431618,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertEqual(rdm.struct.CalculDegreH(),5,"Le degré hyper est faux")

class portiqueDoubleTraverseTestCase2(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.11">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="0,4" id="N2"/>
		<node d="0,5" id="N3"/>
		<node d="4.5,5" id="N4"/>
		<node d="4.5,4" id="N5"/>
		<node d="4.5,0" id="N6" liaison="0"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
		<barre start="N4" end="N5" id="B4"/>
		<barre start="N5" end="N6" id="B5"/>
		<barre start="N5" end="N2" r0="1" id="B6"/>
	</elem>
	<elem id="geo">
		<barre h="" id="*" igz="8.356e-05" s="0.00538" v=""/>
	</elem>
	<elem id="material">
		<barre id="*" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
		</case>
		<case id="cas 2">
			<node d="10.0,10.0,0.0" id="N3"/>
			<barre fp="0.5,10.0,0.0,0.0" id="B4"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.35,1.0" id="combi2"/>
		<combinaison d="1.0,1.0" id="combi1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)

    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 2']
    #Char = rdm.Combis['combi1']
    self.assertAlmostEqual(Char.ddlValue["N3"][0],
				7.0413194272207428e-06,7,
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][1],
				8.8418458635477441e-08, 7, 
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][2],
		-7.4193241267399575e-07, 7,
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-10.77615484481451,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"], -19.643120640104279,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],26.846404299033093,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")

class appui_elast_relaxation_TestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="0.5,0" id="N2" liaison="3,0.0,1000.0,0.0"/>
		<node d="1,0" id="N3" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" r1="1" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="1.0" profil="IPE 80" s="10.0" v="0.04"/>
	</elem>
	<elem id="material">
		<barre id="*" young="1.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1.0,0.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)

    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N1"][2],
		-0.002, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][2],
		0.002, 7,
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],
		-0.001, 7,
      "Le déplacement du noeud N2 n'est pas correct")


class rotule_elast1_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="0.5,0" id="N2"/>
		<node d="1,0" id="N3" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2" k0="10000000000"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="1." profil="IPE 80" s="10." v="0.04"/>
	</elem>
	<elem id="material">
		<barre id="*" young="1.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1.0,0.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)

    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N2"][1],
		-0.020833333333, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N1"][2],
		-0.0625000000, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][2],
		0.0625000000, 7,
      "Le déplacement du noeud N3 n'est pas correct")


class rotule_elast3_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="50,0" id="N2" />
		<node d="100,0" id="N3" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2" k0="0"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="1." profil="IPE 80" s="10." v="0.04"/>
	</elem>
	<elem id="material">
		<barre id="*" young="1.0e9"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<node d="0.0,-1.0,0.0" id="N2"/>
			<depi id="N2" d="0,-1"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1.0" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="0.01" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)

    return rdm



  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N2"][1],
		-0.01, 7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N1"][2],
		-0.02, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][2],
		-0.02, 7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][3],
		0.02, 7,
      "Le déplacement du noeud N2 n'est pas correct")

class rotule_elast4_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="0.5,0" id="N2"/>
		<node d="1,0" id="N3" liaison="0"/>
		<node d="0.5,1" id="N4"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2" k0="0"/>
		<barre start="N4" end="N2" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="1." profil="IPE 80" s="10." v="0.04"/>
	</elem>
	<elem id="material">
		<barre id="*" young="1.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N2" d="0.01,-0.01"/>
			<node d="0.0,-1.0,0.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)

    return rdm



  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N4"][0],
		0.04, 7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N4"][2],
		-0.03, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-0.2,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],0.24,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],0.12,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N2"]["Fy"],0.52,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")

class rotule_elast5_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="0"/>
		<node d="0.5,0" id="N2" />
		<node d="1,0" id="N3" liaison="0"/>
		<node d="0.5,1" id="N4"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" r0="1" id="B2"/>
		<barre start="N4" end="N2" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="1." profil="IPE 80" s="10." v="0.04"/>
	</elem>
	<elem id="material">
		<barre id="*" young="1.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N2" d="0.01,-0.01"/>
			<node d="0.0,-1.0,0.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)

    return rdm



  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N4"][0],
		0.04, 7,
      "Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N4"][2],
		-0.03, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-0.2,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],0.24,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],0.12,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N2"]["Fy"],0.52,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")




class dep_imp_relaxation_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="0.5,0"  id="N2"/>
		<node d="1,0" id="N3" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" r1="1" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.08" id="*" igz="1.0" profil="IPE 80" s="10.0" v="0.04"/>
	</elem>
	<elem id="material">
		<barre id="*" young="1.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<depi id="N2" d="0,0.01"/>
			<node d="0.0,-1.0,0.0" id="N2"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)

    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N1"][2],
		0.02, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N3"][2],
		-0.02, 7,
      "Le déplacement du noeud N3 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N2"][1],
		0.01, 7,
      "Le déplacement du noeud N2 n'est pas correct")



class appui_elastiqueTestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.2">
	<elem id='node'>
		<node d='0,0' id='N1' liaison='3,1000,1000,1000'/>
		<node d='0.5,1.5' id='N2'/>
		<node d='2.2,1.7' id='N3'/>
		<node d='1,0' id='aa' liaison='3,1000,1000,1000'/>			</elem>
	<elem id='barre'>
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B3"/>
		<barre start="N3" end="aa" id="B5"/>
	</elem>
	<elem id='geo'>
		<barre s='1.0' igz='1.0' id='*'/>
	</elem>
	<elem id='material'>
		<barre id='*' mv='7800.0' young='200000.0'/>
	</elem>
	<elem id='char'>
		<case id='cas 1'>
			<node d='1.0,0.0,0.0' id='N2'/>
		</case>
	</elem>
	<elem id='combinaison'>
		<combinaison d='1.0' id='combi2'/>
		<combinaison d='1.0' id='combi1'/>
	</elem>
	<elem id='prefs'>
		<unit d='1e-8' id='I'/>
		<unit d='1.0' id='M'/>
		<unit d='1.0' id='L'/>
		<unit d='1e-4' id='S'/>
		<unit d='1e6' id='E'/>
		<unit d='1.0' id='F'/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)

    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N1"][0],
		0.000600647075988, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N1"][1],
		0.00028908270662, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["N1"][2],
		-0.000563080097492, 7,
      "Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["aa"][0],
		0.00039935292401281907, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["aa"][1],
		-0.00028908270661923911, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.ddlValue["aa"][2],
		-0.00064783719588687428, 7,
      "Le déplacement du noeud N4 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fx"],-0.600647075988,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Fy"],-0.289082706619,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char.Reactions["N1"]["Mz"],0.563080097492,7, 
      "La réaction d'appui du noeud N1 n'est pas correct")


class charge_repartieTestCase(unittest.TestCase):
  # test vérifié sous rdm6, comparaison 2 barres identiques mais avec 2 ou 4 points

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.11">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="2.7,0" id="N2"/>
		<node d="5.2,0" id="N3"/>
		<node d="10,0" id="N4" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
		<barre start="N3" end="N4" id="B3"/>
	</elem>
	<elem id="geo">
		<barre h="" id="*" igz="8.5e-05" s="0.00538" v=""/>
	</elem>
	<elem id="material">
		<barre id="*" mv="2000.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B2" qu="%0,%1,0.0,-1000.0"/>
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
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)


    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.11">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="10,0" id="N2" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre h="" id="*" igz="8.5e-05" s="0.00538" v=""/>
	</elem>
	<elem id="material">
		<barre id="*" mv="2000.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" qu="2.7,5.2,0.0,-1000.0"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0" id="combi1"/>
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
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)
    return rdm1, rdm2


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    rdm2 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    Char2 = rdm2.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N1"][2],
		-0.000916916053922, 7,
	"Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N1"][2],Char2.ddlValue["N1"][2],7,
	"Différence entre les deux études")
    self.assertAlmostEqual(Char1.ddlValue["N2"][1],
		-0.00218380533088, 7,
	"Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(rdm2.DepPoint(Char2, "B1",2.7)[1], 
		-0.00218380533088, 7,
	"Le déplacement sur la barre n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N2"][2],-0.000592618259804 , 7,
	"Rotation différente")


class charge_tri_TestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm1, self.rdm2 = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
    #rdm1 = fakeRdm(xml)
    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.0">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="@N1,1.6666666,0" id="N3"/>
		<node d="5,0" id="N2" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N3" id="B1"/>
		<barre start="N3" end="N2" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="1e-08" s="0.0001" v="0.15"/>
		<barre h="" id="B2" igz="1e-08" s="0.0001" v=""/>
	</elem>
	<elem id="material">
		<barre id="B1" mv="7800.0" young="200000000000.0"/>
		<barre alpha="1e-5" id="B2" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" tri="@,%,%,0.0,1.0,90.0"/>
		</case>
	</elem>
	<elem id="combinaison">
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="L"/>
		<unit d="1.0" id="S"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm1 = fakeRdm(xml)
    #rdm2 = fakeRdm(xml)

    string="""<?xml version="1.0" ?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.0">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="5,0" id="N2" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="1e-08" s="0.0001" v="0.15"/>
	</elem>
	<elem id="material">
		<barre id="B1" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B1" tri="@,%0,%0.3333333,0.0,1.0,90.0"/>
		</case>
	</elem>
	<elem id="combinaison">
	</elem>
	<elem id="prefs">
		<unit d="1.0" id="C"/>
		<unit d="1.0" id="E"/>
		<unit d="1" id="F"/>
		<unit d="1.0" id="I"/>
		<unit d="1.0" id="M"/>
		<unit d="1.0" id="S"/>
		<unit d="1.0" id="L"/>
	</elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm2 = fakeRdm(xml)

    return rdm1, rdm2


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm1 = self.rdm1
    rdm2 = self.rdm2
    Char1 = rdm1.Chars['cas 1']
    Char2 = rdm2.Chars['cas 1']
    self.assertAlmostEqual(Char1.ddlValue["N1"][2],
		0.000507942129722, 7,
	"Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N1"][2],Char2.ddlValue["N1"][2],7,
	"Différence entre les deux études")
    self.assertAlmostEqual(Char1.ddlValue["N2"][2],
		-0.000360055555926, 7,
	"Le déplacement du noeud N2 n'est pas correct")
    self.assertAlmostEqual(rdm2.DepPoint(Char2, "B1",1.6666)[1], 
		Char1.ddlValue["N3"][1], 7,
	"Le déplacement sur la barre n'est pas correct")
    self.assertAlmostEqual(Char1.ddlValue["N3"][2],0.000154327159506 , 7,
	"Rotation différente")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],-0.64814812963 , 7,
	"Réaction différente")
    self.assertAlmostEqual(Char2.Reactions["N1"]['Fy'],-0.64814812963 , 7,
	"Réaction différente")


class charge_trapeze_TestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
    string="""<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.0">
	<elem id="node">
		<node d="0,0" id="N1" liaison="1"/>
		<node d="@N1,1.6666666,0" id="N2"/>
		<node d="5,0" id="N3" liaison="2"/>
	</elem>
	<elem id="barre">
		<barre start="N1" end="N2" id="B1"/>
		<barre start="N2" end="N3" id="B2"/>
	</elem>
	<elem id="geo">
		<barre h="0.3" id="*" igz="1e-08" s="0.0001" v="0.15"/>
		<barre h="" id="B2" igz="1e-08" s="0.0001" v=""/>
	</elem>
	<elem id="material">
		<barre id="B1" mv="7800.0" young="200000000000.0"/>
		<barre alpha="1e-5" id="B2" mv="7800.0" young="200000000000.0"/>
	</elem>
	<elem id="char">
		<case id="cas 1">
			<barre id="B2" qu="%0,%0.9,0.0,0.875"/>
		</case>
		<case id="cas 3">
			<barre id="B2" qu="%0,%0.1,0.0,-0.875"/>
		</case>
		<case id="cas 4">
			<barre id="B2" tri="@,%0,%0.9,0.0,1.125,90.0"/>
		</case>
		<case id="cas 5">
			<barre id="B2" tri="@,%0,%0.1,0.0,-0.125,90.0"/>
		</case>
		<case id="cas 6">
			<barre id="B2" tri="@,%0.1,%0.9,1.0,2.0,90.0"/>
		</case>
	</elem>
	<elem id="combinaison">
		<combinaison d="1.0,1.0,1.0,1.0,0.0" id="Combinaison 1"/>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    #rdm2 = self.rdm2
    Char1 = rdm.Chars['cas 6']
    Char2 = rdm.Combis['Combinaison 1']
    #Char2.Reactions = Char2.GetCombiReac()
    self.assertAlmostEqual(Char1.ddlValue["N1"][2],
		Char2.ddlValue["N1"][2], 7,
	"Le déplacement du noeud N1 n'est pas correct")
    self.assertAlmostEqual(rdm.DepPoint(Char1, "B2",2.5)[1], 
		rdm.DepPoint(Char2, "B2",2.5)[1], 7,
	"Le déplacement sur la barre n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],Char2.Reactions["N1"]['Fy'] , 7,
	"Réaction différente")


class BarreAssym_TestCase(unittest.TestCase):
  # test vérifié sous rdm6

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
    string="""<?xml version='1.0' encoding='UTF-8'?>
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char1 = rdm.Combis['combi1']
    self.assertEqual(Char1.EndBarSol['B8'][0][0], 0.,
	"Effort dans la barre non nul")
    self.assertEqual(Char1.EndBarSol['B10'][0][0], 0.,
	"Effort dans la barre non nul")
    self.assertEqual(Char1.EndBarSol['B12'][0][0], 0.,
	"Effort dans la barre non nul")
    self.assertAlmostEqual(Char1.ddlValue["N7"][0],
		2.33250625709e-06, 7,
      "Le déplacement du noeud N7 n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fx'],-481.573027779,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],-404.024101211,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")

class BarreAssym2_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
    string="""<?xml version='1.0' encoding='UTF-8'?>
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
    <barre end="N4" id="B8" r0="1" r1="1" start="N2" mode="-1" />
    <barre end="N3" id="B9" r0="1" r1="1" start="N1" mode="-1" />
    <barre end="N6" id="B10" r0="1" r1="1" start="N3" mode="-1" />
    <barre end="N5" id="B11" r0="1" r1="1" start="N4" mode="-1" />
    <barre end="N8" id="B12" r0="1" r1="1" start="N5" mode="-1" />
    <barre end="N7" id="B13" r0="1" r1="1" start="N6" mode="-1" />
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char1 = rdm.Combis['combi1']
    self.assertEqual(Char1.EndBarSol['B9'][0][0], 0.,
	"Effort dans la barre non nul")
    self.assertEqual(Char1.EndBarSol['B11'][0][0], 0.,
	"Effort dans la barre non nul")
    self.assertEqual(Char1.EndBarSol['B13'][0][0], 0.,
	"Effort dans la barre non nul")
    self.assertAlmostEqual(Char1.ddlValue["N7"][0],
		2.33224976587e-06, 7,
      "Le déplacement du noeud N7 n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fx'],0,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],-404.234149495,7, 
      "La réaction d'appui du noeud N1 n'est pas correcte")


class Para1_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
    string="""<data pyBar="http://open.btp.free.fr/?/pyBar" version="2.4">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="2,0" id="N2" liaison="1" />
    <arc d="0.5" id="N3" name="Parabole2" pos_on_curve="true" r="0" />
  </elem>
  <elem id="barre">
    <parabola end="N2" f="0.4" id="Parabole2" r0="0" r1="0" start="N1" />
    <barre end="N3" id="B2" r0="0" r1="0" start="N1" />
    <barre end="N2" id="B3" r0="0" r1="0" start="N3" />
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char1 = rdm.Chars['cas1']
    self.assertAlmostEqual(Char1.ddlValue["N3"][1],
		-8.33124858642e-10, 7,
      "Le déplacement du noeud N7 n'est pas correct")
    Char1 = rdm.Chars['cas2']
    self.assertAlmostEqual(Char1.ddlValue["N3"][1],
		-5.88538367739e-10, 7,
      "Le déplacement du noeud N7 n'est pas correct")
    Char1 = rdm.Combis['combi1']
    self.assertAlmostEqual(Char1.ddlValue["N3"][1],
		-2.01020159412e-09, 7,
      "Le déplacement du noeud N7 n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fx'],-348.326654202,5, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],2098.22175428,5, 
      "La réaction d'appui du noeud N1 n'est pas correcte")


class Poteau_rotule_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()    

  def _genere_instance(self):
    string="""<?xml version='1.0' encoding='UTF-8'?>
<data pyBar="http://open.btp.free.fr/?/pyBar" version="3.2">
  <elem id="node">
    <node d="0,0" id="N1" liaison="0" />
    <node d="0,2" id="N2" />
  </elem>
  <elem id="barre">
    <barre end="N2" id="B1" r0="0" r1="0" start="N1" k0="10000000"/>
  </elem>
  <elem id="geo">
    <barre id="*" igz="1e-5" s="1e-4" />
  </elem>
  <elem id="material">
    <barre id="*" young="200e9" />
  </elem>
  <elem id="char">
    <case id="cas 1">
      <pp d="false" />
      <node d="10,0.0,0.0" id="N2" />
    </case>
  </elem>
  <elem id="combinaison" />
  <elem id="prefs">
    <unit d="1.0" id="C" />
    <unit d="1000000000.0" id="E" />
    <unit d="1000.0" id="F" />
    <unit d="1.0" id="I" />
    <unit d="1.0" id="M" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="S" />
    <const g="9.81" />
    <conv conv="1.0" />
  </elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm

  def test_object(self):
    rdm = self.rdm
    Char = rdm.Chars['cas 1']
    self.assertAlmostEqual(Char.ddlValue["N1"][3],
		-0.002, 7,
      "Le déplacement du noeud N1 n'est pas correct")


class Para2_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
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
      <arc id="Parabole2" proj="1" qu="%0.0,1.0,0.0,-1000.0,0.0,-1000.0" />
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    #Char1 = rdm.Combis['combi1']
    Char1 = rdm.Chars['cas1']
    #self.assertAlmostEqual(Char1.ddlValue["N3"][1],
#		-4.22034000375e-09, 7,
#      "Le déplacement du noeud N7 n'est pas correct")
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],1000,5, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N2"]['Fy'],1000,5, 
      "La réaction d'appui du noeud N1 n'est pas correcte")



class Para3_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
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
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    Char1 = rdm.Combis['combi1']
    #Char1 = rdm.Chars['cas1']
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],2098.2,1, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N2"]['Fy'],2098.2,1, 
      "La réaction d'appui du noeud N1 n'est pas correcte")



class ArcRadial_TestCase(unittest.TestCase):

  def setUp(self):
    self.rdm = self._genere_instance()
    
  def _genere_instance(self):
    # test de la charge répartie par morceau
    # comparaison avec structures avec ajout de noeuds
    string="""<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.0">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="2,0" id="N2" liaison="2" />
    <node d="1,-0" id="N3" />
  </elem>
  <elem id="barre">
    <arc center="N3" end="N2" id="Arc1" r0="0" r1="0" start="N1" />
  </elem>
  <elem id="geo">
    <barre id="*" igz="1" s="1" />
  </elem>
  <elem id="material">
    <barre id="*" young="2e9" />
  </elem>
  <elem id="char">
    <case id="cas1">
      <pp d="false" />
      <arc id="Arc1" proj="2" qu="%0.0,1.0,0.0,-1.0,0.0,-1.0" />
    </case>
    <case id="cas2" />
  </elem>
  <elem id="combinaison">
    <combinaison d="1.0,1.0" id="Combinaison 1" />
  </elem>
  <elem id="prefs">
    <unit d="1.0" id="M" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="I" />
    <unit d="1.0" id="F" />
    <unit d="1.0" id="S" />
    <unit d="1.0" id="E" />
    <unit d="1.0" id="C" />
    <const g="9.81" />
    <conv conv="1.0" />
  </elem>
</data>"""
    xml = fakeReadXMLString(string)
    rdm = fakeRdm(xml)
    return rdm


  def test_object(self): # les méthodes préfixées par test sont executées dans 
    # l'ordre ou elles apparaissent
    rdm = self.rdm
    #Char1 = rdm.Combis['combi1']
    Char1 = rdm.Chars['cas1']
    self.assertAlmostEqual(Char1.Reactions["N1"]['Fy'],1,3, 
      "La réaction d'appui du noeud N1 n'est pas correcte")
    self.assertAlmostEqual(Char1.Reactions["N2"]['Fy'],1,3, 
      "La réaction d'appui du noeud N1 n'est pas correcte")




if __name__ == '__main__':
  unittest.main()

