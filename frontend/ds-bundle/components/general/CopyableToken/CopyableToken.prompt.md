CopyableToken from frontend. Use via `window.Insureflow.CopyableToken` (bundle loaded from the root `_ds_bundle.js`).

There's no email infra in this backend -- activation tokens are returned
once in the API response and never re-shown, so the admin/broker-admin
performing the approval/staff-creation action must copy it manually.
