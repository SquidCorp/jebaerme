import { describe, expect, it } from "vitest";
import { gatewayErrorMessage } from "@/lib/gateway-error";

describe("gatewayErrorMessage", () => {
  it("reads a string error field", () => {
    expect(gatewayErrorMessage({ error: "upstream_error" }, "fallback")).toBe(
      "upstream_error",
    );
  });

  it("uses the fallback when the payload has no string error", () => {
    expect(gatewayErrorMessage({ error: 502 }, "fallback")).toBe("fallback");
    expect(gatewayErrorMessage(null, "fallback")).toBe("fallback");
    expect(gatewayErrorMessage("nope", "fallback")).toBe("fallback");
  });
});
