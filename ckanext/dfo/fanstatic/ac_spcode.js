var field_name = 'species_codes_js'


function load_sp_data(){
    console.log(sp_data_js)
    var sp_data = JSON.parse(sp_data_str)
    sp_data.forEach(function(value){
        var tbl_row = `<tr>
              <td>${sp_data.sp_code}</td>
              <td>${sp_data.age_data}</td>
              <td>${sp_data.obs_type}</td>
            </tr>`
        console.log(tbl_row)
        $('#ac_js_table').append(tbl_row)
    })
})


}

$(document).ready(function() {
    console.log('Activate species codes composite field on '+field_name)
    load_sp_data()
})
