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

  // .design-sync/previews/Button.tsx
  var Button_exports = {};
  __export(Button_exports, {
    FullWidth: () => FullWidth,
    Sizes: () => Sizes,
    States: () => States,
    Variants: () => Variants
  });
  init_define_import_meta_env();

  // src/components/ui/Button.tsx
  init_define_import_meta_env();
  var import_jsx_runtime = __toESM(require_react_shim());
  var VARIANT_CLASSES = {
    brand: "bg-brand text-white border-transparent hover:bg-brand-strong focus-visible:ring-brand-medium",
    secondary: "bg-neutral-secondary-medium text-body border-border-default-medium hover:bg-neutral-tertiary-medium hover:text-heading focus-visible:ring-neutral-tertiary",
    tertiary: "bg-neutral-primary-soft text-body border-border-default hover:bg-neutral-secondary-medium hover:text-heading focus-visible:ring-neutral-tertiary-soft",
    success: "bg-success text-white border-transparent hover:bg-success-strong focus-visible:ring-success-medium",
    danger: "bg-danger text-white border-transparent hover:bg-danger-strong focus-visible:ring-danger-medium",
    warning: "bg-warning text-white border-transparent hover:bg-warning-strong focus-visible:ring-warning-medium",
    dark: "bg-dark text-white border-transparent hover:bg-dark-strong focus-visible:ring-neutral-tertiary",
    ghost: "bg-transparent text-heading border-transparent hover:bg-neutral-secondary-medium focus-visible:ring-neutral-tertiary"
  };
  var SIZE_CLASSES = {
    xs: "text-xs px-3 py-1.5",
    sm: "text-sm px-3 py-2",
    base: "text-sm px-4 py-2.5",
    lg: "text-base px-5 py-3",
    xl: "text-base px-6 py-3.5"
  };
  function Button({
    variant = "brand",
    size = "base",
    className = "",
    disabled,
    children,
    ...rest
  }) {
    const hasGlint = variant !== "ghost" && !disabled;
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
      "button",
      {
        className: `inline-flex items-center justify-center gap-2 rounded-base border font-medium whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:border-border-default-medium disabled:bg-disabled disabled:text-fg-disabled ${hasGlint ? "glint" : ""} ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`,
        disabled,
        ...rest,
        children
      }
    );
  }

  // .design-sync/previews/Button.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function Variants() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-wrap gap-3 p-4", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "brand", children: "Brand" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "secondary", children: "Secondary" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "tertiary", children: "Tertiary" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "success", children: "Success" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "danger", children: "Danger" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "warning", children: "Warning" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "dark", children: "Dark" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "ghost", children: "Ghost" })
    ] });
  }
  function Sizes() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-wrap items-center gap-3 p-4", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { size: "xs", children: "Extra small" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { size: "sm", children: "Small" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { size: "base", children: "Base" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { size: "lg", children: "Large" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { size: "xl", children: "Extra large" })
    ] });
  }
  function States() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-wrap gap-3 p-4", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "brand", children: "Active" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "brand", disabled: true, children: "Disabled" }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "secondary", disabled: true, children: "Secondary disabled" })
    ] });
  }
  function FullWidth() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 w-64", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Button, { variant: "brand", className: "w-full", children: "Sign in" }) });
  }
  return __toCommonJS(Button_exports);
})();
