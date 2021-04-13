// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.

// This file belongs in:
// dfo/fanstatic

"use strict";

ckan.module('map_filter', function ($) {
  return {
    initialize: function () {
      console.log("map_filter initialized for element: ", this.el);

      var mymap = L.map('filtermap', {drawControl: true}).setView([52.079354, -132.303103], 5);

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
      }).addTo(mymap);

      // FeatureGroup is to store editable layers
      var drawnItems = new L.FeatureGroup();
      mymap.addLayer(drawnItems);
      var drawControl = new L.Control.Draw({
        edit: {
          featureGroup: drawnItems
          }
      });
      mymap.addControl(drawControl);

      var toolbar = L.Toolbar();
      toolbar.addToolbar(mymap);

    }
  };
});
