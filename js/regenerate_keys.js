
$('button#REGENERATE_KEYS').click(
	function(){
		$('input#_command').val("REGENERATE_KEYS");
		$('form#config_block_form').submit()
	}
);
