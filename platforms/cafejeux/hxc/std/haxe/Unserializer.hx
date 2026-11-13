package haxe;
class Unserializer {
	var s : String;
	var pos : Int;
	var scache : Array<String>;
	public function new( s : String ) { this.s = s; pos = 0; scache = []; }
	function readInt() : Int {
		var start = pos;
		if( s.charAt(pos) == "-" ) pos++;
		while( pos < s.length ) { var c = s.charCodeAt(pos); if( c < 48 || c > 57 ) break; pos++; }
		return Std.parseInt(s.substr(start, pos - start));
	}
	function readFloat() : Float {
		var start = pos;
		while( pos < s.length ) { var c = s.charAt(pos); if( "0123456789+-.eE".indexOf(c) < 0 ) break; pos++; }
		return Std.parseFloat(s.substr(start, pos - start));
	}
	public function unserialize() : Dynamic {
		var c = s.charAt(pos++);
		switch( c ) {
		case "n": return null;
		case "z": return 0;
		case "t": return true;
		case "f": return false;
		case "k": return Math.NaN;
		case "m": return Math.NEGATIVE_INFINITY;
		case "p": return Math.POSITIVE_INFINITY;
		case "i": return readInt();
		case "d": return readFloat();
		case "y":
			var len = readInt(); pos++;
			var str = StringTools.urlDecode(s.substr(pos, len));
			pos += len; scache.push(str); return str;
		case "R": return scache[readInt()];
		case "a":
			var a = [];
			while( true ) {
				var ch = s.charAt(pos);
				if( ch == "h" ) { pos++; break; }
				if( ch == "u" ) { pos++; var n = readInt(); for( i in 0...n ) a.push(null); continue; }
				a.push(unserialize());
			}
			return a;
		case "l":
			var l = new List();
			while( s.charAt(pos) != "h" ) l.add(unserialize());
			pos++;
			return l;
		case "o":
			var o : Dynamic = {};
			while( s.charAt(pos) != "g" ) { var k = unserialize(); o[untyped k] = unserialize(); }
			pos++;
			return o;
		case "w":
			var en = unserialize(); var cn = unserialize(); pos++;
			var n = readInt();
			var args = [];
			for( i in 0...n ) args.push(unserialize());
			var e = Type.resolveEnum(en);
			return Type.createEnum(e, cn, args);
		}
		throw "Unserializer : format inconnu " + c;
		return null;
	}
	public static function run( v : String ) : Dynamic {
		return new Unserializer(v).unserialize();
	}
}
