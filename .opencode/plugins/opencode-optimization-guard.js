const ALLOWED_FILE = "rel_optimization/new_strategy.py";
const TRUTHY_VALUES = new Set(["on", "true", "1"]);
let baselineFiles = new Set();

function isOptimizationEnabled() {
  const raw = process.env.OPENCODE_OPTIMIZATION;
  if (!raw) {
    return false;
  }
  return TRUTHY_VALUES.has(String(raw).toLowerCase());
}

async function getChangedFiles($) {
  const unstaged = await $`git diff --name-only`;
  const staged = await $`git diff --name-only --cached`;
  const combined = `${unstaged.toString()}\n${staged.toString()}`;
  return combined
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

export const OptimizationGuard = async ({ $ }) => {
  return {
    "tool.execute.before": async () => {
      if (!isOptimizationEnabled()) {
        return;
      }

      const changedFiles = await getChangedFiles($);
      baselineFiles = new Set(changedFiles);
    },
    "tool.execute.after": async () => {
      if (!isOptimizationEnabled()) {
        return;
      }

      const changedFiles = await getChangedFiles($);
      const newlyChanged = changedFiles.filter((file) => !baselineFiles.has(file));
      const disallowed = newlyChanged.filter((file) => file !== ALLOWED_FILE);

      if (disallowed.length > 0) {
        throw new Error(
          `OPENCODE_OPTIMIZATION is enabled. Only ${ALLOWED_FILE} may be edited. ` +
            `Disallowed new changes detected: ${disallowed.join(", ")}`
        );
      }
    },
  };
};
