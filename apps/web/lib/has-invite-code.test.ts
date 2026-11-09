import { describe, expect, it } from "vitest";
import { hasInviteCode } from "./has-invite-code";

describe("hasInviteCode", () => {
  it("is false when code is missing", () => {
    expect(hasInviteCode({})).toBe(false);
  });

  it("is false when code is empty or whitespace", () => {
    expect(hasInviteCode({ code: "" })).toBe(false);
    expect(hasInviteCode({ code: "   " })).toBe(false);
    expect(hasInviteCode({ code: ["", "  "] })).toBe(false);
  });

  it("is true when a code is present", () => {
    expect(hasInviteCode({ code: "invite-1" })).toBe(true);
    expect(hasInviteCode({ code: ["", "invite-1"] })).toBe(true);
  });
});
