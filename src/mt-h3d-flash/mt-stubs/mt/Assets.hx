package mt;
// Reconstitution KotionTwin de mt.Assets (absente de l'archive) : textures chargées depuis openfl.Assets.
class Assets {
	public static var USE_HALF_SIZE = false;
	static var cache : Map<String, h2d.Tile> = new Map();
	public static function getTile(url:String, ?retain:Bool=false) : Void->h2d.Tile {
		return function() {
			var t = cache.get(url);
			if( t == null ) {
				var bd = openfl.Assets.getBitmapData(url, false);
				t = bd == null ? h2d.Tile.fromColor(0xFFFF00FF, 4, 4) : h2d.Tile.fromFlashBitmap(bd, retain);
				cache.set(url, t);
			}
			return t;
		}
	}
	public static function getTileDeferred(url:String, worker:mt.Worker, onComplete:h2d.Tile->Void, ?retain:Bool=false) {
		var f = getTile(url, retain);
		var t : h2d.Tile = null;
		var task = worker.enqueue(new mt.Worker.WorkerTask(function() t = f()));
		task.onComplete = function() onComplete(t);
	}
}
