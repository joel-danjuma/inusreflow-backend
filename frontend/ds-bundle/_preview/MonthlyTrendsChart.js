"use strict";
var __dsPreview = (() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __esm = (fn, res, err) => function __init() {
    if (err) throw err[0];
    try {
      return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
    } catch (e) {
      throw err = [e], e;
    }
  };
  var __commonJS = (cb, mod) => function __require() {
    try {
      return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
    } catch (e) {
      throw mod = 0, e;
    }
  };
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // <define:import.meta.env>
  var init_define_import_meta_env = __esm({
    "<define:import.meta.env>"() {
    }
  });

  // shim:react-shim
  var require_react_shim = __commonJS({
    "shim:react-shim"(exports, module) {
      init_define_import_meta_env();
      var R = window.React;
      function np(p, k) {
        var o = {};
        for (var x in p) if (x !== "children") o[x] = p[x];
        if (k !== void 0) o.key = k;
        return o;
      }
      function jsx3(t, p, k) {
        var c = p && p.children;
        return c === void 0 ? R.createElement(t, np(p, k)) : R.createElement(t, np(p, k), c);
      }
      function jsxs2(t, p, k) {
        return R.createElement.apply(R, [t, np(p, k)].concat(p.children));
      }
      module.exports = R;
      module.exports.jsx = jsx3;
      module.exports.jsxs = jsxs2;
      module.exports.jsxDEV = function(t, p, k, s) {
        return (s ? jsxs2 : jsx3)(t, p, k);
      };
      module.exports.Fragment = R.Fragment;
    }
  });

  // .design-sync/previews/MonthlyTrendsChart.tsx
  var MonthlyTrendsChart_exports = {};
  __export(MonthlyTrendsChart_exports, {
    Empty: () => Empty,
    SixMonths: () => SixMonths,
    TwelveMonths: () => TwelveMonths
  });
  init_define_import_meta_env();

  // src/components/dashboard/MonthlyTrendsChart.tsx
  init_define_import_meta_env();
  var import_react = __toESM(require_react_shim());

  // src/lib/money.ts
  init_define_import_meta_env();
  var NAIRA_FORMATTER = new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN"
  });
  function koboToNaira(kobo) {
    return kobo / 100;
  }
  function formatNaira(kobo) {
    return NAIRA_FORMATTER.format(koboToNaira(kobo));
  }

  // src/components/dashboard/MonthlyTrendsChart.tsx
  var import_jsx_runtime = __toESM(require_react_shim());
  var COMPACT_NAIRA = new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    notation: "compact",
    maximumFractionDigits: 1
  });
  function monthLabel(monthKey) {
    const [year, month] = monthKey.split("-").map(Number);
    return new Date(year, month - 1, 1).toLocaleDateString("en-NG", { month: "short" });
  }
  function niceMax(value) {
    if (value <= 0) return 100;
    const magnitude = 10 ** Math.floor(Math.log10(value));
    const normalized = value / magnitude;
    const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
    return step * magnitude;
  }
  var CHART_HEIGHT_PX = 200;
  function MonthlyTrendsChart({
    data
  }) {
    const [hoverIndex, setHoverIndex] = (0, import_react.useState)(null);
    const maxAmount = Math.max(...data.map((d) => d.amount_kobo), 0);
    const axisMax = niceMax(maxAmount);
    const peakIndex = data.reduce(
      (best, d, i) => d.amount_kobo > (data[best]?.amount_kobo ?? -1) ? i : best,
      0
    );
    const hasActivity = maxAmount > 0;
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs", children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", { className: "text-base font-medium text-heading", children: "Premiums Trend" }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "mt-1 text-sm text-body", children: "Successfully collected premiums, last 6 months." }),
      !hasActivity ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "mt-8 mb-4 text-center text-sm text-body", children: "No premium activity in the last 6 months yet." }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "mt-6 flex gap-3", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
          "div",
          {
            className: "flex w-12 flex-none flex-col justify-between text-right text-xs text-body-subtle",
            style: { height: CHART_HEIGHT_PX },
            children: [
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: COMPACT_NAIRA.format(axisMax / 100) }),
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: COMPACT_NAIRA.format(axisMax / 200) }),
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "0" })
            ]
          }
        ),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "flex-1", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "relative flex items-end justify-between gap-2 border-l border-border-light", children: [
            [0, 0.5, 1].map((fraction) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "div",
              {
                className: "absolute right-0 left-0 border-t border-border-light",
                style: { bottom: fraction * CHART_HEIGHT_PX }
              },
              fraction
            )),
            data.map((point, i) => {
              const heightPx = Math.max(2, point.amount_kobo / axisMax * CHART_HEIGHT_PX);
              return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
                "div",
                {
                  className: "relative flex flex-1 flex-col items-center justify-end",
                  style: { height: CHART_HEIGHT_PX },
                  onMouseEnter: () => setHoverIndex(i),
                  onMouseLeave: () => setHoverIndex(null),
                  onFocus: () => setHoverIndex(i),
                  onBlur: () => setHoverIndex(null),
                  tabIndex: 0,
                  role: "img",
                  "aria-label": `${monthLabel(point.month)}: ${formatNaira(point.amount_kobo)}`,
                  children: [
                    i === peakIndex && point.amount_kobo > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "mb-1 text-xs font-medium text-heading", children: COMPACT_NAIRA.format(point.amount_kobo / 100) }),
                    hoverIndex === i && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "absolute bottom-full z-10 mb-2 rounded-default border border-border-default bg-neutral-primary-soft px-2.5 py-1.5 text-xs whitespace-nowrap shadow-md", children: [
                      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "font-medium text-heading", children: formatNaira(point.amount_kobo) }),
                      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "text-body-subtle", children: monthLabel(point.month) })
                    ] }),
                    /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
                      "div",
                      {
                        className: "w-full max-w-6 rounded-t-sm bg-brand transition-opacity hover:opacity-80",
                        style: { height: heightPx }
                      }
                    )
                  ]
                },
                point.month
              );
            })
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "mt-2 flex justify-between gap-2", children: data.map((point) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "flex-1 text-center text-xs text-body-subtle", children: monthLabel(point.month) }, point.month)) })
        ] })
      ] })
    ] });
  }

  // .design-sync/previews/MonthlyTrendsChart.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  var sixMonths = [
    { month: "2024-01", amount_kobo: 245e6 },
    { month: "2024-02", amount_kobo: 312e6 },
    { month: "2024-03", amount_kobo: 289e6 },
    { month: "2024-04", amount_kobo: 421e6 },
    { month: "2024-05", amount_kobo: 378e6 },
    { month: "2024-06", amount_kobo: 51e7 }
  ];
  var twelveMonths = [
    { month: "2023-07", amount_kobo: 18e7 },
    { month: "2023-08", amount_kobo: 22e7 },
    { month: "2023-09", amount_kobo: 195e6 },
    { month: "2023-10", amount_kobo: 26e7 },
    { month: "2023-11", amount_kobo: 3e8 },
    { month: "2023-12", amount_kobo: 45e7 },
    { month: "2024-01", amount_kobo: 245e6 },
    { month: "2024-02", amount_kobo: 312e6 },
    { month: "2024-03", amount_kobo: 289e6 },
    { month: "2024-04", amount_kobo: 421e6 },
    { month: "2024-05", amount_kobo: 378e6 },
    { month: "2024-06", amount_kobo: 51e7 }
  ];
  function SixMonths() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(MonthlyTrendsChart, { data: sixMonths }) });
  }
  function TwelveMonths() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(MonthlyTrendsChart, { data: twelveMonths }) });
  }
  function Empty() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(MonthlyTrendsChart, { data: [] }) });
  }
  return __toCommonJS(MonthlyTrendsChart_exports);
})();
