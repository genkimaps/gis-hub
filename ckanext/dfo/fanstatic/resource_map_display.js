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

      /**  We must include www. in the URL, or cookies (which contains the session of logged-in user) 
       * will NOT be included in the request. In other words, suppose a user is browsing to 
       * https://www.gis-hub.ca/dataset/some-dataset and then tries to access a map preview URL at 
       * https://gis-hub.ca/map_preview/blah-blah, the auth cookie will NOT be sent, because for security 
       * reasons, the browser thinks that https://www.gis-hub.ca and https://gis-hub.ca are completely 
       * different servers. 
       */
        
      var vector_url = 'https://www.gis-hub.ca/map_preview/' +this.options.resource+ 
        '/geoserver/gwc/service/tms/1.0.0/hubdata:' +geoserverlayer+
        '@EPSG%3A' +projection_epsg+ '@pbf/{z}/{x}/{-y}.pbf'
      console.log('Vector preview: ' +vector_url)
      
      var mvtLayer = new ol.layer.VectorTile({
        source: new ol.source.VectorTile({
          tilePixelRatio: 1, // oversampling when > 1
          tileGrid: ol.tilegrid.createXYZ({maxZoom: 15}),
          format: new ol.format.MVT(),
          // url: 'https://maps.gis-hub.ca/geoserver/gwc/service/tms/1.0.0/hubdata:' +geoserverlayer+
          //     '@EPSG%3A' +projection_epsg+ '@pbf/{z}/{x}/{-y}.pbf'
          url: vector_url
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

      var extWebMercator = ol.proj.transformExtent(ext, 'EPSG:4326', 'EPSG:'+projection_epsg)
      console.log('Extent Web Mercator: '+JSON.stringify(extWebMercator))

      map.getView().fit(extWebMercator)
    }
  };
});
