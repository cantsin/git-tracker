/* jshint esnext:true */

import { bind_creation } from '/js/common';

bind_creation($('#apply_tags_form'));

let fetch_el = $("#fetch_repository");
fetch_el.on("opened", function() {
  let url = fetch_el.data('url');
  let fetch = $.ajax({ type: 'GET', url: url });
  fetch.done(function(response) {
    if(response.success) {
      window.location = response.success;
    }
    if(response.error) {
      fetch_el.append('<div data-alert class="temporary alert-box alert">' + response.error + '</div>');
    }
  });
  fetch.fail(function(jqXHR, status, error) {
    fetch_el.append('<div data-alert class="temporary alert-box alert">' + status + ': ' + error + '</div>');
  });
});
