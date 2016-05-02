(function($) {
  var cloneCount = 1;
  var all_comments = {};
  var cached_forms = {};
  var current_form = null;
  var animating = false;

  var render_comments = function(selector) {
    var comments = all_comments[selector];
    var $comments = $("<ul>");
    $comments.addClass("comment-list");
    $.each(comments, function(i, comment) {
      var $l = $("<li>");

      var $d = $("<div>");
      $d.appendTo($l);
      $d.addClass("comment");
      $d.attr("id", "c" + comment["comment_id"]);

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

      if (comment["poster"] == logged_in_user) {
        // add edit/delete links
        var $delete = $("<span>").addClass("comment-delete");
        $delete.data("comment_id", comment['comment_id']);

        var $delete_button = $("<button>").addClass("btn btn-small ask-delete").text(gettext("Delete comment"));
        $delete_button.on('click', confirm_delete_comment);
        $delete_button.appendTo($delete);

        var $c = $("<span>").addClass("confirm-delete").hide();
        var $text = $("<span>").text(gettext("Are you sure?")).appendTo($c);
        var $yes = $("<button>").text(gettext("Delete")).addClass("btn btn-small").appendTo($c);
        var $no = $("<button>").text(gettext("Cancel")).addClass("btn btn-small").appendTo($c);

        $yes.on("click", delete_comment);
        $no.on("click", cancel_delete_comment);

        $c.appendTo($delete);

        // TODO integrate editor form neatly

        $delete.appendTo($meta);
      }

      $meta.appendTo($d);

      $d.appendTo($comments);
    });
    return $comments;
  };

  var confirm_delete_comment = function(event) {
    var $container = $(this).parents(".comment-delete");

    $container.find(".ask-delete").hide();
    $container.find(".confirm-delete").show();
  };

  var cancel_delete_comment = function(event) {
    var $container = $(this).parents(".comment-delete");

    $container.find(".confirm-delete").hide();
    $container.find(".ask-delete").show();
  };

  var delete_comment = function(event) {
    var $container = $(this).parents(".comment-delete");
    $.post("/comments/delete/" + $container.data("comment_id") + "/").done(function() {
             var $com = $container.parents(".comment");
             $com.fadeOut(400, function() { $com.remove(); });
    });
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

  var hide_comment_form = function($form) {
    var $p = $form.prev("p");

    var deferred = $.Deferred();

    $form.hide(400, function() {
      $form.detach();
      var offset = $p.offset();
      if ($(document).scrollTop() > offset["top"] + $p.outerHeight()) {
	$(document).scrollTop(offset["top"]);
      }
      update().done(function() {
        deferred.resolve();
      });
    });

    return deferred.promise();
  };

  var toggle_comment_form = function(e) {
    e.preventDefault();

    // do nothing if we're currently doing something with the ui
    if (animating) {
      return;
    }
    animating = true;

    // select the closest paragraph ancestor (P)
    var target = get_closest_p(e.target);
    if (typeof target == "null") {
      // bogus click
      return;
    }
    var selector = $(target).data("selector");
    var $target = $(target);

    if (!commenting_enabled && !(selector in all_comments)) {
      // just do nothing
      return;
    }

    // determine whether we're opening or closing the comments
    if (current_form != null) {
      if (current_form == selector) {
        // close this form
        var $p = $(get_closest_p(e.target));
        var $form = $p.next(".comment-form");
        hide_comment_form($form).done(function() {
          current_form = null;
          animating = false;
        });
      } else {
        // hide the previously open form
        if (cached_forms[current_form].closest(document.documentElement).length) {
          hide_comment_form(cached_forms[current_form]).done(function() {
            // only proceed with form building after the hiding is done
            build_comment_form(selector, $target);
          }).done(function() { animating = false });
        }
      }
    } else {
      build_comment_form(selector, $target).done(function() { animating = false; });
    }
  };

  var build_comment_form = function(selector, $target) {
    var $existing_form = cached_forms[selector];
    var deferred = $.Deferred();

    if (typeof $existing_form !== "undefined") {
      // reuse the existing form
      $existing_form.insertAfter($target);
      $existing_form.show(400, function() { deferred.resolve() });
      current_form = selector;
      return deferred.promise();
    }

    var $form = $(".snippets .comment-form").clone();
    cached_forms[selector] = $form;
    current_form = selector;

    // render comments
    $comments = render_comments(selector);
    $comments.prependTo($form);

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
    var $textarea = $form.find("textarea");
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
    $form.insertAfter($target);
    $form.show(400, function() { deferred.resolve() });

    return deferred.promise();
  };

  // get new comments and return a deferred
  var update = function() {
    return $.get(comments_url).done(function(data) {
      all_comments = data["content"];
      $("#content_block p").addClass("commentable");
      $("#content_block p").each(function() {
        var $this = $(this);
        var $div;
        if ($this.find(".comments-bubble").length) {
          $div = $this.find(".comments-bubble");
        } else {
          $div = $("<div>");
          $div.addClass("comments-bubble");
          $div.prependTo($this);
        }

        var bubble_html = "";
        if (commenting_enabled) {
          bubble_html += "<i class=\"fa fa-comments\"></i>";
          bubble_html += "<small><a href=\"#\">" + gettext("Write a comment") + "</a></small>";
        }

        $div.html(bubble_html);
      });

      $.each(all_comments, function(selector, comments) {
	var $comment_counter = $(selector).find(".comment-counter");
	if ($comment_counter.length == 0) {
	  $comment_counter = $("<small>");
	  $comment_counter.addClass("comment-counter");
          var $bubble = $(selector).find(".comments-bubble");
          $bubble.html("<i class=\"fa fa-comments\"></i>");
          var $a = $("<a href=\"#\">");
          $comment_counter.appendTo($a);
          $a.appendTo($bubble);
	}

	var text = ngettext(
	  "Read %s comment",
	  "Read %s comments",
	  comments.length
	);
	$comment_counter.text(interpolate(text, [comments.length]));
      });
    });
  };

  $(document).ready(function() {
    update().done(function() {
      $("#content_block p").on("click", toggle_comment_form);
      // Some browsers won't propagate click events from elements
      // positioned outside their parent element
      $("#content_block .comments-bubble").on("click", toggle_comment_form);
      // Create canonical selector data attributes, allowing us to
      // mess with DOM from now on
      $("#content_block p").each(function() {
        $(this).data("selector", OptimalSelect.select(this));
      });

      if (location.hash.length) {
        var comment_match = /#c(\d+)/.exec(location.hash);
        var comment_id = parseInt(comment_match[1]);
        if (comment_id > 0) {
          var comment_selector = null;
          $.each(all_comments, function(selector, comments) {
            $.each(comments, function(idx, comment) {
              if (comment['comment_id'] == comment_id) {
                comment_selector = selector;
                return false;
              }
            });
            if (comment_selector !== null) {
              return false;
            }
          });

          animating = true;
          build_comment_form(comment_selector, $(comment_selector)).done(function() {
            var offset = $(comment_selector).offset();
            $(document).scrollTop(offset.top - 25);
            $("#c" + comment_id).addClass("bc-base--lightest");
            animating = false;
          });
        }
      }
    });
  });
})(jQuery);
