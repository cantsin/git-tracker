/* jshint esnext:true */

jQuery.fn.toObservable = function(eventName, selector) {
  return Rx.Observable.fromEvent(this, eventName, selector);
};

export function bind_creation(form_el) {
  form_el.toObservable('submit').subscribe(e => {
    form_el.find('.temporary').remove();
    form_el.append('<i class="temporary fa fa-circle-o-notch fa-spin"></i>');
    let data = form_el.serialize();
    let submit = $.ajax({ type: 'POST',
                          url: form_el.attr('action'),
                          data: data });
    submit.done(function(response) {
      form_el.find('i.temporary').remove();
      if(response.success) {
        window.location = response.success;
      }
      if(response.error) {
        form_el.append('<div data-alert class="temporary alert-box alert">' + response.error + '</div>');
      }
    });
    submit.fail(function(jqXHR, status, error) {
      form_el.append('<div data-alert class="temporary alert-box alert">' + status + ': ' + error + '</div>');
    });
    e.preventDefault();
    return false;
  });
}

bind_creation($('#repository_form'));
bind_creation($('#tag_form'));
