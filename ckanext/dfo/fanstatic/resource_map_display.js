/**
 * Renders a full map preview for a resource, including all vector geometries or raster tiles. 
 * 
 * This file belongs in:
 * /dfo/fanstatic
 */

 "use strict";

 ckan.module('dfo_map_display', function ($) {
    return {
      initialize: function () {
        console.log("dfo_map_display initialized for element: ", this.el);
  
        // Options passed to this JavaScript module by the calling template.
        var layer_name = this.options.layername;
        console.log('Rendering map preview: '+layer_name)

        }
    };
});
