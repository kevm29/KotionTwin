package mt.device;
enum GameCenterService { GooglePlayGames; AppleGameCenter; }
class GameCenter {
	public static function isAvailable() return false;
	public static function isLogged() return false;
	public static function service() : GameCenterService return null;
	public static function name() : String return "";
	public static function connect(?cb:Bool->Void) {}
	public static function showAchievements() {}
}
