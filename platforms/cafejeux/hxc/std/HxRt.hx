// Bibliothèque d'exécution de hxc (KotionTwin) : ce que Haxe 2 fournissait pour Flash 8.
class HxRt {
	static var init = setup();

	static function setup() {
		untyped {
			var ap = Array.prototype;
			ap.copy = function() { return __this__().slice(); };
			ap.insert = function(i, x) { __this__().splice(i, 0, x); };
			ap.remove = function(x) {
				var a = __this__();
				var i = 0;
				while( i < a.length ) {
					if( a[i] == x ) { a.splice(i, 1); return true; }
					i++;
				}
				return false;
			};
			ap.iterator = function() { return HxRt.arrayIter(__this__()); };
			ASSetPropFlags(ap, null, 7, 0);
			Math.NaN = Number.NaN;
			Math.POSITIVE_INFINITY = Number.POSITIVE_INFINITY;
			Math.NEGATIVE_INFINITY = Number.NEGATIVE_INFINITY;
			Math.isNaN = isNaN;
			Math.isFinite = isFinite;
			String.fromCharCode = String.fromCharCode;
		}
		return true;
	}

	public static function arrayIter( a : Dynamic ) : Dynamic {
		var o : Dynamic = {};
		o.a = a; o.i = 0;
		o.hasNext = function() { return untyped __this__().i < __this__().a.length; };
		o.next = function() { var me = untyped __this__(); var v = me.a[me.i]; me.i++; return v; };
		return o;
	}

	public static function iter( v : Dynamic ) : Dynamic {
		if( untyped __instanceof__(v, Array) ) return arrayIter(v);
		if( v.iterator != null ) return v.iterator();
		return v;
	}

	public static function bind( o : Dynamic, name : String ) : Dynamic {
		var f = o[untyped name];
		if( untyped __typeof__(f) != "function" ) return f;
		var g = function() { return f.apply(o, untyped arguments); };
		untyped g.__fname = name;
		return g;
	}

	public static function cb( f : Dynamic, args : Array<Dynamic> ) : Dynamic {
		return function() { return f.apply(null, args.concat(untyped arguments)); };
	}

	public static var created : Dynamic = null;

	public static function newNative( cl : Dynamic, nat : Dynamic, args : Dynamic ) : Dynamic {
		// classe dérivée d'une classe native (BitmapData…) : super() crée l'objet natif (superNative)
		created = null;
		var tmp : Dynamic = {};
		tmp.__proto__ = cl.prototype;
		cl.apply(tmp, args);
		var o = created;
		created = null;
		return if( o == null ) tmp else o;
	}

	public static function superNative( t : Dynamic, nat : Dynamic, a : Array<Dynamic> ) : Dynamic {
		var o : Dynamic = switch( a.length ) {
			case 0: untyped __new__(nat);
			case 1: untyped __new__(nat, a[0]);
			case 2: untyped __new__(nat, a[0], a[1]);
			case 3: untyped __new__(nat, a[0], a[1], a[2]);
			case 4: untyped __new__(nat, a[0], a[1], a[2], a[3]);
			default: untyped __new__(nat, a[0], a[1], a[2], a[3], a[4]);
		};
		var k : Array<Dynamic> = untyped __keys__(t);
		for( f in k ) o[f] = t[f];
		o.__proto__ = t.__proto__;
		created = o;
		return o;
	}

	public static function enumName( e : Dynamic ) : String {
		return e.__enum__.__ename__;
	}
}
