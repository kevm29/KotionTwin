// Remplace le @:build(mt.data.Texts.build(...)) Haxe 2 (port Haxe 3, KotionTwin)
class Text {
	static var ALL : Map<String,String>;
	public static function init( raw : String ) ALL = mt.data.Texts.parseXml(raw);
	static function resolve( id : String ) return ALL != null && ALL.exists(id) ? ALL.get(id) : "#" + id + "#";
	public static var contracts(get, never) : String;
	static function get_contracts() return resolve("contracts");
}
