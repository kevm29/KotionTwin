package mt.net;
#if macro
import haxe.macro.Expr;
#end
// Bouchon KotionTwin : pas de serveur de jeu, les requêtes échouent proprement.
class Codec {
	macro public static function addObfuDown(e:Expr) return macro null;
	macro public static function addObfuUp(e:Expr) return macro null;
	#if !macro
	public static function getInitData() : Dynamic return null;
	public static function requestUrl(url:String, data:Dynamic, onData:Dynamic->Void, ?onError:Dynamic->Void) {
		if( onError != null ) haxe.Timer.delay(function() onError("offline"), 1);
	}
	#end
}
