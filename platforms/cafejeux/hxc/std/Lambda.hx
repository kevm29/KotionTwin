class Lambda {
	public static function array( it : Dynamic ) : Array<Dynamic> { var a = []; for( x in it ) a.push(x); return a; }
	public static function list( it : Dynamic ) : Dynamic { var l = new List(); for( x in it ) l.add(x); return l; }
	public static function exists( it : Dynamic, f : Dynamic ) : Bool { for( x in it ) if( f(x) ) return true; return false; }
	public static function has( it : Dynamic, v : Dynamic ) : Bool { for( x in it ) if( x == v ) return true; return false; }
	public static function count( it : Dynamic ) : Int { var n = 0; for( x in it ) n++; return n; }
	public static function map( it : Dynamic, f : Dynamic ) : Dynamic { var l = new List(); for( x in it ) l.add(f(x)); return l; }
	public static function filter( it : Dynamic, f : Dynamic ) : Dynamic { var l = new List(); for( x in it ) if( f(x) ) l.add(x); return l; }
	public static function iter( it : Dynamic, f : Dynamic ) { for( x in it ) f(x); }
	public static function indexOf( it : Dynamic, v : Dynamic ) : Int { var i = 0; for( x in it ) { if( x == v ) return i; i++; } return -1; }
}
