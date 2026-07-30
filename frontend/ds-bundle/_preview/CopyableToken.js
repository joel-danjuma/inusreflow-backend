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

  // .design-sync/previews/CopyableToken.tsx
  var CopyableToken_exports = {};
  __export(CopyableToken_exports, {
    Default: () => Default,
    LongToken: () => LongToken
  });
  init_define_import_meta_env();

  // src/components/ui/CopyableToken.tsx
  init_define_import_meta_env();
  var import_react = __toESM(require_react_shim());
  var import_jsx_runtime = __toESM(require_react_shim());
  function CopyableToken({ token }) {
    const [copied, setCopied] = (0, import_react.useState)(false);
    async function handleCopy() {
      await navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2e3);
    }
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "flex items-center gap-2 rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5", children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", { className: "min-w-0 flex-1 truncate font-mono text-sm text-heading", children: token }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
        "button",
        {
          type: "button",
          onClick: handleCopy,
          className: "shrink-0 rounded-default border border-border-default px-2 py-1 text-xs font-medium text-heading transition-colors hover:bg-neutral-tertiary-medium",
          children: copied ? "Copied!" : "Copy"
        }
      )
    ] });
  }

  // .design-sync/previews/CopyableToken.tsx
  var import_jsx_runtime2 = __toESM(require_react_shim());
  function Default() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 space-y-3 max-w-sm", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(CopyableToken, { token: "sk_live_abc123xyz456789" }) });
  }
  function LongToken() {
    return /* @__PURE__ */ (0, import_jsx_runtime2.jsx)("div", { className: "p-4 max-w-md", children: /* @__PURE__ */ (0, import_jsx_runtime2.jsx)(CopyableToken, { token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c" }) });
  }
  return __toCommonJS(CopyableToken_exports);
})();
