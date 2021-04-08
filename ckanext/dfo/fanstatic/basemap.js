// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.

// This file belongs in:
// dfo/fanstatic

"use strict";

ckan.module('dfo_test_map', function ($) {
  return {
    initialize: function () {
      console.log('dfo_extent_map initialized for element: ', this.el);

      // Access some options passed to this JavaScript module by the calling
      // template.

      var map = L.map('map', {drawControl: true}).setView([49.458875, -128.130508], 8);

      // Tile background layer
      var esriImagery = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
      // var mapboxImagery = 'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw'
      L.tileLayer(
        esriImagery, {
        maxZoom: 18,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
          '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
          'Imagery © <a href="https://www.esri.com/">ESRI</a>',
        // id: 'mapbox.streets'
      }).addTo(map);

      var bounds = [[49.458875, -128.130508], [50.785927, -124.673699]];

      // create an orange rectangle
      var boundingBox = L.rectangle(bounds, {color: "#ff7800", weight: 1});
      map.addLayer(boundingBox);

      // FeatureGroup is to store editable layers
      var drawnItems = new L.FeatureGroup();
      map.addLayer(drawnItems);
      var drawControl = new L.Control.Draw({
        edit: {
          featureGroup: drawnItems
        }
      });
      map.addControl(drawControl);


    }
  };
});