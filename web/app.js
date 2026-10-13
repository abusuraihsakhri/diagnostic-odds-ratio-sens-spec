"use strict";
(function () {
  const form = document.getElementById("calculator");
  const message = document.getElementById("message");
  const correction = document.getElementById("correction");
  const exportButton = document.getElementById("export");
  let latest = null;

  function percent(value) {
    return value === null ? "Undefined" : (100 * value).toFixed(1) + "%";
  }
  function number(value) {
    if (value === null) return "Undefined";
    if (value === Infinity) return "∞";
    if (!Number.isFinite(value)) return "Not estimable";
    if (value === 0) return "0";
    return value >= 1000 ? value.toLocaleString("en-US", { maximumFractionDigits: 1 })
      : value.toFixed(value >= 10 ? 2 : 3);
  }
  function range(values, formatter) {
    return values ? "95% CI " + formatter(values[0]) + " – " + formatter(values[1])
      : "95% CI unavailable";
  }
  function set(id, value, ci) {
    document.getElementById("metric-" + id).textContent = value;
    document.getElementById("ci-" + id).textContent = ci;
  }
  function render(table, pretest) {
    const result = DiagnosticMetrics.calculate(table);
    const positive = DiagnosticMetrics.posterior(pretest / 100, result.lrPositive);
    const negative = DiagnosticMetrics.posterior(pretest / 100, result.lrNegative);

    set("sens", percent(result.sensitivity), range(result.intervals.sensitivity, percent));
    set("spec", percent(result.specificity), range(result.intervals.specificity, percent));
    set("ppv", percent(result.ppv), range(result.intervals.ppv, percent));
    set("npv", percent(result.npv), range(result.intervals.npv, percent));
    set("dor", number(result.dor), range(result.intervals.dor, number));
    set("youden", number(result.youden), "Range −1 to +1");
    set("lrpos", number(result.lrPositive), "Positive test likelihood ratio");
    set("lrneg", number(result.lrNegative), "Negative test likelihood ratio");
    set("prevalence", percent(result.prevalence), "Observed reference-positive fraction");
    set("postpos", percent(positive), "After a positive test");
    set("postneg", percent(negative), "After a negative test");
    correction.hidden = !result.corrected;
    message.textContent = "Calculated from " + result.total + " observations; no data were transmitted.";
    message.className = "message success";
    latest = { table, pretest, result, positive, negative };
    exportButton.disabled = false;
  }

  function readValue(id) {
    const input = document.getElementById(id);
    if (!input.value.trim()) throw new Error(input.labels[0].textContent + " is required.");
    const value = Number(input.value);
    if (!Number.isFinite(value)) throw new Error("Enter valid numeric values.");
    return value;
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    try {
      render({
        tp: readValue("tp"), fp: readValue("fp"),
        fn: readValue("fn"), tn: readValue("tn")
      }, readValue("pretest"));
    } catch (error) {
      message.textContent = error.message;
      message.className = "message error";
      exportButton.disabled = true;
      latest = null;
    }
  });

  document.getElementById("reset").addEventListener("click", function () {
    form.reset();
    form.requestSubmit();
  });

  exportButton.addEventListener("click", function () {
    if (!latest) return;
    const r = latest.result;
    const entries = [
      ["TP", latest.table.tp], ["FP", latest.table.fp],
      ["FN", latest.table.fn], ["TN", latest.table.tn],
      ["sample_size", r.total], ["sensitivity", r.sensitivity],
      ["specificity", r.specificity], ["ppv", r.ppv], ["npv", r.npv],
      ["lr_positive", r.lrPositive], ["lr_negative", r.lrNegative],
      ["diagnostic_odds_ratio", r.dor], ["youden_j", r.youden],
      ["prevalence", r.prevalence], ["dor_zero_cell_correction", r.corrected],
      ["pretest_probability", latest.pretest / 100],
      ["posttest_probability_positive", latest.positive],
      ["posttest_probability_negative", latest.negative]
    ];
    for (const [name, interval] of Object.entries(r.intervals)) {
      entries.push([name + "_ci95_lower", interval ? interval[0] : null]);
      entries.push([name + "_ci95_upper", interval ? interval[1] : null]);
    }
    const csv = "metric,value\r\n" + entries.map(([name, value]) =>
      name + "," + (value === null ? "" : String(value))).join("\r\n") + "\r\n";
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "diagnostic-performance.csv";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  form.requestSubmit();
})();
