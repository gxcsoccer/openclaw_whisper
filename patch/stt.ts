/**
 * Local speech-to-text via whisper.cpp STT service.
 *
 * Expects the openclaw_whisper server running at STT_SERVER_URL (default http://127.0.0.1:8765).
 */

import { readFile } from "node:fs/promises";
import { basename } from "node:path";

const STT_SERVER_URL = process.env.STT_SERVER_URL ?? "http://127.0.0.1:8765";

export async function transcribeAudio(
  filePath: string,
  log?: (msg: string) => void,
): Promise<string> {
  const fileBuffer = await readFile(filePath);
  const fileName = basename(filePath);

  const formData = new FormData();
  formData.append("file", new Blob([fileBuffer]), fileName);

  const url = `${STT_SERVER_URL}/transcribe`;
  log?.(`stt: sending ${fileName} (${fileBuffer.length} bytes) to ${url}`);

  const resp = await fetch(url, {
    method: "POST",
    body: formData,
    signal: AbortSignal.timeout(120_000),
  });

  if (!resp.ok) {
    const body = await resp.text().catch(() => "");
    throw new Error(`STT server returned ${resp.status}: ${body.slice(0, 200)}`);
  }

  const data = (await resp.json()) as { text?: string };
  const text = data.text?.trim() ?? "";
  log?.(`stt: transcription (${text.length} chars): ${text.slice(0, 100)}`);
  return text;
}
