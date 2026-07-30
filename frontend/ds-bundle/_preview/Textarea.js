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
      function jsxs3(t, p, k) {
        return R.createElement.apply(R, [t, np(p, k)].concat(p.children));
      }
      module.exports = R;
      module.exports.jsx = jsx3;
      module.exports.jsxs = jsxs3;
      module.exports.jsxDEV = function(t, p, k, s) {
        return (s ? jsxs3 : jsx3)(t, p, k);
      };
      module.exports.Fragment = R.Fragment;
    }
  });

  // .design-sync/previews/Textarea.tsx
  var Textarea_exports = {};
  __export(Textarea_exports, {
    Default: () => Default,
    Disabled: () => Disabled,
    WithError: () => WithError
  });
  init_define_import_meta_env();

  // src/components/ui/Textarea.tsx
  init_define_import_meta_env();
  var import_jsx_runtime = __toESM(require_react_shim());
  function Textarea({ label, id, error, className = "", ...rest }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", { htmlFor: id, className: "mb-2 block text-sm font-medium text-heading", children: label }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
        "textarea",
        {
          id,
          rows: 3,
          className: `block w-full rounded-base border bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs transition-all placeholder:text-body focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:bg-disabled disabled:text-fg-disabled ${error ? "border-border-danger focus:border-border-danger focus:ring-danger" : "border-border-default-medium hover:border-border-default-strong focus:border-border-brand focus:ring-brand"} ${className}`,
          "aria-invalid": Boolean(error),
          "aria-describedby": error ? `${id}-error` : void 0,
          ...rest
        }
      ),
      error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { id: `${id}-error`, className: "mt-1.5 text-sm text-fg-danger", children: error })
    ] });
  }

  // .design-sync/previews/Textarea.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function Default() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "p-4 max-w-sm space-y-4", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Textarea, { id: "notes", label: "Policy notes", placeholder: "Enter any additional notes about this policy…", rows: 4 }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Textarea, { id: "rejection-reason", label: "Rejection reason", placeholder: "Explain why this application is being rejected…", rows: 3 })
    ] });
  }
  function WithError() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-sm", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
      Textarea,
      {
        id: "notes-error",
        label: "Policy notes",
        defaultValue: "x",
        error: "Notes must be at least 20 characters.",
        rows: 4
      }
    ) });
  }
  function Disabled() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-sm", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
      Textarea,
      {
        id: "notes-disabled",
        label: "Submission notes",
        defaultValue: "Policy accepted as-is. No modifications required.",
        disabled: true,
        rows: 3
      }
    ) });
  }
  return __toCommonJS(Textarea_exports);
})();
