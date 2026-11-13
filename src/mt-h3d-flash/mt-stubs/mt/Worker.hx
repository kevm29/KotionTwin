package mt;
// Reconstitution KotionTwin : file de tâches exécutées une par image (à l'origine, threads/« workers »).
class WorkerTask {
	public var fn : Void->Void;
	public var onComplete : Void->Void;
	public var done(default,null) : Bool = false;
	public function new(fn:Void->Void) { this.fn = fn; }
	@:allow(mt.Worker) function run() {
		fn();
		done = true;
		if( onComplete != null ) onComplete();
	}
}

class Worker {
	var queue : Array<WorkerTask> = [];
	var running = false;
	public function new(?a:Dynamic) {}
	public function enqueue(t:WorkerTask) : WorkerTask {
		queue.push(t);
		if( !running ) { running = true; haxe.Timer.delay(next, 1); }
		return t;
	}
	function next() {
		var t = queue.shift();
		if( t == null ) { running = false; return; }
		t.run();
		haxe.Timer.delay(next, 1);
	}
	public function isEmpty() return queue.length == 0 && !running;
	public function dispose() { queue = []; }
	public function checkDone() {}
	public function stop() { queue = []; }
}
