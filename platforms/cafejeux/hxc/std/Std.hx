class Std {
	public static function is( v : Dynamic, t : Dynamic ) : Bool {
		if( v == null ) return false;
		if( t == String ) return untyped __typeof__(v) == "string";
		if( t == Float ) return untyped __typeof__(v) == "number";
		if( t == Int ) return untyped (__typeof__(v) == "number") && (__int__(v) == v);
		if( t == Bool ) return untyped __typeof__(v) == "boolean";
		if( t == Dynamic ) return true;
		if( t.__ename__ != null ) return v.__enum__ == t;
		return untyped __instanceof__(v, t);
	}
	public static function string( v : Dynamic ) : String {
		if( v == null ) return "null";
		if( untyped __typeof__(v) == "string" ) return v;
		if( v.__enum__ != null ) {
			if( v.length <= 2 ) return v[0];
			var a = [];
			for( i in 2...v.length ) a.push(string(v[i]));
			return v[0] + "(" + a.join(",") + ")";
		}
		if( untyped __instanceof__(v, Array) ) {
			var a = [];
			for( i in 0...v.length ) a.push(string(v[i]));
			return "[" + a.join(",") + "]";
		}
		return untyped String(v);
	}
	public static function int( x : Float ) : Int {
		return untyped __int__(x);
	}
	public static function parseInt( x : String ) : Null<Int> {
		var v = untyped _global["parseInt"](x);
		if( untyped isNaN(v) ) return null;
		return v;
	}
	public static function parseFloat( x : String ) : Float {
		return untyped _global["parseFloat"](x);
	}
	public static function random( x : Int ) : Int {
		return untyped __int__(Math.random() * x);
	}
}
