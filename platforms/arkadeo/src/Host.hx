import flash.display.*;
import flash.events.*;
import flash.text.*;
import flash.net.*;
import flash.system.*;
import flash.geom.*;

/**
 * Hôte Arkadeo pour KotionTwin.
 *
 * Les game.swf d'Arkadeo contiennent une classe façade `api.AKApi` (renommée `api_.AKApi_`)
 * dont chaque méthode délègue à l'objet statique `AKApi_.api_`, fourni à l'origine par
 * le chargeur du site arkadeo.com (absent de l'archive). Cet hôte charge game.swf,
 * installe un objet qui implémente cette interface (noms suffixés par « _ »),
 * instancie `Game_` puis appelle `update_(true)` à chaque image.
 *
 * FlashVars : game (url du SWF, défaut game.swf), title, levels (nb de niveaux en
 * progression, défaut 20), id (clé de sauvegarde), modes ("both" | "league" | "progression").
 */
class Host extends Sprite {
	static inline var W = 600;
	static inline var H = 480;
	static inline var BAR = 20;

	var params : Dynamic;
	var gameUrl : String;
	var title : String;
	var levels : Int;
	var saveId : String;
	var modes : String;

	var so : SharedObject;
	var save : Dynamic;

	// partie en cours
	var loader : Loader;
	var game : Dynamic;
	var updateName : String;
	var gameRoot : MovieClip;
	var playing : Bool;
	var mode : Int; // 0 = GM_PROGRESSION, 1 = GM_LEAGUE
	var level : Int;
	var seed : Int;
	var score : Int;
	var frame : Int;
	var overFrame : Int;
	var won : Null<Bool>;
	var events : Array<{f:Int, v:Int}>;
	var state : String;
	var tokensTaken : Int;
	var tokens : Array<Dynamic>;
	var waitingEngine : Bool;
	var baseFps : Float;
	var lastTime : Float;
	var realFps : Float;

	// entrées
	var keys : Map<Int,Bool>;
	var toggled : Map<Int,Bool>;
	var clicked : Bool;
	var mouseDown : Bool;

	// interface
	var layer : Sprite;
	var bar : Sprite;
	var barLeft : TextField;
	var barCenter : TextField;
	var barRight : TextField;
	var barMC : Sprite;
	var progress : Shape;
	var overlay : Sprite;

	public static function main() {
		var h = new Host();
		flash.Lib.current.addChild(h);
	}

	public function new() {
		super();
		if( stage != null ) init(null) else addEventListener(Event.ADDED_TO_STAGE, init);
	}

	function init(_) {
		removeEventListener(Event.ADDED_TO_STAGE, init);
		stage.scaleMode = StageScaleMode.SHOW_ALL;
		stage.align = StageAlign.TOP_LEFT;
		params = loaderInfo.parameters;
		gameUrl = p("game", "game.swf");
		title = p("title", "Arkadeo");
		levels = Std.parseInt(p("levels", "20"));
		saveId = p("id", gameUrl);
		modes = p("modes", "both");
		keys = new Map();
		toggled = new Map();
		try {
			so = SharedObject.getLocal("kotiontwin_arkadeo_" + ~/[^a-zA-Z0-9_-]/g.replace(saveId, "_"), "/");
			save = so.data;
		} catch( e : Dynamic ) {
			save = {};
		}
		if( save.unlocked == null ) save.unlocked = 1;
		if( save.best == null ) save.best = 0;
		if( save.state == null ) save.state = null;

		layer = new Sprite();
		addChild(layer);
		buildBar();
		stage.addEventListener(KeyboardEvent.KEY_DOWN, onKeyDown);
		stage.addEventListener(KeyboardEvent.KEY_UP, onKeyUp);
		stage.addEventListener(MouseEvent.MOUSE_DOWN, function(_) { clicked = true; mouseDown = true; });
		stage.addEventListener(MouseEvent.MOUSE_UP, function(_) mouseDown = false);
		stage.addEventListener(Event.DEACTIVATE, function(_) { keys = new Map(); mouseDown = false; });
		addEventListener(Event.ENTER_FRAME, onFrame);
		if( modes == "league" ) startGame(1, 1) else showMenu();
	}

	function p( k : String, def : String ) : String {
		var v = Reflect.field(params, k);
		return v == null || v == "" ? def : Std.string(v);
	}

	function flush() {
		try { if( so != null ) so.flush(); } catch( e : Dynamic ) {}
	}

	// ------------------------------------------------------------------ API

	// AKConst : entier « sécurisé » ; les jeux appellent get(), add(c) et set(c).
	static function cval( c : Dynamic ) : Int {
		if( c == null ) return 0;
		if( Std.is(c, Int) || Std.is(c, Float) ) return Std.int(c);
		return c.get_();
	}

	function makeConst( v : Int ) : Dynamic {
		var o : Dynamic = {};
		o.get_ = function() return v;
		o.add_ = function(c:Dynamic) { v += cval(c); return o; };
		o.sub_ = function(c:Dynamic) { v -= cval(c); return o; };
		o.set_ = function(c:Dynamic) { v = cval(c); return o; };
		o.toString = function() return Std.string(v);
		return o;
	}

	function makeApi() : Dynamic {
		var me = this;
		var a : Dynamic = {};
		a.getSeed_ = function() return me.seed;
		a.gameOver_ = function(win:Dynamic) me.onGameOver(win == true);
		a.getGameMode_ = function() return me.mode;
		a.getLevel_ = function() return me.level;
		a.isReplay_ = function() return false;
		a.getLang_ = function() return "fr";
		a.isDown_ = function(k:Dynamic, k2:Dynamic, k3:Dynamic) return me.isDown(k) || me.isDown(k2) || me.isDown(k3);
		a.isToggled_ = function(k:Dynamic, k2:Dynamic, k3:Dynamic) return me.isToggled(k) || me.isToggled(k2) || me.isToggled(k3);
		a.unrecordedIsDown_ = function(k:Dynamic) return me.isDown(k);
		a.unrecordedIsToggled_ = function(k:Dynamic) return me.isToggled(k);
		// isClicked = bouton de la souris enfoncé (les jeux détectent eux-mêmes le front),
		// éventuellement au-dessus de l'objet d'affichage donné.
		a.isClicked_ = function(?d:DisplayObject) {
			if( !me.mouseDown && !me.clicked ) return false;
			if( d == null || Std.is(d, Stage) ) return true;
			return d.hitTestPoint(me.stage.mouseX, me.stage.mouseY, true);
		};
		a.getCustomValue_ = function(v:Dynamic) return v;
		a.emitEvent_ = function(v:Dynamic) me.events.push({ f : me.frame, v : v });
		a.getEvent_ = function() : Dynamic {
			if( me.events.length == 0 || me.events[0].f >= me.frame ) return null;
			return me.events.shift().v;
		};
		a.const_ = function(v:Int) return me.makeConst(v);
		a.aconst_ = function(arr:Array<Int>) return [for( v in arr ) me.makeConst(v)];
		a.addScore_ = function(c:Dynamic) {
			if( c == null ) return;
			me.score += cval(c);
			me.refreshBar();
		};
		a.getScore_ = function() return me.score;
		a.setProgression_ = function(r:Float) me.setProgress(r);
		a.saveState_ = function(s:String) { me.state = s; me.save.state = s; me.flush(); };
		a.getState_ = function() return me.state;
		a.getInGamePrizeTokens_ = function() return me.tokens;
		a.getRealInGamePrizeTokens_ = function() return me.tokens;
		a.takePrizeTokens_ = function(t:Dynamic) {
			if( t == null ) return;
			try me.tokensTaken += t.amount_.get_() catch( e : Dynamic ) me.tokensTaken++;
			me.refreshBar();
		};
		a.getPerf_ = function() return 1.0;
		a.getPerfCap_ = function() return 1.0;
		a.getBaseFramerate_ = function() return me.baseFps;
		a.getRealFramerate_ = function() return me.realFps;
		a.setMouseArcade_ = function(b:Bool) {};
		a.setUseMouse_ = function(b:Bool) {};
		a.setStatusText_ = function(t:String, ?align:String) me.setStatus(t, align);
		a.setStatusMC_ = function(mc:DisplayObject, ?align:String) me.setStatusMC(mc, align);
		a.isLowQuality_ = function() return false;
		a.getUserName_ = function() return "Joueur";
		a.getFrame_ = function() return me.frame;
		a.waitEngine_ = function() me.waitingEngine = true;
		a.engineReady_ = function() me.waitingEngine = false;
		return a;
	}

	function isDown( k : Dynamic ) return k != null && keys.get(Std.int(k)) == true;
	function isToggled( k : Dynamic ) return k != null && toggled.get(Std.int(k)) == true;

	function onKeyDown( e : KeyboardEvent ) {
		if( keys.get(e.keyCode) != true ) toggled.set(e.keyCode, true);
		keys.set(e.keyCode, true);
	}
	function onKeyUp( e : KeyboardEvent ) {
		keys.remove(e.keyCode);
	}

	// ------------------------------------------------------------------ partie

	function makeTokens() {
		// Jetons « kdo » (Prize Tokens) proposés en Ligue : 3 jetons de valeurs croissantes.
		tokens = [];
		if( mode != 1 ) return;
		var amounts = [1, 3, 5];
		for( i in 0...amounts.length ) {
			var t : Dynamic = {};
			t.amount_ = makeConst(amounts[i]);
			t.score_ = makeConst(0);
			t.frame_ = i + 1;
			tokens.push(t);
		}
	}

	function startGame( m : Int, l : Int ) {
		clearOverlay();
		stopGame();
		mode = m;
		level = l;
		seed = Std.random(0x3FFFFFFF);
		score = 0;
		frame = 0;
		overFrame = -1;
		won = null;
		events = [];
		tokensTaken = 0;
		waitingEngine = false;
		state = save.state;
		makeTokens();
		setStatus("", null);
		setStatusMC(null, null);
		setProgress(-1);
		refreshBar();
		showMessage("Chargement…");
		loader = new Loader();
		loader.contentLoaderInfo.addEventListener(Event.INIT, onGameInit);
		loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, function(e) showMessage("Impossible de charger " + gameUrl));
		var ctx = new LoaderContext(false, new ApplicationDomain());
		loader.load(new URLRequest(gameUrl), ctx);
	}

	function onGameInit( _ ) {
		clearOverlay();
		var dom = loader.contentLoaderInfo.applicationDomain;
		// game.swf d'origine (noms obfusqués « api_.AKApi_ ») ou jeu recompilé par KotionTwin (« api.AKApi »)
		var api = makeApi();
		if( dom.hasDefinition("api_.AKApi_") ) {
			var ak : Dynamic = dom.getDefinition("api_.AKApi_");
			ak.api_ = api;
		} else {
			var ak : Dynamic = dom.getDefinition("api.AKApi");
			ak.api = api;
		}
		// masque les traces de debug laissées dans certains jeux (« Game.hx:350 : … » affichés à l'écran)
		for( n in [["haxe_.Log_", "trace_"], ["haxe.Log", "trace"]] ) {
			if( !dom.hasDefinition(n[0]) ) continue;
			var log : Dynamic = dom.getDefinition(n[0]);
			try Reflect.setField(log, n[1], function(v:Dynamic, ?i:Dynamic) { flash.Lib.trace(Std.string(v)); }) catch( e : Dynamic ) {}
		}
		baseFps = loader.contentLoaderInfo.frameRate;
		realFps = baseFps;
		try stage.frameRate = baseFps catch( e : Dynamic ) {}
		gameRoot = cast loader.content;
		// l'ajout à la scène déclenche flash.Boot (initialisation statique du jeu)
		layer.addChild(loader);
		var gcl : Class<Dynamic> = cast dom.getDefinition(dom.hasDefinition("Game_") ? "Game_" : "Game");
		try {
			game = Type.createInstance(gcl, []);
			gameRoot.addChild(cast game);
		} catch( e : Dynamic ) {
			showMessage("Erreur au démarrage du jeu :\n" + Std.string(e));
			trace(e);
			return;
		}
		updateName = Reflect.field(game, "update_") != null ? "update_" : "update";
		playing = true;
		lastTime = flash.Lib.getTimer();
		stage.focus = stage;
	}

	function stopGame() {
		playing = false;
		game = null;
		if( loader != null ) {
			if( loader.parent != null ) loader.parent.removeChild(loader);
			try loader.unloadAndStop(true) catch( e : Dynamic ) {}
			loader = null;
		}
		gameRoot = null;
	}

	function onFrame( _ ) {
		if( playing && game != null && !waitingEngine ) {
			frame++;
			try {
				Reflect.callMethod(game, Reflect.field(game, updateName), [true]);
			} catch( e : Dynamic ) {
				trace("Erreur dans le jeu : " + Std.string(e));
				if( Std.is(e, flash.errors.Error) ) trace((e:flash.errors.Error).getStackTrace());
			}
			var now = flash.Lib.getTimer();
			var dt = now - lastTime;
			lastTime = now;
			if( dt > 0 ) realFps = realFps * 0.9 + (1000 / dt) * 0.1;
			if( overFrame >= 0 && frame - overFrame > Std.int(baseFps * 2.5) && overlay == null ) showEnd();
		}
		toggled = new Map();
		clicked = false;
	}

	function onGameOver( win : Bool ) {
		if( overFrame >= 0 ) return;
		won = win;
		overFrame = frame;
		if( mode == 1 ) {
			if( score > save.best ) save.best = score;
		} else if( win && level >= save.unlocked && level < levels ) {
			save.unlocked = level + 1;
		}
		flush();
		submitScore();
	}

	// Envoie le score de fin de partie au site (assets/js/play.js : tableau local + classement en ligne).
	function submitScore() {
		if( score <= 0 ) return;
		try {
			if( flash.external.ExternalInterface.available )
				flash.external.ExternalInterface.call("ktSubmitScore", score, { mode : mode == 1 ? "Ligue" : "Progression niveau " + level });
		} catch( e : Dynamic ) {
			trace("ktSubmitScore indisponible : " + Std.string(e));
		}
	}

	// ------------------------------------------------------------------ barre d'état

	function tf( size : Int, color : Int, bold = false, align = "left" ) {
		var t = new TextField();
		var f = new TextFormat("_sans", size, color, bold);
		f.align = switch( align ) { case "center": TextFormatAlign.CENTER; case "right": TextFormatAlign.RIGHT; default: TextFormatAlign.LEFT; };
		t.defaultTextFormat = f;
		t.selectable = false;
		t.mouseEnabled = false;
		return t;
	}

	function buildBar() {
		bar = new Sprite();
		bar.y = H - BAR;
		var g = bar.graphics;
		g.beginFill(0x12141c);
		g.drawRect(0, 0, W, BAR);
		g.beginFill(0x2a2f3f);
		g.drawRect(0, 0, W, 1);
		progress = new Shape();
		bar.addChild(progress);
		barLeft = tf(12, 0xd8dcea, true, "left");
		barCenter = tf(12, 0xffffff, false, "center");
		barRight = tf(12, 0xffd34e, true, "right");
		for( t in [barLeft, barCenter, barRight] ) {
			t.y = 2;
			t.height = BAR;
			bar.addChild(t);
		}
		barLeft.x = 8; barLeft.width = 200;
		barCenter.x = 150; barCenter.width = 300;
		barRight.x = W - 208; barRight.width = 200;
		barMC = new Sprite();
		bar.addChild(barMC);
		addChild(bar);
	}

	function refreshBar() {
		if( barLeft == null ) return;
		barLeft.text = mode == 1 ? "Ligue" : "Progression · niveau " + level;
		var r = "";
		if( mode == 1 ) r = "Score : " + fmt(score);
		if( tokensTaken > 0 ) r = "Kdo : " + tokensTaken + (r == "" ? "" : "   " + r);
		barRight.text = r;
	}

	function setStatus( t : String, align : String ) {
		barCenter.text = t == null ? "" : t;
	}

	function setStatusMC( mc : DisplayObject, align : String ) {
		while( barMC.numChildren > 0 ) barMC.removeChildAt(0);
		if( mc == null ) return;
		barMC.addChild(mc);
		var b = mc.getBounds(barMC);
		mc.y += (BAR - b.height) / 2 - b.y;
		mc.x += switch( align ) {
			case "left": 8 - b.x;
			case "right": W - 8 - b.width - b.x;
			default: (W - b.width) / 2 - b.x;
		};
	}

	function setProgress( r : Float ) {
		var g = progress.graphics;
		g.clear();
		if( r < 0 ) return;
		if( r > 1 ) r = 1;
		g.beginFill(0x3d7bd9, 0.55);
		g.drawRect(0, 1, W * r, BAR - 1);
	}

	static function fmt( n : Int ) {
		var s = Std.string(n);
		var out = "";
		while( s.length > 3 ) {
			out = " " + s.substr(s.length - 3) + out;
			s = s.substr(0, s.length - 3);
		}
		return s + out;
	}

	// ------------------------------------------------------------------ écrans

	function clearOverlay() {
		if( overlay != null && overlay.parent != null ) overlay.parent.removeChild(overlay);
		overlay = null;
	}

	function newOverlay( alpha : Float ) {
		clearOverlay();
		overlay = new Sprite();
		var g = overlay.graphics;
		g.beginFill(0x0b0d14, alpha);
		g.drawRect(0, 0, W, H - BAR);
		addChild(overlay);
		return overlay;
	}

	function label( parent : Sprite, text : String, size : Int, y : Float, color = 0xffffff, bold = false ) {
		var t = tf(size, color, bold, "center");
		t.multiline = true;
		t.wordWrap = true;
		t.width = W - 40;
		t.x = 20;
		t.y = y;
		t.text = text;
		t.height = t.textHeight + 8;
		parent.addChild(t);
		return t;
	}

	function button( parent : Sprite, text : String, x : Float, y : Float, w : Float, h : Float, enabled : Bool, cb : Void->Void, accent = false ) {
		var b = new Sprite();
		var draw = function(over:Bool) {
			var g = b.graphics;
			g.clear();
			var c = !enabled ? 0x2a2e3a : accent ? (over ? 0xffd34e : 0xf0b92d) : (over ? 0x4b78d6 : 0x3561bd);
			g.lineStyle(1, enabled ? 0xffffff : 0x3a3f4f, enabled ? 0.25 : 1);
			g.beginFill(c);
			g.drawRoundRect(0, 0, w, h, 12, 12);
		};
		draw(false);
		var t = tf(h > 30 ? 16 : 13, enabled ? (accent ? 0x1d1500 : 0xffffff) : 0x6b7184, true, "center");
		t.width = w;
		t.text = text;
		t.height = t.textHeight + 6;
		t.y = (h - t.textHeight) / 2 - 2;
		b.addChild(t);
		b.x = x; b.y = y;
		if( enabled ) {
			b.buttonMode = true;
			b.useHandCursor = true;
			b.mouseChildren = false;
			b.addEventListener(MouseEvent.ROLL_OVER, function(_) draw(true));
			b.addEventListener(MouseEvent.ROLL_OUT, function(_) draw(false));
			b.addEventListener(MouseEvent.CLICK, function(_) cb());
		}
		parent.addChild(b);
		return b;
	}

	function showMessage( msg : String ) {
		var o = newOverlay(0.85);
		label(o, msg, 16, 200, 0xffffff);
	}

	function showMenu() {
		stopGame();
		mode = -1;
		setStatus("", null);
		setStatusMC(null, null);
		setProgress(-1);
		barLeft.text = "Arkadeo";
		barRight.text = save.best > 0 ? "Record : " + fmt(save.best) : "";
		var o = newOverlay(1);
		var g = o.graphics;
		g.beginGradientFill(GradientType.LINEAR, [0x1b2140, 0x0b0d14], [1, 1], [0, 255], (function() { var m = new Matrix(); m.createGradientBox(W, H, Math.PI / 2); return m; })());
		g.drawRect(0, 0, W, H - BAR);
		label(o, title, 34, 28, 0xffffff, true);
		label(o, "Arkadeo · Motion Twin", 13, 76, 0x8f97b3);
		var y = 112.0;
		if( modes != "progression" ) {
			label(o, "Ligue : une partie, un score à battre." + (save.best > 0 ? "  Record : " + fmt(save.best) : ""), 13, y, 0xc9cee0);
			button(o, "Jouer en Ligue", W / 2 - 120, y + 26, 240, 40, true, function() startGame(1, 1), true);
			y += 92;
		}
		if( modes != "league" ) {
			label(o, "Progression : réussissez chaque niveau pour débloquer le suivant.", 13, y, 0xc9cee0);
			y += 28;
			var cols = 10;
			var bw = 46, bh = 34, gap = 8;
			var x0 = (W - (cols * bw + (cols - 1) * gap)) / 2;
			for( i in 0...levels ) {
				var l = i + 1;
				var cx = x0 + (i % cols) * (bw + gap);
				var cy = y + Std.int(i / cols) * (bh + gap);
				button(o, Std.string(l), cx, cy, bw, bh, l <= save.unlocked, function() startGame(0, l));
			}
		}
	}

	function showEnd() {
		var o = newOverlay(0.78);
		var t : String, sub : String;
		if( mode == 1 ) {
			t = "Partie terminée";
			sub = "Score : " + fmt(score) + "\nRecord : " + fmt(save.best);
		} else {
			t = won ? "Niveau " + level + " réussi !" : "Niveau " + level + " échoué";
			sub = won ? (level < levels ? "Le niveau " + (level + 1) + " est débloqué." : "Vous avez terminé tous les niveaux !") : "Retentez votre chance.";
		}
		if( tokensTaken > 0 ) sub += "\nKdo ramassés : " + tokensTaken;
		label(o, t, 30, 120, won == false && mode == 0 ? 0xff8a7a : 0xffd34e, true);
		label(o, sub, 16, 172, 0xffffff);
		var by = 280.0;
		if( mode == 0 && won && level < levels ) {
			button(o, "Niveau suivant", W / 2 - 250, by, 160, 40, true, function() startGame(0, level + 1), true);
			button(o, "Rejouer", W / 2 - 80, by, 160, 40, true, function() startGame(mode, level));
			button(o, "Menu", W / 2 + 90, by, 160, 40, true, showMenu);
		} else {
			button(o, "Rejouer", W / 2 - 170, by, 160, 40, true, function() startGame(mode, level), true);
			button(o, "Menu", W / 2 + 10, by, 160, 40, true, showMenu);
		}
	}
}
