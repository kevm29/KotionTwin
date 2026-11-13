package flash;
class Lib {
	public static var current : Dynamic = untyped _root;
	public static var _root : Dynamic = untyped _root;
	public static var _global : Dynamic = untyped __global__();
	public static function getTimer() : Int { return untyped __getTimer__(); }
	public static function getURL( url : String, ?target : String ) { untyped _root.getURL(url, target); }
	public static function trace( v : Dynamic ) { haxe.Log.trace(v); }
}
