$(function() {
    function submit_mainform() {
	$('#id_next').val(this);
	$('#id_mainform').submit();
	return false;
    }
    function mainpage_reset_onclick() {
	if ($('.itr').length ||
	    $('#id_title').val() ||
	    $('#id_note').val() ||
	    $('#id_internal_note').val()) {
	    return confirm('Skutečně chcete smazat pohledávku?');
	} else {
	    return true;
	}
    }
    function mainpage_load_button_onclick() {
	if ($('#id_load').val()) {
	    if ($('.itr').length ||
		$('#id_title').val() ||
		$('#id_note').val() ||
		$('#id_internal_note').val()) {
		return confirm('Skutečně chcete načíst jinou pohledávku?');
	    } else {
		return true;
	    }
	} else {
	    alert('Nejprve vyberte soubor pro načtení');
	    return false;
	}
    }
    function mainpage_load_onchange() {
	$('#id_load_button').click();
	return true;
    }
    function debitform_updatemodels() {
	if ($('[value=fixed]').c()) {
	    class_enable($('#id_fa'));
	    if (!$('#id_fixed_amount').val()) {
		$('#id_fixed_currency_0').val('CZK');
	    }
	    $('#id_principal_currency_0').val('CZK');
	    class_disable($('#id_pr1, #id_pr2'));
	    $('#id_principal_debit').val(0);
	} else {
	    $('#id_fixed_currency_0').val('CZK');
	    class_disable($('#id_fa'));
	    class_enable($('#id_pr1, #id_pr2'));
	    if ($('#id_principal_debit').val() != '0') {
		$('#id_principal_amount').d(true).r();
		$('#id_principal_currency_0').val('CZK').d(true);
	    } else {
		$('#id_principal_currency_0').d(false);
		if (!$('#id_principal_amount').val()) {
		    $('#id_principal_currency_0').val('CZK');
		}
	    }
	}
	$('.currsel').change();
	if ($('[value=per_annum]').c()) {
	    class_enable($('#id_pa'));
	} else {
	    class_disable($('#id_pa'));
	}
	if ($('[value=per_mensem]').c()) {
	    class_enable($('#id_pm'));
	} else {
	    class_disable($('#id_pm'));
	}
	if ($('[value=per_diem]').c()) {
	    class_enable($('#id_pd'));
	} else {
	    class_disable($('#id_pd'));
	}
	if ($('[value=cust1]').c()) {
	    class_enable($('#id_cust1'));
	} else {
	    class_disable($('#id_cust1'));
	}
	if ($('[value=cust2]').c()) {
	    class_enable($('#id_cust2'));
	} else {
	    class_disable($('#id_cust2'));
	}
	if ($('[value=cust3]').c()) {
	    class_enable($('#id_cust3'));
	} else {
	    class_disable($('#id_cust3'));
	}
	if ($('[value=cust5]').c()) {
	    class_enable($('#id_cust5'));
	} else {
	    class_disable($('#id_cust5'));
	}
	if ($('[value=cust6]').c()) {
	    class_enable($('#id_cust6'));
	} else {
	    class_disable($('#id_cust6'));
	}
	if ($('[value=cust4]').c()) {
	    class_enable($('#id_cust4'));
	} else {
	    class_disable($('#id_cust4'));
	}
	return true;
    }
    function credit_reorder() {
	var $t = $(this);
	var $s = $('div.debord select');
	var ci = $s.index($t);
	var nv = $t.val();
	var pv = $t.data('pv');
	var cd;
	if ($s.filter('[value=' + nv + ']').get(0) == this) {
	    cd = 1;
	} else {
	    cd = -1;
	}
	for (;;) {
	    $t.data('pv', $t.val());
	    if (pv == nv) {
		return true;
	    }
	    ci += cd;
	    $t = $s.eq(ci);
	    $t.val(pv);
	    pv = $t.data('pv');
	}
    }
    function fxform_updatefields() {
	$('.curr_from').text($('#id_currency_from').val().toUpperCase());
	$('.curr_to').text($('#id_currency_to').val().toUpperCase());
	return true;
    }
    if ($('#id_mainform').length) {
	$('#id_next').r();
	$('#id_reset').click(mainpage_reset_onclick);
	$('#id_load_button').click(mainpage_load_button_onclick);
	$('#id_load').change(mainpage_load_onchange);
	$('#id_mainform a').click(submit_mainform);
	$('#id_rounding').change(function () { $('#id_mainform').submit(); });
    }
    if ($('#id_debitform').length) {
	if ($('#id_lock_fixed').val()) {
	    $('.immune').removeClass('immune');
	    $('[name=model]').slice(1).d(true);
	}
	$('[name=model], #id_principal_debit').change(debitform_updatemodels)
	    .first().change();
    }
    if ($('#id_creditform').length) {
	$dl = $('div.debord select').each(
	    function() { $(this).data('pv', $(this).val()); } )
	    .change(credit_reorder);
    }
    if ($('#id_fxrateform').length) {
	$('#id_currency_from, #id_currency_to')
	    .on('change keyup', fxform_updatefields).first().change();
    }
});
