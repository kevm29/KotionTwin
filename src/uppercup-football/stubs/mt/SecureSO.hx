package mt;
// Bouchon KotionTwin : stockage local simple (SharedObject, sans chiffrement AES).
class SecureSO {
	var so : flash.net.SharedObject;
	public function new(o:{name:String, aesKey:String, aesIv:String}) {
		so = flash.net.SharedObject.getLocal("kt_" + o.name);
	}
	public function get(k:String) : String return Reflect.field(so.data, k);
	public function set(k:String, v:String) { Reflect.setField(so.data, k, v); try so.flush() catch(e:Dynamic) {} }
	public function deviceId() return "web";
}
