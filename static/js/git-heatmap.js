/* jshint esnext:true */

let id = "#heatmap";
let url = $(id).data("url");
let end = new Date($(id).data("end") * 1000);
let start = new Date($(id).data("start") * 1000);
let months = Math.ceil((end.getTime() - start.getTime()) / (30 * 24 * 60 * 60 * 1000)) + 1;
let month_span = Math.min(months, 4);

// adjust starting time if we have too broad a time range
if (months >= 4) {
  start = end;
  start.setMonth(end.getMonth() - 3);
}

let calendar = new CalHeatMap();

let parser = function(data) {
  let stats = {};
  for (let d in data.result) {
    stats[data.result[d].date] = data.result[d].value;
  }
  return stats;
};

calendar.init({
  data: url + "?start={{t:start}}&end={{t:end}}",
  start: start,
  itemSelector : id,
  afterLoadData: parser,
  domain: "month",
  subDomain: "x_day",
  range: month_span,
  cellSize: 15,
  cellPadding: 3,
  cellRadius: 5,
  domainGutter: 15,
  legend: [1, 3, 6, 12],
  legendOrientation: "horizontal",
  legendVerticalPosition: "bottom",
  legendHorizontalPosition: "left",
  legendCellSize: 15,
  legendCellPadding: 3,
  label: {
    position: "top"
  }
});