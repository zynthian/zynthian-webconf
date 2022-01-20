$('#zynthian_midi_profile_saveas_script').click(
	function(){
		fname = prompt("Enter a name for the new MIDI profile:","")
		if (!fname){
			alert("You have to enter a valid name!");
		} else {
			inputName = $("#zynthian_midi_profile_saveas_fname")
			inputName.val(fname)
			inputName[0].form.submit();
		}
	}
);
