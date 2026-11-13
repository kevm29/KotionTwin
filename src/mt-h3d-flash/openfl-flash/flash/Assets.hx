package flash;
// openfl.Assets (cible Flash) : ressources intégrées au SWF, enregistrées par un module généré.
class Assets {
	public static var bitmaps : Map<String, Void->flash.display.BitmapData> = new Map();
	public static var bytes : Map<String, Void->flash.utils.ByteArray> = new Map();
	public static var sounds : Map<String, Void->flash.media.Sound> = new Map();
	public static var fonts : Map<String, Void->flash.text.Font> = new Map();
	static var cache : Map<String, flash.display.BitmapData> = new Map();
	public static function getBitmapData(id:String, ?useCache=true) : flash.display.BitmapData {
		if( useCache && cache.exists(id) ) return cache.get(id);
		var f = bitmaps.get(id);
		if( f == null ) { trace("Asset manquant : " + id); return null; }
		var b = f();
		if( useCache ) cache.set(id, b);
		return b;
	}
	public static function getBytes(id:String) : flash.utils.ByteArray {
		var f = bytes.get(id);
		if( f == null ) { trace("Asset manquant : " + id); return null; }
		return f();
	}
	public static function getText(id:String) : String {
		var b = getBytes(id);
		if( b == null ) return null;
		b.position = 0;
		return b.readUTFBytes(b.length);
	}
	public static function getSound(id:String, ?useCache=true) : flash.media.Sound {
		var f = sounds.get(id);
		if( f == null ) { trace("Asset manquant : " + id); return null; }
		return f();
	}
	public static function getFont(id:String, ?useCache=true) : flash.text.Font {
		var f = fonts.get(id);
		if( f == null ) { trace("Police manquante : " + id); return null; }
		return f();
	}
	public static function loadSound(id:String, ?cb:flash.media.Sound->Void) { var s = getSound(id); if( cb != null ) cb(s); }
	public static inline function getMusic(id:String, ?useCache=true) return getSound(id, useCache);
	public static function exists(id:String, ?type:Dynamic) return bitmaps.exists(id) || bytes.exists(id) || sounds.exists(id) || fonts.exists(id);
}
