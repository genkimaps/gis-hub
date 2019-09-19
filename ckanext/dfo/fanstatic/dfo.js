$(document).ready(function() {
    $('.start-download').click(function() {
        $('.modal').modal('hide');
        var a = $('<a>', {
            href: $(this).data('download')
        }).appendTo('body');
        a[0].click();
        a.remove();
    });

    $('.section-collapse').click(function() {
        $(this).toggleClass('fa-plus-square fa-minus-square');
        $(this).closest('.additional-info').find('section-data').toggleFade();
    });
});
