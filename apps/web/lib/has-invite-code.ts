function isPresent(value: string): boolean {
  return value.trim().length > 0;
}

export function hasInviteCode(
  searchParams: Record<string, string | string[] | undefined>,
): boolean {
  const code = searchParams.code;
  if (typeof code === "string") {
    return isPresent(code);
  }
  if (Array.isArray(code)) {
    return code.some(isPresent);
  }
  return false;
}
