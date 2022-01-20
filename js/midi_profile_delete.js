$('#zynthian_midi_profile_delete_script').click(
	function(){
		if (confirm('Do you really want to delete the selected MIDI profile?')){
				buttonElem = $('#zynthian_midi_profile_delete_script');
				buttonElem.val("1");
				buttonElem[0].form.submit();
		}
	}
);
