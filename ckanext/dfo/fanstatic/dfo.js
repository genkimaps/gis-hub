$(document).ready(function() {
    $('.start-download').click(function() {
        $('.modal').modal('hide');
        var a = $('<a>', {
            href: $(this).data('download')
        }).appendTo('body');
        a[0].click();
        a.remove();
    });
});
