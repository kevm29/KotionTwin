/*
 * KotionTwin — conteneur d'un client CaféJeux (remplace le client CaféJeux d'origine).
 * Crée le jeu dans un clip, fait tourner mt.Timer, la file de messages et game.main().
 * FlashVars : pid = 0 ou 1 (joueur de cette copie du jeu).
 */
class Main {

	static var game : Dynamic;

	static function main() {
		var root : flash.MovieClip = flash.Lib.current;
		var pid = Std.parseInt(Std.string(untyped root.pid));
		if( pid == null ) pid = 0;
		var mc = root.createEmptyMovieClip("game", 1);
		var cl = Type.resolveClass("Game");
		game = Type.createInstance(cl, [mc]);
		MMApi.init(game, pid);
		root.onEnterFrame = loop;
	}

	static function loop() {
		mt.Timer.update();
		MMApi.process();
		game.main();
	}
}
