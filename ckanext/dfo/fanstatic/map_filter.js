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

      var mymap = L.map('filtermap').setView([52.079354, -132.303103], 5);

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

      // FeatureGroup is to store editable layers. Make sure to add them to map.
      var drawnItems = new L.FeatureGroup();
      mymap.addLayer(drawnItems)

      // Add draw control toolbar to map.
      var drawControl = new L.Control.Draw({
          position: 'topright',
          // Disable everything except draw rectangle.
          draw: {
            polygon: false,
            polyline: false,
            circle: false,
            marker: false,
            circlemarker: false
          },
          edit: {
              featureGroup: drawnItems
          }
      });
      mymap.addControl(drawControl);

      var popup = L.popup();

      function onMapClick(e) {
        popup
          .setLatLng(e.latlng)
          .setContent("You clicked the map at " + e.latlng.toString())
          .openOn(mymap);
      }

      // Enable drawn shapes to be saved on the map.
      mymap.on('draw:created', function (e) {
          var type = e.layerType,
              layer = e.layer;

          layer.on('click', function(e) {
            popup
              .setLatLng(e.latlng)
              .setContent("North: " + layer.getBounds()._northEast.lat.toString() +
                          "West: " + layer.getBounds()._southWest.lng.toString() +
                          "South: " + layer.getBounds()._southWest.lat.toString() +
                          "East: " + layer.getBounds()._northEast.lng.toString()
                          )
              .openOn(mymap);
              console.log(layer.getBounds())
          });

          // Need to add layers to drawnItems FeatureGroup to make them editable.
          drawnItems.addLayer(layer);
      });
    }
  };
});
