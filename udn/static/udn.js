$(function() {
    function bbMouseEnter() {
	$(this).children('img').first().attr('src', '/static/bbr.svg');
    }
    function bbMouseLeave() {
	$(this).children('img').first().attr('src', '/static/bb.svg');
    }
    function bMouseEnter() {
	$(this).children('img').first().attr('src', '/static/br.svg');
    }
    function bMouseLeave() {
	$(this).children('img').first().attr('src', '/static/b.svg');
    }
    function fMouseEnter() {
	$(this).children('img').first().attr('src', '/static/fr.svg');
    }
    function fMouseLeave() {
	$(this).children('img').first().attr('src', '/static/f.svg');
    }
    function ffMouseEnter() {
	$(this).children('img').first().attr('src', '/static/ffr.svg');
    }
    function ffMouseLeave() {
	$(this).children('img').first().attr('src', '/static/ff.svg');
    }
    var pl_bb = new Image();
    pl_bb.src = '/static/bbr.svg';
    var pl_b = new Image();
    pl_b.src = '/static/br.svg';
    var pl_f = new Image();
    pl_f.src = '/static/fr.svg';
    var pl_ff = new Image();
    pl_ff.src = '/static/ffr.svg';
    $('a:has(img.navbb)').hover(bbMouseEnter, bbMouseLeave);
    $('a:has(img.navb)').hover(bMouseEnter, bMouseLeave);
    $('a:has(img.navf)').hover(fMouseEnter, fMouseLeave);
    $('a:has(img.navff)').hover(ffMouseEnter, ffMouseLeave);
});
