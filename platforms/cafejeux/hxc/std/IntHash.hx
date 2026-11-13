class IntHash<T> {
	var h : Dynamic;
	public function new() { h = {}; }
	public function set( k : Int, v : Dynamic ) { h[k] = v; }
	public function get( k : Int ) : Dynamic { return h[k]; }
	public function exists( k : Int ) : Bool { return untyped h.hasOwnProperty(k); }
	public function remove( k : Int ) : Bool { var e = exists(k); untyped __delete__(h, k); return e; }
	public function keys() : Dynamic {
		var a = [];
		for( k in Reflect.fields(h) ) a.push(Std.parseInt(k));
		return a.iterator();
	}
	public function iterator() : Dynamic {
		var a = [];
		for( k in Reflect.fields(h) ) a.push(h[untyped k]);
		return a.iterator();
	}
}
