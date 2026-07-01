"""
Generates docs/Insureflow_API_Reference.pdf — the external-facing API reference
for insurance companies and their brokers. Run with:
    uv run python scripts/generate_api_docs.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_PATH = Path(__file__).parent.parent / "docs" / "Insureflow_API_Reference.pdf"

# ── Colour palette ────────────────────────────────────────────────────────────
BRAND       = colors.HexColor("#1A3C5E")   # deep navy
ACCENT      = colors.HexColor("#2E7D9F")   # teal
POST_COL    = colors.HexColor("#2E7D9F")
GET_COL     = colors.HexColor("#2E8B57")
PATCH_COL   = colors.HexColor("#B8860B")
LIGHT_GREY  = colors.HexColor("#F4F6F8")
MID_GREY    = colors.HexColor("#DEE2E6")
CODE_BG     = colors.HexColor("#F0F3F7")
TEXT        = colors.HexColor("#1C1C1E")
MUTED       = colors.HexColor("#6C757D")

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

STYLES = {
    "cover_title": S("cover_title", fontSize=32, leading=40, textColor=colors.white,
                     alignment=TA_CENTER, fontName="Helvetica-Bold"),
    "cover_sub":   S("cover_sub",   fontSize=14, leading=20, textColor=colors.HexColor("#C8D8E8"),
                     alignment=TA_CENTER, fontName="Helvetica"),
    "cover_meta":  S("cover_meta",  fontSize=10, leading=14, textColor=colors.HexColor("#A0B8CC"),
                     alignment=TA_CENTER, fontName="Helvetica"),
    "h1":          S("h1",  fontSize=22, leading=28, textColor=BRAND, fontName="Helvetica-Bold",
                     spaceBefore=14, spaceAfter=6),
    "h2":          S("h2",  fontSize=15, leading=20, textColor=BRAND, fontName="Helvetica-Bold",
                     spaceBefore=12, spaceAfter=4),
    "h3":          S("h3",  fontSize=12, leading=16, textColor=ACCENT, fontName="Helvetica-Bold",
                     spaceBefore=8, spaceAfter=3),
    "body":        S("body", fontSize=10, leading=15, textColor=TEXT, fontName="Helvetica"),
    "body_small":  S("body_small", fontSize=9, leading=13, textColor=TEXT, fontName="Helvetica"),
    "note":        S("note", fontSize=9, leading=13, textColor=MUTED, fontName="Helvetica-Oblique"),
    "code":        S("code", fontSize=9, leading=13, textColor=colors.HexColor("#2D2D2D"),
                     fontName="Courier", backColor=CODE_BG, leftIndent=8, rightIndent=8,
                     spaceBefore=2, spaceAfter=2),
    "bullet":      S("bullet", fontSize=10, leading=15, textColor=TEXT, fontName="Helvetica",
                     leftIndent=14, bulletIndent=4),
    "toc_entry":   S("toc_entry", fontSize=10, leading=16, textColor=BRAND, fontName="Helvetica"),
}

W, H = A4  # 595.27 x 841.89 pt


# ── Helpers ───────────────────────────────────────────────────────────────────

def hr(color=MID_GREY, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=4)

def sp(h=0.3):
    return Spacer(1, h * cm)

def p(text, style="body"):
    return Paragraph(text, STYLES[style])

def code(text):
    return Paragraph(text, STYLES["code"])

def method_badge(method):
    col = {"POST": POST_COL, "GET": GET_COL, "PATCH": PATCH_COL}.get(method, ACCENT)
    return (
        f'<font color="white"><b> {method} </b></font>',
        col,
    )

def route_header(method, path, title):
    """Returns a Table row with coloured method badge + path + title."""
    badge_text, badge_col = method_badge(method)
    badge = Paragraph(badge_text, ParagraphStyle(
        "badge", fontSize=9, leading=12, textColor=colors.white,
        fontName="Helvetica-Bold", alignment=TA_CENTER))
    path_p = Paragraph(f"<b>{path}</b>", ParagraphStyle(
        "path", fontSize=11, leading=14, textColor=BRAND, fontName="Courier-Bold"))
    title_p = Paragraph(title, ParagraphStyle(
        "rtitle", fontSize=10, leading=13, textColor=MUTED, fontName="Helvetica-Oblique"))
    tbl = Table(
        [[badge, path_p, title_p]],
        colWidths=[1.6*cm, 9.5*cm, None],
        rowHeights=[0.7*cm],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), badge_col),
        ("BACKGROUND", (1, 0), (-1, 0), LIGHT_GREY),
        ("ALIGN",      (0, 0), (0, 0), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return tbl

def param_table(rows, title="Parameters"):
    """rows: list of (name, type, required, description)"""
    header = [
        Paragraph("<b>Field</b>",       STYLES["body_small"]),
        Paragraph("<b>Type</b>",        STYLES["body_small"]),
        Paragraph("<b>Required</b>",    STYLES["body_small"]),
        Paragraph("<b>Description</b>", STYLES["body_small"]),
    ]
    data = [header] + [
        [Paragraph(f"<font name='Courier'>{n}</font>", STYLES["body_small"]),
         Paragraph(f"<i>{t}</i>", STYLES["body_small"]),
         Paragraph("Yes" if r else "No", STYLES["body_small"]),
         Paragraph(d, STYLES["body_small"])]
        for n, t, r, d in rows
    ]
    tbl = Table(data, colWidths=[3.5*cm, 2.5*cm, 1.8*cm, 9.2*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID",         (0, 0), (-1, -1), 0.3, MID_GREY),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl

def response_table(rows):
    """rows: list of (field, type, description)"""
    header = [
        Paragraph("<b>Field</b>",       STYLES["body_small"]),
        Paragraph("<b>Type</b>",        STYLES["body_small"]),
        Paragraph("<b>Description</b>", STYLES["body_small"]),
    ]
    data = [header] + [
        [Paragraph(f"<font name='Courier'>{n}</font>", STYLES["body_small"]),
         Paragraph(f"<i>{t}</i>", STYLES["body_small"]),
         Paragraph(d, STYLES["body_small"])]
        for n, t, d in rows
    ]
    tbl = Table(data, colWidths=[4*cm, 2.8*cm, 10.2*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("GRID",         (0, 0), (-1, -1), 0.3, MID_GREY),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


# ── Cover page ────────────────────────────────────────────────────────────────

def cover_page():
    # Full-page navy rectangle drawn via a 1-row table
    cover = Table(
        [[Paragraph("", STYLES["cover_title"])]],
        colWidths=[W - 4*cm],
        rowHeights=[H - 4*cm],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND),
    ]))

    title_block = Table(
        [
            [Paragraph("Insureflow", STYLES["cover_title"])],
            [sp(0.4)],
            [Paragraph("API Reference", STYLES["cover_title"])],
            [sp(0.6)],
            [Paragraph("Integration Guide for Insurance Companies &amp; Brokers",
                       STYLES["cover_sub"])],
            [sp(1.2)],
            [Paragraph("Version 1.0  ·  Confidential", STYLES["cover_meta"])],
        ],
        colWidths=[W - 4*cm],
    )
    title_block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [title_block, PageBreak()]


# ── Document sections ─────────────────────────────────────────────────────────

def overview_section():
    return [
        p("Overview", "h1"), hr(BRAND, 1),
        sp(0.2),
        p("This document describes the Insureflow REST API for <b>Insurance Company Admins</b> "
          "and their <b>Broker Admins / Broker Staff</b>. It covers every endpoint your "
          "team will interact with — from onboarding and authentication through policyholder "
          "management, premium collection, and viewing commission configurations."),
        sp(0.3),
        p("Endpoints reserved for the Insureflow platform operator (approval workflows, "
          "settlement retries, system metrics) are intentionally omitted from this guide."),
        sp(0.4),

        p("Base URL", "h2"),
        code("https://api.insureflow.tech/api/v1"),
        p("All paths in this document are relative to the base URL above. Replace the host "
          "with the sandbox base URL during integration testing:", "body_small"),
        code("https://sandbox.api.insureflow.tech/api/v1"),
        sp(0.4),

        p("Authentication", "h2"),
        p("All authenticated endpoints require a <b>Bearer token</b> obtained from "
          "<font name='Courier'>POST /auth/login</font>. Pass it in every request:"),
        code("Authorization: Bearer &lt;access_token&gt;"),
        sp(0.2),
        p("Tokens expire after <b>60 minutes</b>. Re-authenticate to obtain a fresh token."),
        sp(0.4),

        p("Money &amp; Rate Conventions", "h2"),
        p("All monetary amounts throughout the API are expressed as <b>integer kobo</b> "
          "(1 NGN = 100 kobo). Floats are never used for money. Example: ₦5,000 is sent "
          "and returned as <font name='Courier'>500000</font>.", "body"),
        sp(0.2),
        p("Commission rates are expressed as <b>integer basis points (bps)</b> "
          "(1 bps = 0.01%). Example: 0.5% = <font name='Courier'>50</font> bps."),
        sp(0.4),

        p("Idempotency", "h2"),
        p("Payment endpoints (<font name='Courier'>POST /payments</font> and "
          "<font name='Courier'>POST /payments/bulk</font>) require an "
          "<font name='Courier'>Idempotency-Key</font> header — a UUID v4 you generate "
          "per request. Replaying the same key returns the original response without "
          "creating a duplicate charge. Use a new key for every genuinely new payment attempt."),
        code("Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000"),
        sp(0.4),

        p("Error Responses", "h2"),
        p("All errors return JSON with a <font name='Courier'>detail</font> string:"),
        code('{ "detail": "human-readable error message" }'),
        sp(0.2),
        param_table([
            ("400", "HTTP status", False, "Validation error — check the detail for the specific field or rule that failed."),
            ("401", "HTTP status", False, "Missing or expired Bearer token."),
            ("403", "HTTP status", False, "Authenticated but not permitted for this resource."),
            ("404", "HTTP status", False, "Resource not found, or not owned by your tenant."),
            ("409", "HTTP status", False, "Conflict — e.g. duplicate payment, broker has no active insurer assignment."),
            ("422", "HTTP status", False, "Business rule violation — e.g. installment not in a payable status."),
            ("502", "HTTP status", False, "Upstream payment gateway error (Squad). Retry after a short delay."),
        ], title="HTTP status codes"),
        sp(0.4),

        p("Rate Limiting", "h2"),
        p("Payment endpoints are rate-limited per broker account (<b>60 requests/min</b>) "
          "and per IP address (<b>120 requests/min</b>). Exceeding either limit returns "
          "<b>HTTP 429</b>. These limits are designed to prevent runaway automation, not "
          "normal bulk workflows."),
        sp(0.4),

        p("Roles &amp; Permissions", "h2"),
        p("Four roles govern access. This guide covers the bottom three:"),
        param_table([
            ("Insurance Company Admin", "Role", False,
             "Full access to own company: set settlement account, manage broker commission rates, view all installments/reminders under the company."),
            ("Broker Admin", "Role", False,
             "Full broker access: create policyholders, policies, submit payments, manage broker staff."),
            ("Broker Staff", "Role", False,
             "Same as Broker Admin except cannot create or manage other staff accounts."),
        ], title="Roles"),
        PageBreak(),
    ]


def auth_section():
    return [
        p("1. Authentication", "h1"), hr(BRAND, 1), sp(0.2),
        p("Both Insurance Company Admins and Broker Admins/Staff use the same two endpoints "
          "to activate their account on first login and to obtain a JWT on subsequent logins."),
        sp(0.3),

        # ── POST /auth/activate ──────────────────────────────────────────────
        route_header("POST", "/auth/activate", "Activate a new account"), sp(0.2),
        p("Called once after receiving an activation token. Sets the account password "
          "and marks the account active. The token is single-use and expires on first use."),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("token",    "string", True,  "The one-time activation token provided by Insureflow upon approval."),
            ("password", "string", True,  "Chosen password. Min 8 characters. Must contain at least one uppercase letter and one digit."),
        ]),
        sp(0.2),
        p("Response", "h3"),
        p("HTTP 204 No Content on success. No response body."),
        sp(0.4),

        # ── POST /auth/login ─────────────────────────────────────────────────
        route_header("POST", "/auth/login", "Obtain a Bearer token"), sp(0.2),
        p("Standard OAuth2 password flow. Sends credentials as "
          "<b>application/x-www-form-urlencoded</b> (form data, not JSON)."),
        sp(0.2),
        p("Request form fields", "h3"),
        param_table([
            ("username", "string", True, "The account email address."),
            ("password", "string", True, "The account password."),
        ]),
        sp(0.2),
        p("Response body", "h3"),
        response_table([
            ("access_token", "string", "JWT Bearer token. Valid for 60 minutes."),
            ("token_type",   "string", 'Always "bearer".'),
        ]),
        sp(0.2),
        p("Note: login is blocked while the parent organisation (insurance company or broker) "
          "is in <font name='Courier'>pending</font>, <font name='Courier'>rejected</font>, "
          "or <font name='Courier'>suspended</font> status.", "note"),
        PageBreak(),
    ]


def insurance_company_section():
    return [
        p("2. Insurance Company", "h1"), hr(BRAND, 1), sp(0.2),
        p("These endpoints are used by the <b>Insurance Company Admin</b> role. "
          "Onboarding (POST) is unauthenticated — all other endpoints require a "
          "valid Insurance Company Admin Bearer token."),
        sp(0.3),

        # ── POST /insurance-companies ────────────────────────────────────────
        route_header("POST", "/insurance-companies", "Submit onboarding application"), sp(0.2),
        p("Registers a new insurance company with Insureflow. No authentication required. "
          "The company starts in <font name='Courier'>pending</font> status and must be "
          "approved by an Insureflow operator before the contact email's account is activated."),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("name",          "string",  True, "Legal name of the insurance company."),
            ("contact_email", "string",  True, "Email address of the primary admin contact. "
                                               "An activation token will be sent to this address upon approval."),
        ]),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("id",             "UUID",     "Unique identifier for this insurance company. Store this — it is required in many subsequent calls."),
            ("name",           "string",   "Company name as registered."),
            ("contact_email",  "string",   "Admin contact email."),
            ("status",         "string",   "Onboarding status: pending | approved | rejected | suspended."),
            ("rejection_reason","string",  "Populated if status is rejected. null otherwise."),
            ("settlement_bank_code",    "string", "null until set via the settlement-account endpoint."),
            ("settlement_account_number","string","null until set via the settlement-account endpoint."),
            ("settlement_account_name", "string", "null until set via the settlement-account endpoint."),
            ("created_at",     "datetime", "ISO 8601 UTC timestamp."),
        ]),
        sp(0.4),

        # ── GET /insurance-companies/{company_id} ────────────────────────────
        route_header("GET", "/insurance-companies/{company_id}", "Get company details"), sp(0.2),
        p("Returns the current state of the insurance company record. Only accessible "
          "to the Insurance Company Admin of that specific company."),
        sp(0.2),
        p("Path parameters", "h3"),
        param_table([
            ("company_id", "UUID", True, "The insurance company's UUID (from the onboarding response)."),
        ]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Same fields as the 201 response above."),
        sp(0.4),

        # ── POST /insurance-companies/{company_id}/settlement-account ────────
        route_header("POST", "/insurance-companies/{company_id}/settlement-account",
                     "Set settlement bank account"), sp(0.2),
        p("Registers the GTBank account where Insureflow will transfer premium proceeds "
          "(net of commission) after each successful payment. Performs a live name-enquiry "
          "lookup against the Nigerian Interbank Settlement System (NIBSS) to verify the "
          "account before saving — the response includes the confirmed "
          "<font name='Courier'>settlement_account_name</font>."),
        sp(0.2),
        p("This step is required for settlement payouts to fire. Without it, payments "
          "can still be collected but proceeds will not be transferred to the insurer "
          "until a settlement account is on file.", "note"),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("bank_code",      "string", True,
             "6-digit NIP institution code for the destination bank. "
             "Examples: GTBank = 000013, Access Bank = 000014, Zenith Bank = 000015, "
             "First Bank = 000016, UBA = 000004. Note: this is NOT the 3-digit CBN code."),
            ("account_number", "string", True,
             "10-digit NUBAN account number at that bank."),
        ]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Returns the updated insurance company object. "
          "<font name='Courier'>settlement_account_name</font> will be populated with the "
          "name returned by the live NIBSS lookup."),
        sp(0.2),
        p("Important: the live NIBSS lookup is performed even in the sandbox environment. "
          "You must supply a real account number — dummy values will return HTTP 424.", "note"),
        PageBreak(),
    ]


def broker_section():
    return [
        p("3. Broker", "h1"), hr(BRAND, 1), sp(0.2),
        p("Broker onboarding is initiated by the broker themselves (unauthenticated). "
          "The broker must be approved by Insureflow <i>and</i> assigned to your insurance "
          "company before their account can be used to create policyholders or collect "
          "payments. Staff management requires a Broker Admin token."),
        sp(0.3),

        # ── POST /brokers ────────────────────────────────────────────────────
        route_header("POST", "/brokers", "Submit broker onboarding application"), sp(0.2),
        p("No authentication required. The broker starts in "
          "<font name='Courier'>pending</font> status."),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("name",          "string", True, "Legal name of the broker organisation."),
            ("contact_email", "string", True, "Primary admin email. An activation token is sent here upon approval and insurer assignment."),
        ]),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("id",              "UUID",     "Broker UUID. Store this."),
            ("name",            "string",   "Broker name."),
            ("contact_email",   "string",   "Admin contact email."),
            ("status",          "string",   "pending | approved | rejected | suspended."),
            ("rejection_reason","string",   "Populated if rejected. null otherwise."),
            ("created_at",      "datetime", "ISO 8601 UTC."),
        ]),
        sp(0.4),

        # ── GET /brokers/{broker_id} ─────────────────────────────────────────
        route_header("GET", "/brokers/{broker_id}", "Get broker details"), sp(0.2),
        p("Broker Admins and Staff can only retrieve their own broker record."),
        sp(0.2),
        p("Path parameters", "h3"),
        param_table([("broker_id", "UUID", True, "The broker's UUID.")]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Same fields as the 201 response above."),
        sp(0.4),

        # ── POST /brokers/{broker_id}/staff ──────────────────────────────────
        route_header("POST", "/brokers/{broker_id}/staff",
                     "Create a broker staff account (Broker Admin only)"), sp(0.2),
        p("Creates an additional login account scoped to the same broker organisation, "
          "with the <b>Broker Staff</b> role (can create policyholders and collect payments "
          "but cannot manage other staff). Returns a single-use activation token."),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("email", "string", True, "Email address for the new staff account."),
        ]),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("activation_token", "string",
             "One-time token. Relay this to the new staff member — "
             "they call POST /auth/activate to set their password. "
             "The token is not stored and cannot be retrieved again."),
        ]),
        PageBreak(),
    ]


def policyholder_section():
    return [
        p("4. Policyholders", "h1"), hr(BRAND, 1), sp(0.2),
        p("Policyholders are the insured individuals whose premiums brokers collect. "
          "All policyholder endpoints require a <b>Broker Admin or Broker Staff</b> token. "
          "Policyholders are scoped to the broker's active insurance company assignment — "
          "the insurance company context is derived server-side from the token, never sent "
          "by the caller."),
        sp(0.2),
        p("Note: the API path uses <font name='Courier'>/users</font> for policyholders "
          "for legacy compatibility reasons.", "note"),
        sp(0.3),

        # ── POST /users ──────────────────────────────────────────────────────
        route_header("POST", "/users", "Create a policyholder"), sp(0.2),
        p("Registers a new policyholder in the system. At least "
          "<font name='Courier'>full_name</font> is required; the remaining fields are "
          "optional but recommended for reminder delivery and identity verification."),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("full_name",             "string",  True,  "Full legal name of the policyholder."),
            ("email",                 "string",  False, "Email address for payment reminders. Optional."),
            ("phone_number",          "string",  False, "Phone number in local format, e.g. 08012345678. Optional."),
            ("identification_number", "string",  False, "Government ID number (NIN, passport, etc.). Stored encrypted at rest. Optional."),
        ]),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("id",                    "UUID",     "Policyholder UUID. Required when creating a policy."),
            ("broker_id",             "UUID",     "The broker who created this record."),
            ("insurance_company_id",  "UUID",     "The insurance company this policyholder belongs to."),
            ("full_name",             "string",   "Full name as provided."),
            ("email",                 "string",   "null if not provided."),
            ("phone_number",          "string",   "null if not provided."),
            ("identification_number", "string",   "null if not provided. Masked in responses."),
            ("created_at",            "datetime", "ISO 8601 UTC."),
        ]),
        sp(0.4),

        # ── GET /users/{policyholder_id} ─────────────────────────────────────
        route_header("GET", "/users/{policyholder_id}", "Get a policyholder"), sp(0.2),
        p("Path parameters", "h3"),
        param_table([("policyholder_id", "UUID", True, "The policyholder's UUID.")]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Same fields as the 201 response above."),
        sp(0.4),

        # ── GET /users ───────────────────────────────────────────────────────
        route_header("GET", "/users", "List policyholders"), sp(0.2),
        p("Returns all policyholders under the requesting broker. Insurance Company Admins "
          "can pass any broker_id under their company to view that broker's policyholders."),
        sp(0.2),
        p("Query parameters", "h3"),
        param_table([
            ("broker_id", "UUID", True, "Filter by broker. Broker roles can only query their own broker_id."),
        ]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Array of policyholder objects."),
        PageBreak(),
    ]


def policy_section():
    return [
        p("5. Policies", "h1"), hr(BRAND, 1), sp(0.2),
        p("A policy records the terms of a policyholder's cover: premium amount, "
          "payment frequency, and start date. Creating a policy automatically generates "
          "a rolling window of <b>12 upcoming installment rows</b> in "
          "<font name='Courier'>due</font> status — one per payment period. "
          "All policy endpoints require a <b>Broker</b> or <b>Insurance Company Admin</b> token."),
        sp(0.3),

        # ── POST /policies ───────────────────────────────────────────────────
        route_header("POST", "/policies", "Create a policy"), sp(0.2),
        p("Requires a Broker Admin or Broker Staff token."),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("policyholder_id",    "UUID",   True,
             "UUID of the policyholder this policy covers."),
            ("premium_amount_kobo","integer",True,
             "Premium amount per payment period, in <b>kobo</b>. "
             "Must be greater than 0. Example: ₦5,000 = 500000."),
            ("premium_frequency",  "string", True,
             "Payment schedule. One of: <b>monthly</b> | <b>quarterly</b> | <b>annually</b>."),
            ("start_date",         "date",   True,
             "Policy commencement date in ISO 8601 format (YYYY-MM-DD). "
             "The first installment due date is derived from this."),
            ("policy_type",        "string", False,
             "Open string label for the type of cover. Defaults to GENERIC. "
             "Examples: LIFE, MOTOR, HEALTH — any string is accepted."),
        ]),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("id",                   "UUID",     "Policy UUID. Required to list installments."),
            ("policyholder_id",      "UUID",     "The covered policyholder."),
            ("broker_id",            "UUID",     "The broker who created this policy."),
            ("insurance_company_id", "UUID",     "The underwriting insurance company."),
            ("policy_type",          "string",   "Policy type label."),
            ("premium_amount_kobo",  "integer",  "Per-period premium amount in kobo."),
            ("premium_frequency",    "string",   "monthly | quarterly | annually."),
            ("start_date",           "date",     "Policy start date (YYYY-MM-DD)."),
            ("status",               "string",   "active | cancelled."),
            ("created_at",           "datetime", "ISO 8601 UTC."),
        ]),
        sp(0.4),

        # ── GET /policies/{policy_id} ────────────────────────────────────────
        route_header("GET", "/policies/{policy_id}", "Get a policy"), sp(0.2),
        param_table([("policy_id", "UUID", True, "The policy UUID.")]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Same fields as the 201 response above."),
        sp(0.4),

        # ── GET /policies ────────────────────────────────────────────────────
        route_header("GET", "/policies", "List policies for a policyholder"), sp(0.2),
        p("Query parameters", "h3"),
        param_table([
            ("user_id", "UUID", True, "The policyholder UUID to retrieve policies for."),
        ]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Array of policy objects."),
        sp(0.4),

        # ── GET /policies/{policy_id}/installments ───────────────────────────
        route_header("GET", "/policies/{policy_id}/installments",
                     "List installments for a policy"), sp(0.2),
        p("Returns all installment rows for the given policy, ordered by "
          "<font name='Courier'>due_date</font> ascending."),
        sp(0.2),
        p("Path parameters", "h3"),
        param_table([("policy_id", "UUID", True, "The policy UUID.")]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        response_table([
            ("id",         "UUID",    "Installment UUID. Required when initiating a payment."),
            ("policy_id",  "UUID",    "The parent policy."),
            ("due_date",   "date",    "Date this installment is due (YYYY-MM-DD)."),
            ("amount_kobo","integer", "Amount due for this installment in kobo."),
            ("status",     "string",  "due | overdue | paid | cancelled. "
                                      "Overdue is set automatically by a daily scheduled job "
                                      "when due_date has passed. Only due and overdue installments "
                                      "can be paid."),
            ("created_at", "datetime","ISO 8601 UTC."),
        ]),
        PageBreak(),
    ]


def installments_section():
    return [
        p("6. Installments", "h1"), hr(BRAND, 1), sp(0.2),
        p("Cross-policy installment listing — useful for building a dashboard of "
          "all upcoming or overdue payments across every policy under a broker. "
          "For installments under a single known policy, use "
          "<font name='Courier'>GET /policies/{policy_id}/installments</font> instead."),
        sp(0.3),

        # ── GET /installments ────────────────────────────────────────────────
        route_header("GET", "/installments", "List installments"), sp(0.2),
        p("Results are automatically scoped to the caller's visibility: "
          "Broker roles see only their own broker's installments; "
          "Insurance Company Admins see all installments under their company."),
        sp(0.2),
        p("Query parameters", "h3"),
        param_table([
            ("status", "string", False,
             "Optional filter. One of: <b>due</b> | <b>overdue</b> | <b>paid</b> | <b>cancelled</b>. "
             "Omit to return all statuses."),
        ]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Array of installment objects. Same fields as listed in section 5 "
          "(GET /policies/{policy_id}/installments)."),
        sp(0.2),
        p("Installment statuses explained:", "h3"),
        param_table([
            ("due",       "status", False, "Payment is not yet past its due date. Payable."),
            ("overdue",   "status", False, "Past due date and not yet paid. Still payable. "
                                           "Set automatically by a daily scheduled job."),
            ("paid",      "status", False, "Successfully collected. Not payable again."),
            ("cancelled", "status", False, "Cancelled. Not payable."),
        ], title="Installment statuses"),
        PageBreak(),
    ]


def payments_section():
    return [
        p("7. Payments", "h1"), hr(BRAND, 1), sp(0.2),
        p("Premium payments are initiated by <b>Broker Admins or Broker Staff</b>. "
          "Insureflow creates a <b>Squad Dynamic Virtual Account</b> (DVA) for each "
          "payment — a short-lived Nigerian bank account number scoped to the exact "
          "amount due. The policyholder (or broker on their behalf) transfers that "
          "exact amount into the virtual account before it expires."),
        sp(0.2),
        p("Once the transfer is detected, Insureflow independently verifies it with "
          "the payment gateway and — on confirmation — marks the installment paid, "
          "posts the accounting entries, and triggers a real-time settlement payout "
          "to the insurance company's registered settlement account.", "body"),
        sp(0.2),
        p("Key constraints:", "h3"),
        p("• Only installments with status <b>due</b> or <b>overdue</b> can be paid.", "bullet"),
        p("• The broker must be actively assigned to the insurer that owns the policy.", "bullet"),
        p("• Both single and bulk endpoints are idempotent via the Idempotency-Key header.", "bullet"),
        p("• Rate limit: 60 requests/min per broker, 120/min per IP.", "bullet"),
        sp(0.3),

        # ── POST /payments ───────────────────────────────────────────────────
        route_header("POST", "/payments", "Initiate a single payment"), sp(0.2),
        p("Creates a payment for one installment. Returns a virtual account number "
          "and bank that the payer must transfer the exact installment amount into before "
          "the VA expires (default expiry: <b>30 minutes</b>)."),
        sp(0.2),
        p("Required headers", "h3"),
        param_table([
            ("Authorization",  "string", True, "Bearer &lt;broker_access_token&gt;"),
            ("Idempotency-Key","UUID",   True, "A UUID v4 you generate per payment attempt. "
                                               "Replaying the same key within the expiry window "
                                               "returns the original response without a new charge."),
        ]),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("installment_id", "UUID", True,
             "UUID of the due or overdue installment to collect."),
        ]),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("id",                         "UUID",     "Payment UUID. Use this to poll status."),
            ("installment_id",             "UUID",     "The installment being collected."),
            ("broker_id",                  "UUID",     "The initiating broker."),
            ("insurance_company_id",       "UUID",     "The underwriting insurer."),
            ("amount_kobo",                "integer",  "Amount to transfer, in kobo. The payer MUST transfer exactly this amount."),
            ("status",                     "string",   "initiated on creation. See status table below."),
            ("squad_transaction_ref",      "string",   "Insureflow's unique reference for this payment with the gateway."),
            ("squad_virtual_account_number","string",  "The Nigerian bank account number to transfer funds into."),
            ("squad_virtual_account_bank", "string",   "The bank name for that account (e.g. GTBank)."),
            ("va_expires_at",              "datetime", "ISO 8601 UTC. The virtual account stops accepting transfers after this time."),
            ("failure_reason",             "string",   "null unless status is failed, mismatch, or expired."),
            ("created_at",                 "datetime", "ISO 8601 UTC."),
        ]),
        sp(0.2),
        p("Payment status values:", "h3"),
        param_table([
            ("initiated", "status", False, "Virtual account created. Awaiting transfer from payer."),
            ("success",   "status", False, "Transfer confirmed. Installment marked paid. Settlement payout triggered."),
            ("mismatch",  "status", False, "Transfer received but amount did not match. Gateway will refund the payer."),
            ("expired",   "status", False, "VA window elapsed before a transfer was received."),
            ("failed",    "status", False, "Gateway or processing error. See failure_reason."),
        ], title="Payment statuses"),
        sp(0.4),

        # ── GET /payments/{payment_id} ───────────────────────────────────────
        route_header("GET", "/payments/{payment_id}", "Get payment status"), sp(0.2),
        p("Poll this endpoint after presenting the virtual account to the payer. "
          "Status transitions from <font name='Courier'>initiated</font> to a terminal "
          "state once the transfer is processed (typically within seconds of the transfer "
          "being detected, plus a brief webhook processing delay)."),
        sp(0.2),
        p("Path parameters", "h3"),
        param_table([("payment_id", "UUID", True, "The payment UUID from the POST /payments response.")]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Same fields as the 201 response above."),
        PageBreak(),
    ]


def bulk_payments_section():
    return [
        p("8. Bulk Payments", "h1"), hr(BRAND, 1), sp(0.2),
        p("Bulk payments allow a broker to collect multiple installments in a single "
          "action — one bank transfer covers all of them. Insureflow creates one "
          "virtual account for the combined total. On confirmation, every installment "
          "in the batch is marked paid, and exactly <b>one settlement payout</b> is sent "
          "to the insurer (never one per installment)."),
        sp(0.2),
        p("Maximum batch size: <b>500 installments</b> per request.", "note"),
        sp(0.3),

        # ── POST /payments/bulk ──────────────────────────────────────────────
        route_header("POST", "/payments/bulk", "Initiate a bulk payment"), sp(0.2),
        p("All installments must belong to the requesting broker and the same "
          "insurance company, and must be in <font name='Courier'>due</font> or "
          "<font name='Courier'>overdue</font> status. If any single installment "
          "fails validation the <b>entire batch is rejected</b> before any charge is made."),
        sp(0.2),
        p("Required headers", "h3"),
        param_table([
            ("Authorization",   "string", True, "Bearer &lt;broker_access_token&gt;"),
            ("Idempotency-Key", "UUID",   True, "UUID v4. Same semantics as single payments."),
        ]),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("installment_ids", "array[UUID]", True,
             "List of installment UUIDs to collect. Min 1, max 500. "
             "All must be due/overdue and owned by the requesting broker."),
        ]),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("id",                          "UUID",          "Payment batch UUID."),
            ("broker_id",                   "UUID",          "The initiating broker."),
            ("insurance_company_id",        "UUID",          "The underwriting insurer."),
            ("total_amount_kobo",           "integer",       "Sum of all installment amounts in kobo. Transfer exactly this amount."),
            ("item_count",                  "integer",       "Number of installments in this batch."),
            ("status",                      "string",        "initiated | success | mismatch | expired | failed."),
            ("squad_transaction_ref",       "string",        "Unique gateway reference for this batch."),
            ("squad_virtual_account_number","string",        "Bank account to transfer the total into."),
            ("squad_virtual_account_bank",  "string",        "Bank name."),
            ("va_expires_at",               "datetime",      "Transfer deadline (ISO 8601 UTC). Default 30 minutes from creation."),
            ("failure_reason",              "string",        "null unless failed."),
            ("created_at",                  "datetime",      "ISO 8601 UTC."),
            ("items",                       "array[object]", "Each item: {id, installment_id, amount_kobo}."),
        ]),
        sp(0.4),

        # ── GET /payments/bulk/{batch_id} ────────────────────────────────────
        route_header("GET", "/payments/bulk/{batch_id}", "Get bulk payment status"), sp(0.2),
        p("Path parameters", "h3"),
        param_table([("batch_id", "UUID", True, "The payment batch UUID.")]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Same fields as the 201 response above."),
        PageBreak(),
    ]


def reminders_section():
    return [
        p("9. Reminders", "h1"), hr(BRAND, 1), sp(0.2),
        p("Reminders notify a policyholder that an installment is due or overdue. "
          "They can be triggered by either <b>Insurance Company Admins</b> or "
          "<b>Broker Admins/Staff</b>. The installment must be in "
          "<font name='Courier'>overdue</font> status before a reminder can be sent."),
        sp(0.3),

        # ── POST /reminders ──────────────────────────────────────────────────
        route_header("POST", "/reminders", "Send a payment reminder"), sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("installment_id", "UUID", True, "UUID of the overdue installment to send a reminder for."),
        ]),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("id",             "UUID",     "Reminder UUID."),
            ("installment_id", "UUID",     "The installment this reminder is for."),
            ("broker_id",      "UUID",     "The broker associated with this installment's policy."),
            ("sent_by",        "UUID",     "UUID of the platform user who triggered this reminder."),
            ("channel",        "string",   "Delivery channel. Currently always email."),
            ("status",         "string",   "queued | sent | failed."),
            ("sent_at",        "datetime", "Timestamp of delivery. null while queued."),
            ("created_at",     "datetime", "ISO 8601 UTC."),
        ]),
        sp(0.4),

        # ── GET /reminders ───────────────────────────────────────────────────
        route_header("GET", "/reminders", "List reminders"), sp(0.2),
        p("Query parameters", "h3"),
        param_table([
            ("broker_id", "UUID", True, "Filter by broker. Broker roles can only query their own broker_id."),
        ]),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Array of reminder objects."),
        PageBreak(),
    ]


def commission_section():
    return [
        p("10. Commission Configurations", "h1"), hr(BRAND, 1), sp(0.2),
        p("The Insureflow commission model is a three-way split of each premium: "
          "a portion goes to <b>GTBank</b> (payment processing), a portion to "
          "<b>Insureflow</b> (platform fee), and an optional portion to the "
          "<b>Broker</b> (set by the insurance company per broker). "
          "The remainder after these deductions is settled to the insurer."),
        sp(0.2),
        p("All rates are in <b>basis points (bps)</b>. 1 bps = 0.01%. "
          "Example: 50 bps = 0.5%.", "note"),
        sp(0.2),
        p("Insurance Company Admins can set per-broker commission rates for brokers "
          "assigned to their company. Global and platform-level rates are managed "
          "by Insureflow operators only and are not configurable here."),
        sp(0.3),

        # ── POST /commission-configs ─────────────────────────────────────────
        route_header("POST", "/commission-configs",
                     "Set broker commission rate (Insurance Company Admin only)"), sp(0.2),
        p("Creates or updates the commission rate for a specific broker under your company. "
          "Rates are versioned — changing a rate closes the old record and inserts a new "
          "one. Historical payments always reflect the rate that was active at the time "
          "of collection; retroactive changes never occur."),
        sp(0.2),
        p("Request body", "h3"),
        param_table([
            ("scope",              "string",  True,
             'Must be <b>"broker"</b> for Insurance Company Admin calls.'),
            ("broker_id",          "UUID",    True,
             "UUID of the broker to set this rate for. Must be actively assigned to your company."),
            ("gtbank_rate_bps",    "integer", True,
             "GTBank processing fee in basis points. Range 0–10000. "
             "Consult Insureflow for the agreed platform default (currently 50 bps)."),
            ("insureflow_rate_bps","integer", True,
             "Insureflow platform fee in basis points. Range 0–10000. "
             "Consult Insureflow for the agreed platform default (currently 50 bps)."),
            ("broker_rate_bps",    "integer", False,
             "Broker commission in basis points. Range 0–10000. Optional — null means no broker commission. "
             "This amount is deducted from the insurer's settlement proceeds."),
        ]),
        sp(0.2),
        p("Example: to give a broker a 1% commission with standard platform rates:", "h3"),
        code('{ "scope": "broker", "broker_id": "...", "gtbank_rate_bps": 50, '
             '"insureflow_rate_bps": 50, "broker_rate_bps": 100 }'),
        sp(0.2),
        p("With the above config on a ₦10,000 (1,000,000 kobo) premium:", "h3"),
        param_table([
            ("GTBank fee",       "50 bps",  False, "₦50 (5,000 kobo)"),
            ("Insureflow fee",   "50 bps",  False, "₦50 (5,000 kobo)"),
            ("Broker commission","100 bps", False, "₦100 (10,000 kobo)"),
            ("Insurer receives", "remainder",False,"₦9,800 (980,000 kobo)"),
        ], title="Commission split example"),
        sp(0.2),
        p("Response — HTTP 201", "h3"),
        response_table([
            ("id",                   "UUID",     "Commission config UUID."),
            ("scope",                "string",   "broker for insurer-set rates."),
            ("insurance_company_id", "UUID",     "null for broker scope."),
            ("broker_id",            "UUID",     "The broker this rate applies to."),
            ("gtbank_rate_bps",      "integer",  "GTBank rate in basis points."),
            ("insureflow_rate_bps",  "integer",  "Insureflow rate in basis points."),
            ("broker_rate_bps",      "integer",  "Broker rate in basis points. null if not set."),
            ("effective_from",       "datetime", "When this rate became active (ISO 8601 UTC)."),
            ("effective_to",         "datetime", "When this rate was superseded. null means currently active."),
            ("created_by",           "UUID",     "UUID of the admin who set this rate."),
        ]),
        sp(0.4),

        # ── GET /commission-configs ──────────────────────────────────────────
        route_header("GET", "/commission-configs", "List commission configurations"), sp(0.2),
        p("Insurance Company Admins see all configs for their company: global rates, "
          "company-level rates, and per-broker rates for their assigned brokers. "
          "Broker roles see global rates and their own broker-scoped rates only."),
        sp(0.2),
        p("Response — HTTP 200", "h3"),
        p("Array of commission config objects, ordered newest first."),
        PageBreak(),
    ]


def integration_flow_section():
    return [
        p("11. Integration Flow", "h1"), hr(BRAND, 1), sp(0.2),
        p("The sections below describe the recommended end-to-end integration sequence "
          "for both a new insurance company and a new broker."),
        sp(0.3),

        p("A. Onboarding a new Insurance Company", "h2"),
        param_table([
            ("1", "Action", False, "POST /insurance-companies — submit application. Receive company_id."),
            ("2", "Action", False, "Wait for Insureflow approval. Activation token delivered to contact_email."),
            ("3", "Action", False, "POST /auth/activate — set admin password using the token."),
            ("4", "Action", False, "POST /auth/login — obtain Bearer token (valid 60 min)."),
            ("5", "Action", False, "POST /insurance-companies/{company_id}/settlement-account — register GTBank settlement account (6-digit NIP bank_code required)."),
            ("6", "Action", False, "POST /commission-configs — optionally set broker commission rates once brokers are assigned."),
        ], title="Insurance company setup"),
        sp(0.4),

        p("B. Onboarding a Broker", "h2"),
        param_table([
            ("1", "Action", False, "POST /brokers — broker submits application. Receive broker_id."),
            ("2", "Action", False, "Insureflow approves the broker and assigns them to your company. Activation token delivered to broker's contact_email."),
            ("3", "Action", False, "POST /auth/activate — broker sets their admin password."),
            ("4", "Action", False, "POST /auth/login — broker obtains Bearer token."),
            ("5", "Action", False, "Optionally: POST /brokers/{broker_id}/staff to provision additional staff logins."),
        ], title="Broker setup"),
        sp(0.4),

        p("C. Collecting a Premium (Single Payment)", "h2"),
        param_table([
            ("1", "Action", False, "POST /users — broker creates policyholder record."),
            ("2", "Action", False, "POST /policies — broker creates policy. 12 installments auto-generated."),
            ("3", "Action", False, "GET /policies/{policy_id}/installments — retrieve installment list; pick the due installment_id."),
            ("4", "Action", False, "POST /payments — broker initiates payment. Response contains virtual_account_number, bank, amount_kobo, and va_expires_at."),
            ("5", "Action", False, "Present the virtual account details to the policyholder (or transfer on their behalf). The EXACT amount_kobo (converted to NGN) must be sent before va_expires_at."),
            ("6", "Action", False, "Poll GET /payments/{payment_id} until status transitions from initiated to success, mismatch, expired, or failed."),
            ("7", "Action", False, "On success: installment is marked paid. Settlement payout fires automatically to the insurer's registered account."),
        ], title="Single payment flow"),
        sp(0.4),

        p("D. Collecting Multiple Premiums (Bulk Payment)", "h2"),
        param_table([
            ("1", "Action", False, "Collect the installment_ids for all due/overdue installments to pay (max 500)."),
            ("2", "Action", False, "POST /payments/bulk — one request, one virtual account returned with the combined total."),
            ("3", "Action", False, "Transfer the total_amount_kobo (as NGN) into the virtual account before va_expires_at."),
            ("4", "Action", False, "Poll GET /payments/bulk/{batch_id} for status. On success, all installments in the batch are marked paid and one settlement payout fires."),
        ], title="Bulk payment flow"),
        sp(0.4),

        p("E. Handling Payment Failures", "h2"),
        p("If a payment reaches <font name='Courier'>mismatch</font> status, the payer "
          "transferred an incorrect amount and the gateway will refund them. Initiate a new "
          "payment (new Idempotency-Key) for the correct amount."),
        sp(0.1),
        p("If a payment reaches <font name='Courier'>expired</font> status, the virtual "
          "account window elapsed without a transfer. Initiate a new payment."),
        sp(0.1),
        p("If a payment reaches <font name='Courier'>failed</font> status, check the "
          "<font name='Courier'>failure_reason</font> field. Gateway errors (HTTP 502 from "
          "our API) are transient — retry after a short delay with a new Idempotency-Key."),
        PageBreak(),
    ]


def appendix_section():
    return [
        p("Appendix A — NIP Bank Codes (Common)", "h1"), hr(BRAND, 1), sp(0.2),
        p("Use these 6-digit codes in the <font name='Courier'>bank_code</font> field of "
          "<font name='Courier'>POST /insurance-companies/{id}/settlement-account</font>. "
          "This is not an exhaustive list — contact Insureflow for the full table."),
        sp(0.3),
        param_table([
            ("000013", "GTBank",           False, "Guaranty Trust Bank Plc"),
            ("000014", "Access Bank",      False, "Access Bank Plc"),
            ("000015", "Zenith Bank",      False, "Zenith Bank Plc"),
            ("000016", "First Bank",       False, "First Bank of Nigeria Plc"),
            ("000004", "UBA",              False, "United Bank for Africa Plc"),
            ("000008", "Fidelity Bank",    False, "Fidelity Bank Plc"),
            ("000010", "Ecobank",          False, "Ecobank Nigeria Plc"),
            ("000011", "Unity Bank",       False, "Unity Bank Plc"),
            ("000023", "Citibank",         False, "Citibank Nigeria Ltd"),
            ("000026", "Taj Bank",         False, "Taj Bank Limited"),
            ("000027", "Globus Bank",      False, "Globus Bank Limited"),
            ("090267", "Kuda Bank",        False, "Kuda Microfinance Bank"),
            ("000021", "Standard Chartered",False,"Standard Chartered Bank Nigeria"),
        ], title="NIP codes"),
        sp(0.4),

        p("Appendix B — Quick Reference", "h1"), hr(BRAND, 1), sp(0.2),
        param_table([
            ("POST /auth/activate",                                 "No auth",      False, "Activate account on first login"),
            ("POST /auth/login",                                    "No auth",      False, "Obtain Bearer token"),
            ("POST /insurance-companies",                          "No auth",      False, "Submit insurer onboarding"),
            ("GET  /insurance-companies/{id}",                     "IC Admin",     False, "Get company details"),
            ("POST /insurance-companies/{id}/settlement-account",  "IC Admin",     False, "Register settlement bank account"),
            ("POST /brokers",                                      "No auth",      False, "Submit broker onboarding"),
            ("GET  /brokers/{id}",                                 "Broker",       False, "Get broker details"),
            ("POST /brokers/{id}/staff",                           "Broker Admin", False, "Create broker staff account"),
            ("POST /users",                                        "Broker",       False, "Create policyholder"),
            ("GET  /users/{id}",                                   "Broker/IC",    False, "Get policyholder"),
            ("GET  /users",                                        "Broker/IC",    False, "List policyholders"),
            ("POST /policies",                                     "Broker",       False, "Create policy (auto-generates installments)"),
            ("GET  /policies/{id}",                                "Broker/IC",    False, "Get policy"),
            ("GET  /policies",                                     "Broker/IC",    False, "List policies for a policyholder"),
            ("GET  /policies/{id}/installments",                   "Broker/IC",    False, "List installments for a policy"),
            ("GET  /installments",                                 "Broker/IC",    False, "List all installments (with optional status filter)"),
            ("POST /payments",                                     "Broker",       False, "Initiate single payment — returns virtual account"),
            ("GET  /payments/{id}",                                "Broker/IC",    False, "Get payment status"),
            ("POST /payments/bulk",                                "Broker",       False, "Initiate bulk payment (up to 500 installments)"),
            ("GET  /payments/bulk/{id}",                           "Broker/IC",    False, "Get bulk payment batch status"),
            ("POST /reminders",                                    "Broker/IC",    False, "Send overdue reminder"),
            ("GET  /reminders",                                    "Broker/IC",    False, "List reminders"),
            ("POST /commission-configs",                           "IC Admin",     False, "Set broker commission rate"),
            ("GET  /commission-configs",                           "Broker/IC",    False, "List commission configurations"),
        ], title="All endpoints"),
    ]


# ── Page header / footer callbacks ────────────────────────────────────────────

def on_page(canvas, doc):
    canvas.saveState()
    # Header bar
    canvas.setFillColor(BRAND)
    canvas.rect(doc.leftMargin, H - doc.topMargin + 0.3*cm,
                W - doc.leftMargin - doc.rightMargin, 0.25*cm, fill=1, stroke=0)
    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, doc.bottomMargin - 0.5*cm,
                      "Insureflow API Reference v1.0  |  Confidential")
    canvas.drawRightString(W - doc.rightMargin, doc.bottomMargin - 0.5*cm,
                           f"Page {doc.page}")
    canvas.restoreState()


# ── Build ─────────────────────────────────────────────────────────────────────

def build():
    doc = SimpleDocTemplate(
        str(OUT_PATH),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="Insureflow API Reference",
        author="Insureflow",
    )

    story = []
    story += cover_page()
    story += overview_section()
    story += auth_section()
    story += insurance_company_section()
    story += broker_section()
    story += policyholder_section()
    story += policy_section()
    story += installments_section()
    story += payments_section()
    story += bulk_payments_section()
    story += reminders_section()
    story += commission_section()
    story += integration_flow_section()
    story += appendix_section()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Written: {OUT_PATH}")


if __name__ == "__main__":
    build()
