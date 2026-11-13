class StringTools {
	public static function urlEncode( s : String ) : String { return untyped _global["escape"](s); }
	public static function urlDecode( s : String ) : String { return untyped _global["unescape"](s); }
	public static function startsWith( s : String, p : String ) : Bool { return s.substr(0, p.length) == p; }
	public static function endsWith( s : String, p : String ) : Bool { return s.substr(s.length - p.length) == p; }
	public static function replace( s : String, a : String, b : String ) : String { return s.split(a).join(b); }
	public static function trim( s : String ) : String { return ltrim(rtrim(s)); }
	public static function ltrim( s : String ) : String { var i = 0; while( i < s.length && s.charCodeAt(i) <= 32 ) i++; return s.substr(i); }
	public static function rtrim( s : String ) : String { var i = s.length; while( i > 0 && s.charCodeAt(i - 1) <= 32 ) i--; return s.substr(0, i); }
	public static function lpad( s : String, c : String, l : Int ) : String { while( s.length < l ) s = c + s; return s; }
	public static function rpad( s : String, c : String, l : Int ) : String { while( s.length < l ) s = s + c; return s; }
	public static function hex( n : Int, ?digits : Int ) : String {
		var s = untyped n.toString(16);
		s = s.toUpperCase();
		if( digits != null ) while( s.length < digits ) s = "0" + s;
		return s;
	}
	public static function htmlEscape( s : String ) : String { return s.split("&").join("&amp;").split("<").join("&lt;").split(">").join("&gt;"); }
}
