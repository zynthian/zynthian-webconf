$('#zynthian_wiring_layout_delete_script').click(
	function(){
		if (confirm('Do you really want to delete the selected customization profile?')){
				$('#_command').val("DELETE")
				buttonElem = $('#zynthian_wiring_layout_delete_script');
				buttonElem.val("1");
				buttonElem[0].form.submit();
		}
	}
);
