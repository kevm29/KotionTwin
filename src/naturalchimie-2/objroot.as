this.attachMovie("object", "smc", 1, {_x: 6, _y: 17});
function _set(s) {
	var infos = s.split(";");
	apply(this, infos);
}
function apply(mc, infos) {
	for (var mm in mc) {
		var m = mc[mm];
		if (typeof m == "movieclip") {
			if (m._name == "smc") {
				m.gotoAndStop(infos[0]);
				infos.shift();
				if (infos.length > 0)
					apply(m, infos);
			}
		}
	}
}
stop();
