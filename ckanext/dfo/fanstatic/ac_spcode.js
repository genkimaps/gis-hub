
var spRowCount = 0
function load_sp_data(sp_data){
    
    /*
        This function is used when EDITING species codes in the GIS Hub dataset editing interface.
        It is loaded by ac_spcode_js.html.

        There are two use cases:
        1. load existing species codes from the dataset's metadata
        2. load a new blank species code from the template
        In both cases, the species code (containing data, or blank) is a table row,
        with a select2() drop-down element in the first column.

        This function append each row using templates. Once loaded, set values using jQuery.
        Ensure row count value only goes up, not down.  Initialize to 0, each time 
        this function is called, the new value for i will always be greater than the 
        last row in the table.  Add this value to existing Id (row count) 
    */
    console.log(`Species table has (up to) ${spRowCount} rows`)
    sp_data.forEach(function(item, i){

        spRowCount++
        i = spRowCount

        // Hidden input field for Select2 dropdown
        var selectSpCode = `<input type="text" id="sp_code${i}" class="sp_code" style="width: 300px;">`

        var selectAgeData = `<select id="age_data${i}" class="age_data form-control" style="width: 60px;">
            <option value="" selected></option>
            <option value="True">True</option>
            <option value="False">False</option>
            </select>`
        
        var selectObsType = `<select id="obs_type${i}" class="obs_type form-control" style="width: 180px;">
            <option value="" selected></option>
            <option value="Targeted">Targeted observation</option>
            <option value="Incidental">Incidental observation</option>
            <option value="Inferred">Inferred</option>
            </select>`
        
        var removeSpeciesBtn = `<div class="btn btn-danger" id="remove-species${i}" style="margin-left: 10px;">
            <i class="fa fa-minus" aria-hidden="true"></i>
            </div>`

        var tbl_row = `<tr id="species${i}">`
              + '<td>' +selectSpCode+ '</td>'
              + '<td>' +selectAgeData+ '</td>'
              + '<td>' +selectObsType+removeSpeciesBtn+ '</td>'
              + '</tr>';
        $('#ac_js_table').append(tbl_row)

        // Set values in row
        console.log(`Add data: row: ${i} code: ${item.sp_code} age: ${item.age_data} obs: ${item.obs_type}`)
        /* We must first set the value on the sp_code field, which is linked to the Select2 object
            When we activate .select2() on this input, it must have a value, or the initSelection() 
            function inside the select2() activation mechanism will not be called. See docs: 
            https://select2.github.io/select2/ "This function will only be called when 
            there is initial input to be processed."
        */
        $('#sp_code'+i).val(item.sp_code)

        // Activate select2 on the sp code field
        $('#sp_code'+i).select2(ajax_spcodes)
        $('#age_data'+i).val(item.age_data)
        $('#obs_type'+i).val(item.obs_type)
        /* Bind the change detect events. Although select2 has its own event handlers, 
           we can also use the generic jQuery .on('change') for select2  */
        $(`#sp_code${i}, #age_data${i}, #obs_type${i}`).on('change', function(){
            // console.log('Species data has changed')
            speciesTableChanged()
        })

        // Bind remove species button to parent <tr>
        $(`#remove-species${i}`).on('click', function(){
            // console.log('remove')
            $(`#species${i}`).remove()
            speciesTableChanged()
        })
    })
    
}

function speciesTableChanged (){
    // console.log('Change in ac_js_table')
    // Collect all the species code data, to string
    var sp_list = []
    $('#ac_js_table tr').each(function(i){
        // To get the species code and name from the select2 dropdown:
        // $('#sp_code0').select2('data')  returns an object like: 
        // {id: "629", text: "629 - EUBALAENA JAPONICA (NORTH PACIFIC RIGHT WHALE)"}
        var sp_data = $(this).find('.sp_code').select2('data')
        console.debug('Select2 contains: '+JSON.stringify(sp_data))
        var age = $(this).find('.age_data').val()
        var obs = $(this).find('.obs_type').val()
        var sp = {sp_code: sp_data.id, sp_name: sp_data.text, age_data: age, obs_type: obs}
        sp_list.push(sp)
    })
    var sp_string = JSON.stringify(sp_list)
    console.log('Species codes changed: ' +sp_string)
    $('#field-species_codes').val(sp_string)
}


$(document).ready(function() {
    console.log('Page loaded. Activating species codes field.')
    // Get value from the field data
    var sp_data_str = $('#field-species_codes').val()

    // Load default value if blank
    if (sp_data_str === ''){
        console.log('Using template (blank) sp code JSON')
        sp_data_str = "[{\"sp_code\": \"\", \"sp_name\": \"\", \"age_data\": \"\", \"obs_type\": \"\"}]"
    }

    console.log('Load codes: ' +sp_data_str)
    var sp_data = JSON.parse(sp_data_str)
    load_sp_data(sp_data)
})

// Add blank species row on click
$('#add-species').on('click', function() {
    var sp_blank = [{sp_data: '', sp_name: '', age_data: '', obs_type: ''}]
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
        console.debug('Initial value: ' + element.val())
        var data = {id: element.val(), text: element.val()};
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
