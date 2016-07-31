function courtchanged(event) {
    $('#id_courtroom option').slice(1).remove();
    $('#id_judge option').slice(1).remove();
    var court = $(event.target).val();
    if (court) {
	$.get('/psj/court/' + court + '/', null, function(response) {
	    $('#id_courtroom option')
		.after($(response).filter('#courtroom').children());
	    $('#id_courtroom option:first').s(true);
	    $('#id_judge option')
		.after($(response).filter('#judge').children());
	    $('#id_judge option:first').s(true);
	});
    }
}
$(function() {
    $('#id_court').change(courtchanged);
});
