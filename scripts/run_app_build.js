const { spawnSync } = require("node:child_process");

const env = { ...process.env };
env.NEXT_PUBLIC_SUPABASE_URL =
  env.NEXT_PUBLIC_SUPABASE_URL || "https://ziyjzprjlefidadtqfnx.supabase.co";
env.NEXT_PUBLIC_SUPABASE_ANON_KEY =
  env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "sb_publishable_PAZnGLd4Eo9hwbpUaVYqWA_Q0ZsB-of";

const result = spawnSync("npm", ["--prefix", "app", "run", "build"], {
  stdio: "inherit",
  env,
});

process.exit(result.status ?? 1);

