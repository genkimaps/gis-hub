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

const urlBase = 'https://www.gis-hub.ca/map_preview/';

function createTargetLayer(spatialtype, resource_id, geoserverlayer, projection_epsg){
  /**
   * Create an OpenLayers layer object of the appropriate type. 
   * For raster: ol.layer.Image with a WMS source
   * For vector: ol.layer.Tile with a XYZ source in Mapbox ol.format.MVT() format
   */

  if (spatialtype === 'raster') {
    var raster_url = urlBase + resource_id + '/geoserver/hubdata/wms';
    console.log('Raster preview URL: ' +raster_url)
    var untiledRasterLayer = new ol.layer.Image({
      source: new ol.source.ImageWMS({
        ratio: 1,
        url: raster_url,
        params: {
          'FORMAT': 'image/png',
          'VERSION': '1.1.1',  
          'LAYERS': 'hubdata:' +geoserverlayer,
          'exceptions': 'application/vnd.ogc.se_inimage',
        }
      })
    });
    return untiledRasterLayer;

  } else if (spatialtype === 'vector') {
    var vector_url = urlBase + resource_id + 
        '/geoserver/gwc/service/tms/1.0.0/hubdata:' +geoserverlayer+
        '@EPSG%3A' +projection_epsg+ '@pbf/{z}/{x}/{-y}.pbf'
    console.log('Vector preview URL: ' +vector_url)
    
    var mvtLayer = new ol.layer.VectorTile({
      source: new ol.source.VectorTile({
        tilePixelRatio: 1, // oversampling when > 1
        tileGrid: ol.tilegrid.createXYZ({maxZoom: 15}),
        format: new ol.format.MVT(),
        url: vector_url
      })
    })
    return mvtLayer;

  } else {
    console.error(`Unknown spatial type: ${spatialtype}`);
  }
}

ckan.module('dfo_map_display', function ($) {
  return {
    initialize: function () {
      console.log("dfo_map_display initialized for element: ", this.el);

      // Options passed to this JavaScript module by the calling template.
      var geoserverlayer = this.options.geoserverlayer;
      var resource_id = this.options.resource;
      var spatialtype = this.options.spatialtype;
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
        
      console.log(`Map preview: ${spatialtype} layer: ${geoserverlayer}, resource: ${this.options.lyrname} (id: ${resource_id})`);

      var targetLayer = createTargetLayer(spatialtype, resource_id, geoserverlayer, projection_epsg);

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
          targetLayer
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
      console.debug('Extent Lat-Lon: '+JSON.stringify(ext))

      var extWebMercator = ol.proj.transformExtent(ext, 'EPSG:4326', 'EPSG:'+projection_epsg)
      console.debug('Extent Web Mercator: '+JSON.stringify(extWebMercator))

      map.getView().fit(extWebMercator)
    }
  };
});
