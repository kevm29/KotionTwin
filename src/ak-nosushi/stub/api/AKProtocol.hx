package api;

enum GameMode {
	GM_PROGRESSION;
	GM_LEAGUE;
}

/** Entier « sécurisé » fourni par l'hôte (méthodes get_/add_/set_). */
abstract AKConst(Dynamic) {
	public inline function get() : Int return this.get_();
	public inline function add( c : AKConst ) : AKConst return this.add_(c);
	public inline function set( c : AKConst ) : AKConst return this.set_(c);
}

abstract SecureInGamePrizeTokens(Dynamic) {
	public var amount(get, never) : AKConst;
	public var score(get, never) : AKConst;
	public var frame(get, never) : Int;
	inline function get_amount() : AKConst return this.amount_;
	inline function get_score() : AKConst return this.score_;
	inline function get_frame() : Int return this.frame_;
}
