class List<T> {
	var items : Array<Dynamic>;
	public var length(getLength, null) : Int;
	public function new() { items = []; }
	function getLength() : Int { return items.length; }
	public function add( x : Dynamic ) { items.push(x); }
	public function push( x : Dynamic ) { items.unshift(x); }
	public function pop() : Dynamic { return if( items.length == 0 ) null else items.shift(); }
	public function first() : Dynamic { return items[0]; }
	public function last() : Dynamic { return items[items.length - 1]; }
	public function isEmpty() : Bool { return items.length == 0; }
	public function clear() { items = []; }
	public function remove( x : Dynamic ) : Bool { return items.remove(x); }
	public function iterator() : Dynamic { return HxRt.arrayIter(items.copy()); }
	public function filter( f : Dynamic ) : Dynamic { var l = new List(); for( x in items ) if( f(x) ) l.add(x); return l; }
	public function map( f : Dynamic ) : Dynamic { var l = new List(); for( x in items ) l.add(f(x)); return l; }
	public function join( sep : String ) : String { return items.join(sep); }
	public function toString() : String { return "{" + items.join(", ") + "}"; }
}
