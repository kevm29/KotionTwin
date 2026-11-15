class Type {
	public static function getClass( o : Dynamic ) : Dynamic { return if( o == null ) null else o.__class__; }
	public static function getEnum( o : Dynamic ) : Dynamic { return if( o == null ) null else o.__enum__; }
	public static function getClassName( c : Dynamic ) : String { return c.__name__; }
	public static function getEnumName( e : Dynamic ) : String { return e.__ename__; }
	public static function resolveClass( name : String ) : Dynamic { return path(name); }
	public static function resolveEnum( name : String ) : Dynamic { return path(name); }
	static function path( name : String ) : Dynamic {
		var o : Dynamic = untyped __global__();
		// attention : _global == null est vrai en AVM1, on ne teste donc pas o avant la première étape
		var parts = name.split(".");
		for( i in 0...parts.length ) {
			if( i > 0 && o == null ) return null;
			o = o[untyped parts[i]];
		}
		return o;
	}
	public static function createInstance( cl : Dynamic, args : Array<Dynamic> ) : Dynamic {
		if( cl.__new != null ) return cl.__new.apply(cl, args);
		var o : Dynamic = {};
		o.__proto__ = cl.prototype;
		o.__constructor__ = cl;
		cl.apply(o, args);
		return o;
	}
	public static function createEmptyInstance( cl : Dynamic ) : Dynamic {
		var o : Dynamic = {};
		o.__proto__ = cl.prototype;
		return o;
	}
	public static function createEnum( e : Dynamic, c : String, ?params : Array<Dynamic> ) : Dynamic {
		var f = e[untyped c];
		if( params == null || params.length == 0 ) {
			if( untyped __typeof__(f) == "function" ) return f.apply(e, []);
			return f;
		}
		return f.apply(e, params);
	}
	public static function enumIndex( e : Dynamic ) : Int { return e[1]; }
	public static function enumConstructor( e : Dynamic ) : String { return e[0]; }
	public static function enumParameters( e : Dynamic ) : Array<Dynamic> { return e.slice(2); }
	public static function getEnumConstructs( e : Dynamic ) : Array<String> { return e.__constructs__; }
	public static function enumEq( a : Dynamic, b : Dynamic ) : Bool {
		if( a == b ) return true;
		if( a == null || b == null ) return false;
		if( a[0] != b[0] ) return false;
		for( i in 2...a.length ) if( !enumEq(a[i], b[i]) ) return false;
		return true;
	}
	public static function allEnums( e : Dynamic ) : Array<Dynamic> {
		var out = [];
		for( c in getEnumConstructs(e) ) { var v = e[untyped c]; if( untyped __typeof__(v) != "function" ) out.push(v); }
		return out;
	}
}
