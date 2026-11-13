package mt;
// Reconstitution KotionTwin de mt.Timer (absent de l'archive) : facteur de temps « tmod ».
class Timer {
	public static var wantedFps = 40.0;
	public static var maxDeltaTime = 0.5;
	public static var oldTime = haxe.Timer.stamp();
	public static var tmod_factor = 0.95;
	public static var calc_tmod = 1.0;
	public static var tmod = 1.0;
	public static var deltaT = 1.0;
	public static function update() {
		var newTime = haxe.Timer.stamp();
		deltaT = newTime - oldTime;
		oldTime = newTime;
		if (deltaT < maxDeltaTime)
			calc_tmod = calc_tmod * tmod_factor + (1 - tmod_factor) * deltaT * wantedFps;
		else
			deltaT = 1 / wantedFps;
		tmod = calc_tmod;
	}
	public static function fps() { return wantedFps / tmod; }
}
