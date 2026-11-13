package secure;
import GameData._ArtefactId;

// KotionTwin : remplace le serveur de Naturalchimie 2 pour une « partie libre » en solo.
// getData("d") fournit la configuration de partie (zone de départ du Palais de Stime Pounk),
// load() simule /act/start et /act/end ; le score final est envoyé à la page (ktSubmitScore).
class Codec {
	public static var displayError : String -> Void;
	public static var VERSION = "kotion";

	public static function getData(name : String) : Dynamic {
		var chain : Array<_ArtefactId> = [];
		for (i in 0...12) chain.push(_Elt(i));
		return {
			_mode : "dft",
			_chain : chain,
			_chWeight : [110, 110, 106, 106, 104, 102, 102, 100, 95, 95, 90, 80],
			_chainknown : 12,
			_object : -1,
			_userobjects : [],
			_artefacts : [
				{_id : _Elts(2, null), _freq : 4500},
				{_id : _Elts(2, _Neutral), _freq : 500},
				{_id : _Dynamit(0), _freq : 30},
				{_id : _Dynamit(1), _freq : 15},
				{_id : _Alchimoth, _freq : 10}
			],
			_grid : [],
			_bg : "305:-10:steampunk",
			_spirit : null,
			_texture : null,
			_pnj_url : "pnj.swf",
			_object_url : "swf/objectMc.swf",
			_helps : [],
			_qmin : 0,
			_playCount : 0,
			_quest : null,
			_sound : "1;1;35",
			_music : "game",
			_worldMod : null,
			_mod : false
		};
	}

	public static function load(url : String, v : Dynamic, cb : Dynamic -> Void) {
		if (url.indexOf("/act/start") >= 0) {
			cb({_id : 1, _token : 0, _gold : 0, _goldScore : null, _rcheck : v._rcode ^ 0xAD0AD0, _error : null});
		} else if (url.indexOf("/act/end") >= 0) {
			var score : Int = v._score;
			try { flash.external.ExternalInterface.call("ktSubmitScore", score); } catch (e : Dynamic) {}
			cb({_endUrl : "javascript:void(window.ktGameEnded ? ktGameEnded(" + score + ") : 0)"});
		}
	}
}
