export function gatewayErrorMessage(
  payload: unknown,
  fallback: string,
): string {
  if (typeof payload === "object" && payload !== null && "error" in payload) {
    const error = payload.error;
    if (typeof error === "string") {
      return error;
    }
  }
  return fallback;
}
