function changeMixerValue(ctrl, val){
	console.log("Audio Mixer Set: " + ctrl + " = " + val)

	var socketMessage = {
		"handler_name": "AudioConfigMessageHandler",
		"data": 'UPDATE_AUDIO_MIXER/' + ctrl + "/" + val
	};
	window.zynthianSocket.send(JSON.stringify(socketMessage));

/*
	$.post("hw-audio-mixer/" + ctrl + "/" + val,
		null,
		function(data, status) {
			if (status=="success") {
				if (data && "errors" in data) {
					console.log("Audio Mixer Error: " + data["errors"])
				}
			} else {
				console.log("Audio Mixer Response: " + status)
			}
		}
	);
*/
}

$(document).ready(function () {
	$("input[data-provide='slider']").on('change',function(ev) {
		var ctrl = $(ev.target).attr('id')
		var val = $(ev.target).val()
		if (ctrl.substr(0,26)=="ZYNTHIAN_CONTROLLER_VALUE_") ctrl = ctrl.substr(26)
			changeMixerValue(ctrl, val);
	});
	$("input[data-provide='checkbox']").on('change',function(ev) {
		var ctrl = $(ev.target).attr('id')
		var val = $(ev.target).val()
		if (!$(ev.target)[0].checked) val="off";
		if (ctrl.substr(0,26)=="ZYNTHIAN_CONTROLLER_VALUE_") ctrl = ctrl.substr(26)
			changeMixerValue(ctrl, val);
	});
	$("select").on('change',function(ev) {
		var ctrl = $(ev.target).attr('id')
		var val = $(ev.target).val()
		if (ctrl){
		    if (ctrl.substr(0,26)=="ZYNTHIAN_CONTROLLER_VALUE_")
		        ctrl = ctrl.substr(26)
		    changeMixerValue(ctrl, val);
		}
	});
});
