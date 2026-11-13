package haxe;
class Timer {
	var id : Dynamic;
	public function new( ms : Int ) {
		var me = this;
		id = untyped _global["setInterval"](function() { me.run(); }, ms);
	}
	public function stop() {
		if( id == null ) return;
		untyped _global["clearInterval"](id);
		id = null;
	}
	public dynamic function run() {}
	public static function delay( f : Dynamic, ms : Int ) : Dynamic {
		var t = new haxe.Timer(ms);
		t.run = function() { t.stop(); f(); };
		return t;
	}
	// API de Haxe 1, encore utilisée par certains jeux
	public static function delayed( f : Dynamic, ms : Int ) : Dynamic {
		return function() { haxe.Timer.delay(f, ms); };
	}
	public static function stamp() : Float { return untyped __getTimer__() / 1000; }
}
