// Point d'entrée KotionTwin (remplace l'ApplicationMain généré par l'outil OpenFL).
@:access(WebMain)
class KtMain {
	static function main() {
		var s = flash.Lib.current.stage;
		s.scaleMode = flash.display.StageScaleMode.NO_SCALE;
		s.align = flash.display.StageAlign.TOP_LEFT;
		new WebMain();
	}
}
