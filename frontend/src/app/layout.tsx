import type {
  Metadata,
} from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "SearchIntel AI",
  description:
    "SEO, GEO, AEO and AI search visibility intelligence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
