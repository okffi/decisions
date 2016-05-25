(function($) {
  // Embed OSM
  var map = L.map("search_map").setView([60.204, 24.920], 11);

  L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  var searchLayer = L.layerGroup().addTo(map);
  var circle;

  var geosearch = function(e) {
    // AJAX request things around the given q
    e.preventDefault();

    // disable the search button while we work
    $("#search-button").prop("disabled", true);

    $.get(geosearch_url, $("#search-form").serialize())
      .done(function(data) {
        if (data.status !== "ok") {
          console.log("not rendering search results because " + data.status);
          return;
        }

        // clear previous layer
        searchLayer.remove()
        searchLayer = L.layerGroup().addTo(map);

        // drop the center circle
        circle = L
          .circle(data.center.coordinates, data.radius)
          .addTo(searchLayer);

        // draw pins around the center
        $.each(data.points, function(i, item) {
          var $popupContent = $("<div>")
                .append($("<h4>").text(item.title))
                .append($("<div>").html(item.description))
                .append($("<a>").attr("href", item.link).text(gettext("Read more")))
                .append($("<p>").text(item.timesince));

          L.marker(item.coordinates, {
            title: item.title
          }).bindPopup($popupContent[0]).addTo(searchLayer);
        });

        // draw polygons around the center
        $.each(data.polygons, function(i, item) {
          var $popupContent = $("<div>")
                .append($("<h4>").text(item.title))
                .append($("<div>").html(item.description))
                .append($("<a>").attr("href", item.link).text(gettext("Read more")))
                .append($("<p>").text(item.timesince));

          var poly = L.polygon(item.coordinates);
          poly = poly.bindPopup($popupContent[0]);
          poly = poly.addTo(searchLayer);
        });

        // zoom the map around the center circle
        map.fitBounds(circle.getBounds(), {
          paddingTopLeft: [5, 5],
          paddingBottomRight: [5, 5]
        });

        // write the form parameters into the document url
        var params = [];
        var q = encodeURIComponent($("#search-input").val());
        var d = encodeURIComponent($("#search-distance").val());
        params.push("q=" + q);
        if ($("#search-distance").val()) {
          params.push("d=" + d);
        }
        location.hash = params.join("&");

        // write the query into the text search link
        var cur_href = $("#text-search-link").attr("href");
        var bare_href = cur_href.split("?", 1)[0];
        $("#text-search-link").attr("href", bare_href + "?q=" + q);

        if (can_subscribe) {
          $(".map-subscribe").show();
          // write the query into the subscribe link and show it
          var cur_sub_href = $("#map-subscribe-link").attr("href");
          var bare_sub_href = cur_sub_href.split("?", 1)[0];
          $("#map-subscribe-link").attr(
            "href",
            bare_sub_href + "?q=" + q + "&d=" + d + "&t=1"
          );
        }
        // re-enable the search button
        $("#search-button").prop("disabled", false);
      });
  };
  $(document).ready(function() {
    $(".map-subscribe").hide();
    $("#search-form").on("submit", geosearch);
    if (location.hash.length) {
      // comprehend the hash and write its values to the form and submit it
      var params = location.hash.split("&");
      $.each(params, function(i, item) {
        var param = item.split("=", 2);
        var key = param[0];
        if (key.startsWith("#")) {
          key = key.slice(1);
        }
        var value = decodeURIComponent(param[1]);
        if (key === "q") {
          $("#search-input").val(value);
        } else if (key === "d") {
          $("#search-distance").val(value);
        }
      });
      $("#search-form").trigger("submit");
    }

    // update the size of the circle live
    $("#search-distance").on("change", function() {
      circle.setRadius($("#search-distance").val());
    });
    // after the range slider is let go, refresh the display
    $("#search-distance").on("blur", function() {
      $("#search-form").trigger("submit");
    });
  });
})(jQuery)
