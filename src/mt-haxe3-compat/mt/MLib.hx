package mt;

// Reconstitution de mt.MLib (absente de l'archive WebGamesArchives), d'après l'usage
// qu'en font les jeux et la bibliothèque de Motion Twin (inspirée de polygonal Mathematics).
class MLib {
	public static inline var PI : Float = 3.141592653589793;
	public static inline var PI2 : Float = 6.283185307179586;
	public static inline var PIHALF : Float = 1.5707963267948966;
	public static inline var EPS : Float = 1e-6;
	public static inline var RAD_DEG : Float = 57.29577951308232;
	public static inline var DEG_RAD : Float = 0.017453292519943295;

	public static inline function toRad(deg:Float) : Float return deg * DEG_RAD;
	public static inline function toDeg(rad:Float) : Float return rad * RAD_DEG;
	public static inline function min(a:Int, b:Int) : Int return a < b ? a : b;
	public static inline function max(a:Int, b:Int) : Int return a > b ? a : b;
	public static inline function fmin(a:Float, b:Float) : Float return a < b ? a : b;
	public static inline function fmax(a:Float, b:Float) : Float return a > b ? a : b;
	public static inline function iabs(x:Int) : Int return x < 0 ? -x : x;
	public static inline function fabs(x:Float) : Float return x < 0 ? -x : x;
	public static inline function sign(x:Float) : Int return x > 0 ? 1 : (x < 0 ? -1 : 0);
	public static inline function round(x:Float) : Int return Math.round(x);
	public static inline function floor(x:Float) : Int return Math.floor(x);
	public static inline function ceil(x:Float) : Int return Math.ceil(x);
	public static inline function clamp(x:Int, min:Int, max:Int) : Int return x < min ? min : (x > max ? max : x);
	public static inline function fclamp(x:Float, min:Float, max:Float) : Float return x < min ? min : (x > max ? max : x);
	public static inline function inRange(x:Float, min:Float, max:Float) : Bool return x >= min && x <= max;
	public static inline function isPow2(x:Int) : Bool return x > 0 && (x & (x - 1)) == 0;
	public static inline function frandRange(min:Float, max:Float) : Float return min + Math.random() * (max - min);
	public static function wrap(x:Int, lower:Int, upper:Int) : Int {
		var n = upper - lower + 1;
		if( n <= 0 ) return lower;
		var r = (x - lower) % n;
		if( r < 0 ) r += n;
		return lower + r;
	}
	public static function wrapToPi(a:Float) : Float {
		a = (a + PI) % PI2;
		if( a < 0 ) a += PI2;
		return a - PI;
	}
	// modulo signé : résultat dans [0, m[
	public static function sMod(x:Float, m:Float) : Float {
		var r = x % m;
		if( r < 0 ) r += m;
		return r;
	}
	// modulo centré : résultat dans [-m, m[
	public static function hMod(x:Float, m:Float) : Float {
		while( x > m ) x -= m * 2;
		while( x < -m ) x += m * 2;
		return x;
	}
}
