"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { calculate, posterior } = require("./metrics.js");

test("reference 2x2 table", () => {
  const r = calculate({tp:95, fp:10, fn:5, tn:90});
  assert.equal(r.sensitivity, 0.95);
  assert.equal(r.specificity, 0.9);
  assert.equal(r.dor, 171);
  assert.ok(Math.abs(r.youden - 0.85) < 1e-12);
  assert.ok(Math.abs(r.ppv - 95/105) < 1e-12);
  assert.ok(Math.abs(r.npv - 90/95) < 1e-12);
  assert.equal(r.corrected, false);
  assert.ok(r.intervals.sensitivity[0] < r.sensitivity);
});
test("zero cells use correction; undefined PPV remains null", () => {
  const r = calculate({tp:0, fp:0, fn:10, tn:20});
  assert.equal(r.ppv, null);
  assert.equal(r.intervals.ppv, null);
  assert.equal(r.corrected, true);
  assert.ok(Number.isFinite(r.dor));
});
test("invalid and missing groups are rejected", () => {
  for (const data of [
    {tp:-1,fp:1,fn:1,tn:1},{tp:1.2,fp:1,fn:1,tn:1},
    {tp:0,fp:1,fn:0,tn:1},{tp:1,fp:0,fn:1,tn:0}
  ]) assert.throws(() => calculate(data));
});
test("Bayesian update uses unrounded likelihood ratios", () => {
  const r = calculate({tp:95,fp:10,fn:5,tn:90});
  assert.ok(Math.abs(posterior(.2,r.lrPositive) - 0.7037037037) < 1e-9);
  assert.ok(posterior(.2,r.lrNegative) < .02);
  assert.throws(() => posterior(1, r.lrPositive));
});
test("perfect specificity and sensitivity handle infinite and zero ratios", () => {
  const r = calculate({tp:10,fp:0,fn:0,tn:10});
  assert.equal(r.lrPositive, Infinity);
  assert.equal(r.lrNegative, 0);
  assert.equal(posterior(.2,Infinity), 1);
});
