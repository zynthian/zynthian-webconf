$('#zynthian_midi_profile_delete_script').click(
	function(){
		if (confirm('Are you sure?')){
				buttonElem = $('#zynthian_midi_profile_delete_script');
				buttonElem.val("1");
				buttonElem[0].form.submit();
		}
	}
);
