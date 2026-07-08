import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
let artifactTool;
try {
  artifactTool = await import("@oai/artifact-tool");
} catch (error) {
  if (!process.env.ARTIFACT_TOOL_PATH) {
    throw error;
  }
  artifactTool = await import(process.env.ARTIFACT_TOOL_PATH);
}
const { SpreadsheetFile, Workbook } = artifactTool;

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(scriptDir, "../..");
const inputPath = path.join(scriptDir, "device_selector_dataset_expected_fidelity.json");
const outputDir = path.join(root, "output/spreadsheets");
const outputPath = path.join(outputDir, "MQT_device_selector_dataset_expected_fidelity.xlsx");

const coreFeatureNames = [
  "num_qubits",
  "depth",
  "program_communication",
  "critical_depth",
  "entanglement_ratio",
  "parallelism",
  "liveness",
];

function colName(indexZeroBased) {
  let n = indexZeroBased + 1;
  let s = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    s = String.fromCharCode(65 + rem) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function featureDescription(name) {
  if (name.startsWith("gate_count_")) {
    return {
      group: "Gate count",
      description: `Conteggio del gate OpenQASM '${name.replace("gate_count_", "")}' nel circuito sorgente.`,
    };
  }
  const descriptions = {
    num_qubits: ["Basic circuit size", "Numero di qubit logici del circuito sorgente."],
    depth: ["Basic circuit size", "Profondita' del circuito sorgente prima della compilazione hardware-specific."],
    program_communication: ["Structural feature", "Misura SupermarQ legata alle interazioni/comunicazioni tra qubit."],
    critical_depth: ["Structural feature", "Frazione di gate a due qubit sul percorso critico; valori alti indicano maggiore sequenzialita'."],
    entanglement_ratio: ["Structural feature", "Rapporto tra operazioni entangling/a due qubit e operazioni totali."],
    parallelism: ["Structural feature", "Misura della possibilita' di eseguire operazioni in parallelo."],
    liveness: ["Structural feature", "Frazione della matrice qubit-tempo in cui i qubit sono attivi."],
  };
  const [group, description] = descriptions[name] ?? ["Other", ""];
  return { group, description };
}

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
await fs.mkdir(outputDir, { recursive: true });

const labelNames = Object.keys(payload.label_distribution ?? {});
const candidateSummary =
  labelNames.length === 1
    ? `In questo dataset locale c'e' un solo device candidato, quindi tutte le label sono ${labelNames[0]}.`
    : `In questo dataset locale ci sono ${labelNames.length} device candidati: ${labelNames.join(", ")}.`;

const gateFeatureNames = payload.feature_names.filter((feature) => feature.startsWith("gate_count_"));
const orderedCoreFeatureNames = coreFeatureNames.filter((feature) =>
  payload.feature_names.includes(feature),
);
const otherFeatureNames = payload.feature_names.filter(
  (feature) => !orderedCoreFeatureNames.includes(feature) && !gateFeatureNames.includes(feature),
);
const datasetFeatureNames = [...orderedCoreFeatureNames, ...otherFeatureNames, ...gateFeatureNames];

const wb = Workbook.create();
const dataset = wb.worksheets.add("Dataset");
const xmatrix = wb.worksheets.add("X Matrix");
const legend = wb.worksheets.add("Feature Legend");
const summary = wb.worksheets.add("Summary");

dataset.showGridLines = false;
xmatrix.showGridLines = false;
legend.showGridLines = false;
summary.showGridLines = false;

const idHeaders = [
  "index",
  "name",
  "label_device",
  "score",
];
const headers = [...idHeaders, ...datasetFeatureNames];
const rows = payload.rows.map((row) => [
  row.index,
  row.name,
  row.label_device,
  row.score_values[0] ?? null,
  ...datasetFeatureNames.map((feature) => row.features[feature]),
]);

dataset.getRangeByIndexes(0, 0, 1, headers.length).values = [headers];
dataset.getRangeByIndexes(1, 0, rows.length, headers.length).values = rows;

const lastCol = colName(headers.length - 1);
const lastRow = rows.length + 1;
dataset.tables.add(`A1:${lastCol}${lastRow}`, true, "DeviceSelectorDataset");
dataset.freezePanes.freezeRows(1);
dataset.freezePanes.freezeColumns(2);

dataset.getRange(`A1:${lastCol}1`).format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
  borders: { preset: "all", style: "thin", color: "#D9E2F3" },
};
dataset.getRange(`A2:${lastCol}${lastRow}`).format = {
  borders: { preset: "inside", style: "thin", color: "#E7EAF0" },
};
dataset.getRange("A:A").format.columnWidth = 8;
dataset.getRange("B:B").format.columnWidth = 16;
dataset.getRange("C:C").format.columnWidth = 20;
dataset.getRange("D:D").format.columnWidth = 16;
dataset.getRange("E:F").format.columnWidth = 18;
dataset.getRange(`G:${lastCol}`).format.columnWidth = 14;
dataset.getRange(`D2:D${lastRow}`).format.numberFormat = "0.0000000000";
dataset.getRange(`E2:F${lastRow}`).format.numberFormat = "0";
dataset.getRange(`G2:K${lastRow}`).format.numberFormat = "0.000000";
if (gateFeatureNames.length > 0) {
  const gateStartCol = colName(idHeaders.length + orderedCoreFeatureNames.length + otherFeatureNames.length);
  dataset.getRange(`${gateStartCol}2:${lastCol}${lastRow}`).format.numberFormat = "0";
}
dataset.getRange(`A1:${lastCol}${lastRow}`).format.font = { name: "Calibri", size: 10 };

const xHeaders = ["name", ...payload.feature_names];
const xRows = payload.rows.map((row) => [
  row.name,
  ...payload.feature_names.map((feature) => row.features[feature]),
]);
const xLastCol = colName(xHeaders.length - 1);
const xLastRow = xRows.length + 1;
xmatrix.getRangeByIndexes(0, 0, 1, xHeaders.length).values = [xHeaders];
xmatrix.getRangeByIndexes(1, 0, xRows.length, xHeaders.length).values = xRows;
xmatrix.tables.add(`A1:${xLastCol}${xLastRow}`, true, "XMatrix");
xmatrix.freezePanes.freezeRows(1);
xmatrix.freezePanes.freezeColumns(1);
xmatrix.getRange(`A1:${xLastCol}1`).format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
  borders: { preset: "all", style: "thin", color: "#D9E2F3" },
};
xmatrix.getRange(`A2:${xLastCol}${xLastRow}`).format = {
  borders: { preset: "inside", style: "thin", color: "#E7EAF0" },
};
xmatrix.getRange("A:A").format.columnWidth = 16;
xmatrix.getRange(`B:${xLastCol}`).format.columnWidth = 14;
if (payload.feature_names.length > 0) {
  xmatrix.getRange(`B2:${xLastCol}${xLastRow}`).format.numberFormat = "0.000000";
}
if (gateFeatureNames.length > 0) {
  const xGateEndCol = colName(gateFeatureNames.length);
  xmatrix.getRange(`B2:${xGateEndCol}${xLastRow}`).format.numberFormat = "0";
}
for (const featureName of ["num_qubits", "depth"]) {
  const featureIndex = payload.feature_names.indexOf(featureName);
  if (featureIndex >= 0) {
    const col = colName(featureIndex + 1);
    xmatrix.getRange(`${col}2:${col}${xLastRow}`).format.numberFormat = "0";
  }
}
xmatrix.getRange(`A1:${xLastCol}${xLastRow}`).format.font = { name: "Calibri", size: 10 };

const legendHeaders = ["feature_name", "group", "description"];
const legendRows = payload.feature_names.map((feature) => {
  const info = featureDescription(feature);
  return [feature, info.group, info.description];
});
legend.getRange("A1:C1").values = [legendHeaders];
legend.getRangeByIndexes(1, 0, legendRows.length, 3).values = legendRows;
legend.tables.add(`A1:C${legendRows.length + 1}`, true, "FeatureLegend");
legend.freezePanes.freezeRows(1);
legend.getRange("A1:C1").format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
};
legend.getRange(`A2:C${legendRows.length + 1}`).format = {
  borders: { preset: "inside", style: "thin", color: "#E7EAF0" },
  wrapText: true,
};
legend.getRange("A:A").format.columnWidth = 28;
legend.getRange("B:B").format.columnWidth = 22;
legend.getRange("C:C").format.columnWidth = 80;
legend.getRange(`A1:C${legendRows.length + 1}`).format.font = { name: "Calibri", size: 10 };

const summaryRows = [
  ["Campo", "Valore"],
  ["Metrica", payload.metric],
  ["Numero campioni", payload.sample_count],
  ["Numero feature in X", payload.feature_count],
  ["Foglio X Matrix", "Contiene nome circuito + tutte le 49 colonne della matrice X."],
  ["File sorgente", "training_data_expected_fidelity.npy + names_list + scores_list"],
  ["Interpretazione X", "Feature vector del circuito target-independent, non del circuito compilato."],
  ["Interpretazione y", "Device migliore secondo lo score della figure of merit."],
  ["Nota smoke test", candidateSummary],
  ["Distribuzione label", JSON.stringify(payload.label_distribution)],
];
summary.getRangeByIndexes(0, 0, summaryRows.length, 2).values = summaryRows;
summary.getRange("A1:B1").format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
};
summary.getRange(`A2:A${summaryRows.length}`).format = {
  fill: "#F2F6FA",
  font: { bold: true },
};
summary.getRange(`A1:B${summaryRows.length}`).format = {
  borders: { preset: "all", style: "thin", color: "#D9E2F3" },
  wrapText: true,
};
summary.getRange("A:A").format.columnWidth = 24;
summary.getRange("B:B").format.columnWidth = 88;
summary.getRange(`A1:B${summaryRows.length}`).format.font = { name: "Calibri", size: 10 };

const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(outputPath);
await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
console.log(outputPath);




