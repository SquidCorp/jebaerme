import type { Metadata } from "next";

import "./globals.scss";

export const metadata: Metadata = {
  title: "Jeremy Baer | Portfolio",
  description: "Chat with my virtual clone",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
