/* jshint esnext:true */

let id = "#heatmap";
let url = $(id).data("url");
let end = new Date($(id).data("end") * 1000);
let start = new Date($(id).data("start") * 1000);
let months = Math.ceil((end.getTime() - start.getTime()) / (30 * 24 * 60 * 60 * 1000));
let calendar = new CalHeatMap();

let parser = function(data) {
  let stats = {};
  for (let d in data) {
    stats[data[d].date] = data[d].value;
  }
  return stats;
};

calendar.init({
  data: url + "?start={{t:start}}&end={{t:end}}",
  start: start,
  itemSelector : id,
  afterLoadData: parser,
  domain : "month",
  subDomain : "day",
  range : months,
  scale: [1, 3, 6, 12]
});
