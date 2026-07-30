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

  // .design-sync/previews/MaskedField.tsx
  var MaskedField_exports = {};
  __export(MaskedField_exports, {
    AccountNumber: () => AccountNumber,
    Default: () => Default
  });
  init_define_import_meta_env();

  // src/components/pii/MaskedField.tsx
  init_define_import_meta_env();
  var import_react = __toESM(require_react_shim());

  // src/lib/mask.ts
  init_define_import_meta_env();
  function maskTail(value, visibleChars = 4) {
    if (value.length <= visibleChars) return value;
    return `•••• ${value.slice(-visibleChars)}`;
  }

  // src/components/pii/MaskedField.tsx
  var import_jsx_runtime = __toESM(require_react_shim());
  function MaskedField({ value, label }) {
    const [revealed, setRevealed] = (0, import_react.useState)(false);
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "inline-flex items-center gap-2", children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "font-mono text-sm text-heading", children: revealed ? value : maskTail(value) }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
        "button",
        {
          type: "button",
          onClick: () => setRevealed((r) => !r),
          className: "text-xs font-medium text-fg-brand hover:underline",
          "aria-label": revealed ? `Hide ${label}` : `Show ${label}`,
          children: revealed ? "Hide" : "Show"
        }
      )
    ] });
  }

  // .design-sync/previews/MaskedField.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function Default() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-col gap-3 p-4 max-w-sm rounded-base bg-neutral-primary-soft", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-col gap-1", children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "text-xs text-body-subtle", children: "NIN" }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(MaskedField, { label: "NIN", value: "12345678901" })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-col gap-1", children: [
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "text-xs text-body-subtle", children: "BVN" }),
        /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(MaskedField, { label: "BVN", value: "22198765432" })
      ] })
    ] });
  }
  function AccountNumber() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-sm rounded-base bg-neutral-primary-soft", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-col gap-1", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("span", { className: "text-xs text-body-subtle", children: "Bank account number" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(MaskedField, { label: "Bank account number", value: "0123456789" })
    ] }) });
  }
  return __toCommonJS(MaskedField_exports);
})();
