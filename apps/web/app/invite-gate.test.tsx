import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InviteGate } from "./invite-gate";

describe("InviteGate", () => {
  it("blocks the app when the invite code is missing", async () => {
    const ui = await InviteGate({
      searchParams: Promise.resolve({}),
      children: <p>secret chat</p>,
    });
    render(ui);

    expect(screen.getByRole("heading", { name: /ouch/i })).toBeInTheDocument();
    expect(screen.queryByText("secret chat")).not.toBeInTheDocument();
  });

  it("shows children when an invite code is present", async () => {
    const ui = await InviteGate({
      searchParams: Promise.resolve({ code: "invite-1" }),
      children: <p>secret chat</p>,
    });
    render(ui);

    expect(screen.getByText("secret chat")).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /ouch/i }),
    ).not.toBeInTheDocument();
  });
});
