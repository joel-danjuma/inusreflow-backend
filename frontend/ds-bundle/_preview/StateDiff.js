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

  // .design-sync/previews/StateDiff.tsx
  var StateDiff_exports = {};
  __export(StateDiff_exports, {
    BrokerApproval: () => BrokerApproval,
    NewRecord: () => NewRecord,
    PolicyUpdate: () => PolicyUpdate
  });
  init_define_import_meta_env();

  // src/components/audit/StateDiff.tsx
  init_define_import_meta_env();
  var import_jsx_runtime = __toESM(require_react_shim());
  function formatValue(value) {
    if (value === null || value === void 0) return "—";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }
  function StateDiff({
    before,
    after
  }) {
    if (!before && !after) {
      return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "text-sm text-body-subtle", children: "No state recorded for this event." });
    }
    const keys = /* @__PURE__ */ new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})]);
    const rows = [...keys].filter((key) => {
      const beforeValue = before?.[key];
      const afterValue = after?.[key];
      return JSON.stringify(beforeValue) !== JSON.stringify(afterValue);
    });
    if (rows.length === 0) {
      return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "text-sm text-body-subtle", children: "No fields changed." });
    }
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", { className: "w-full text-left text-sm", children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { className: "border-b border-border-default text-body-subtle", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", { className: "py-1.5 pr-4 font-medium", children: "Field" }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", { className: "py-1.5 pr-4 font-medium", children: "Before" }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", { className: "py-1.5 font-medium", children: "After" })
      ] }) }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", { children: rows.map((key) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { className: "border-b border-border-default last:border-b-0", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", { className: "py-1.5 pr-4 font-mono text-xs text-heading", children: key }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", { className: "py-1.5 pr-4 text-fg-danger", children: formatValue(before?.[key]) }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", { className: "py-1.5 text-fg-success-strong", children: formatValue(after?.[key]) })
      ] }, key)) })
    ] });
  }

  // .design-sync/previews/StateDiff.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function PolicyUpdate() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-lg", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
      StateDiff,
      {
        before: {
          status: "active",
          premium_amount_kobo: 45e5,
          premium_frequency: "monthly"
        },
        after: {
          status: "lapsed",
          premium_amount_kobo: 45e5,
          premium_frequency: "monthly"
        }
      }
    ) });
  }
  function BrokerApproval() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-lg", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
      StateDiff,
      {
        before: {
          status: "pending",
          approved_by: null,
          approved_at: null
        },
        after: {
          status: "approved",
          approved_by: "admin@insureflow.com",
          approved_at: "2024-06-15T10:32:00Z"
        }
      }
    ) });
  }
  function NewRecord() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-lg", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
      StateDiff,
      {
        before: null,
        after: {
          name: "Apex Insurance Brokers Ltd",
          status: "pending",
          email: "admin@apexbrokers.com",
          created_at: "2024-06-15T09:00:00Z"
        }
      }
    ) });
  }
  return __toCommonJS(StateDiff_exports);
})();
