/* jshint esnext:true */

import { bind_creation } from '../js/common.js';

bind_creation($('#add_emails_form'));

// delete user emails.
$("#add_emails_form").find('li a').click(function() {
  let uri = $(this).attr('href');
  let result = $.getJSON(uri);
  $(this).parents('li').fadeOut();
  return false;
});
