module.exports = {
  extends: ["@commitlint/config-conventional"],
  parserPreset: {
    parserOpts: {
      headerPattern:
        /^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert): (ANI-\d+) (.+)$/,
      headerCorrespondence: ["type", "jiraTask", "subject"],
    },
  },
  rules: {
    "animus-header-format": [2, "always"],
    "header-max-length": [2, "always", 100],
    "type-enum": [
      2,
      "always",
      [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
        "revert",
      ],
    ],
    "subject-empty": [2, "never"],
    "type-empty": [2, "never"],
  },
  plugins: [
    {
      rules: {
        "animus-header-format": (parsed) => {
          const header = parsed.header || "";
          const isValid = /^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert): ANI-\d+ .+$/.test(
            header,
          );

          return [
            isValid,
            'commit message must follow "type: ANI-123 description"',
          ];
        },
        "jira-task-required": (parsed) => {
          const jiraTask = parsed.jiraTask || "";
          const isValid = /^ANI-\d+$/.test(jiraTask);

          return [
            isValid,
            'commit message must include a Jira task id in the format "ANI-123"',
          ];
        },
      },
    },
  ],
  ignores: [(message) => message.startsWith("Merge ")],
  defaultIgnores: true,
};
