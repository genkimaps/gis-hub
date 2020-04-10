console.log("Autocomplete for custom CKAN endpoints--JS loaded");

// Docs for older Select2 bundled with CKAN, version 3.5.3
// http://select2.github.io/select2/

var ac_url = '/api/3/action/ac_species_code'
var ajax_1line = {
//    multiple: true,
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
        url: ac_url,
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
                ac.push({id: match, text: match})
            });
            return { results: ac };
        }
    }
}

var field_name = 'sp_code'
$(document).ready(function() {
    console.log('Activate Select2 ajax on '+field_name);
    $('#field-'+field_name).select2(ajax_1line);
});
