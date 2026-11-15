/*
 * KotionTwin — API CaféJeux recréée (l'API réseau d'origine, ../api, n'est pas dans l'archive).
 *
 * Chaque joueur fait tourner sa propre copie du jeu dans son propre lecteur Ruffle.
 * Le « serveur » est la page hôte (platforms/cafejeux/host.js) : elle relaie les messages
 * entre les deux copies, comme le faisait le serveur CaféJeux, pour jouer à deux sur le même
 * écran ou contre une IA.
 *
 * Protocole avec la page hôte (ExternalInterface) :
 *   jeu -> hôte : cjSend(pid, type, donnée)
 *       ready | msg (message sérialisé) | endTurn | victory ("1","0","n") | gameOver
 *       colors ("moi,adversaire") | infos (html) | log | print | error
 *   hôte -> jeu : cjPush(type, mine, donnée), mis en file et traité à chaque image,
 *       sauf si le jeu a verrouillé la file avec lockMessages(true)
 *       init | msg | turn ("1" = à moi) | victory ("1","0","n")
 */
class MMApi {

	public static var game : Dynamic;
	public static var pid : Int = 0;
	static var locked = true;
	static var myTurn : Null<Bool> = null;
	static var inbox : Array<Dynamic> = new Array();
	static var queue : Array<Dynamic> = new Array();
	static var victorySent = false;
	static var gameOverSent = false;
	static var dispatching = false;

	// ---------------------------------------------------------------- API utilisée par les jeux

	public static function isMyTurn() : Null<Bool> {
		return myTurn;
	}

	public static function hasControl() : Bool {
		return true;
	}

	public static function isReconnecting() : Bool {
		return false;
	}

	public static function lockMessages( b : Bool ) {
		locked = b;
	}

	public static function sendMessage( msg : Dynamic ) {
		send("msg", haxe.Serializer.run(msg));
	}

	public static function queueMessage( msg : Dynamic ) {
		queue.push(msg);
	}

	public static function sendQueue() {
		var q = queue;
		queue = new Array();
		for( m in q )
			sendMessage(m);
	}

	public static function endTurn( ?msg : Dynamic ) {
		sendQueue();
		if( msg != null )
			sendMessage(msg);
		myTurn = false;
		send("endTurn", "");
	}

	public static function victory( v : Null<Bool> ) {
		if( victorySent ) return;
		victorySent = true;
		send("victory", if( v == null ) "n" else if( v ) "1" else "0");
	}

	public static function gameOver() {
		if( gameOverSent ) return;
		gameOverSent = true;
		send("gameOver", "");
	}

	public static function setColors( me : Int, opp : Int ) {
		send("colors", me + "," + opp);
	}

	public static function setInfos( html : String ) {
		send("infos", html);
	}

	public static function logMessage( txt : String ) {
		send("log", txt);
	}

	public static function print( v : Dynamic ) {
		send("print", Std.string(v));
	}

	// Options de partie (cartes, decks…) : tout est autorisé en local.
	public static function getOptions( ?mine : Bool ) : Array<Bool> {
		var a = new Array();
		for( i in 0...32 ) a.push(true);
		return a;
	}

	// ---------------------------------------------------------------- liaison avec la page hôte

	static function send( kind : String, data : String ) {
		flash.external.ExternalInterface.call("cjSend", pid, kind, data);
	}

	public static function init( g : Dynamic, p : Int ) {
		game = g;
		pid = p;
		flash.external.ExternalInterface.addCallback("cjPush", null, push);
		send("ready", "");
	}

	static function push( kind : String, mine : Bool, data : String ) {
		inbox.push({ kind : kind, mine : mine, data : data });
	}

	// Appelé à chaque image par Main, avant game.main()
	public static function process() {
		if( dispatching ) return;
		dispatching = true;
		while( !locked && inbox.length > 0 ) {
			var e = inbox.shift();
			try {
				dispatch(e);
			} catch( err : Dynamic ) {
				send("error", e.kind + " : " + Std.string(err));
			}
		}
		dispatching = false;
	}

	static function dispatch( e : Dynamic ) {
		switch( e.kind ) {
		case "init":
			var msg = game.initialize();
			sendMessage(msg);
			endTurn();
		case "msg":
			game.onMessage(e.mine, haxe.Unserializer.run(e.data));
		case "turn":
			myTurn = (e.data == "1");
			send("turnSeen", e.data);
			if( game.onTurnDone != null ) game.onTurnDone();
		case "victory":
			var v : Dynamic = if( e.data == "n" ) null else (e.data == "1");
			victorySent = true;
			if( game.onVictory != null ) game.onVictory(v);
		}
	}
}
