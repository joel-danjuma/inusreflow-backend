StateDiff from frontend. Use via `window.Insureflow.StateDiff` (bundle loaded from the root `_ds_bundle.js`).

Shallow key-by-key diff -- these are shallow state snapshots (status
fields, ids, amounts), not deep objects, so a recursive diff library
would be overkill. Shows only keys that changed or were added/removed.
