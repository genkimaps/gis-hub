

function load_sp_data(sp_data_str){
    console.log('Load codes: ' +sp_data_str)
    var sp_data = JSON.parse(sp_data_str)
    console.log(sp_data)
    /* Append each row using templates. Once loaded, set values using jQuery. */
    sp_data.forEach(function(item, i){

        // var selectSpCode = `<select id="sp_code${i}" class="sp_code form-control">
        //     <option value="" selected></option>
        //     <option value="${item.sp_code}" selected>${item.sp_code}</option>
        //     </select>`
        // Hidden input field for Select2 dropdown
        var selectSpCode = `<input type="text" id="sp_code${i}">`

        var selectAgeData = `<select id="age_data${i}" class="age_data form-control">
            <option value="" selected></option>
            <option value="True">True</option>
            <option value="False">False</option>
            </select>`
        
        var selectObsType = `<select id="obs_type${i}" class="obs_type form-control">
            <option value="" selected></option>
            <option value="Targeted">Targeted observation</option>
            <option value="Incidental">Incidental observation</option>
            <option value="Inferred">Inferred</option>
            </select>`

        console.log(item)
        var tbl_row = `<tr id="species${i}">`
              + '<td class="w60">' +selectSpCode+ '</td>'
              + '<td class="w15">' +selectAgeData+ '</td>'
              + '<td class="w15">' +selectObsType+ '</td>'
              + '</tr>';
        console.log(tbl_row)
        $('#ac_js_table').append(tbl_row)
        // Activate select2 on the sp code field
        $('#sp_code'+i).select2(ajax_spcodes)
        // Attach the select2 change detect event handler
        $('#sp_code'+i).on('select2:select', function (e) {
            var data = e.params.data;
            console.log('Select2 changed: ')
            console.log(data)
        });
        // Set values in row
        console.log('Set age_data '+item.age_data)
        $('#sp_code'+i).val(item.sp_code)
        $('#age_data'+i).val(item.age_data)
        // $('#species'+i).find('.age_data').val(item.age_data)
        console.log('Set obs_type '+item.obs_type)
        $('#obs_type'+i).val(item.obs_type)
        // $('#species'+i).find('.obs_type').val(item.obs_type)
        // Bind the change detect event
        $('#age_data'+i).on('change', function(){
            speciesTableChanged()
        })
        $('#obs_type'+i).on('change', function(){
            speciesTableChanged()
        })
        // $('#species'+i).find('.obs_type.age_data').on('change', function(){
        //     speciesTableChanged()
        // })
    })
}

function speciesTableChanged (){
    console.log('Change in ac_js_table')
    // Collect all the species code data, to string
    var sp_list = []
    $('#ac_js_table tr').each(function(i){
        // To get the species code and name from the select2 dropdown:
        // $('#sp_code0').select2('data')  returns an object like: 
        // {id: "629", text: "629 - EUBALAENA JAPONICA (NORTH PACIFIC RIGHT WHALE)"}
        var code = $(this).find('.sp_code').val()
        var age = $(this).find('.age_data').val()
        var obs = $(this).find('.obs_type').val()
        var sp = {sp_code: code, age_data: age, obs_type: obs}
        sp_list.push(sp)

    })
    var sp_string = JSON.stringify(sp_list)
    console.log(sp_string)
    $('#field-species_codes_js').val(sp_string)
}


$(document).ready(function() {
    console.log('Page loaded.')
    console.log('Activate species codes composite field on species_codes_js')
    // Get value from the text field itself
    // Enable this later once field is active, for now only test
    // var sp_data_str = $('#field-species_codes_js').val()
    var sp_data_str = "[{\"sp_code\": \"01C\", \"age_data\": \"False\", \"obs_type\": \"Inferred\"}]";

    load_sp_data(sp_data_str)
    // Activate change detection on table 
    // console.log('Activate change detection on table')
    // $('#ac_js_table tr').on('.age_data.obs_type', 'change', function() {
    //     speciesTableChanged()
    // })
})


// Code to activate Select2
console.log("Autocomplete JS for custom Species Code CKAN endpoint");
// Docs for older Select2 bundled with CKAN, version 3.5.3
// http://select2.github.io/select2/

var ajax_spcodes = {
    placeholder: "Species code, latin name, common name",
    minimumInputLength: 1,

    // initSelection populates the select box using the values in the linked element,
    // which is the hidden input tag containing the comma-separated list of values.
    // The hidden input tag has an id like id="field-my_field_name"
    // See initSelection in the Documentation section: http://select2.github.io/select2
    initSelection : function (element, callback) {
        var data = [];
        $(element.val().split(",")).each(function () {
            data.push({id: this, text: this});
        });
        callback(data);
    },

    // ajax function fetches results from a CKAN API url, using the characters
    // typed in the input box (when input is >= the minimumInputLength).
    ajax: {
        url: '/api/3/action/ac_species_code',
        dataType: 'json',
        data: function (term, page) {
            console.debug(term);
            return {
                q: term, // search term
            };
        },
        results: function (data) {
            var ac = []
            // CKAN API v3 returns results in a property called 'result' NOT resultS !!
            // Select2 requires that results are in an array of objects with
            // propeties 'id' and 'text'.  https://select2.org/data-sources/formats
            console.debug(data.result)
            data.result.forEach(function(match){
                ac.push({id: match.code, text: match.species_name})
            });
            return { results: ac };
        }
    }
}

// var field_name_spcodes = 'species_codes-0-sp_code'
// $(document).ready(function() {
//     console.log('Activate Select2 ajax on '+field_name_spcodes);
//     $('#field-'+field_name_spcodes).select2(ajax_spcodes);
// });

