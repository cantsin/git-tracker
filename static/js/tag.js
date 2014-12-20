jQuery.fn.toObservable = function (eventName, selector) {
    return Rx.Observable.fromEvent(this, eventName, selector);
};

let add_tag_form = $('#tag_form');
let add_tag_source = add_tag_form.toObservable('submit');
let add_tag = add_tag_source.subscribe(e => {
  add_tag_form.append('<i class="fa fa-circle-o-notch fa-spin"></i>');
  let data = add_tag_form.serialize();
  let submit = $.ajax({ type: 'POST',
                        url: add_tag_form.attr('action'),
                        data: data });
  submit.done(function(response) {
    if(response.success) {
      window.location = response.success
    }
    if(response.error) {
      add_tag_form.append('<div data-alert class="hidden alert-box alert">' + response.error + '</div>');
    }
  });
  submit.fail(function(jqXHR, status, error) {
    console.log(status);
    console.log(error);
  });
  e.preventDefault();
  return false;
});
