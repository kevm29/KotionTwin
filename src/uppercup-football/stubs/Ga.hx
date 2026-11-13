// Bouchon KotionTwin : les statistiques Google Analytics de l'application sont désactivées.
enum GaSocial { Facebook; Twitter; }
enum Affiliation { IAP; }
class Ga {
	public static function init() {}
	public static function event(cat:String, action:String, ?label:String, ?value:Int) {}
	public static function pageview(p:String) {}
	public static function social(net:GaSocial, action:String, target:String) {}
	public static function transaction(id:Dynamic, price:Dynamic, aff:Affiliation, items:Dynamic) {}
}
