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

  // .design-sync/previews/Money.tsx
  var Money_exports = {};
  __export(Money_exports, {
    Default: () => Default,
    InContext: () => InContext
  });
  init_define_import_meta_env();

  // src/components/money/Money.tsx
  init_define_import_meta_env();

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

  // src/components/money/Money.tsx
  var import_jsx_runtime = __toESM(require_react_shim());
  function Money({ kobo, className }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: `tabular-nums ${className ?? ""}`, children: formatNaira(kobo) });
  }

  // .design-sync/previews/Money.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function Default() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-col gap-2 p-4", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "text-2xl font-semibold", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Money, { kobo: 45e4 }) }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "text-xl", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Money, { kobo: 12e6 }) }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "text-base text-body", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Money, { kobo: 100 }) })
    ] });
  }
  function InContext() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-col gap-4 p-4", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex justify-between items-center border-b border-border-default pb-3", children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "text-sm text-body", children: "Premium amount" }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "font-medium", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Money, { kobo: 45e5 }) })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex justify-between items-center border-b border-border-default pb-3", children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "text-sm text-body", children: "Commission (GTBank)" }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "font-medium text-fg-success-strong", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Money, { kobo: 22500 }) })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex justify-between items-center border-b border-border-default pb-3", children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "text-sm text-body", children: "Commission (Insureflow)" }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "font-medium text-fg-success-strong", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Money, { kobo: 22500 }) })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex justify-between items-center", children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "text-sm font-semibold text-heading", children: "Insurer payable" }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "font-semibold", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Money, { kobo: 4455e3 }) })
      ] })
    ] });
  }
  return __toCommonJS(Money_exports);
})();
