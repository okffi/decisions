(function($) {
  // Based on: http://stackoverflow.com/a/23487596
  // Using the text width of the input, scales the input bar to fit.

  var $input = $('#search-input');
  var $dummy = $('<div style="position:absolute; left: -1000%;"></div>').appendTo('body');

  ['font-size', 'font-style', 'font-weight', 'font-family',
   'line-height', 'text-transform', 'letter-spacing'].forEach(function(index) {
     $dummy.css(index, $input.css(index));
  });

  var thresholds = [.15, .30, .60, 1];

  var update_width = function() {
    $dummy.html(this.value);
    var size_ratio = ($dummy.width() + $("#search-go").width() + 15) / $("#search-form").width();

    for (var t in thresholds) {
      if (thresholds[t] > size_ratio) {
        break;
      }
    }

    $("#search-group").css("width", thresholds[t]*100 + "%");
  };


  $input.focus();
  update_width();
  $input.on('input', update_width);
})(jQuery);
