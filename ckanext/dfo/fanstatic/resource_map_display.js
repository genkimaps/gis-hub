/**
 * Renders a full map preview for a resource, including all vector geometries or raster tiles. 
 * 
 * This file belongs in:
 * /dfo/fanstatic
 */

 "use strict";

function simpleStyle(feature) {
  return new ol.style.Style({
      fill: new ol.style.Fill({
      color: '#ADD8E6'
    }),
      stroke: new ol.style.Stroke({
      color: '#880000',
      width: 1
    })
  });
}

ckan.module('dfo_map_display', function ($) {
  return {
    initialize: function () {
      console.log("dfo_map_display initialized for element: ", this.el);

      // Options passed to this JavaScript module by the calling template.
      var geoserverlayer = this.options.geoserverlayer;
      console.log('Rendering map preview: '+geoserverlayer);

      var north = Number.parseFloat(this.options.north);
      var east = Number.parseFloat(this.options.east);
      var south = Number.parseFloat(this.options.south);
      var west = Number.parseFloat(this.options.west);

      const projection_epsg = '900913';
      
      var mvtLayer = new ol.layer.VectorTile({
        source: new ol.source.VectorTile({
          tilePixelRatio: 1, // oversampling when > 1
          tileGrid: ol.tilegrid.createXYZ({maxZoom: 15}),
          format: new ol.format.MVT(),
          url: 'https://maps.gis-hub.ca/geoserver/gwc/service/tms/1.0.0/hubdata:' +geoserverlayer+
              '@EPSG%3A' +projection_epsg+ '@pbf/{z}/{x}/{-y}.pbf'
        })
      })

      var layers = [
          new ol.layer.Tile({
            source: new ol.source.XYZ({
              attributions:
                'Tiles © <a href="https://services.arcgisonline.com/ArcGIS/' +
                'rest/services/World_Topo_Map/MapServer">ArcGIS</a>',
              url:
                'https://server.arcgisonline.com/ArcGIS/rest/services/' +
                'World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            }),
          }),    
          mvtLayer
      ]

      var map = new ol.Map({
        target: 'ol_resource_map',
        view: new ol.View({
          center: ol.proj.transform([-129.31181, 52.00816], 'EPSG:4326', 'EPSG:'+projection_epsg),
          zoom: 10
        }),
        layers: layers
      });

      // Set map view to layer extent
      // https://stackoverflow.com/q/35150114
      var bottomLeft = [west, south];
      var topRight = [east, north];
      var ext = ol.extent.boundingExtent([bottomLeft, topRight]);
      console.log('Extent Lat-Lon: '+JSON.stringify(ext))



    }
  };
});
