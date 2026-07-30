import { ImageResponse } from "next/og";

export const alt = "Insureflow — premium collection and settlement, reconciled";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 96px",
          background: "#112231",
        }}
      >
        <div style={{ display: "flex", fontSize: 72, fontWeight: 700, color: "#ffffff" }}>
          <span>Insure</span>
          <span style={{ color: "#F97316" }}>flow</span>
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 28,
            fontSize: 32,
            color: "rgba(255, 255, 255, 0.7)",
            maxWidth: 820,
          }}
        >
          Premium collection &amp; settlement, reconciled.
        </div>
      </div>
    ),
    { ...size }
  );
}
