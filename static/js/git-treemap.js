/* jshint esnext:true */

let data = $('#treemap').data('tags');
data = data.filter((t) => { return t.count !== 0; });
data = data.sort((a, b) => { return b.count - a.count; });

let labels = R.pluck('tag')(data);

// do we have data to work with?
if(labels.length > 0) {
  // normalize the data.
  let n = data[0].count;
  let count_data = R.pluck('count')(data);
  let counts = count_data.map(function(elem){ return elem / n; })

  let boxFormatter = (coordinates, index) => {
    // we don't have any recursive indices.
    let datapoint = counts[index[0]];

    let saturation = (datapoint * 0.6) + 0.4;
    let brightness = (datapoint * 0.3) + 0.2;
    let color = 'hsb(0.6,' + saturation + ',' + brightness + ')';

    return {'fill' : color};
  };

  let width = $('#treemap').width();
  Treemap.draw('treemap', width, 200, counts, labels, {'box' : boxFormatter});
} else {
  $("#treemap").append('<div data-alert class="alert-box info">Please tag a repository for the tree map to show up.</div>');
}
