

function load_sp_data(sp_data){
    
    /* Append each row using templates. Once loaded, set values using jQuery. */

    // TODO: add to existing Id (row count)
    var spRowCount = $('#ac_js_table tr').length
    console.log(`Species table has ${spRowCount} rows`)
    sp_data.forEach(function(item, i){

        i = i + spRowCount

        // Hidden input field for Select2 dropdown
        var selectSpCode = `<input type="text" id="sp_code${i}" class="sp_code" style="width: 280px;">`

        var selectAgeData = `<select id="age_data${i}" class="age_data form-control" style="width: 100px;">
            <option value="" selected></option>
            <option value="True">True</option>
            <option value="False">False</option>
            </select>`
        
        var selectObsType = `<select id="obs_type${i}" class="obs_type form-control" style="width: 150px;">
            <option value="" selected></option>
            <option value="Targeted">Targeted observation</option>
            <option value="Incidental">Incidental observation</option>
            <option value="Inferred">Inferred</option>
            </select>`
        
        var removeSpeciesBtn = `<div class="btn btn-danger" id="remove-species${i}">
            <i class="fa fa-minus" aria-hidden="true"></i>
            </div>`

        var tbl_row = `<tr id="species${i}">`
              + '<td>' +selectSpCode+ '</td>'
              + '<td>' +selectAgeData+ '</td>'
              + '<td>' +selectObsType+removeSpeciesBtn+ '</td>'
              + '</tr>';
        $('#ac_js_table').append(tbl_row)

        // Set values in row
        console.log(`Set data: code: ${item.sp_code} age: ${item.age_data} obs: ${item.obs_type}`)
        /* We must first set the value on the sp_code field, which is linked to the Select2 object
            When we activate .select2() on this input, it must have a value, or the initSelection() 
            function inside the select2() activation mechanism will not be called. See docs: 
            https://select2.github.io/select2/ "This function will only be called when 
            there is initial input to be processed."
        */
        $('#sp_code'+i).val(item.sp_code)

        // Activate select2 on the sp code field
        $('#sp_code'+i).select2(ajax_spcodes)
        
        // Attach the select2 change detect event handler, 
        // $('#sp_code'+i).on('change', function (e) {
        //     console.log('Select2 for species has changed')
        //     speciesTableChanged()
        // });
        
        $('#age_data'+i).val(item.age_data)
        $('#obs_type'+i).val(item.obs_type)
        /* Bind the change detect events. Although select2 has its own event handlers, 
           we can also use the generic jQuery .on('change') for select2  */
        $(`#sp_code${i}, #age_data${i}, #obs_type${i}`).on('change', function(){
            console.log('Species data has changed')
            speciesTableChanged()
        })

        // Bind remove species button to parent <tr>
        $(`#remove-species${i}`).on('click', function(){
            console.log('remove')
            $(`#species${i}`).remove()
            speciesTableChanged()
        })
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
        var sp_data = $(this).find('.sp_code').select2('data')
        console.log('Select2 has: '+JSON.stringify(sp_data))
        // var code = sp_data.id
        var age = $(this).find('.age_data').val()
        var obs = $(this).find('.obs_type').val()
        var sp = {sp_code: sp_data.id, age_data: age, obs_type: obs}
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

    console.log('Load codes: ' +sp_data_str)
    var sp_data = JSON.parse(sp_data_str)
    console.log(sp_data)

    load_sp_data(sp_data)
})

// Add blank species row on click
$('#add-species').on('click', function() {
    var sp_blank = [{sp_data: '', age_data: '', obs_type: ''}]
    load_sp_data(sp_blank)
})


// Code to activate Select2
console.log("Autocomplete JS for custom Species Code CKAN endpoint");
// Docs for older Select2 bundled with CKAN, version 3.5.3
// http://select2.github.io/select2/

var initVal
var ajax_spcodes = {
    placeholder: "Species code, latin name, common name",
    minimumInputLength: 1,

    /* initSelection populates the select box using the values in the linked element,
     which is the hidden input tag containing the comma-separated list of values.
     The hidden input tag has an id like id="field-my_field_name"
     See initSelection in the Documentation section: http://select2.github.io/select2
     Here we use the form of initSelection() for single select elements. */
    initSelection : function (element, callback) {
        initVal = element
        console.log('Initial value: ' + element.val())
        var data = {id: element.val(), text: element.val()};
        // var data = [];
        // $(element.val().split(",")).each(function () {
        //     data.push({id: this, text: this});
        // });
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



