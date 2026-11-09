import type { ReactNode } from "react";
import { hasInviteCode } from "@/lib/has-invite-code";
import { AccessDenied } from "./access-denied";

type InviteGateProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
  children: ReactNode;
};

export async function InviteGate({ searchParams, children }: InviteGateProps) {
  const params = await searchParams;
  if (!hasInviteCode(params)) {
    return <AccessDenied />;
  }
  return children;
}
