package api;
import api.AKProtocol;

/**
 * Façade Arkadeo réécrite pour KotionTwin : délègue à l'objet `api` fourni
 * par platforms/arkadeo/host.swf (mêmes noms de méthodes, suffixés par « _ »).
 */
class AKApi {
	public static var api : Dynamic;
	static function h() : Dynamic {
		
		return api;
	}
	public static function getSeed() : Int return h().getSeed_();
	public static function gameOver( ?win : Bool ) h().gameOver_(win);
	public static function getGameMode() : GameMode return Type.createEnumIndex(GameMode, h().getGameMode_());
	public static function getLevel() : Int return h().getLevel_();
	public static function isReplay() : Bool return h().isReplay_();
	public static function getLang() : String return h().getLang_();
	public static function isDown( k : Int, ?k2 : Int, ?k3 : Int ) : Bool return h().isDown_(k, k2, k3);
	public static function isToggled( k : Int, ?k2 : Int, ?k3 : Int ) : Bool return h().isToggled_(k, k2, k3);
	public static function isClicked( ?d : flash.display.DisplayObject ) : Bool return h().isClicked_(d);
	public static function getCustomValue( v : Int ) : Int return h().getCustomValue_(v);
	public static function emitEvent( v : Int ) h().emitEvent_(v);
	public static function getEvent() : Null<Int> return h().getEvent_();
	public static function unrecordedIsDown( k : Int ) : Bool return h().unrecordedIsDown_(k);
	public static function unrecordedIsToggled( k : Int ) : Bool return h().unrecordedIsToggled_(k);
	public static function const( v : Int ) : AKConst return h().const_(v);
	public static function aconst( a : Array<Int> ) : Array<AKConst> return h().aconst_(a);
	public static function addScore( c : AKConst ) h().addScore_(c);
	public static function getScore() : Int return h().getScore_();
	public static function setProgression( r : Float ) h().setProgression_(r);
	public static function saveState( s : Dynamic ) h().saveState_(haxe.Serializer.run(s));
	public static function getState() : Dynamic { try return haxe.Unserializer.run(h().getState_()) catch( e : Dynamic ) return null; }
	public static function getInGamePrizeTokens() : Array<SecureInGamePrizeTokens> return h().getInGamePrizeTokens_();
	public static function takePrizeTokens( t : SecureInGamePrizeTokens ) h().takePrizeTokens_(t);
	public static function getPerf() : Float return h().getPerf_();
	public static function getBaseFramerate() : Float return h().getBaseFramerate_();
	public static function setMouseArcade( b : Bool ) h().setMouseArcade_(b);
	public static function setUseMouse( b : Bool ) h().setUseMouse_(b);
	public static function setStatusText( t : String, ?align : String ) h().setStatusText_(t, align);
	public static function setStatusMC( mc : flash.display.DisplayObject, ?align : String ) h().setStatusMC_(mc, align);
	public static function isLowQuality() : Bool return h().isLowQuality_();
	public static function getUserName() : String return h().getUserName_();
	public static function getFrame() : Int return h().getFrame_();
}
