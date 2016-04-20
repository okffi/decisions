(function($) {
  // Embed OSM
  var map = L.map("content_map").setView([60.204, 24.920], 11);

  L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  var normalizeCoord = function(lonlat) {
    // swaps the coordinate axes
    return [lonlat[1], lonlat[0]];
  }

  var normalizePolygon = function(coords) {
    // if the last polygon point is sufficiently equal to the
    // first, drop it
    var e = 1e-12;
        var first = coords[0];
    var last = coords[coords.length - 1];
    if (Math.abs(first[0]-last[0]) < e && Math.abs(first[1]-last[1]) < e) {
      coords.pop();
    }
    return coords.map(normalizeCoord);
  };

  // Request and add markers and polygons
  $.get(geometry_url).done(function(data) {
    data["content"].forEach(function(geo) {
      if (geo['type'] == 'Point') {
        var latlon = normalizeCoord(geo["coordinates"]);
        L.marker(latlon).addTo(map);
      } else if (geo['type'] == 'Polygon') {
        var coords = geo["coordinates"].map(normalizePolygon);
        map.addLayer(L.polygon(coords));
      } else if (geo['type'] == 'MultiPolygon') {
        var multicoords = []
        geo["coordinates"].forEach(function(poly) {
          multicoords.push(poly.map(normalizePolygon));
        });
        map.addLayer(L.polygon(multicoords));
      } else {
        console.log("Unknown geometry: " + geo);
      }
    });
  });

})(jQuery);
