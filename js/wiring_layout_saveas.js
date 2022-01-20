$('#zynthian_wiring_layout_saveas_script').click(
	function(){
		fname = prompt("Enter a name for the customization profile:", $("select[name='ZYNTHIAN_WIRING_LAYOUT_CUSTOM_PROFILE']").val())
		if (!fname){
			alert("You have to enter a valid name!");
		} else {
			$('#_command').val("SAVEAS")
			inputName = $("#zynthian_wiring_layout_saveas_fname")
			inputName.val(fname)
			inputName[0].form.submit();
		}
	}
);
