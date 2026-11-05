#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DATASET_RELATIVE_PATH = path.join("datasets", "topic_and_intent_gate.json");
const RESULTS_RELATIVE_PATH = path.join("results", "intent_gate");
const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const packageDir = path.resolve(scriptDir, "..");
const datasetPath = path.join(packageDir, DATASET_RELATIVE_PATH);
const resultsDir = path.join(packageDir, RESULTS_RELATIVE_PATH);
const apiBaseUrl = (process.env.API_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/$/, "");
const intentUrl = `${apiBaseUrl}/decisions/intent`;

function formatDatetime(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
    "_",
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join("");
}

function csvEscape(value) {
  const text = value == null ? "" : String(value);
  if (/[;"\n\r]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function csvRow(fields) {
  return fields.map(csvEscape).join(";");
}

async function requestIntent(question) {
  const response = await fetch(intentUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state: question }),
  });
  const body = await response.json();
  if (!response.ok) {
    const detail = body?.detail ?? response.statusText;
    throw new Error(`HTTP ${response.status}: ${detail}`);
  }
  return body;
}

function intentAnswer(body) {
  const answer = body?.answers?.intent;
  const choice = typeof answer?.choice === "string" ? answer.choice : "";
  const confidence = typeof answer?.confidence === "number" ? answer.confidence : "";
  return { choice, confidence };
}

async function main() {
  const raw = await readFile(datasetPath, "utf8");
  const dataset = JSON.parse(raw);
  if (!Array.isArray(dataset)) {
    throw new Error(`Expected an array in ${datasetPath}`);
  }

  const rows = [
    csvRow(["question_id", "expected_choice", "actual_choice", "confidence", "match"]),
  ];

  for (const item of dataset) {
    const questionId = item.id;
    const expectedChoice = item.intent;
    let actualChoice = "";
    let confidence = "";
    let match = "";

    try {
      const body = await requestIntent(item.question);
      const answer = intentAnswer(body);
      actualChoice = answer.choice;
      confidence = answer.confidence;
      match = actualChoice !== "" && expectedChoice === actualChoice;
      console.log(
        `#${questionId} expected=${expectedChoice} actual=${actualChoice} confidence=${confidence} match=${match}`,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`#${questionId} failed: ${message}`);
    }

    rows.push(csvRow([questionId, expectedChoice, actualChoice, confidence, match]));
  }

  const filename = `result_eval_intent_gate_${formatDatetime(new Date())}.csv`;
  await mkdir(resultsDir, { recursive: true });
  const outputPath = path.join(resultsDir, filename);
  await writeFile(outputPath, `${rows.join("\n")}\n`, "utf8");
  console.log(`Wrote ${outputPath}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
