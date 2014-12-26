/* jshint esnext:true */

let count = $('#treemap').data('repository_count');
let labels = $('#treemap').data('tags');

// normalize the data.
let n = Math.max.apply(null, count) || 1;
let data = [for (i of count) i / n];

let boxFormatter = (coordinates, index) => {
  // we don't have any recursive indices.
  let datapoint = data[index[0]];

  let saturation = (datapoint * 0.6) + 0.4;
  let brightness = (datapoint * 0.3) + 0.2;
  let color = 'hsb(0.2,' + saturation + ',' + brightness + ')';

  return {'fill' : color};
};

let width = $('#treemap').width();
Treemap.draw('treemap', width, 200, data, labels, {'box' : boxFormatter});
