import { proxyPythonGet } from "@/lib/python";

export async function GET() {
  return proxyPythonGet("/health");
}
