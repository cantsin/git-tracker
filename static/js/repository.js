jQuery.fn.toObservable = function (eventName, selector) {
    return Rx.Observable.fromEvent(this, eventName, selector);
};

let add_repository_form = $('#repository_form');
let add_repository_source = add_repository_form.toObservable('submit');
let add_repository = add_repository_source.subscribe(e => {
  add_repository_form.append('<i class="fa fa-circle-o-notch fa-spin"></i>');
  let data = add_repository_form.serialize();
  let submit = $.ajax({ type: 'POST',
                        url: add_repository_form.attr('action'),
                        data: data });
  submit.done(function(response) {
    if(response.success) {
      window.location = response.url
    }
    if(response.error) {
      add_repository_form.append('<div data-alert class="hidden alert-box alert">' + response.error + '</div>');
    }
  });
  submit.fail(function(jqXHR, status, error) {
    console.log(status);
    console.log(error);
  });
  e.preventDefault();
  return false;
});
