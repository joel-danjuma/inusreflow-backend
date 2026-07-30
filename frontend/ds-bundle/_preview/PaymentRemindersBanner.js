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

  // .design-sync/previews/PaymentRemindersBanner.tsx
  var PaymentRemindersBanner_exports = {};
  __export(PaymentRemindersBanner_exports, {
    ManyOverdue: () => ManyOverdue,
    WithOverdueItems: () => WithOverdueItems
  });
  init_define_import_meta_env();

  // src/components/dashboard/PaymentRemindersBanner.tsx
  init_define_import_meta_env();
  var import_react = __toESM(require_react_shim());
  var import_jsx_runtime = __toESM(require_react_shim());
  function storageKey(overdueCount) {
    return `dismissed:payment-reminders:${overdueCount}`;
  }
  function PaymentRemindersBanner({ overdueCount }) {
    const [dismissed, setDismissed] = (0, import_react.useState)(() => {
      if (overdueCount === 0 || typeof window === "undefined") return overdueCount === 0;
      return window.sessionStorage.getItem(storageKey(overdueCount)) === "1";
    });
    if (overdueCount === 0 || dismissed) return null;
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
      "div",
      {
        role: "alert",
        className: "relative rounded-base border border-border-danger-subtle bg-danger-soft p-4 pr-12",
        children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { className: "text-sm font-medium text-fg-danger-strong", children: [
            overdueCount,
            " overdue ",
            overdueCount === 1 ? "installment needs" : "installments need",
            " ",
            "attention"
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { className: "mt-1 text-sm leading-relaxed text-fg-danger-strong", children: [
            overdueCount === 1 ? "A premium payment is" : "Premium payments are",
            " past due for one or more of your clients. Collect them from the Installments page before they lapse further."
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              type: "button",
              "aria-label": "Dismiss",
              onClick: () => {
                window.sessionStorage.setItem(storageKey(overdueCount), "1");
                setDismissed(true);
              },
              className: "absolute top-3 right-3 rounded-sm p-1 text-fg-danger-strong hover:bg-danger-medium",
              children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("svg", { width: "16", height: "16", viewBox: "0 0 16 16", fill: "none", "aria-hidden": "true", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
                "path",
                {
                  d: "M4 4L12 12M12 4L4 12",
                  stroke: "currentColor",
                  strokeWidth: "1.5",
                  strokeLinecap: "round"
                }
              ) })
            }
          )
        ]
      }
    );
  }

  // .design-sync/previews/PaymentRemindersBanner.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function WithOverdueItems() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-xl", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(PaymentRemindersBanner, { overdueCount: 3 }) });
  }
  function ManyOverdue() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-xl", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(PaymentRemindersBanner, { overdueCount: 12 }) });
  }
  return __toCommonJS(PaymentRemindersBanner_exports);
})();
