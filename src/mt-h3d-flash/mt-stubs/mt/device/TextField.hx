package mt.device;
// Reconstitution KotionTwin : champ de saisie natif (au-dessus de la scène Stage3D) via un TextField Flash.
enum TextFieldType { TF_Text; TF_TextNoAutoCorrect; TF_Number; TF_Email; TF_Password; }
enum TextFieldAction { ACT_Done; ACT_Go; ACT_Next; ACT_Search; ACT_Send; ACT_Default; }

class TextField {
	var tf : flash.text.TextField;
	var fmt : flash.text.TextFormat;
	public var text(get,set) : String;
	public var textColor(default,set) : Int;
	public var maxLength(get,set) : Int;
	public var x(get,set) : Float;
	public var y(get,set) : Float;
	public var width(get,set) : Float;
	public var height(get,set) : Float;
	public var textSize(default,set) : Float;
	public var type : TextFieldType;
	public var actionType : TextFieldAction;
	public dynamic function onTextChanged(s:String) {}
	public dynamic function onFocusChanged(v:Bool) {}
	public dynamic function onAction() {}

	public function new() {
		tf = new flash.text.TextField();
		tf.type = flash.text.TextFieldType.INPUT;
		fmt = new flash.text.TextFormat("_sans", 24, 0xFFFFFF, true);
		tf.defaultTextFormat = fmt;
		tf.width = 200; tf.height = 30;
		flash.Lib.current.stage.addChild(tf);
		tf.addEventListener(flash.events.Event.CHANGE, function(_) onTextChanged(tf.text));
		tf.addEventListener(flash.events.FocusEvent.FOCUS_IN, function(_) onFocusChanged(true));
		tf.addEventListener(flash.events.FocusEvent.FOCUS_OUT, function(_) onFocusChanged(false));
		tf.addEventListener(flash.events.KeyboardEvent.KEY_DOWN, function(e:flash.events.KeyboardEvent) if( e.keyCode == 13 ) onAction());
	}
	function get_text() return tf.text;
	function set_text(v:String) { tf.text = v == null ? "" : v; return v; }
	function set_textColor(v:Int) { fmt.color = v & 0xFFFFFF; apply(); return textColor = v; }
	function set_textSize(v:Float) { fmt.size = Std.int(v); apply(); return textSize = v; }
	function apply() { tf.defaultTextFormat = fmt; tf.setTextFormat(fmt); }
	function get_maxLength() return tf.maxChars;
	function set_maxLength(v:Int) return tf.maxChars = v;
	function get_x() return tf.x; function set_x(v:Float) return tf.x = v;
	function get_y() return tf.y; function set_y(v:Float) return tf.y = v;
	function get_width() return tf.width; function set_width(v:Float) return tf.width = v;
	function get_height() return tf.height; function set_height(v:Float) return tf.height = v;
	public function focus() flash.Lib.current.stage.focus = tf;
	public function destroy() { if( tf.parent != null ) tf.parent.removeChild(tf); }
}
