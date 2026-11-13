class Reflect {
	public static function field( o : Dynamic, f : String ) : Dynamic { return if( o == null ) null else o[untyped f]; }
	public static function setField( o : Dynamic, f : String, v : Dynamic ) { o[untyped f] = v; }
	public static function hasField( o : Dynamic, f : String ) : Bool { return untyped o.hasOwnProperty(f); }
	public static function fields( o : Dynamic ) : Array<String> { return untyped __keys__(o); }
	public static function deleteField( o : Dynamic, f : String ) : Bool { untyped __delete__(o, f); return true; }
	public static function callMethod( o : Dynamic, f : Dynamic, args : Array<Dynamic> ) : Dynamic { return f.apply(o, args); }
	public static function isFunction( f : Dynamic ) : Bool { return untyped __typeof__(f) == "function"; }
	public static function isObject( v : Dynamic ) : Bool { var t = untyped __typeof__(v); return t == "object" || t == "movieclip"; }
	public static function copy( o : Dynamic ) : Dynamic {
		var o2 : Dynamic = {};
		for( f in fields(o) ) o2[untyped f] = o[untyped f];
		return o2;
	}
	public static function compare( a : Dynamic, b : Dynamic ) : Int { return if( a == b ) 0 else if( a > b ) 1 else -1; }
	public static function makeVarArgs( f : Dynamic ) : Dynamic { return function() { return f(untyped arguments); }; }
}
