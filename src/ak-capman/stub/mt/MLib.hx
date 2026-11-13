package mt;
// Sous-ensemble de mt.MLib (absent de l'archive) utilisé par Capman.
class MLib {
	public static inline function isEven( x : Int ) return (x & 1) == 0;
	public static inline function max( a : Int, b : Int ) return a > b ? a : b;
	public static inline function min( a : Int, b : Int ) return a < b ? a : b;
	public static inline function abs( a : Int ) return a < 0 ? -a : a;
	public static inline function fabs( a : Float ) return a < 0 ? -a : a;
}
