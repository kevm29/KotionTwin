package haxe;
class Log {
	public static dynamic function trace( v : Dynamic, ?infos : Dynamic ) : Void {
		untyped flash.external.ExternalInterface.call("console.log", Std.string(v));
	}
	public static function clear() {}
}
