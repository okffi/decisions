(function($) {
  var cloneCount = 1;
  var all_comments = {};
  var cached_forms = {};
  var current_form = null;

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
    var $p = $(get_closest_p(e.target));
    var $form = $p.next(".comment-form");
    hide_comment_form($form);
  };

  var hide_comment_form = function($form) {
    var $p = $form.prev("p");

    // don't accept more click events during animation
    $p.off("click");

    $form.hide(400, function() {
      // remove the form from the DOM
      $form.detach();
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

    if (current_form != null && current_form != selector) {
      // hide the previously open form
      hide_comment_form(cached_forms[current_form]);
    }

    var $existing_form = cached_forms[selector];
    if (typeof $existing_form !== "undefined") {
      // toggle the target paragraph's event handler
      $target.off("click");
      $target.on("click", close_comment_form);
      // reuse the existing form
      $existing_form.insertAfter($(target));
      $existing_form.show(400);
      current_form = selector;
      return;
    }

    var $form = $(".snippets .comment-form").clone();
    cached_forms[selector] = $form;
    current_form = selector;

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

    // maybe show a feedback text beside the submit button if there's enough text
    var text_max = 300;
    var show_threshold = 173;
    var $textarea = $form.find("textarea")
    $textarea.on("keyup", function() {
      var text_length = $textarea.val().length;
      var text_remaining = text_max - text_length;
      if (text_length > show_threshold) {
        var feedback_text = gettext("%s/%s characters used");
        $form.find(".length-feedback").html(interpolate(feedback_text, [text_length, text_max]));
      } else {
        $form.find(".length-feedback").html("");
      }
      if (text_length > text_max) {
        $form.find("button[type=submit]").prop("disabled", true);
      } else {
        $form.find("button[type=submit]").prop("disabled", false);
      }
    });

    // make the textarea resize with comment length
    $textarea.css('height:' + (this.scrollHeight) + 'px;overflow-y:hidden;');
    $textarea.on("input", function () {
      this.style.height = 'auto';
      this.style.height = (this.scrollHeight) + 'px';
    });

    if (!commenting_enabled) {
      $form.find("form").remove();
    }

    // slide in the entire thing
    $form.hide();
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
      });
    });
  };

  $(document).ready(function() {
    update().done(function() {
      $("#content_block p").on("click", make_comment_form);
    });
  });
})(jQuery);
