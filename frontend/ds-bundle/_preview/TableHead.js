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

  // .design-sync/previews/TableHead.tsx
  var TableHead_exports = {};
  __export(TableHead_exports, {
    Default: () => Default
  });
  init_define_import_meta_env();

  // src/components/ui/Table.tsx
  init_define_import_meta_env();
  var import_jsx_runtime = __toESM(require_react_shim());
  function Table({ children }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "overflow-x-auto rounded-base border border-border-default bg-neutral-primary-soft shadow-xs", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("table", { className: "w-full text-left text-sm text-body", children }) });
  }
  function TableHead({ children }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", { className: "border-b border-border-default bg-neutral-secondary-soft", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tr", { children }) });
  }
  function TableHeaderCell({ children }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", { className: "px-6 py-3 text-sm font-medium text-body", children });
  }
  function TableRow({ children }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tr", { className: "border-b border-border-default last:border-b-0 hover:bg-neutral-secondary-soft", children });
  }

  // .design-sync/previews/TableHead.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function Default() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Table, { children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(TableHead, { children: /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)(TableRow, { children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(TableHeaderCell, { children: "Policyholder" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(TableHeaderCell, { children: "Policy type" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(TableHeaderCell, { children: "Premium" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(TableHeaderCell, { children: "Status" })
    ] }) }) }) });
  }
  return __toCommonJS(TableHead_exports);
})();
