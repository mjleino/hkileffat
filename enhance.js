$(document).ready(function() {
	// let's hide shows that have already started
	var now = new Date();
	var h = now.getHours();
	var m = now.getMinutes();
	var $last = $("tr").last();
	if ($last.data("showtimeHour") > h 
			|| ( $last.data("showtimeHour") == h && $last.data("showtimeMinute") >= m) ) {
		// we hide stuff only if not all will be hidden
		$("tr").each(function(i, el) {
			var $el = $(el);
			if ($el.data("showtimeHour") < h || 
					($el.data("showtimeHour") == h && $el.data("showtimeMinute") < m)) {
				$el.hide();
			}
		});
	}
});