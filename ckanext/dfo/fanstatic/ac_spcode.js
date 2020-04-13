
//var sp_code_str
function load_sp_data(sp_data_str){
    console.log('Load codes: ' +sp_data_str)
    var sp_data = JSON.parse(sp_data_str)
    console.log(sp_data)
    sp_data.forEach(function(item){
        console.log(item)
        var tbl_row = '<tr>'
              + '<td>' +item.sp_code+ '</td>'
              + '<td>' +item.age_data+ '</td>'
              + '<td>' +item.obs_type+ '</td>'
              + '</tr>';
        console.log(tbl_row)
        $('#ac_js_table').append(tbl_row)
    })
}


$(document).ready(function() {
    console.log('Activate species codes composite field on species_codes_js')
    // Get value from the text field itself
    var sp_data_str = $('#field-species_codes_js').val()

    load_sp_data(sp_data_str)
})
