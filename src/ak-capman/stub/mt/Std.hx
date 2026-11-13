package mt;
// Remplace mt.Std (absent de l'archive) : reprend Std + quelques extensions utilisées par Capman.
class Std {
	public static inline function int( f : Float ) : Int return TopStd.int(f);
	public static inline function string( s : Dynamic ) : String return TopStd.string(s);
	public static inline function parseInt( s : String ) : Null<Int> return TopStd.parseInt(s);
	public static inline function parseFloat( s : String ) : Float return TopStd.parseFloat(s);
	public static inline function random( n : Int ) : Int return TopStd.random(n);
	public static inline function is( v : Dynamic, t : Dynamic ) : Bool return TopStd.is(v, t);
	public static inline function instance<T:{},S:T>( v : T, c : Class<S> ) : S return TopStd.instance(v, c);
	public static inline function first<T>( a : Array<T> ) : T return a[0];
	public static inline function last<T>( a : Array<T> ) : T return a[a.length - 1];
	public static inline function removeFirst<T>( a : Array<T> ) : T return a.shift();
}
