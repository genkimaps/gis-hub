// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module('dfo_extent_map', function ($) {
  return {
    initialize: function () {
      console.log("dfo_extent_map initialized for element: ", this.el);

      // Access some options passed to this JavaScript module by the calling
      // template.
      var convexhull = this.options.convexhull;
      console.log(convexhull);
    }
  };
});


// var mymap = L.map('mapid').setView([45.2, -109.6], 8);

// // Tile background layer
// var esriImagery = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
// var mapboxImagery = 'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw'
// L.tileLayer(
//   esriImagery, {
//   maxZoom: 18,
//   attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
//     '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
//     'Imagery © <a href="https://www.esri.com/">ESRI</a>',
//   id: 'mapbox.streets'
// }).addTo(mymap);

// L.geoJSON(convexhull).addTo(mymap);
