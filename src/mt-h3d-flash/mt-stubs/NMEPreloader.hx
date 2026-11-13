// Bouchon KotionTwin : préchargeur OpenFL (inutile, tout est intégré au SWF).
class NMEPreloader extends flash.display.Sprite {
	var outline : flash.display.Sprite;
	var progress : flash.display.Sprite;
	public function new() {
		super();
		outline = new flash.display.Sprite(); addChild(outline);
		progress = new flash.display.Sprite(); addChild(progress);
	}
	public function getBackgroundColor() return 0;
	public function getHeight() return flash.Lib.current.stage.stageHeight;
	public function getWidth() return flash.Lib.current.stage.stageWidth;
	public function onInit() {}
	public function onLoaded() { dispatchEvent(new flash.events.Event(flash.events.Event.COMPLETE)); }
	public function onUpdate(bytesLoaded:Int, bytesTotal:Int) {}
}
