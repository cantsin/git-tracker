/* jshint esnext:true */

import { bind_creation } from '/js/common';

bind_creation($('#add_emails_form'));

$("#add_emails_form").find('li a').click(function() {
  let uri = $(this).attr('href');
  let result = $.getJSON(uri);
  $(this).parents('li').fadeOut();
  return false;
});
