/*
 * Hôte Frusion de KotionTwin (ActionScript 1, compilé par tools/as1c.py).
 *
 * Sur Frutiparc, le jeu était chargé dans la fenêtre « Frusion » qui fournissait la classe
 * _global.frusion.gameclient.GameClient (connexion au serveur, disque de jeu, fruticard).
 * Cette classe n'est pas dans l'archive : elle est réécrite ici d'après la version compilée
 * retrouvée dans miniWave2/bumdum.swf, en mode « disque blanc » (version complète, sans
 * classement en ligne). Les emplacements de la fruticard (slots) et les objets gagnés sont
 * conservés dans un SharedObject local (stockage du navigateur via Ruffle).
 *
 * Paramètres (remplacés à la compilation par build.py, ou fournis en flashvars) :
 *   game  : SWF du jeu à charger (relatif à la base)
 *   id    : identifiant de sauvegarde (ex. fp-kaluga)
 *   sizes : tailles des fichiers annexes « nom:octets,nom:octets » (vérifiées par certains jeux)
 */

if (_root.game == undefined) _root.game = "%GAME%";
if (_root.id == undefined) _root.id = "%ID%";
if (_root.sizes == undefined) _root.sizes = "%SIZES%";

var kt_so = SharedObject.getLocal("kotiontwin_" + (_root.id == undefined ? "frusion" : _root.id), "/");
if (kt_so.data.slots == undefined) kt_so.data.slots = new Array();
if (kt_so.data.items == undefined) kt_so.data.items = new Object();
_global.kt_so = kt_so;

var kt_sizes = new Object();
if (_root.sizes != "") {
	var parts = _root.sizes.split(",");
	for (var i = 0; i < parts.length; i++) {
		var kv = parts[i].split(":");
		kt_sizes[kv[0]] = Number(kv[1]);
	}
}
_global.kt_sizes = kt_sizes;

if (_global.frusion == undefined) _global.frusion = new Object();
if (_global.frusion.gameclient == undefined) _global.frusion.gameclient = new Object();

_global.frusion.gameclient.GameClient = function() {
	this.slots = new Array();
	this.forceClose = false;
	this.forcePause = false;
	this.reseting = false;
	this.connected = false;
	this.gameRunning = false;
	this.debug = function() {};
};
var GC = _global.frusion.gameclient.GameClient;
GC.BLACK = 0;
GC.GREY = 1;
GC.WHITE = 2;
GC.RED = 3;

_global.frusion.gameclient.RankingResult = function(score, data, op, os, p, s, rn) {
	this.oldPos = op;
	this.oldScore = os;
	this.bestScorePos = p;
	this.bestScore = s;
	this.rankingName = rn;
	this.rankingScore = score;
	this.rankingData = data;
};

var P = GC.prototype;

// Disque blanc : version complète du jeu, sans limite de parties.
P.isColor = function(c) { return c == 2; };
P.isWhite = function() { return true; };
P.isBlack = function() { return false; };
P.isGrey = function() { return false; };
P.isGray = function() { return false; };
P.isRed = function() { return false; };
P.isChallengeDisc = function() { return false; };
P.getVersion = function() { return "KotionTwin Frusion 1.0"; };
P.getUser = function() { return "Joueur"; };

P.setDebugFunction = function(f) { this.debug = f; };
P.logError = function(code, message) {};
P.fatalError = function(msg, msgUsr) { this.finalize(); };
P.finalize = function() {};

P.getFileInfos = function(fileName) {
	var s = _global.kt_sizes[fileName];
	return { name: fileName, size: s };
};

// Les réponses du serveur arrivaient de façon asynchrone : on rappelle le jeu à l'image suivante.
P.kt_later = function(name) {
	var self = this;
	var id;
	id = setInterval(function() {
		clearInterval(id);
		self[name]();
	}, 30);
};

P.serviceConnect = function() {
	this.gameDisc = { discType: 2, gameId: _root.id, files: new Object(), width: Stage.width, height: Stage.height };
	// « Course du jour » (Burning Kiwi) : choisie chaque jour parmi les 6 circuits, ou imposée par flashvar.
	var day = Math.floor(new Date().getTime() / 86400000);
	this.dailyData = (_root.daily != undefined) ? _root.daily : "<daily trk=\"" + (day % 6) + "\" day=\"" + day + "\"/>";
	this.startTime = new Date();
	// copie des emplacements sauvegardés
	var saved = _global.kt_so.data.slots;
	this.slots = new Array();
	for (var k in saved) this.slots[k] = saved[k];
	this.connected = true;
	this.kt_later("onServiceConnect");
};

P.closeService = function() {
	this.connected = false;
	this.debug("closeService");
	// Sur Frutiparc la fenêtre du jeu se fermait : on relance le jeu depuis le début.
	if (_global.kt_game != undefined) loadMovieNum(_global.kt_game, 0);
};
P.forceCloseService = function() {
	if (!this.connected) this.closeService();
};

P.saveSlot = function(slotId, slot) {
	if (slot != undefined) this.slots[slotId] = slot;
	_global.kt_so.data.slots[slotId] = this.slots[slotId];
	_global.kt_so.flush();
};

P.startGame = function() {
	this.gameRunning = true;
	this.onStartGame();
};
P.endGame = function() {
	this.gameRunning = false;
	this.onEndGame();
};
P.giveItem = function(item) {
	_global.kt_so.data.items[item] = true;
	_global.kt_so.flush();
};
P.giveAccessory = function(item) {
	this.giveItem(item);
};
P.saveScore = function(score, data) {
	this.gameRunning = false;
	var best = _global.kt_so.data.best;
	if (best == undefined || score > best) {
		_global.kt_so.data.best = score;
		_global.kt_so.flush();
	}
	this.ranking = new _global.frusion.gameclient.RankingResult(score, data);
	this.onSaveScoreFruticard();
	this.onSaveScore();
};

// Rappels redéfinis par les jeux
P.onServiceConnect = function() {};
P.onPause = function() {};
P.onGameClose = function() {
	if (this.gameRunning) this.endGame();
	this.closeService();
};
P.onGameReset = function() {
	if (this.gameRunning && !this.isWhite()) {
		this.endGame();
		this.closeService();
	}
};
P.onStartGame = function() {};
P.onEndGame = function() {};
P.onSaveScoreFruticard = function() {};
P.onSaveScore = function() {};
P.onError = function() { this.onGameClose(); };

ASSetPropFlags(GC.prototype, null, 1);

// Chargement du jeu à la place de l'hôte (_global est conservé).
_global.kt_game = _root.game;
loadMovieNum(_root.game, 0);
