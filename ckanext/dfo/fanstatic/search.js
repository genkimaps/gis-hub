$().ready(function(){
   $('input[name="range_picker"]').daterangepicker({
       "locale": {
           "format": "YYYY-MM-DD",
           "separator": " - ",
           "applyLabel": "Apply",
           "cancelLabel": "Clear",
           "fromLabel": "From",
           "toLabel": "To",
           "weekLabel": "W",
           "daysOfWeek": [
               "Su",
               "Mo",
               "Tu",
               "We",
               "Th",
               "Fr",
               "Sa"
           ],
           "monthNames": [
               "January",
               "February",
               "March",
               "April",
               "May",
               "June",
               "July",
               "August",
               "September",
               "October",
               "November",
               "December"
           ],
           "firstDay": 1
       },
       "showCustomRangeLabel": false,
       "autoUpdateInput": false,
       "alwaysShowCalendars": true,
       "ranges": {
           'Summer': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
           'Autumn': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
           'Winter': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
           'Spring': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
           'Last 7 Days': [moment().subtract(6, 'days'), moment()],
           'Last 30 Days': [moment().subtract(29, 'days'), moment()],
        }
    }).on('apply.daterangepicker', function(ev, picker) {
        $(this).val(picker.startDate.format('YYYY-MM-DD') + ' - ' + picker.endDate.format('YYYY-MM-DD'));
    }).on('cancel.daterangepicker', function(ev, picker) {
        $(this).val('');
    });
});