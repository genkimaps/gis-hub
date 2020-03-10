
// Only after document loaded
$(function() {

    console.log('doc ready in autocomp')

    // Configure species autocomplete
    $('#ac_selector').select2({
//        console.log('Applying select2 to elements')
        minimumInputLength: 3,
        // https://github.com/harvesthq/chosen/issues/1081#issuecomment-15088027
        search_contains: true,
        ajax: {
            url: 'https://www.gis-hub.ca/api/3/action/tag_autocomplete?',
            delay: 250,
            type: "GET",
            // Use json data
            dataType: 'json',
            contentType: "application/json; charset=utf-8",
            data: function (params) {
                var querydata = {
                    query: params.term,
                    vocabulary_id: 'weather'
                    // Removed from URL: vocabulary_id=weather
                }
                param_str = $.param(querydata)
                console.log(param_str)
                // Try to stringify for URL-encoded format
                url_params = url + param_str
                console.log(url_params)
                return url_params
//                return JSON.stringify(query)

            },
            processResults: function (data) {
                console.log('Result: ')
                console.log(data)
                var res = data.items.map(function (item) {
                    return {id: item.id, text: item.name};
                });
                return {
                    results: res
                }
            }
        },
    })

    // Add species to list when selected
    $('#species_selector').on('select2:select', function (e) {
        var data = e.params.data
        console.log(data)
        var sp = $('#species_selector').val()
        console.log('Adding ' +sp)
        addSpecies(data.id, data.text)
    })

    // Remove when X clicked
    $('#species_enabled').on('click', '.sp-remove', function(){
        var id = $(this).parent().attr('id')
        console.log('Removing ' +id)
        $( '#'+id ).remove()
    })

    // Get all the enabled species ids and save
    $('#saveSpeciesList').click(function() {
        var id_list = []
        $('.sp-id').each( function() {
            id_list.push($(this).attr('id'))
        })
        // Get current project
        var selectedItemId = $('#itemId').val()
        var data = {project_id: selectedItemId, id_list: id_list}
        console.log('Saving ' +id_list.length+ ' species for ' +selectedItemId)
        var result = $.post({
            url: backendHost + '/project_species',
            data: JSON.stringify(data),
            dataType: "json",
            contentType: "application/json; charset=utf-8",
        })
        result.done(function( ){
            $('#saveSpeciesList').html('Saved')
            $('#saveSpeciesList').prop( 'disabled', true )
        })
    })
})
