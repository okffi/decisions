(function($) {
  var cloneCount = 1;
  var all_comments = {};

  var render_comments = function(selector) {
    var comments = all_comments[selector];
    var $comments = $("<ul>");
    $comments.addClass("comment-list");
    $.each(comments, function(i, comment) {
      var $l = $("<li>");

      var $d = $("<div>");
      $d.appendTo($l);
      $d.addClass("comment");

      var $p = $("<p>");
      $p.addClass("comment__body");
      $p.html(comment["text"]);
      $p.appendTo($d);

      var $meta = $("<p>");
      $meta.addClass("comment__meta");

      var $poster = $("<span>");
      $poster.addClass("comment-poster");
      var poster_text = gettext("posted by <strong>%s</strong>");
      $poster.html(interpolate(poster_text, [comment["poster"]]));
      $poster.appendTo($meta);

      var $date = $("<time>");
      $date.addClass("comment-date");
      $date.text(comment["created"]);
      $date.attr("datetime", comment["created_timestamp"]);
      $date.appendTo($meta);

      $meta.appendTo($d);

      $d.appendTo($comments);
    });
    return $comments;
  };

  var get_closest_p = function(element) {
    while (element !== null && element.tagName.toUpperCase() !== "P") {
      element = element.parentElement;
    }
    if (element === null) {
      console.log("no p element ancestor for this click!");
      return null;
    }
    return element;
  };

  var close_comment_form = function(e) {
    // can be bound to a button on the form or the p element itself
    if (e.target.tagName.toUpperCase() === "BUTTON") {
      var $form = $(e.target).parents(".comment-form");
      var $p = $form.prev("p");
    } else {
      var $p = $(get_closest_p(e.target));
      var $form = $p.next(".comment-form");
    }

    // don't accept more click events during animation
    $p.off("click");

    $form.hide(400, function() {
      var offset = $p.offset();
      if ($(document).scrollTop() > offset["top"] + $p.outerHeight()) {
	$(document).scrollTop(offset["top"]);
      }
      update().done(function() {
        // toggle the paragraph's handler back
	$p.on("click", make_comment_form);
      });
    });
  };

  var make_comment_form = function(e) {
    // select the closest paragraph ancestor (P)
    var target = get_closest_p(e.target);
    if (typeof target == "null") {
      // bogus click
      return;
    }
    var selector = OptimalSelect.select(target);
    var $target = $(target);

    if (!commenting_enabled && !(selector in all_comments)) {
      // just do nothing
      return;
    }

    var $existing_form = $(target).next(".comment-form");
    if ($existing_form.length > 0) {
      // toggle the target paragraph's event handler
      $target.off("click");
      $target.on("click", close_comment_form);
      // reuse the existing form
      $existing_form.show(400);
      return;
    }

    var $form = $(".snippets .comment-form").clone();

    // render comments
    $comments = render_comments(selector);
    $comments.prependTo($form);

    // toggle the type of handler on the target
    $target.off("click");
    $target.on("click", close_comment_form);

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
    $form.find(".dismiss-button").on("click", close_comment_form);

    // ajax submit comment
    $form.find(":input[type=submit]").on("click", function(e) {
      e.preventDefault();
      var $actual_form = $form.find("form");
      $.post($actual_form.attr("action"), $actual_form.serialize())
	.done(function() {
	  $actual_form.hide(400, function() {
	    $actual_form.remove();
	    $(".dismiss-button").show();
	  });
	  update().done(function() {
	    var $new_comments = render_comments(selector);
	    $comments.remove();
	    $new_comments.prependTo($form);
	  });
	});
    });

    if (!commenting_enabled) {
      $form.find("form").remove();
    }

    // slide in the entire thing
    $form.hide();
    $form.insertAfter($(target));
    $form.show(400, function() {
      if (!commenting_enabled) { $(".dismiss-button").show(); }
    });
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
      });
    });
  };

  $(document).ready(function() {
    update().done(function() {
      $("#content_block p").on("click", make_comment_form);
    });
  });
})(jQuery);
