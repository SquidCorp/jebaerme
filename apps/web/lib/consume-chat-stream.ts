import { gatewayErrorMessage } from "@/lib/gateway-error";

export async function consumeChatStream(
  response: Response,
  onPiece: (piece: string) => void,
): Promise<void> {
  if (!response.ok) {
    const payload: unknown = await response.json();
    throw new Error(
      gatewayErrorMessage(payload, `Gateway returned ${response.status}`),
    );
  }
  if (!response.body) {
    throw new Error("Gateway returned an empty stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    const piece = done
      ? decoder.decode()
      : decoder.decode(value, { stream: true });
    if (piece) {
      onPiece(piece);
    }
    if (done) {
      break;
    }
  }
}
