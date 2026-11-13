package mt;
// Bouchon KotionTwin : console de débogage de Motion Twin (absente de l'archive).
class Console {
	static var buf : Array<String> = [];
	public static function log(?a:Dynamic, ?b:Dynamic) { buf.push(Std.string(a)); if( buf.length > 200 ) buf.shift(); }
	public static function dbg(?a:Dynamic, ?b:Dynamic) log(a, b);
	public static function dump() return buf.join("\n");
}
