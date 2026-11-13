package haxe;
// Format de haxe.Serializer (sans cache d'objets), suffisant pour les messages des jeux.
class Serializer {
	var buf : Array<String>;
	var shash : Dynamic;
	var scount : Int;
	public function new() { buf = []; shash = {}; scount = 0; }
	public function toString() : String { return buf.join(""); }
	function str( s : String ) {
		var x = shash["$" + s];
		if( x != null ) { buf.push("R" + x); return; }
		shash["$" + s] = scount++;
		var e = StringTools.urlEncode(s);
		buf.push("y" + e.length + ":" + e);
	}
	public function serialize( v : Dynamic ) {
		var t = untyped __typeof__(v);
		if( v == null ) buf.push("n");
		else if( t == "number" ) {
			if( untyped isNaN(v) ) buf.push("k");
			else if( !(untyped isFinite(v)) ) buf.push(if( v < 0 ) "m" else "p");
			else if( v == 0 ) buf.push("z");
			else if( untyped __int__(v) == v && v > -1073741824 && v < 1073741824 ) buf.push("i" + v);
			else buf.push("d" + v);
		}
		else if( t == "boolean" ) buf.push(if( v ) "t" else "f");
		else if( t == "string" ) str(v);
		else if( v.__enum__ != null ) {
			buf.push("w"); str(v.__enum__.__ename__); str(v[0]); buf.push(":" + (v.length - 2));
			for( i in 2...v.length ) serialize(v[i]);
		}
		else if( untyped __instanceof__(v, Array) ) {
			buf.push("a");
			var nulls = 0;
			for( i in 0...v.length ) {
				var x = v[i];
				if( x == null ) { nulls++; continue; }
				if( nulls > 0 ) { buf.push(if( nulls == 1 ) "n" else "u" + nulls); nulls = 0; }
				serialize(x);
			}
			if( nulls > 0 ) buf.push(if( nulls == 1 ) "n" else "u" + nulls);
			buf.push("h");
		}
		else if( v.iterator != null && v.add != null ) {
			buf.push("l");
			for( x in v ) serialize(x);
			buf.push("h");
		}
		else {
			buf.push("o");
			for( f in Reflect.fields(v) ) { str(f); serialize(v[untyped f]); }
			buf.push("g");
		}
	}
	public static function run( v : Dynamic ) : String {
		var s = new Serializer();
		s.serialize(v);
		return s.toString();
	}
}
