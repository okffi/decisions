(function($) {
  var cloneCount = 1;
  var all_comments = {};

  var render_comments = function(selector) {
    var comments = all_comments[selector];
    var $comments = $("<ul>");
    $comments.addClass("comment-list");
    $.each(comments, function(i, comment) {
      var $d = $("<li>");
      $d.addClass("comment");
      var $p = $("<p>");
      $p.text(comment["text"]);
      $d.append($p)
      var $date = $("<p>");
      $date.text(comment["created"]);
      $d.append($date)
      $comments.append($d);
    });
    return $comments;
  };

  var make_comment_form = function(e) {
    var target = e.target;
    var selector = OptimalSelect.select(target);

    var $form = $(".snippets .comment-form").clone();

    // render comments
    $comments = render_comments(selector);
    $comments.prependTo($form);

    // disable content clicks while commenting form is open
    $("#content_block p").off("click");

    // fix up labels/field IDs to be unique and matching
    $form.find("label[for]").each(function() {
      var $t = $(this);
      $t.attr("for", cloneCount.toString() + "_" + $t.attr("for"));
    });
    $form.find(":input[id]").each(function() {
      var $t = $(this);
      $t.attr("id", cloneCount.toString() + "_" + $t.attr("id"));
    });
    $form.find("#" + cloneCount.toString() + "_" + "id_selector").val(selector);
    cloneCount++;


    // close commenting
    $form.find(".dismiss-button").on("click", function() {
      $form.hide(400, function() {
	var offset = $(target).offset();
	if ($(document).scrollTop() > offset["top"] + $(target).outerHeight()) {
	  $(document).scrollTop(offset["top"]);
	}
	$form.remove();
	update();
	$("#content_block p").on("click", make_comment_form);
      });
    });

    // ajax submit comment
    $form.find(":input[type=submit]").on("click", function(e) {
      e.preventDefault();
      var $actual_form = $form.find("form");
      $.post($actual_form.attr("action"), $actual_form.serialize())
	.done(function() {
	  $actual_form.hide(400, function() {
	    $actual_form.remove();
	  });
	  update().done(function() {
	    var $new_comments = render_comments(selector);
	    $comments.remove();
	    $new_comments.prependTo($form);
	  });
	});
    });

    // slide in the entire thing
    $form.hide()
    $form.insertAfter($(target));
    $form.show(400);
  };

  // get new comments and return a deferred
  var update = function() {
    return $.get(comments_url).done(function(data) {
      all_comments = data["content"];
      $.each(all_comments, function(selector, comments) {
	var $comment_counter = $(selector).find(".comment-counter");
	if ($comment_counter.length == 0) {
	  $comment_counter = $("<small>");
	  $comment_counter.addClass("comment-counter badge");
	  $comment_counter.appendTo($(selector));
	}

	var text = ngettext(
	  "%s comment",
	  "%s comments",
	  comments.length
	);
	$comment_counter.text(interpolate(text, [comments.length]));
      })
    });
  };

  $(document).ready(function() {
    update().done(function() {
      $("#content_block p").on("click", make_comment_form);
    });
  });
})(jQuery);
