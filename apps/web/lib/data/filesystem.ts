import { access, readFile } from "node:fs/promises";
import { accessSync, constants as fsConstants } from "node:fs";
import path from "node:path";

export type LoadState<T> =
  | {
      status: "ready";
      data: T;
    }
  | {
      status: "missing";
      message: string;
    };

export function resolveProjectRoot(): string {
  const envRoot = process.env.RIDEFARE_PROJECT_ROOT;
  if (envRoot) {
    return envRoot;
  }

  const candidates = [process.cwd(), path.resolve(process.cwd(), "..", "..")];
  for (const candidate of candidates) {
    const processedDir = path.join(candidate, "data", "processed");
    try {
      accessSync(processedDir, fsConstants.F_OK);
      return candidate;
    } catch {
      continue;
    }
  }

  return process.cwd();
}

export async function fileExists(filePath: string): Promise<boolean> {
  try {
    await access(filePath, fsConstants.F_OK);
    return true;
  } catch {
    return false;
  }
}

export async function readJsonFile<T>(filePath: string): Promise<T> {
  const raw = await readFile(filePath, "utf-8");
  return JSON.parse(raw) as T;
}
