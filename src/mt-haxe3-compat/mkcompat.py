# Génère la couche de compatibilité (API 2014 de la bibliothèque Motion Twin) pour Uppercup.
import os, re, sys
L = sys.argv[1]   # libs-haxe3
O = sys.argv[2]   # dossier de sortie
def rd(p): return open(os.path.join(L, p), encoding='latin-1').read()
def wr(p, s):
    p = os.path.join(O, p); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='latin-1').write(s)
def sub(s, a, b, count=1):
    if a not in s: raise SystemExit('motif absent: ' + a[:60])
    return s.replace(a, b, count)

# Cooldown : constructeur sans fps, set/hasSet/get/getFloat en images, update(?dt)
s = rd('mt/Cooldown.hx')
s = sub(s, 'public function new(fps:Float) {', 'public function new(?fps:Float=30) {')
s = sub(s, 'public function update(dt:Float) {', 'public function update(?dt:Float=1.0) {')
s = s.rstrip()[:-1] + '''
	// --- API 2014 (KotionTwin) ---
	public inline function set(k:String, frames:Float, ?allowLower:Bool=true) setF(k, frames, allowLower);
	public inline function hasSet(k:String, frames:Float) return hasSetF(k, frames);
	public inline function get(k:String) : Int return Std.int(getF(k));
	public inline function getFloat(k:String) : Float return getF(k);
}
'''
wr('mt/Cooldown.hx', s)

# Delayer : new(?fps), add(cb, ms), addFrame, update(?dt)
s = rd('mt/Delayer.hx')
s = sub(s, 'public function new(fps:Float) {', 'public function new(?fps:Float=30) {')
s = sub(s, 'public function update(dt:Float) {', 'public function update(?dt:Float=1.0) {')
s = s.rstrip()[:-1] + '''
	// --- API 2014 (KotionTwin) ---
	// add(cb, ms) (2014) ou add(id, cb, ms) (2015)
	public function add(a:Dynamic, b:Dynamic, ?c:Dynamic) {
		if( Std.is(a, String) || a == null && Reflect.isFunction(b) ) addMs(a, b, c);
		else addMs(null, a, b);
	}
	public function addFrame(cb:Void->Void, frames:Float) addF(cb, frames);
	public function addFrameBased(cb:Void->Void, frames:Float) addF(cb, frames);
}
'''
wr('mt/Delayer.hx', s)

# Tweenie : new(?fps), create(...) = createMs, update(?dt)
s = rd('mt/deepnight/Tweenie.hx')
s = sub(s, 'public function new(fps:Float) {', 'public function new(?fps:Float=30) {')
s = sub(s, '	public macro function createMs(', '''	public macro function create(ethis:Expr, field:ExprOf<Dynamic>, toExpr:ExprOf<Float>, ?tp:ExprOf<TType>, ?ms:ExprOf<Float>) {
		return buildCreateExpr(ethis, field, toExpr, tp, ms);
	}

	public macro function createMs(''')
s = sub(s, '	public function chainMs(', '''	// chain(to, ?ease, ?ms) (2015)
	public function chain(to:Float, ?a:Dynamic, ?b:Dynamic) {
		return if( a != null && Reflect.isEnumValue(a) ) chainMs(to, a, b) else chainMs(to, null, a);
	}

	public function chainMs(''')
wr('mt/deepnight/Tweenie.hx', s)

# Lib.shuffle (ancienne API : renvoie une copie mélangée)
s = rd('mt/deepnight/Lib.hx')
s = sub(s, '	public static function shuffleArray<T>(', '''	public static function shuffle<T>(arr:Array<T>, randFunc:Int->Int) : Array<T> {
		var a = arr.copy();
		shuffleArray(a, randFunc);
		return a;
	}

	public static function shuffleArray<T>(''')
wr('mt/deepnight/Lib.hx', s)
print('ok')

# mui : surcharges onWatchChange non typées (refusées par Haxe 3.4)
for f, old in [('Check.hx','override function onWatchChange(v:Bool)'),('Check.hx','override function onWatchChange(v)'),('Label.hx','override function onWatchChange(v)'),('TextInput.hx','override function onWatchChange(v)')]:
    p = 'mt/deepnight/mui/' + f
    s = open(os.path.join(O, p), encoding='latin-1').read() if os.path.exists(os.path.join(O, p)) else rd(p)
    if old in s:
        s = s.replace(old, 'override function onWatchChange(v:Dynamic)')
    wr(p, s)

# Processus 2014 (deprecated) dans le paquet mt.deepnight
for f in ['Process', 'FProcess', 'TinyProcess']:
    s = rd('mt/deepnight/deprecated/%s.hx' % f).replace('package mt.deepnight.deprecated;', 'package mt.deepnight;')
    wr('mt/deepnight/%s.hx' % f, s)

# Cinematic : new(?fps), update(?dt)
s = rd('mt/deepnight/Cinematic.hx')
s = re.sub(r'public function new\(\s*fps\s*:\s*(Int|Float)\s*\)', r'public function new(?fps:\1=30)', s)
s = re.sub(r'public function update\(\s*dt\s*:\s*Float\s*\)', 'public function update(?dt:Float=1.0)', s)
wr('mt/deepnight/Cinematic.hx', s)
print('ok2')

# BSprite.setCenter (ancien nom de setCenterRatio)
s = rd('mt/deepnight/slb/BSprite.hx')
s = sub(s, '	public inline function setCenterRatio(', '	public inline function setCenter(xr:Float, yr:Float) setCenterRatio(xr, yr);\n\n	public inline function setCenterRatio(')
wr('mt/deepnight/slb/BSprite.hx', s)

# FParticle : gestion globale 2014 (ALL, LIMIT, update(), clearAll()), bounce, destroy(), reset() public
s = rd('mt/deepnight/FParticle.hx')
s = sub(s, '	public static var DEFAULT_BOUNDS', '''	public static var ALL : Array<FParticle> = [];
	public static var LIMIT : Int = 9999;
	public var bounce(get,set) : Float;
	inline function get_bounce() return bounceMul;
	inline function set_bounce(v:Float) return bounceMul = v;

	public static var DEFAULT_BOUNDS''')
s = sub(s, '		//ALL.push(this);', '''		ALL.push(this);
		if( ALL.length > LIMIT )
			ALL[0].destroy();''')
s = sub(s, '	function reset(?x=0., ?y=0.) {', '	public function reset(?x=0., ?y=0.) {')
s = sub(s, '	public function update() {', '''	public function destroy() {
		ALL.remove(this);
		kill();
		if( parent!=null ) parent.removeChild(this);
	}

	public static function clearAll() {
		for( p in ALL.copy() ) p.destroy();
		ALL = [];
	}

	public static function update() {
		for( p in ALL.copy() ) {
			p.updateOne();
			if( p.killed ) p.destroy();
		}
	}

	public function updateOne() {''')
wr('mt/deepnight/FParticle.hx', s)
print('ok3')

# mt.Process : le constructeur n'appelle plus une méthode init() publique (conflit avec Room.init de Monster Hotel)
s = rd('mt/Process.hx')
s = sub(s, '	public function new(?parent : Process) {\n		init();', '	public function new(?parent : Process) {\n		initProcess();')
s = sub(s, '	public function init(){', '	function initProcess(){')
wr('mt/Process.hx', s)
print('ok4')
