#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const TOPIC_NOUL_THRESHOLD = 0.75;
const DATASET_RELATIVE_PATH = path.join("datasets", "topic_and_intent_gate.json");
const RESULTS_RELATIVE_PATH = path.join("results", "topic_gate");
const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const packageDir = path.resolve(scriptDir, "..");
const datasetPath = path.join(packageDir, DATASET_RELATIVE_PATH);
const resultsDir = path.join(packageDir, RESULTS_RELATIVE_PATH);
const apiBaseUrl = (process.env.API_BASE_URL ?? DEFAULT_BASE_URL).replace(/\/$/, "");
const topicUrl = `${apiBaseUrl}/decisions/topic`;

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

function isTopicAllowed(noul) {
  return typeof noul === "number" && noul >= TOPIC_NOUL_THRESHOLD;
}

async function requestTopic(question) {
  const response = await fetch(topicUrl, {
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

function filterOutScore(body) {
  const noul = body?.answers?.filter_out?.noul;
  return typeof noul === "number" ? noul : "";
}

async function main() {
  const raw = await readFile(datasetPath, "utf8");
  const dataset = JSON.parse(raw);
  if (!Array.isArray(dataset)) {
    throw new Error(`Expected an array in ${datasetPath}`);
  }

  const rows = [csvRow(["question_id", "expected_output", "actual_output", "filter_out_score"])];

  for (const item of dataset) {
    const questionId = item.id;
    const expectedOutput = item.allowed;
    let actualOutput = "";
    let score = "";

    try {
      const body = await requestTopic(item.question);
      score = filterOutScore(body);
      actualOutput = score === "" ? "" : isTopicAllowed(score);
      console.log(
        `#${questionId} expected=${expectedOutput} actual=${actualOutput} score=${score}`,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`#${questionId} failed: ${message}`);
    }

    rows.push(csvRow([questionId, expectedOutput, actualOutput, score]));
  }

  const filename = `result_eval_topic_gate_${formatDatetime(new Date())}.csv`;
  await mkdir(resultsDir, { recursive: true });
  const outputPath = path.join(resultsDir, filename);
  await writeFile(outputPath, `${rows.join("\n")}\n`, "utf8");
  console.log(`Wrote ${outputPath}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
