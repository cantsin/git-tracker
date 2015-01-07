/* jshint esnext:true */

import { bind_creation } from '/js/common';

bind_creation($('#add_emails_form'));

$("#add_emails_form").find('li a').click(function() {
  let uri = $(this).attr('href');
  let result = $.getJSON(uri);
  $(this).parents('li').fadeOut();
  return false;
});

$("input:file").change(function(e) {
  let split_filename = $(this).val().split('\\');
  let filename = split_filename[split_filename.length - 1];
  $(this).parent().next().remove();
  let html = '<label>Uploaded file: ' + filename + '</label>';
  $(this).parent().after(html);
});
