class Hash<T> {
	var h : Dynamic;
	public function new() { h = {}; }
	public function set( k : String, v : Dynamic ) { h["$" + k] = v; }
	public function get( k : String ) : Dynamic { return h["$" + k]; }
	public function exists( k : String ) : Bool { return untyped h.hasOwnProperty("$" + k); }
	public function remove( k : String ) : Bool { var e = exists(k); untyped __delete__(h, "$" + k); return e; }
	public function keys() : Dynamic {
		var a = [];
		for( k in Reflect.fields(h) ) a.push(k.substr(1));
		return a.iterator();
	}
	public function iterator() : Dynamic {
		var a = [];
		for( k in Reflect.fields(h) ) a.push(h[untyped k]);
		return a.iterator();
	}
}
