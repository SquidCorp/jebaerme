import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AccessDenied } from "./access-denied";

describe("AccessDenied", () => {
  it("explains that access is invite-only", () => {
    render(<AccessDenied />);

    expect(screen.getByRole("heading", { name: /ouch/i })).toBeInTheDocument();
    expect(screen.getByText(/this clone is invite-only/i)).toBeInTheDocument();
    expect(
      screen.getByText(/open the invitation link you were sent/i),
    ).toBeInTheDocument();
  });
});
