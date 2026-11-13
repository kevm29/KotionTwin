# Plateforme Frutiparc (Frusion)

Sur Frutiparc (2004-2005), les jeux s'ouvraient dans une fenêtre « Frusion » qui leur fournissait la
classe `frusion.gameclient.GameClient` : connexion au serveur, type de disque (noir, gris, blanc),
emplacements de la fruticard, scores et objets. Cette classe n'est pas dans l'archive.

- `frusion-host.as` : hôte réécrit en ActionScript 1. Il définit `_global.frusion.gameclient.GameClient`
  (d'après la version compilée retrouvée dans `Frutiparc/Games/miniWave2/bumdum.swf`), en mode
  « disque blanc » (version complète, sans classement en ligne), puis charge le jeu dans `_level0`.
  Les emplacements de la fruticard, le meilleur score et les objets gagnés sont gardés dans un
  SharedObject local (stockage du navigateur via Ruffle).
- `build.py` : copie les fichiers de chaque jeu dans `games/<id>/`, reconstitue les SWF assemblés par
  l'outil interne « swfmake » (`tools/swfmerge.py`) et compile `host.swf` avec `tools/as1c.py`.

```
python3 platforms/frutiparc/build.py <WebGamesArchives>/Frutiparc/Games            # tous les jeux
python3 platforms/frutiparc/build.py <WebGamesArchives>/Frutiparc/Games fp-kaluga  # un seul
```

Outils maison (Python 3, sans dépendance) :

- `tools/as1c.py` : petit compilateur ActionScript 1 (sous-ensemble JavaScript) vers SWF AVM1.
- `tools/swfmerge.py` : fusion de bibliothèques SWF avec renumérotation des identifiants.
- `tools/avm1dis.py` : désassembleur AVM1 (lecture du code des SWF d'origine).
- `tools/swfhead.py` : taille de scène, cadence et version d'un SWF.
