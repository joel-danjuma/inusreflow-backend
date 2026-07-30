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

  // .design-sync/previews/Alert.tsx
  var Alert_exports = {};
  __export(Alert_exports, {
    WithTitle: () => WithTitle,
    WithoutTitle: () => WithoutTitle
  });
  init_define_import_meta_env();

  // src/components/ui/Alert.tsx
  init_define_import_meta_env();
  var import_jsx_runtime = __toESM(require_react_shim());
  var VARIANT_CLASSES = {
    brand: "bg-brand-softer border-border-brand-subtle text-fg-brand-strong",
    success: "bg-success-soft border-border-success-subtle text-fg-success-strong",
    danger: "bg-danger-soft border-border-danger-subtle text-fg-danger-strong",
    warning: "bg-warning-soft border-border-warning-subtle text-fg-warning"
  };
  function Alert({
    variant = "brand",
    title,
    children
  }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { role: "alert", className: `rounded-base border p-4 ${VARIANT_CLASSES[variant]}`, children: [
      title && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "text-sm font-medium", children: title }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "text-sm leading-relaxed", children })
    ] });
  }

  // .design-sync/previews/Alert.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function WithTitle() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-col gap-3 p-4 max-w-md", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Alert, { variant: "brand", title: "Policy updated", children: "Your policy details have been saved and will take effect next billing cycle." }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Alert, { variant: "success", title: "Payment confirmed", children: "₦45,000 collected for policy POL-2024-001. Settlement initiated." }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Alert, { variant: "danger", title: "Payment failed", children: "We couldn't process your payment. Please check your account balance and try again." }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Alert, { variant: "warning", title: "Action required", children: "3 installments are overdue. Please settle outstanding premiums to keep your policy active." })
    ] });
  }
  function WithoutTitle() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { className: "flex flex-col gap-3 p-4 max-w-md", children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Alert, { variant: "brand", children: "Your account is pending admin approval." }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Alert, { variant: "success", children: "Broker onboarded successfully." }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Alert, { variant: "danger", children: "Invalid credentials. Please try again." }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(Alert, { variant: "warning", children: "Your session will expire in 5 minutes." })
    ] });
  }
  return __toCommonJS(Alert_exports);
})();
