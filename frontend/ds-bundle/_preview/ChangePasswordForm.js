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
      function jsx5(t, p, k) {
        var c = p && p.children;
        return c === void 0 ? R.createElement(t, np(p, k)) : R.createElement(t, np(p, k), c);
      }
      function jsxs3(t, p, k) {
        return R.createElement.apply(R, [t, np(p, k)].concat(p.children));
      }
      module.exports = R;
      module.exports.jsx = jsx5;
      module.exports.jsxs = jsxs3;
      module.exports.jsxDEV = function(t, p, k, s) {
        return (s ? jsxs3 : jsx5)(t, p, k);
      };
      module.exports.Fragment = R.Fragment;
    }
  });

  // .design-sync/previews/ChangePasswordForm.tsx
  var ChangePasswordForm_exports = {};
  __export(ChangePasswordForm_exports, {
    Default: () => Default
  });
  init_define_import_meta_env();

  // src/components/forms/ChangePasswordForm.tsx
  init_define_import_meta_env();
  var import_react = __toESM(require_react_shim());

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

  // src/components/ui/Input.tsx
  init_define_import_meta_env();
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function Input({ label, id, error, className = "", ...rest }) {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsxs)("div", { children: [
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("label", { htmlFor: id, className: "mb-2 block text-sm font-medium text-heading", children: label }),
      /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(
        "input",
        {
          id,
          className: `block w-full rounded-base border bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs transition-all placeholder:text-body focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:bg-disabled disabled:text-fg-disabled ${error ? "border-border-danger focus:border-border-danger focus:ring-danger" : "border-border-default-medium hover:border-border-default-strong focus:border-border-brand focus:ring-brand"} ${className}`,
          "aria-invalid": Boolean(error),
          "aria-describedby": error ? `${id}-error` : void 0,
          ...rest
        }
      ),
      error && /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("p", { id: `${id}-error`, className: "mt-1.5 text-sm text-fg-danger", children: error })
    ] });
  }

  // src/components/forms/ChangePasswordForm.tsx
  var import_jsx_runtime3 = __toESM(require_react_shim());
  function ChangePasswordForm() {
    const [currentPassword, setCurrentPassword] = (0, import_react.useState)("");
    const [newPassword, setNewPassword] = (0, import_react.useState)("");
    const [confirmPassword, setConfirmPassword] = (0, import_react.useState)("");
    const [error, setError] = (0, import_react.useState)(null);
    const [submitting, setSubmitting] = (0, import_react.useState)(false);
    async function handleSubmit(event) {
      event.preventDefault();
      setError(null);
      if (newPassword !== confirmPassword) {
        setError("Passwords don't match.");
        return;
      }
      setSubmitting(true);
      try {
        const response = await fetch("/api/auth/change-password", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
          })
        });
        const data = await response.json();
        if (!response.ok) {
          setError(data.detail ?? "Couldn't change your password.");
          return;
        }
        window.location.href = data.orgApproved ? "/dashboard" : "/pending-approval";
      } catch {
        setError("Couldn't reach the server. Check your connection and try again.");
      } finally {
        setSubmitting(false);
      }
    }
    return /* @__PURE__ */ (0, import_jsx_runtime3.jsxs)("form", { onSubmit: handleSubmit, className: "space-y-5", children: [
      error && /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
        "div",
        {
          role: "alert",
          className: "rounded-base border border-border-danger-subtle bg-danger-soft px-4 py-3 text-sm text-fg-danger-strong",
          children: error
        }
      ),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
        Input,
        {
          id: "current-password",
          label: "Current password (or one-time password)",
          type: "password",
          autoComplete: "current-password",
          required: true,
          value: currentPassword,
          onChange: (e) => setCurrentPassword(e.target.value)
        }
      ),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
        Input,
        {
          id: "new-password",
          label: "New password",
          type: "password",
          autoComplete: "new-password",
          required: true,
          minLength: 8,
          value: newPassword,
          onChange: (e) => setNewPassword(e.target.value)
        }
      ),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(
        Input,
        {
          id: "confirm-password",
          label: "Confirm new password",
          type: "password",
          autoComplete: "new-password",
          required: true,
          minLength: 8,
          value: confirmPassword,
          onChange: (e) => setConfirmPassword(e.target.value)
        }
      ),
      /* @__PURE__ */ (0, import_jsx_runtime3.jsx)(Button, { type: "submit", disabled: submitting, className: "w-full", children: submitting ? "Saving…" : "Set new password" })
    ] });
  }

  // .design-sync/previews/ChangePasswordForm.tsx
  var import_jsx_runtime4 = __toESM(require_react_shim());
  function Default() {
    return /* @__PURE__ */ (0, import_jsx_runtime4.jsx)("div", { className: "p-6 max-w-sm", children: /* @__PURE__ */ (0, import_jsx_runtime4.jsx)(ChangePasswordForm, {}) });
  }
  return __toCommonJS(ChangePasswordForm_exports);
})();
