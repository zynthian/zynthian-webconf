$('#zynthian_midi_profile_new_script').click(
	function(){
		inputName = $('#zynthian_midi_profile_new_script_name');
		if (!inputName.val()){
			alert('Please enter a name for the new profile!');
		} else {
			inputName[0].form.submit();
		}
	}
);
