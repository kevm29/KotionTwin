# Outils partagés des jeux Flash 8 autonomes

- `kt-host.js` : charge Ruffle (local puis CDN) et monte un SWF (`mount`), avec le rendu
  `wgpu-webgl` requis par `BitmapData.draw` ; `store` (localStorage protégé) ; `h()` pour le DOM.
- `persistcodec.js` : `mt.PersistCodec` de Motion Twin (encode/decode, options `crc`, `obfu`, `refs`).
- `haxeser.js` : sérialisation Haxe 2 (`haxe.Serializer`/`Unserializer`), énumérations comprises.
- `md5.js` : MD5 (clé de contrôle de Miniville).

Outils hors navigateur dans `tools/` : `swfdis.py` (désassembleur AVM1), `avm1dec.py` (pseudo-JS),
`avm1.py` (assembleur et réécriture de SWF), `check_images.py` (images des SWF non vides).
