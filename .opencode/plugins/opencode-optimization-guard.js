const ALLOWED_FILE = "rel_optimization/new_strategy.py";
const TRUTHY_VALUES = new Set(["on", "true", "1"]);
let runCounter = 0;
let baselineChangedFiles = [];

function isOptimizationEnabled() {
  const raw = process.env.OPENCODE_OPTIMIZATION;
  if (!raw) {
    return false;
  }
  return TRUTHY_VALUES.has(String(raw).toLowerCase());
}

function getOptimizationState() {
  const raw = process.env.OPENCODE_OPTIMIZATION;
  const normalized = raw ? String(raw).toLowerCase() : "";
  return {
    raw: raw ?? null,
    normalized,
    enabled: TRUTHY_VALUES.has(normalized),
  };
}


async function logEvent(client, message, extra = {}) {
  const payload = {
    service: "opencode-optimization-guard",
    message,
    extra,
  };
  if (client?.app?.log) {
    await client.app.log({
      body: {
        ...payload,
        level: "info",
      },
    });
  }
}

function summarizeToolContext(input, output) {
  const metadata = output?.metadata ?? null;
  const metadataKeys = metadata ? Object.keys(metadata) : null;
  const metadataFiles = metadata?.files;
  let metadataFilesSummary = null;
  if (Array.isArray(metadataFiles)) {
    metadataFilesSummary = {
      type: "array",
      length: metadataFiles.length,
      sample: metadataFiles.slice(0, 5),
    };
  } else if (metadataFiles !== undefined) {
    metadataFilesSummary = {
      type: typeof metadataFiles,
    };
  }
  const diffLength =
    typeof metadata?.diff === "string" ? metadata.diff.length : null;
  const attachments = Array.isArray(output?.attachments)
    ? output.attachments.map((attachment) => ({
        type: attachment?.type ?? null,
        name: attachment?.name ?? null,
        path: attachment?.path ?? null,
      }))
    : null;
  return {
    inputKeys: input ? Object.keys(input) : null,
    outputKeys: output ? Object.keys(output) : null,
    inputTool: input?.tool ?? null,
    inputArgsKeys: input?.args ? Object.keys(input.args) : null,
    inputCwd: input?.cwd ?? null,
    inputDirectory: input?.directory ?? null,
    outputCwd: output?.cwd ?? null,
    outputDirectory: output?.directory ?? null,
    outputPaths: output?.paths ?? null,
    outputFiles: output?.files ?? null,
    outputStatus: output?.status ?? null,
    outputMetadataKeys: metadataKeys,
    outputMetadataFilesSummary: metadataFilesSummary,
    outputMetadataDiffLength: diffLength,
    outputAttachments: attachments,
  };
}

function diffFiles(current, baseline) {
  const baselineSet = new Set(baseline);
  return current.filter((file) => !baselineSet.has(file));
}

async function commandOutputToText(result) {
  if (typeof result === "string") {
    return result;
  }
  if (result?.stdout !== undefined) {
    return String(result.stdout);
  }
  if (typeof result?.text === "function") {
    return await result.text();
  }
  return String(result ?? "");
}

async function getChangedFiles($) {
  const unstaged = await $`git diff --name-only`.quiet();
  const staged = await $`git diff --name-only --cached`.quiet();
  const untracked = await $`git ls-files -o --exclude-standard`.quiet();
  const unstagedText = await commandOutputToText(unstaged);
  const stagedText = await commandOutputToText(staged);
  const untrackedText = await commandOutputToText(untracked);
  const combined = `${unstagedText}\n${stagedText}\n${untrackedText}`;
  const files = combined
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
  return Array.from(new Set(files));
  }


export const OptimizationGuard = async ({ $, client }) => {
  const optimizationState = getOptimizationState();
  await logEvent(client, "plugin initialized", {
    optimization: optimizationState,
  });
  return {
    "tool.execute.before": async (input, output) => {
      const runId = ++runCounter;
      const optimization = getOptimizationState();
      await logEvent(client, "tool.execute.before entry", {
        runId,
        optimization,
        context: summarizeToolContext(input, output),
      });
      const changedFiles = await getChangedFiles($);
      baselineChangedFiles = changedFiles;
      await logEvent(client, "captured baseline for tool run", {
        runId,
        baselineCount: changedFiles.length,
        baselineFiles: changedFiles,
      });

      if (!optimization.enabled) {
        await logEvent(client, "tool.execute.before optimization disabled", {
          runId,
        });
      }
    },
    "tool.execute.after": async (input, output) => {
      const runId = runCounter;
      const optimization = getOptimizationState();
      const gitStatusResult = await $`git status --porcelain`.quiet();
      const gitDiffResult = await $`git diff --name-only`.quiet();
      const gitStatusText = (await commandOutputToText(gitStatusResult)).trim();
      const gitDiffText = (await commandOutputToText(gitDiffResult)).trim();
      await logEvent(client, "tool.execute.after git snapshot", {
        runId,
        tool: input?.tool ?? null,
        gitStatus: gitStatusText,
        gitDiff: gitDiffText,
      });
      await logEvent(client, "tool.execute.after entry", {
        runId,
        optimization,
        context: summarizeToolContext(input, output),
      });
      const changedFiles = await getChangedFiles($);
      const newlyChangedFiles = diffFiles(changedFiles, baselineChangedFiles);
      const gitDisallowed = newlyChangedFiles.filter((file) => file !== ALLOWED_FILE);

      await logEvent(client, "checked git diff after tool run", {
        runId,
        changedFiles,
        baselineChangedFiles,
        newlyChangedFiles,
        disallowed: gitDisallowed,
      });

      if (!optimization.enabled) {
        await logEvent(client, "tool.execute.after optimization disabled", {
          runId,
        });
        return;
      }

      if (gitDisallowed.length > 0) {
        await logEvent(client, "disallowed changes detected", {
          runId,
          disallowed: gitDisallowed,
        });
        throw new Error(
          `OPENCODE_OPTIMIZATION is enabled. Only ${ALLOWED_FILE} may be edited. ` +
            `Disallowed new changes detected: ${gitDisallowed.join(", ")}`
        );
      }
    },
  };
};
