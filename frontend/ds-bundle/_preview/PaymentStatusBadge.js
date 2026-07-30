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
      function jsx4(t, p, k) {
        var c = p && p.children;
        return c === void 0 ? R.createElement(t, np(p, k)) : R.createElement(t, np(p, k), c);
      }
      function jsxs2(t, p, k) {
        return R.createElement.apply(R, [t, np(p, k)].concat(p.children));
      }
      module.exports = R;
      module.exports.jsx = jsx4;
      module.exports.jsxs = jsxs2;
      module.exports.jsxDEV = function(t, p, k, s) {
        return (s ? jsxs2 : jsx4)(t, p, k);
      };
      module.exports.Fragment = R.Fragment;
    }
  });

  // .design-sync/previews/PaymentStatusBadge.tsx
  var PaymentStatusBadge_exports = {};
  __export(PaymentStatusBadge_exports, {
    AllStatuses: () => AllStatuses
  });
  init_define_import_meta_env();

  // src/components/badges/StatusBadge.tsx
  init_define_import_meta_env();

  // src/components/ui/Badge.tsx
  init_define_import_meta_env();
  var import_jsx_runtime = __toESM(require_react_shim());
  var VARIANT_CLASSES = {
    brand: "bg-brand-softer border-border-brand-subtle text-fg-brand-strong",
    neutral: "bg-neutral-primary-soft border-border-default text-heading",
    gray: "bg-neutral-secondary-medium border-border-default text-heading",
    danger: "bg-danger-soft border-border-danger-subtle text-fg-danger-strong",
    success: "bg-success-soft border-border-success-subtle text-fg-success-strong",
    warning: "bg-warning-soft border-border-warning-subtle text-fg-warning",
    dark: "bg-dark border-transparent text-white"
  };
  function Badge({
    variant = "neutral",
    children
  }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
      "span",
      {
        className: `inline-flex items-center rounded-default border px-1.5 py-0.5 text-xs font-medium ${VARIANT_CLASSES[variant]}`,
        children
      }
    );
  }

  // src/lib/enums.ts
  init_define_import_meta_env();
  var PAYMENT_STATUS = {
    initiated: { label: "In progress", variant: "brand" },
    success: { label: "Success", variant: "success" },
    mismatch: { label: "Mismatch (auto-refunded)", variant: "warning" },
    expired: { label: "Expired (auto-refunded)", variant: "warning" },
    failed: { label: "Failed", variant: "danger" }
  };

  // src/components/badges/StatusBadge.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function PaymentStatusBadge({ status }) {
    const { label, variant } = PAYMENT_STATUS[status];
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Badge, { variant, children: label });
  }

  // .design-sync/previews/PaymentStatusBadge.tsx
  var import_jsx_runtime3 = __toESM(require_react_shim());
  function AllStatuses() {
    return /* @__PURE__ */ (0, import_jsx_runtime3.jsxs)("div", { className: "flex flex-wrap gap-2 p-4", children: [
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(PaymentStatusBadge, { status: "initiated" }),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(PaymentStatusBadge, { status: "success" }),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(PaymentStatusBadge, { status: "mismatch" }),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(PaymentStatusBadge, { status: "expired" }),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(PaymentStatusBadge, { status: "failed" })
    ] });
  }
  return __toCommonJS(PaymentStatusBadge_exports);
})();
