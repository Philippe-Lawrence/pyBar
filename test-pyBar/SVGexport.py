#!/usr/bin/env python
# -*- coding: utf-8 -*-

from classSVGExport import SVGExport, fromXML_SVGExport



string="""<data pyBar="http://pybar.fr/index.php?page=logiciel-pybar" version="3.1">
  <elem id="node">
    <node d="0,0" id="N1" liaison="1" />
    <node d="10,0" id="N2" liaison="2" />
    <node d="22,0" id="N3" liaison="2" />
    <node d="30,0" id="N4" liaison="2" />
  </elem>
  <elem id="barre">
    <barre end="N2" id="B1" r0="0" r1="0" start="N1" />
    <barre end="N3" id="B2" r0="0" r1="0" start="N2" />
    <barre end="N4" id="B3" r0="0" r1="0" start="N3" />
  </elem>
  <elem id="geo">
    <barre h="0.16" id="*" igz="9.25e-06" profil="UPN 160" s="0.0024" v="0.08" />
  </elem>
  <elem id="material">
    <barre id="B2,B3" mv="3000" young="200000000000" />
    <barre id="B1" mv="6000" young="210000000000" />
  </elem>
  <elem id="char">
    <case id="CP">
      <pp d="false" />
    </case>
    <case id="Q1">
      <barre id="B1" qu="0,,0.0,-10000.0" />
    </case>
    <case id="Q2">
      <barre id="B2" qu="0,,0.0,-10000.0" />
    </case>
    <case id="Q3">
      <barre id="B3" qu="0,,0.0,-10000.0" />
    </case>
  </elem>
  <elem id="combinaison">
    <combinaison d="1.35,1.5,0.0,0.0" id="1,35G+1,5Q1" />
    <combinaison d="1.35,1.5,1.5,1.5" id="1,35G+1,5Q1+1,5Q2+1,5Q3" />
    <combinaison d="1.35,1.5,0.0,1.5" id="1,35G+1,5Q1+1,5Q3" />
    <combinaison d="1.35,0.0,1.5,0.0" id="1,35G+1,5Q2" />
    <combinaison d="1.35,0.0,0.0,1.5" id="1,35G+1,5Q3" />
    <combinaison d="1.0,1.0,1.0,1.0" id="G+Q1+Q2+Q3" />
  </elem>
  <elem id="prefs">
    <unit d="1.0" id="I" />
    <unit d="1.0" id="M" />
    <unit d="1.0" id="S" />
    <unit d="1.0" id="L" />
    <unit d="1.0" id="F" />
    <unit d="1.0" id="E" />
    <unit d="1.0" id="C" />
    <const g="9.81" />
    <conv conv="1.0" />
  </elem>
</data>"""

output = "test.svg"

# Lecture des données soit à partir d'un fichier
myfile = "/home/plawrence/pyBar/Fichiers pyBar/distro/poutre4appuis.dat"
SVG = SVGExport(myfile, 500, 500)
# soit à partir d'une chaine de caractère contenant du xml
#SVG = fromXML_SVGExport(string, 500, 500)
SVG.printDiagram(output)
SVG.printCharDiagram(output, 1)
#SVG.printNDiagram(output, [1,2,3])
#SVG.printVDiagram(output, [1,2,3])
#SVG.printMDiagram(output, [1,2,3])


