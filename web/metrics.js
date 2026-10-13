(function (root, factory) {
  "use strict";
  const api = factory();
  root.DiagnosticMetrics = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis, function () {
  "use strict";
  const Z = 1.959963984540054;
  const CELLS = ["tp", "fp", "fn", "tn"];

  function validate(input) {
    for (const key of CELLS) {
      const count = input[key];
      if (typeof count !== "number" || !Number.isSafeInteger(count) || count < 0) {
        throw new Error(key.toUpperCase() + " must be a non-negative whole number.");
      }
    }
    if (input.tp + input.fn === 0 || input.fp + input.tn === 0) {
      throw new Error("Both reference-positive and reference-negative groups must contain observations.");
    }
    if (!Number.isSafeInteger(CELLS.reduce((n, key) => n + input[key], 0))) {
      throw new Error("The combined sample size is too large.");
    }
  }

  function wilson(k, n) {
    if (n === 0) return null;
    const p = k / n;
    const denominator = 1 + (Z * Z) / n;
    const centre = p + (Z * Z) / (2 * n);
    const margin = Z * Math.sqrt((p * (1 - p) + (Z * Z) / (4 * n)) / n);
    return [Math.max(0, (centre - margin) / denominator),
            Math.min(1, (centre + margin) / denominator)];
  }

  function calculate(input) {
    validate(input);
    const { tp, fp, fn, tn } = input;
    const total = tp + fp + fn + tn;
    const sensitivity = tp / (tp + fn);
    const specificity = tn / (tn + fp);
    const ppv = tp + fp ? tp / (tp + fp) : null;
    const npv = tn + fn ? tn / (tn + fn) : null;
    const lrPositive = specificity < 1 ? sensitivity / (1 - specificity)
      : sensitivity > 0 ? Infinity : null;
    const lrNegative = specificity > 0 ? (1 - sensitivity) / specificity
      : sensitivity < 1 ? Infinity : null;
    const corrected = Math.min(tp, fp, fn, tn) === 0;
    const a = tp + (corrected ? 0.5 : 0);
    const b = fp + (corrected ? 0.5 : 0);
    const c = fn + (corrected ? 0.5 : 0);
    const d = tn + (corrected ? 0.5 : 0);
    const dor = (a * d) / (b * c);
    const logDor = Math.log(a) + Math.log(d) - Math.log(b) - Math.log(c);
    const se = Math.sqrt(1 / a + 1 / b + 1 / c + 1 / d);
    const dorCI = [Math.exp(logDor - Z * se), Math.exp(logDor + Z * se)];
    return {
      total, sensitivity, specificity, ppv, npv, lrPositive, lrNegative, dor,
      youden: sensitivity + specificity - 1,
      prevalence: (tp + fn) / total, corrected,
      intervals: {
        sensitivity: wilson(tp, tp + fn),
        specificity: wilson(tn, tn + fp),
        ppv: wilson(tp, tp + fp),
        npv: wilson(tn, tn + fn),
        dor: dorCI
      }
    };
  }

  function posterior(pretestProbability, likelihoodRatio) {
    if (!Number.isFinite(pretestProbability) || pretestProbability <= 0 || pretestProbability >= 1) {
      throw new Error("Pre-test probability must be greater than 0% and less than 100%.");
    }
    if (likelihoodRatio === null) return null;
    if (likelihoodRatio === Infinity) return 1;
    const odds = pretestProbability / (1 - pretestProbability) * likelihoodRatio;
    return odds / (1 + odds);
  }
  return { calculate, posterior, wilson };
});
