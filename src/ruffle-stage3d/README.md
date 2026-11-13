# Ruffle corrigé pour les jeux Stage3D

Ruffle 0.7.1 (et ses nightlies d'octobre 2026) recrée son `RenderPipeline` wgpu à chaque changement
d'état Stage3D (programme, blend, textures…). En WebGL, l'ancien programme GL est détruit avec le
pipeline, donc un jeu qui alterne entre plusieurs shaders recompile et relie ses shaders **à chaque
image**. Mesure sur Monster Hotel : environ 18 `linkProgram` par image et 83 % du temps passé dans
la compilation des shaders.

`0001-cache-des-pipelines-stage3d.patch` ajoute dans `render/wgpu/src/context3d/current_pipeline.rs`
un cache des pipelines indexé par l'état complet (programme, formats des attributs, textures, cible,
blend, masque, culling, profondeur/stencil, échantillonnage). Le cache est vidé au-delà de 512 entrées.

Ce Ruffle n'est utilisé que par les jeux dont l'entrée du catalogue a `"ruffle": "assets/ruffle-stage3d/ruffle.js"`
(aujourd'hui Monster Hotel). Les autres jeux gardent Ruffle 0.7.1 officiel.

Recompiler : `sh build.sh` (environ 30 min ; voir les prérequis en tête du script).
