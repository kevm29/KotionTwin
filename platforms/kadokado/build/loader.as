// Loader de remplacement KadoKado (AVM1 / Flash 8) pour KotionTwin.
// Compilé avec avm1c.py (voir build.py). Remplace api/loader.swf, qui attendait
// gameinit.xml et le serveur KadoKado.
//
// FlashVars : swf  = chemin du jeu (relatif à la base Ruffle), défaut "game.swf"
//             gid  = identifiant du jeu (clé du record dans le SharedObject)
//             attach = nom d'export du clip de code ("90D*" pour les jeux Haxe obfusqués)
//
// Les SWF KadoKado sont obfusqués par un hachage déterministe commun à tous les jeux :
//   KKApi=";ndCG"  Manager="980Sb"  init="}-B2"  main="0D 6"
// On définit les noms obfusqués ET les noms en clair.

var SWF = _root.swf; if (SWF == undefined || SWF == "") SWF = "game.swf";
var GID = _root.gid; if (GID == undefined || GID == "") GID = SWF;
var ATTACH = _root.attach; if (ATTACH == undefined || ATTACH == "") ATTACH = "90D*";

// Jeux MotionTypes (anciens jeux, FlashVar mt=1) : la bibliothèque d'exécution MT (Std, Log…)
// était fournie par le loader d'origine (sprite exporté "}ND*9", fonction "}-B2"(clip)).
// build.sh réinjecte ce DoAction d'origine (mt_runtime.bin) dans loader.swf.
var MT = _root.mt == "1";
var rt = null;
if (MT) rt = _root.attachMovie("}ND*9", "mtrt", 5);

var W = 300; var H = 300; var BAR = 20;

var score = 0;
var best = 0;
var over = false;
var overTimer = 0;
var manager = null;
var gameClip = null;
var codeClip = null;
var lastShown = -1;

var so = SharedObject.getLocal("kotiontwin-kadokado", "/");
if (so.data.best == undefined) so.data.best = {};
if (so.data.best[GID] != undefined) best = so.data.best[GID];

function notify(ev) {
	if (flash.external.ExternalInterface.available) {
		flash.external.ExternalInterface.call("KotionTwinKK", ev, GID, score, best);
	}
}

// ------------------------------------------------------------------ KKApi
var api = {};
api.available = function() { return true; };
api.isLocal = function() { return true; };
api.saveScore = function(p) { endGame(p); };
api.gameOver = function(p) { endGame(p); };
api.setScore = function(s) { score = Number(s); return score; };
api.addScore = function(s) { if (!over) score = score + Number(s); return score; };
api.getScore = function() { return score; };
api["const"] = function(v) { return v; };
api.aconst = function(a) { var r = []; for (var i = 0; i < a.length; i++) r.push(a[i]); return r; };
api.cadd = function(a, b) { return Number(a) + Number(b); };
api.cmult = function(a, b) { return Number(a) * Number(b); };
api.val = function(c) { return c; };
api.flagCheater = function() { };
api.registerButton = function(mc) { };
api.processing = function(b) { };
api.getPeriod = function() { return 0; };
api.t = function(s) { return s; };

var OBF = {available: "(kJ+1(", isLocal: "03(H;", saveScore: "}(Rc5", gameOver: "7T4cF(",
	setScore: "}B)Y_", addScore: "5b)bA(", getScore: "{8}XA(", "const": "-Q)9)", aconst: "*G6KR",
	cadd: "3B(*", cmult: "4u57)", val: "8kN", flagCheater: "0ze*c", registerButton: "7vdL6(",
	processing: "-p3G*", getPeriod: "}Mzy-(", t: "]"};
var names = ["available", "isLocal", "saveScore", "gameOver", "setScore", "addScore", "getScore", "const",
	"aconst", "cadd", "cmult", "val", "flagCheater", "registerButton", "processing", "getPeriod", "t"];
for (var i = 0; i < names.length; i++) api[OBF[names[i]]] = api[names[i]];
_global[";ndCG"] = api;
_global.KKApi = api;

// ------------------------------------------------------------------ interface
function fmt(n) {
	var s = String(Math.floor(n)); var out = ""; var c = 0;
	for (var i = s.length - 1; i >= 0; i--) {
		out = s.charAt(i) + out; c++;
		if (c % 3 == 0 && i > 0 && s.charAt(i - 1) != "-") out = " " + out;
	}
	return out;
}
function rect(mc, x, y, w, h, col, alpha) {
	mc.beginFill(col, alpha); mc.moveTo(x, y); mc.lineTo(x + w, y); mc.lineTo(x + w, y + h);
	mc.lineTo(x, y + h); mc.lineTo(x, y); mc.endFill();
}
function label(mc, name, depth, x, y, w, h, size, color, bold, align) {
	mc.createTextField(name, depth, x, y, w, h);
	var t = mc[name];
	var f = new TextFormat("_sans", size, color, bold);
	f.align = align;
	t.setNewTextFormat(f); t.selectable = false; t.embedFonts = false;
	return t;
}

var bar = _root.createEmptyMovieClip("bar", 20);
bar._y = H;
bar.beginGradientFill("linear", [0x3b2a5c, 0x1d1430], [100, 100], [0, 255],
	{matrixType: "box", x: 0, y: 0, w: W, h: BAR, r: Math.PI / 2});
bar.moveTo(0, 0); bar.lineTo(W, 0); bar.lineTo(W, BAR); bar.lineTo(0, BAR); bar.lineTo(0, 0); bar.endFill();
rect(bar, 0, 0, W, 1, 0xffcc33, 100);
var tLab = label(bar, "lab", 1, 4, 1, 60, 18, 10, 0xffcc33, true, "left"); tLab.text = "SCORE";
var tScore = label(bar, "sc", 2, 46, 0, 110, 19, 13, 0xffffff, true, "left");
var tBest = label(bar, "be", 3, 150, 1, 146, 18, 10, 0xc9b8ee, false, "right");
function showScore() {
	if (score != lastShown) { tScore.text = fmt(score); lastShown = score; }
}
function showBest() { tBest.text = "RECORD " + fmt(best); }
showBest(); showScore();

// ------------------------------------------------------------------ fin de partie
function endGame(p) {
	if (over) return;
	over = true; overTimer = 0;
	if (score > best) {
		best = score; so.data.best[GID] = best; so.flush(); showBest();
	}
	showScore();
	notify("gameover");
	// tableau des scores du site (assets/js/play.js)
	if (flash.external.ExternalInterface.available) flash.external.ExternalInterface.call("ktSubmitScore", score);
}
function showOverlay() {
	var o = _root.createEmptyMovieClip("overlay", 30);
	rect(o, 0, 0, W, H, 0x000000, 60);
	rect(o, 30, 95, 240, 110, 0x1d1430, 92);
	rect(o, 30, 95, 240, 2, 0xffcc33, 100);
	var t1 = label(o, "t1", 1, 30, 103, 240, 24, 16, 0xffcc33, true, "center"); t1.text = "PARTIE TERMINÉE";
	var t2 = label(o, "t2", 2, 30, 130, 240, 30, 22, 0xffffff, true, "center"); t2.text = fmt(score);
	var t3 = label(o, "t3", 3, 30, 160, 240, 18, 11, 0xc9b8ee, false, "center"); t3.text = "Record : " + fmt(best);
	var t4 = label(o, "t4", 4, 30, 180, 240, 18, 11, 0xffffff, false, "center"); t4.text = "Cliquez pour rejouer";
	o.onRelease = function() { restart(); };
}

// ------------------------------------------------------------------ chargement du jeu
function findManager() {
	var m = null;
	if (codeClip != null) m = codeClip["980Sb"];
	if (m == undefined && codeClip != null) m = codeClip.Manager;
	if (m == undefined) m = gameClip["980Sb"];
	if (m == undefined) m = gameClip.Manager;
	if (m == undefined) m = _global["980Sb"];
	if (m == undefined) m = _global.Manager;
	return m;
}
function managerInit(m, mc) {
	if (m["}-B2"] != undefined) m["}-B2"](mc); else m.init(mc);
}
function managerMain(m) {
	if (m["0D 6"] != undefined) m["0D 6"](); else m.main();
}

function start() {
	waiting = 0; score = 0; over = false; overTimer = 0; lastShown = -1; manager = null; codeClip = null;
	showScore();
	var holder = _root.createEmptyMovieClip("game", 10);
	var msk = _root.createEmptyMovieClip("gmask", 11);
	rect(msk, 0, 0, W, H, 0xff00ff, 100);
	holder.setMask(msk);
	gameClip = holder.createEmptyMovieClip("swf", 1);
	var mcl = new MovieClipLoader();
	var lis = {};
	lis.onLoadInit = function(mc) {
		gameClip = mc;
		var c = mc.attachMovie(ATTACH, "_c", 10);
		if (c == undefined) c = mc.attachMovie("code", "_c", 10);
		if (c != undefined) { c.gotoAndStop(1); codeClip = c; } else codeClip = mc;
		if (MT && rt != null) rt["}-B2"].apply(rt, [codeClip]);
		waiting = 1;
	};
	lis.onLoadError = function(mc, err) { tBest.text = "Erreur de chargement : " + SWF; };
	mcl.addListener(lis);
	mcl.loadClip(SWF, gameClip);
}
function restart() {
	_root.overlay.removeMovieClip();
	_root.game.removeMovieClip();
	_root.gmask.removeMovieClip();
	start();
}

var waiting = 0;
_root.onEnterFrame = function() {
	if (waiting > 0) {
		// le code du clip attaché s'exécute à la fin de la frame : on attend que Manager existe
		var m = findManager();
		if (m != undefined && m != null) {
			waiting = 0; manager = m; managerInit(manager, codeClip); notify("start");
		} else {
			waiting++;
			if (waiting > 200) { waiting = 0; tBest.text = "Manager introuvable"; notify("nomanager"); }
		}
	}
	if (manager != null && manager != undefined) {
		if (!over || overTimer < 50) managerMain(manager);
		if (over) {
			overTimer++;
			if (overTimer == 50) showOverlay();
		}
	}
	showScore();
};

start();
